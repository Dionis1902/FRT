import asyncio
from base64 import urlsafe_b64encode

from pyrogram import Client, handlers, raw
from pyrogram.errors import BadRequest, SessionPasswordNeeded, FloodWait
from pyrogram.session import Auth, Session

from add_accounts.base import AddAccount
from config import __version__
from db.utils import save_account
from settings import Settings
from web.connection_manager import ConnectionManager
from web.utils import pack_session_string
from utils import proxy_to_dict


class ByQrCode(AddAccount):
    def __init__(self, tab_id):
        super().__init__(tab_id)
        self._client = None
        self._nearest = None
        self._task = None
        self._hint = None

    @ConnectionManager.handler('close_qr_code', lambda: AddAccount._INSTANCE)
    async def _on_close(self):
        if self:
            await self._on_disconnect()

    async def _on_disconnect(self):
        if self._task:
            self._task.cancel()
            self._task = None

    async def _get_qr_code(self, token):
        token = urlsafe_b64encode(token).decode('utf8')
        await self._manager.send_data(qrcode_login=f'tg://login?token={token}')

    async def _login(self, r):
        if isinstance(r, raw.types.auth.LoginTokenSuccess):
            self._client.me = await self._client.get_me()
            status, account_data = await save_account(self._client, pack_session_string(await self._client.storage.dc_id(),
                                                                                        await self._client.storage.api_id(),
                                                                                        await self._client.storage.test_mode(),
                                                                                        await self._client.storage.auth_key(),
                                                                                        self._client.me.id,
                                                                                        await self._client.storage.is_bot()))
            await self._manager.alert(['Updated already saved account', 'Success add to db'][status], ['warning', 'success'][status])
            await self._manager.broadcast(add_new_user=account_data)
            await self._on_disconnect()

        elif isinstance(r, raw.types.auth.LoginTokenMigrateTo):
            await self._check_session(dc_id=r.dc_id)
            await self._generate_qr_code()

    @ConnectionManager.handler('password_qr_code', lambda: AddAccount._INSTANCE)
    async def _enter_password(self, password):
        if not self:
            return
        try:
            await self._client.check_password(password)
        except BadRequest:
            await self._manager.send_data(ask_password=dict(hint=self._hint, to_qr_code=True))
            return
        try:
            r = await self._client.invoke(
                raw.functions.auth.ExportLoginToken(
                    api_id=self._api_id, api_hash=self._api_hash, except_ids=[]
                )
            )
            await self._login(r)
        except FloodWait as e:
            await self._manager.alert(f'A wait of {e.value} seconds is required', 'danger')
            await self._on_disconnect()

    async def _raw_handler(self, client: Client, update: raw.base.Update, *_, **__):
        if isinstance(update, raw.types.auth.LoginToken) and self._nearest.nearest_dc != await client.storage.dc_id():
            await self._check_session(dc_id=self._nearest.nearest_dc)
        if isinstance(update, raw.types.UpdateLoginToken):
            try:
                r = await client.invoke(
                    raw.functions.auth.ExportLoginToken(
                        api_id=self._api_id, api_hash=self._api_hash, except_ids=[]
                    )
                )
                await self._login(r)
            except (SessionPasswordNeeded,):
                self._hint = await self._client.get_password_hint()
                await self._manager.send_data(ask_password=dict(hint=self._hint, to_qr_code=True))
            except FloodWait as e:
                await self._manager.alert(f'A wait of {e.value} seconds is required', 'danger')
                await self._on_disconnect()

    async def _check_session(self, dc_id: int):
        await self._client.session.stop()
        await self._client.storage.dc_id(dc_id)
        await self._client.storage.auth_key(
            await Auth(
                self._client, await self._client.storage.dc_id(),
                await self._client.storage.test_mode()
            ).create()
        )
        self._client.session = Session(
            self._client, await self._client.storage.dc_id(),
            await self._client.storage.auth_key(), await self._client.storage.test_mode()
        )
        return await self._client.session.start()

    async def _generate_qr_code(self):
        try:
            r = await self._client.invoke(
                raw.functions.auth.ExportLoginToken(
                    api_id=self._api_id, api_hash=self._api_hash, except_ids=[]
                )
            )
            if isinstance(r, raw.types.auth.LoginToken):
                await self._get_qr_code(r.token)
                await asyncio.sleep(30)
        except FloodWait as e:
            await self._manager.alert(f'A wait of {e.value} seconds is required', 'danger')
            await self._on_disconnect()

    async def _create_qrcodes(self):
        if not self._client.is_initialized:
            await self._client.dispatcher.start()
            self._client.is_initialized = True
        while True:
            await self._generate_qr_code()

    async def start(self):
        await self._manager.broadcast(lock_buttons=True)
        await self._manager.alert('Wait to qr code')
        self._client = Client('by_qr_code', api_id=self._api_id, api_hash=self._api_hash, proxy=proxy_to_dict(Settings.get('proxy')),
                              in_memory=True, app_version=f'FRT {__version__}', device_model='FRT')
        await self._client.connect()
        self._nearest = await self._client.invoke(raw.functions.help.GetNearestDc())

        self._client.add_handler(
            handlers.RawUpdateHandler(
                self._raw_handler
            )
        )

        await self._check_session(self._nearest.nearest_dc)
        try:
            self._task = asyncio.create_task(self._create_qrcodes())
            await self._task
        finally:
            await self._manager.send_data(close_qr_code=None)
            await self._client.stop()
            await self._end()
