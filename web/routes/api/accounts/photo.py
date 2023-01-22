import io
import os

from fastapi import APIRouter, File, UploadFile
from fastapi.params import Depends
from starlette.responses import FileResponse

from db import database
from db.models import accounts
from db.utils import save_account
from web import ConnectionManager
from web.utils import depends_image_path, depends_account, get_manager, get_manager_form, depends_account_form
from web.utils.context_manager import login_account
from utils import get_hash

photo_router = APIRouter(prefix='/photo', tags=['Photo'])


@photo_router.post('/')
async def add_account_photo(file: UploadFile = File(), manager: ConnectionManager = Depends(get_manager_form),
                            account=Depends(depends_account_form)):
    await manager.broadcast(lock_buttons=True)
    photo = io.BytesIO(await file.read())
    photo.name = file.filename
    async with login_account(account, manager) as client:
        if not client.is_initialized:
            return
        await client.set_profile_photo(photo=photo)
        await save_account(client, account.session_string)
        await manager.broadcast(reload_page=True)
    return {'success': True}


@photo_router.get('/{photo_id}')
async def get_account_photo(path: str = Depends(depends_image_path)):
    return FileResponse(path)


@photo_router.delete('/{photo_id}')
async def delete_account_photo(photo_id: str, manager: ConnectionManager = Depends(get_manager),
                               account=Depends(depends_account), path: str = Depends(depends_image_path)):
    await manager.broadcast(lock_buttons=True)
    async with login_account(account, manager) as client:
        if not client.is_initialized:
            return
        async for photo in client.get_chat_photos('me'):
            if get_hash(photo.file_unique_id) == photo_id:
                await client.delete_profile_photos(photo.file_id)
        os.remove(path)
        photos = account.photos
        photos.remove(photo_id)
        await database.execute(accounts.update().where(accounts.c.user_id == account.user_id).values(photos=photos))
        await manager.broadcast(reload_page=True)
    return {'success': True}
