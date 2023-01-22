import asyncio
import os
import random
import re

import names
from fastapi import APIRouter, Depends, Response, Form, HTTPException
from pyrogram.errors import UsernameNotModified, UsernameOccupied, UsernameInvalid, Flood
from starlette.responses import FileResponse

from add_accounts.by_session import BySession
from db import database
from db.models import accounts
from db.utils import save_account, delete_account
from web import ConnectionManager
from web.models import *
from web.routes.api.accounts.add_account import add_accounts_router
from web.routes.api.accounts.photo import photo_router
from web.utils import depends_account, get_manager, get_manager_form, get_first_name, get_last_name
from web.utils.context_manager import login_account

router = APIRouter(prefix='/accounts', tags=['Account'])


@router.get('/', response_model=list[SmallAccountInfo], description='Get all accounts from database')
async def get_accounts(only_premium: bool = False, with_spam_block: bool = True):
    query = accounts.select().order_by(accounts.c.id)
    if only_premium:
        query = query.where(accounts.c.is_premium)
    if not with_spam_block:
        query = query.where(accounts.c.spam_block == 'No')
    return await database.fetch_all(query)


@router.delete('/')
async def delete_accounts(tab_id: str, ids: str):
    manager = ConnectionManager('/accounts', tab_id)
    if ids == 'all':
        data = 'all'
        query = accounts.select()
    else:
        data = [int(id_) for id_ in ids.split(',') if id_.isdigit()]
        query = accounts.select().where(accounts.c.user_id.in_(data))
    for account in await database.fetch_all(query):
        await delete_account(account)
    await manager.alert(f'Success delete {data if isinstance(data, str) else len(data)} accounts')
    await manager.broadcast(clear_table=data)
    return {'success': True}


@router.get('/{user_id}', response_model=AccountInfo, description='Get info about account bu user_id')
async def get_account(account=Depends(depends_account)):
    return account


@router.get('/{user_id}/tdata')
async def get_account(user_id: str):
    path = os.path.join(os.getcwd(), 'data', 'tdata', f'{user_id}.zip')
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail='Tdata not found')
    return FileResponse(path)


@router.get('/export/')
async def export_accounts(ids: str = 'all'):
    if ids == 'all':
        query = accounts.select()
    else:
        query = accounts.select().where(accounts.c.user_id.in_((int(id_) for id_ in ids.split(',') if id_.isdigit())))
    data = '\n'.join([account.session_string for account in await database.fetch_all(query)])
    return Response(content=data, media_type='text/plain')


@router.get('/{user_id}/code', description='Return 2FA code for login')
async def get_code(account=Depends(depends_account), manager: ConnectionManager = Depends(get_manager)):
    await manager.broadcast(lock_buttons=True)
    async with login_account(account, manager) as client:
        if not client.is_initialized:
            return {'success': False}
        messages = [i async for i in client.get_chat_history(777000, limit=1)]
        if messages:
            code = re.findall(r'\d{5}', messages[0].text)
            if code:
                await manager.alert(f'Code <b>{code[0]}</b> (Copied to clipboard)')
                await manager.broadcast(lock_buttons=False)
                return {'success': True, 'code': code[0]}
    await manager.alert('Code not\'t found', 'danger')
    await manager.broadcast(lock_buttons=False)
    return {'success': False}


@router.get('/{user_id}/validate')
async def account_validate(account=Depends(depends_account), manager: ConnectionManager = Depends(get_manager)):
    await manager.broadcast(lock_buttons=True)

    async with login_account(account, manager) as client:
        if not client.is_initialized:
            return {'success': False}
        await save_account(client, account.session_string)
    await manager.broadcast(reload_page=False)
    return {'success': True}


@router.get('/validate/')
async def account_validate(ids: str, tab_id: str):
    validate_accounts = BySession(tab_id)
    if not validate_accounts:
        return {'success': False}
    if ids == 'all':
        query = accounts.select()
    else:
        query = accounts.select().where(accounts.c.user_id.in_([int(id_) for id_ in ids.split(',') if id_.isdigit()]))
    session_strings = [i.session_string for i in await database.fetch_all(query)]
    asyncio.create_task(validate_accounts.start(session_strings))
    return {'success': True}


@router.post('/{user_id}', description='Update account')
async def update_account(manager: ConnectionManager = Depends(get_manager_form), account=Depends(depends_account),
                         first_name: str = Form(), last_name: str = Form(None), username: str = Form(None),
                         bio: str = Form(None), proxy: str = Form(None)):
    if proxy != account.proxy:
        await database.execute(accounts.update().where(accounts.c.user_id == account.user_id).values(proxy=proxy))

    if account.first_name == first_name and account.last_name == last_name \
            and account.bio == bio and account.username == username:
        return {'success': False}
    await manager.broadcast(lock_buttons=True)
    updated_data = dict(first_name=account.first_name, last_name=account.last_name, bio=account.bio, username=account.username)
    async with login_account(account, manager) as client:
        if not client.is_initialized:
            return {'success': False}
        if (account.first_name != first_name or account.last_name != last_name or account.bio != bio) and \
                await client.update_profile(first_name=first_name, last_name=last_name, bio=bio):
            updated_data.update(first_name=first_name, last_name=last_name, bio=bio)
            await database.execute(accounts.update().where(accounts.c.user_id == account.user_id).values(first_name=first_name, last_name=last_name, bio=bio))
        try:
            if (account.username != username) and await client.set_username(username):
                updated_data.update(username=username)
                await database.execute(accounts.update().where(accounts.c.user_id == account.user_id).values(username=username))
        except (UsernameInvalid, UsernameOccupied, UsernameNotModified) as e:
            await manager.alert(e.__doc__, 'danger')
        except Flood as e:
            await manager.alert(f'Ban for change username <b>{e.value}</b> seconds', 'danger')
    await manager.broadcast(update_account_info=updated_data)
    await manager.broadcast(lock_buttons=False)
    return {'success': True}


@router.get('/random/')
async def get_random_data():
    first_name, last_name = get_first_name(), get_last_name()

    return dict(first_name=first_name, last_name=last_name, username=f'{names.get_last_name()}{random.randint(1900, 2020)}'.lower())


router.include_router(add_accounts_router)
router.include_router(photo_router)
