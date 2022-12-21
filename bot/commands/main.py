import os.path
from pyrogram import Client
from bot.language import *
from bot.utils import Whitelist, random_string
from bot.utils import for_admin, for_allowed_users
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.utils import AccountsManager


async def get_id(client, message):
    await client.send_message(message.chat.id, USER_ID.format(user_id=message.chat.id))


@for_admin
async def add_user(client, message):
    if len(message.command) == 2 and message.command[1].isdigit():
        await Whitelist.add(int(message.command[1]))
        await client.send_message(message.chat.id, SUCCESS_ADD_USER.format(user_id=message.command[1]))
    else:
        await client.send_message(message.chat.id, INVALID_COMMAND_USAGE)


@for_allowed_users
async def add_account_by_file(client, message):
    name = random_string()
    file = await message.download(file_name=name + '.session')
    app = Client(os.path.join('downloads', name))
    try:
        await app.start()
        me = await app.get_me()
        if me.is_bot:
            await app.stop()
            await client.send_message(message.chat.id, THIS_IS_BOT, reply_to_message_id=message.id)
            return
        await AccountsManager.add_user(client, message, app)
        await app.stop()
    except (Exception,):
        await client.send_message(message.chat.id, INVALID_ACCOUNT, reply_to_message_id=message.id)
    finally:
        await app.storage.close()
        os.remove(file)


@for_allowed_users
async def accounts_count(client, message):
    await client.send_message(message.chat.id, ACCOUNTS_COUNT.format(**await AccountsManager.get_count()))


@for_allowed_users
async def menu(client, message):
    await client.send_message(message.chat.id, BOT_FUNCTIONS,
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=callback_data)]
                                                                 for callback_data, text in FUNCTIONS.items()]))
