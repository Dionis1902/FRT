import base64
import struct

from pyrogram.errors import UserDeactivatedBan, UserDeactivated
from pyrogram.storage import Storage

from add_accounts.base import AddAccount
from add_accounts.custom_client import CustomClient
from config import __version__
from db import database
from db.models import accounts
from db.utils import save_account, delete_account
from settings import Settings
from web.utils import bytes_to_session_string, tdata_to_session_string
from utils import proxy_to_dict, is_zip, is_sqlite


class BySession(AddAccount):
    async def _login_by_session_string(self, session_string):
        client = CustomClient('by_session_string', api_id=self._api_id, api_hash=self._api_hash,
                              session_string=session_string, proxy=proxy_to_dict(Settings.get('proxy')),
                              app_version=f'FRT {__version__}', device_model='FRT')
        await client.start()
        status, user_id = await save_account(client, session_string)
        await client.stop()
        return status, user_id

    async def _single_session_string(self, session_string):
        try:
            status, user_id = await self._login_by_session_string(session_string)
        except (UserDeactivatedBan, UserDeactivated) as e:
            await self._manager.alert(e.__doc__, 'danger')
            return
        except (Exception,):
            await self._manager.alert('Some problems with this session string', 'danger')
            return

        await self._manager.alert(['Updated already saved account', 'Success add to db'][status], ['warning', 'success'][status])
        await self._manager.broadcast(add_new_user=user_id)

    async def _multiply_session_string(self, session_strings):
        AddAccount._PROGRESS = {'total_count': len(session_strings), 'success_added': 0, 'already_added': 0, 'error_added': 0}

        await self._manager.broadcast(update_or_create_progress=AddAccount._PROGRESS)
        for session_string in session_strings:
            try:
                status, account_data = await self._login_by_session_string(session_string)
            except (Exception,):
                AddAccount._PROGRESS['error_added'] += 1
                if account := await database.fetch_one(accounts.select().where(accounts.c.session_string == session_string)):
                    await delete_account(account)
                continue
            else:
                if status:
                    AddAccount._PROGRESS['success_added'] += 1
                else:
                    AddAccount._PROGRESS['already_added'] += 1
                await self._manager.broadcast(add_new_user=account_data)
            finally:
                await self._manager.broadcast(update_or_create_progress=AddAccount._PROGRESS)

        if AddAccount._PROGRESS['success_added']:
            await self._manager.alert(f'Success added {AddAccount._PROGRESS["success_added"]} accounts')
        else:
            await self._manager.alert('No account added', 'warning')
        AddAccount._PROGRESS = {'total_count': 0, 'success_added': 0, 'already_added': 0, 'error_added': 0}
        await self._manager.broadcast(remove_progress=True)

    @staticmethod
    def _filter_session_stings(session_strings):
        result = []

        for session_string in set(session_strings):
            if not session_string:
                continue
            try:
                formatted_session_string = base64.urlsafe_b64decode(session_string + '=' * (-len(session_string) % 4))
                if len(session_string) in [Storage.SESSION_STRING_SIZE, Storage.SESSION_STRING_SIZE_64]:
                    struct.unpack(
                        Storage.OLD_SESSION_STRING_FORMAT if len(session_string) == Storage.SESSION_STRING_SIZE else Storage.OLD_SESSION_STRING_FORMAT_64,
                        formatted_session_string)
                else:
                    struct.unpack(Storage.SESSION_STRING_FORMAT, formatted_session_string)
                result.append(session_string)
            except (Exception, ):
                continue

        return result

    async def start(self, session_strings: list[str], files: list[bytes] = None):
        await self._manager.broadcast(lock_buttons=True)
        if files:
            for file_data in files:
                if is_sqlite(file_data):
                    session_strings.append(bytes_to_session_string(file_data))
                elif is_zip(file_data):
                    session_strings += tdata_to_session_string(file_data)
                else:
                    try:
                        session_strings += [line_ for line in file_data.decode().split('\n') if len(line_ := line.strip())]
                    except (Exception, ):
                        pass

        session_strings = self._filter_session_stings(session_strings)

        if len(session_strings) == 1:
            await self._single_session_string(session_strings[0])
        elif len(session_strings) > 1:
            await self._multiply_session_string(session_strings)
        else:
            await self._manager.alert('Accounts in the database have been updated', 'warning')
        await self._end()
