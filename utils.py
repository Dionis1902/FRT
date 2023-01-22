import hashlib
import random
import string


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


def random_string(size=16):
    return ''.join([random.choice(string.ascii_letters) for _ in range(size)])


def is_sqlite(data):
    if len(data) < 100:
        return False
    return data[:16] == b'SQLite format 3\x00'


def is_zip(data):
    return data[:2] == b'\x50\x4b'


def get_hash(data):
    hash_object = hashlib.sha256(data.encode())
    return hash_object.hexdigest()
