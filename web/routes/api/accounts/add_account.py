import asyncio

from fastapi import APIRouter, Form
from fastapi.params import Depends

from add_accounts.by_phone import ByPhone
from add_accounts.by_qrcode import ByQrCode
from add_accounts.by_session import BySession
from web.models import BaseBody
from web.utils import depends_account_data

add_accounts_router = APIRouter(prefix='/add', tags=['Add accounts'])


@add_accounts_router.post('/session')
async def add_accounts_by_session(data: dict = Depends(depends_account_data)):
    add_account = BySession(data['tab_id'])
    if not add_account:
        return {'success': False}
    asyncio.create_task(add_account.start([data['session_string']], [await file.read() for file in data['files']]))
    return {'success': True}


@add_accounts_router.post('/phone')
async def add_account_by_phone(tab_id: str = Form(), phone: str = Form()):
    add_account = ByPhone(tab_id)
    if not add_account:
        return {'success': False}
    asyncio.create_task(add_account.start(phone[1:]))
    return {'success': True}


@add_accounts_router.post('/qrcode')
async def add_account_by_qr_code(data: BaseBody):
    add_account = ByQrCode(data.tab_id)
    if not add_account:
        return {'success': False}
    asyncio.create_task(add_account.start())
    return {'success': True}
