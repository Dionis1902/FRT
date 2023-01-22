import base64
import io
import os
import random
import secrets
import shutil
import struct
import zipfile
from urllib.parse import urlparse

import names
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from opentele.td import TDesktop
from pyrogram import utils

import stream_sqlite
from fastapi import File, Form, HTTPException, UploadFile, Request, Depends
from pyrogram.storage import Storage

from db import database
from db.models import accounts
from functions import FUNCTIONS
from settings import Settings
from utils import random_string
from web.connection_manager import ConnectionManager

security = HTTPBasic()


async def depends_account(user_id: int):
    query = accounts.select().where(accounts.c.user_id == user_id)
    account = await database.fetch_one(query)
    if not account:
        raise HTTPException(status_code=404, detail='Account not found')
    return account


async def depends_account_form(user_id: int = Form()):
    return await depends_account(user_id)


async def get_manager(tab_id: str, request: Request):
    return ConnectionManager(urlparse(request.headers.get('referer', '')).path, tab_id)


async def get_manager_form(request: Request, tab_id: str = Form()):
    return await get_manager(tab_id, request)


async def depends_function(function_id):
    function = FUNCTIONS.get(function_id)
    if not function:
        raise HTTPException(404)
    return function


def depends_account_data(tab_id: str = Form(), files: list[UploadFile] = File(None), session_string: str = Form(None)):
    if not files and not session_string:
        raise HTTPException(status_code=422, detail='Required one of fields "files" or "session_string"')
    return dict(files=files or [], session_string=session_string, tab_id=tab_id)


def depends_image_path(photo_id: str):
    path = os.path.join(os.getcwd(), 'data', 'images', f'{photo_id}.jpg')
    if not os.path.isfile(path):
        raise HTTPException(status_code=404, detail='Photo not found')
    return path


def bytes_to_session_string(data):
    try:
        for _, pragma_table_info, rows in stream_sqlite.stream_sqlite([data], max_buffer_size=1_048_576):
            if 'auth_key' in [i[1] for i in pragma_table_info]:
                row = list(rows)[0]
                row_data = {i[1]: row[i[0]] for i in pragma_table_info}
                return pack_session_string(row_data.get('dc_id', 1), row_data.get('api_id', 0), row_data.get('test_mode', 0),
                                           row_data['auth_key'], row_data.get('user_id', 999999999), row_data.get('is_bot', 0))

    except (Exception,):
        return


def pack_session_string(dc_id, api_id, test_mode, auth_key, user_id, is_bot):
    if user_id < utils.MAX_USER_ID_OLD:
        packed = struct.pack(Storage.SESSION_STRING_FORMAT, dc_id, api_id, test_mode, auth_key, user_id, is_bot)
    else:
        packed = struct.pack(Storage.OLD_SESSION_STRING_FORMAT_64, dc_id, test_mode, auth_key, user_id, is_bot)
    return base64.urlsafe_b64encode(packed).decode().rstrip('=')


def tdata_to_session_string(data):
    folder_name = random_string()
    session_stings = []
    try:
        with zipfile.ZipFile(io.BytesIO(data), 'r') as f:
            for file in f.namelist():
                if file.startswith('tdata/'):
                    f.extract(file, folder_name)

        if not os.path.isdir(folder_name):
            return session_stings

        telegram_desk = TDesktop(os.path.join(folder_name, 'tdata'))

        if not telegram_desk.isLoaded():
            return session_stings

        for account in telegram_desk.accounts:
            session_stings.append(pack_session_string(account.authKey.dcId, account.owner.api.api_id, 0, account.authKey.key, account.UserId, 0))
    finally:
        if os.path.isdir(folder_name):
            shutil.rmtree(folder_name)
        return session_stings


def check_user(credentials: HTTPBasicCredentials = Depends(security)):
    current_username_bytes = credentials.username.encode("utf8")
    correct_username_bytes = Settings.get('username').encode()
    is_correct_username = secrets.compare_digest(
        current_username_bytes, correct_username_bytes
    )
    current_password_bytes = credentials.password.encode("utf8")
    correct_password_bytes = Settings.get('password').encode()
    is_correct_password = secrets.compare_digest(
        current_password_bytes, correct_password_bytes
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


def validate_api_data(request: Request):
    if (not Settings.get('api_id') or not Settings.get('api_hash')) and request.scope['path'] not in ['/settings', '/api/settings', '/']:
        raise HTTPException(status_code=418, detail='Set api_id and api_hash')


def get_first_name():
    return random.choice(Settings.get('first_names')) if Settings.get('first_names') else names.get_first_name()


def get_last_name():
    return random.choice(Settings.get('last_names')) if Settings.get('last_names') else names.get_last_name()
