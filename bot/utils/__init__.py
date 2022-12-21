import os
import random
import string
import hashlib
from bot.utils.accounts_manager import AccountsManager
from bot.utils.register_handler import RegisterHandler
from bot.utils.function_logger import get_logger
from bot.utils.whitelist import Whitelist
from bot.utils.decorators import for_admin, for_allowed_users

DEAD_STICKER_ID = 'CAACAgIAAxkBAAIDt2OXa1TY2W0AAWj3-_V5AY0hwJygbgACwiQAAkodQEj3t3mHRjVvQx4E'


def random_string(size=16):
    return ''.join([random.choice(string.ascii_letters) for _ in range(size)])


def get_name():
    if not os.path.isfile('names.txt'):
        return random_string(6)
    with open('names.txt', 'r', encoding='utf8') as f:
        return random.choice(f.readlines()).strip()


def get_password(phone):
    hash_object = hashlib.sha256(phone.encode())
    return hash_object.hexdigest()


def proxy_to_dict(proxy):
    if not proxy or not proxy.startswith(('http', 'socks4', 'socks5')):
        return
    type_, proxy = proxy.split('://', 1)
    return_data = {'scheme': type_}
    data = proxy.split('@')
    if len(data) == 2:
        user_password = data[0].split(':', 1)
        return_data['username'] = user_password[0]
        return_data['password'] = user_password[1]

    ip_port = data[-1].split(':', 1)
    return_data['hostname'] = ip_port[0]
    if len(ip_port) == 2:
        return_data['port'] = int(ip_port[-1])
    return return_data
