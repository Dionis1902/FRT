import random

from pyrogram.errors import BadRequest

from functions.functions.spam_chat import Function as SpamChat
from functions.utils import Field, Types
from utils import random_string


class Function(SpamChat):
    """Spam messages to chat on behalf of the channel"""

    __id__ = 'spam_chat_by_channel'
    __function_name__ = 'Spam chat by channel'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts', only_premium=True),
                 chats: Field(Types.INPUTS, label_name='Chats link',
                              pattern=r'^https://t.me/(\\w{5,32}|\\+\\w+|joinchat/\\w+)$',
                              placeholder='https://t.me/simple_chat'),
                 messages: Field(Types.TEXTAREA, label_name='Messages',
                                 placeholder='Hello world!'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, chats, messages, settings)

    async def _send_message(self, client, chat):
        channel = await client.create_channel(random_string())
        await client.set_chat_username(channel.id, random_string(32))
        try:
            await client.set_send_as_chat(chat, channel.id)
        except BadRequest as e:
            await client.delete_channel(channel.id)
            raise e
        message = await client.send_message(chat, random.choice(self._messages))
        await client.delete_channel(channel.id)
        return message
