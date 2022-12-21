import uvloop
from pyrogram import filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import BotCommand, ReplyKeyboardRemove
from bot.callback import callback_handler
from bot.commands import *
from bot.custom_filters import is_session_file
from bot.language import *
from bot.utils import RegisterHandler


uvloop.install()

bot = Client('data/bot', api_id=int(os.getenv('API_ID')), api_hash=os.getenv('API_HASH'), bot_token=os.getenv('BOT_TOKEN'))


async def setup():
    async with bot:
        await bot.set_bot_commands([BotCommand(command=command, description=description) for command, description in BOT_COMMANDS.items()])


bot.run(setup())

bot.add_handler(MessageHandler(RegisterHandler.handler, RegisterHandler.filter() & filters.private))

bot.add_handler(MessageHandler(get_id, filters.command(['id']) & filters.private))
bot.add_handler(MessageHandler(menu, filters.command(['menu']) & filters.private))
bot.add_handler(MessageHandler(add_user, filters.command(['add_user']) & filters.private))
bot.add_handler(MessageHandler(ask_phone, filters.regex(r'^\+\d+$') & filters.private))
bot.add_handler(MessageHandler(accounts_count, filters.command(['accounts_count']) & filters.private))
bot.add_handler(MessageHandler(add_account_by_file, is_session_file() & filters.private))

bot.add_handler(CallbackQueryHandler(callback_handler))


@bot.on_message(filters.regex(f'^{CANCEL}$'))
async def cancel_handler(client, message):
    await client.send_message(message.chat.id, CANCELED, reply_markup=ReplyKeyboardRemove())
