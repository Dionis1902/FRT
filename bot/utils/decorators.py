import os

from bot.language import *
from bot.utils import Whitelist


def for_admin(func):
    async def wrapper(*args, **kwargs):
        if args[1].chat.id == int(os.getenv('ADMIN_ID')):
            return await func(*args, **kwargs)
        else:
            await args[0].send_message(args[1].chat.id, THIS_COMMAND_FOR_ADMIN)

    return wrapper


def for_allowed_users(func):
    async def wrapper(*args, **kwargs):
        if args[1].chat.id in [*await Whitelist.get(), int(os.getenv('ADMIN_ID'))]:
            return await func(*args, **kwargs)
        else:
            await args[0].send_message(args[1].chat.id, ASK_ADMIN_ACCESS)

    return wrapper
