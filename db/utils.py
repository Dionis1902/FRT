import asyncio
import hashlib
import os.path
import re

from phone_iso3166.country import phone_country
from pyrogram.errors import YouBlockedUser
from pyrogram.storage import Storage

from db import database
from db.models import accounts
import os.path
from opentele.tl import TelegramClient
from opentele.api import UseCurrentSession
from telethon.crypto import AuthKey
from telethon.sessions import MemorySession
import zipfile
import shutil


async def save_account(client, default_session_string=None):
    if default_session_string and len(default_session_string) not in [Storage.SESSION_STRING_SIZE, Storage.SESSION_STRING_SIZE_64]:
        session_string = default_session_string
    else:
        session_string = await client.export_session_string()

    bio = (await client.get_chat(client.me.id)).bio

    account_data = dict(user_id=client.me.id, session_string=session_string, first_name=client.me.first_name,
                        last_name=client.me.last_name, username=client.me.username, bio=bio, county_code=phone_country(client.me.phone_number).lower(),
                        phone_number=client.me.phone_number, is_premium=client.me.is_premium)

    account_data['spam_block'] = await check_spam_block(client)

    account = await database.fetch_one(accounts.select().where(accounts.c.user_id == client.me.id))

    account_data['photos'] = await get_photos(client, account.photos if account else None)

    query = accounts.update().where(accounts.c.user_id == account.user_id).values(account_data) if account else accounts.insert().values(account_data)

    if not account or (account and account.session_string != session_string) \
            or not os.path.isfile(os.path.join(os.getcwd(), 'data', 'tdata', f'{client.me.id}.zip')):
        await generate_tdata(client)

    await database.execute(query)
    return account is None, account_data


async def get_photos(client, stored_photos=None):
    if stored_photos is None:
        stored_photos = []
    photos = []

    async for photo in client.get_chat_photos('me'):
        hash_name = hashlib.sha256(photo.file_unique_id.encode()).hexdigest()
        if hash_name not in stored_photos:
            await client.download_media(photo.file_id, file_name=os.path.join(os.getcwd(), 'data', 'images', f'{hash_name}.jpg'))
            await asyncio.sleep(.5)
        photos.append({'hash_name': hash_name, 'upload_datetime': photo.date})
    photos = [photo['hash_name'] for photo in sorted(photos, key=lambda x: x['upload_datetime'], reverse=True)]
    for hash_name in set(stored_photos) - set(photos):
        os.remove(os.path.join(os.getcwd(), 'data', 'images', f'{hash_name}.jpg'))
    return photos


async def delete_account(account):
    for hash_name in account.photos:
        if os.path.isfile(photo := os.path.join(os.getcwd(), 'data', 'images', f'{hash_name}.jpg')):
            os.remove(photo)
    if os.path.isfile(tdata := os.path.join(os.getcwd(), 'data', 'tdata', f'{account.user_id}.zip')):
        os.remove(tdata)
    await database.execute(accounts.delete().where(accounts.c.user_id == account.user_id))


async def generate_tdata(client):
    user_id = client.me.id
    session = MemorySession()
    session.set_dc(client.session.dc_id, *client.session.connection.address)
    session.auth_key = AuthKey(client.session.auth_key)

    client_test = TelegramClient(session)

    telegram_desk = await client_test.ToTDesktop(flag=UseCurrentSession)

    folder_name = f'tdata_{user_id}'

    telegram_desk.SaveTData(folder_name)

    files_paths = []
    for root, directories, files in os.walk(folder_name):
        for filename in files:
            file_paths = os.path.join(root, filename)
            files_paths.append(file_paths)

    tdata_folder = os.path.join(os.getcwd(), 'data', 'tdata')

    if not os.path.isdir(tdata_folder):
        os.makedirs(tdata_folder, exist_ok=True)

    with zipfile.ZipFile(os.path.join(tdata_folder, f'{user_id}.zip'), 'w') as f:
        for file in files_paths:
            f.write(file, file.replace(folder_name, 'tdata'))

    shutil.rmtree(folder_name)


async def check_spam_block(client):
    try:
        await client.send_message('SpamBot', '/start')
    except YouBlockedUser:
        await client.unblock_user('SpamBot')
        return await check_spam_block(client)

    await asyncio.sleep(.5)

    messages = [i async for i in client.get_chat_history('SpamBot', limit=1)]
    text = messages[0].text
    lines = text.split('\n')

    if len(lines) == 1:
        if messages[0].entities:
            return 'Need complaint'
        return 'No'
    else:
        result = re.findall(r"\d+\s\w+\s\d{4}", text)
        if not result:
            return 'Permanent'
        else:
            return result[0]
