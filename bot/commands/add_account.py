import asyncio
import os
import re

from pyrogram import Client
from pyrogram.errors import PhoneNumberInvalid, BadRequest, SessionPasswordNeeded, PhoneNumberBanned, FloodWait
from bot.language import *
from bot.utils import AccountsManager, get_name, get_password, RegisterHandler, proxy_to_dict, for_allowed_users
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, User, TermsOfService

cancel = ReplyKeyboardMarkup([[KeyboardButton(CANCEL)]], resize_keyboard=True)


def cancel_add_account(func):
    async def wrapper(*args, **kwargs):
        if args[1].text == CANCEL:
            data = RegisterHandler.get_data(args[1])
            if hasattr(data, 'task') and data.task:
                data.task.cancel()
            RegisterHandler.delete(args[1])
            try:
                app = args[2].get('app')
                if app:
                    await app.disconnect()
            except (Exception,):
                pass
            await args[0].send_message(args[1].chat.id, CANCELED, reply_markup=ReplyKeyboardRemove())
        else:
            await func(*args, **kwargs)

    return wrapper


async def save_account(client, data, message):
    await AccountsManager.add_user(client, message, data.app, None)
    data.app.is_initialized = True
    await data.app.stop()


async def resend_code(bot, app, phone, phone_code_hash, message):
    await asyncio.sleep(181)
    code = await app.resend_code(phone, phone_code_hash)
    await bot.send_message(message.chat.id, NEW_CODE_SENT.format(phone=phone))
    RegisterHandler.update(message, phone_code_hash=code.phone_code_hash)


@cancel_add_account
async def ask_password(client, message):
    data = RegisterHandler.get_data(message)
    try:
        await data.app.check_password(message.text)
        await save_account(client, data, message)
    except BadRequest:
        await client.send_message(message.chat.id, INVALID_PASSWORD.format(hint=data.hint), reply_markup=cancel)
        RegisterHandler.register_next_step(message, ask_password)


@cancel_add_account
async def ask_code(client, message):
    if re.findall(r'^\d{5}$', message.text):
        data = RegisterHandler.get_data(message)
        try:
            user = await data.app.sign_in(data.phone, data.phone_code_hash, message.text)
            if data.task:
                data.task.cancel()
            if not isinstance(user, User):
                await asyncio.sleep(3)
                user = await data.app.sign_up(data.phone, data.phone_code_hash, get_name())
                await data.app.enable_cloud_password(get_password(data.phone), hint='Default password')
                if isinstance(user, TermsOfService):
                    await data.app.accept_terms_of_service(user.id)
            await save_account(client, data, message)
        except BadRequest:
            await client.send_message(message.chat.id, INVALID_CODE, reply_markup=cancel)
            RegisterHandler.register_next_step(message, ask_code)
        except SessionPasswordNeeded:
            hint = await data.app.get_password_hint()
            if hint == 'Default password':
                try:
                    await data.app.check_password(get_password(data.phone))
                    await save_account(client, data, message)
                    return
                except BadRequest:
                    pass
            await client.send_message(message.chat.id, PASSWORD_NEED.format(hint=hint), reply_markup=cancel)
            RegisterHandler.register_next_step(message, ask_password, hint=hint)
    else:
        await client.send_message(message.chat.id, INVALID_CODE_FORMAT, reply_markup=cancel)
        RegisterHandler.register_next_step(message, ask_code)


@for_allowed_users
@cancel_add_account
async def ask_phone(client, message):
    await client.send_message(message.chat.id, CHECK_PHONE.format(phone=message.text))
    app = Client('client', api_id=int(os.getenv('API_ID')), api_hash=os.getenv('API_HASH'), in_memory=True, proxy=proxy_to_dict(os.getenv('PROXY')))
    await app.connect()
    resend_code_task = None
    try:
        code = await app.send_code(message.text)
        if code.type != SentCodeType.APP:
            resend_code_task = asyncio.create_task(resend_code(client, app, message.text, code.phone_code_hash, message))
    except PhoneNumberInvalid:
        await client.send_message(message.chat.id, INVALID_PHONE, reply_markup=cancel)
        RegisterHandler.register_next_step(message, ask_phone)
        await app.disconnect()
        return
    except PhoneNumberBanned:
        await client.send_message(message.chat.id, PHONE_BANNED, reply_markup=ReplyKeyboardRemove())
        await app.disconnect()
        return
    except FloodWait as e:
        await client.send_message(message.chat.id, FLOOD_BAN.format(seconds=e.value), reply_markup=ReplyKeyboardRemove())
        await app.disconnect()
        return
    await client.send_message(message.chat.id, SEND_CODE.format(by=SENT_CODE_DESCRIPTION[code.type]),
                              reply_markup=cancel)
    RegisterHandler.register_next_step(message, ask_code, app=app, phone_code_hash=code.phone_code_hash, phone=message.text, task=resend_code_task)
