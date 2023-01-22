from contextlib import asynccontextmanager

from pyrogram.errors import SessionExpired, SessionRevoked, UserDeactivated, UserDeactivatedBan

from add_accounts.custom_client import CustomClient
from db.utils import delete_account
from settings import Settings
from utils import proxy_to_dict


@asynccontextmanager
async def login_account(account, manager, on_failure=None, on_account_bad=None):
    client = CustomClient('client', api_id=Settings.get('api_id'), api_hash=Settings.get('api_hash'),
                          session_string=account.session_string, proxy=proxy_to_dict(account.proxy or Settings.get('proxy')))
    try:
        await client.start()
    except (SessionExpired, SessionRevoked, UserDeactivated, UserDeactivatedBan) as e:
        await manager.alert(e.__doc__, 'danger')
        await delete_account(account)
        if on_account_bad:
            await on_account_bad
    try:
        yield client
    except (Exception,):
        if on_failure:
            await on_failure
    finally:
        if client.is_initialized:
            await client.stop()
