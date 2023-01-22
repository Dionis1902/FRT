import random

from pyrogram.errors import InviteHashExpired, UsernameInvalid, UsernameNotOccupied
from pyrogram.types import Chat

from functions.base_function import Base
from functions.utils import Field, Types


class Function(Base):
    """Spam messages to chat"""

    __id__ = 'spam_chat'
    __function_name__ = 'Spam chat'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts'),
                 chats: Field(Types.INPUTS, label_name='Chats link',
                              pattern=r'^https://t.me/(\\w{5,32}|\\+\\w+|joinchat/\\w+)$',
                              placeholder='https://t.me/simple_chat'),
                 messages: Field(Types.TEXTAREA, label_name='Messages',
                                 placeholder='Hello world!'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, settings)
        self._chats = chats
        self._messages = messages
        self._skip = []

    def _is_need_finish(self):
        is_need_finish = len(self._skip) == len(self._chats)
        if is_need_finish:
            self._logger.error('No one valid link')
        return is_need_finish

    async def _send_message(self, client, chat):
        return await client.send_message(chat, random.choice(self._messages))

    @Base._check_for_flood
    async def _try_send_message(self, link, client, account):
        if link in self._skip:
            self._logger.error(f'Skipping {link} as it invalid')
            return True
        try:
            if 'joinchat/' in link or '+' in link:
                chat = await client.get_chat(link)
                if isinstance(chat, Chat):
                    await self._send_message(client, chat.id)
                    self._logger.info(f'Success send message to {link}', extra=dict(user_id=account.user_id))
                else:
                    self._logger.info(f'Not joined to {link}', extra=dict(user_id=account.user_id))
            else:
                await self._send_message(client, link.split('/')[-1])
                self._logger.info(f'Success send message to {link}', extra=dict(user_id=account.user_id))
        except InviteHashExpired:
            self._logger.error(f'Link {link} is invalid and will be skipped in the future')
            self._skip.append(link)
        except (UsernameNotOccupied, UsernameInvalid):
            self._logger(f'Group {link} don\'t exist')
            self._skip.append(link)
        return True

    async def _run(self, client, account):
        for link in self._chats:
            if not (await self._try_send_message(link.rstrip('/'), client, account)):
                break
            await self._wait(link != self._chats[-1])
