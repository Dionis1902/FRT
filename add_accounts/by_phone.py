import asyncio
from pyrogram.enums import SentCodeType
from pyrogram.errors import PhoneNumberInvalid, PhoneNumberBanned, FloodWait, BadRequest, SessionPasswordNeeded
from pyrogram.types import User, TermsOfService

from add_accounts.base import AddAccount
from add_accounts.custom_client import CustomClient
from config import __version__
from db import database
from db.models import accounts
from db.utils import save_account
from settings import Settings
from web.connection_manager import ConnectionManager
from web.utils import get_first_name, get_last_name
from utils import get_hash
from utils import proxy_to_dict


sent_code_descriptions = {
    SentCodeType.APP: 'Telegram app',
    SentCodeType.SMS: 'SMS',
    SentCodeType.CALL: 'phone call',
    SentCodeType.FLASH_CALL: 'phone flash call'
}


class ByPhone(AddAccount):
    def __init__(self, tab_id):
        super().__init__(tab_id)
        self._client = None
        self._phone_number = None
        self._code = None
        self._tasks = {}
        self._is_logged = False
        self._hit = None

    async def _resend_code(self):
        await asyncio.sleep(181)
        self._code = await self._client.resend_code(self._phone_number, self._code.phone_code_hash)
        await self._manager.alert('Sms code resend', 'primary')

    @ConnectionManager.handler('close_phone_add', lambda: AddAccount._INSTANCE)
    async def _close(self):
        if not self:
            return
        await self._on_disconnect()

    async def _on_disconnect(self):
        if self._is_logged:
            return
        [task.cancel() for task in self._tasks.values()]
        if self._client and self._client.is_connected and not self._client.is_initialized:
            await self._client.disconnect()
        await self._end()

    async def _stop(self, message, message_type):
        [task.cancel() for task in self._tasks.values()]
        if self._client and self._client.is_connected and not self._client.is_initialized:
            await self._client.disconnect()
        await self._manager.alert(message, message_type)
        await self._end()

    async def _save(self):
        try:
            await self._client.start_after_connect()
        except (Exception,):
            await self._stop('Some error', 'danger')
            return
        status, account_data = await save_account(self._client)
        await self._client.stop()
        await self._stop(['Updated already saved account', 'Success add to db'][status], ['warning', 'success'][status])
        await self._manager.broadcast(add_new_user=account_data)

    async def start(self, phone_number):
        await self._manager.broadcast(lock_buttons=True)
        query = accounts.select().where(accounts.c.phone_number == phone_number)
        if await database.fetch_one(query):
            await self._stop(f'Phone +{phone_number} already in database', 'warning')
            return

        self._client = CustomClient('by_phone', api_id=self._api_id, api_hash=self._api_hash,
                                    in_memory=True, proxy=proxy_to_dict(Settings.get('proxy')), app_version=f'FRT {__version__}', device_model='FRT')
        self._phone_number = phone_number

        try:
            await self._client.connect()
        except (Exception,):
            await self._stop('Some problems with telegram servers', 'danger')
            return

        try:
            code = await self._client.send_code(phone_number)
            if code.type != SentCodeType.APP:
                self._tasks['_resend_code'] = asyncio.create_task(self._resend_code())
        except (PhoneNumberInvalid, PhoneNumberBanned) as e:
            await self._stop(e.__doc__, 'danger')
            return
        except FloodWait as e:
            await self._stop(f'A wait of {e.value} seconds is required', 'danger')
            return

        self._code = code
        await self._manager.send_data(ask_code=f'The confirmation code has been sent via {sent_code_descriptions[code.type]}')

    @staticmethod
    def _store_task(func):
        async def wrapper(self, *args, **kwargs):
            if self._client is None or not self._client.is_connected:
                return
            self._tasks[func.__name__] = asyncio.create_task(func(self, *args, **kwargs))
            await self._tasks[func.__name__]
            self._tasks.pop(func.__name__, None)

        return wrapper

    @ConnectionManager.handler('code', lambda: AddAccount._INSTANCE)
    @_store_task
    async def _enter_code(self, code):
        if not self:
            return
        try:
            user = await self._client.sign_in(self._phone_number, self._code.phone_code_hash, code)
            self._is_logged = True
            if not isinstance(user, User):
                await asyncio.sleep(3)
                user = await self._client.sign_up(self._phone_number, self._code.phone_code_hash,
                                                  get_first_name(), get_last_name() if Settings.get('use_last_name', True) else None)
                if Settings.get('use_password', True):
                    await self._client.enable_cloud_password(get_hash(self._phone_number + Settings.get('hash_password', ''))[:6],
                                                             hint='Default password')
                if isinstance(user, TermsOfService):
                    await self._client.accept_terms_of_service(user.id)
            await self._save()
        except BadRequest:
            await self._manager.alert('Invalid code', 'warning')
            await self._manager.send_data(ask_code=f'The confirmation code has been sent via {sent_code_descriptions[self._code.type]}')
        except SessionPasswordNeeded:
            self._hint = await self._client.get_password_hint()
            if self._hint == 'Default password':
                try:
                    await self._client.check_password(get_hash(self._phone_number + Settings.get('hash_password', ''))[:6])
                    self._is_logged = True
                    await self._save()
                    return
                except BadRequest:
                    pass
            await self._manager.send_data(ask_password=dict(hint=self._hint))

    @ConnectionManager.handler('password', lambda: AddAccount._INSTANCE)
    @_store_task
    async def _enter_password(self, password):
        if not self:
            return
        try:
            await self._client.check_password(password)
            self._is_logged = True
            await self._save()
        except BadRequest:
            await self._manager.alert('Invalid password', 'warning')
            await self._manager.send_data(ask_password=dict(hint=self._hint))
