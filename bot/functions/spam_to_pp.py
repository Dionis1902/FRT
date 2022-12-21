import asyncio
import random
import re
from pyrogram.types import KeyboardButton
from bot.functions import SpamToChat
from bot.functions.base import Base
from bot.language import *
from bot.utils import RegisterHandler


class SpamToPP(SpamToChat):
    async def __start(self, *args):
        client, data, link = args
        user = await self._try_execute(client.get_users(link))
        if not user and not link.isdigit():
            return
        message_text = random.choice(data.messages)
        message = await self._try_execute(self._send_message_by_client(client, user.id if user else int(link), message_text))
        if not message:
            return
        self._logger.info(f'User ID : {user.id if user else link}, Message ID : {message.id}')
        await asyncio.sleep(.1)

    @Base._log_function('spam_to_pp')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        for _ in range(data.repeat_count if data.account_counts != 1 else 1):
            async for client in self._get_accounts(data.account_counts, timeout=data.timeout):
                for [link] in data.links:
                    for _ in range(data.repeat_count if data.account_counts == 1 else 1):
                        await self.__start(client, data, link)

    @Base._cancel_function
    async def _ask_link(self, _, message):
        link_data = re.findall(r'^@?(\w{5,32})$', message.text or '')
        links = []
        if message.document and message.document.mime_type == 'text/plain':
            links = await self._get_file_content(message, func=lambda x: re.findall(r'^@?(\w{5,32})$', x))
            if not links:
                await self._send_message(NO_ONE_NICK_NAME_IN_FILE)
                RegisterHandler.register_next_step(message, self._ask_link)
                return
        elif link_data:
            links = [link_data]

        if links:
            await self._send_message(ENTER_MESSAGE, reply_markup=[[KeyboardButton(DEAD_STICKER)]])
            RegisterHandler.register_next_step(message, self._ask_message, links=links)
        else:
            await self._send_message(INVALID_NICKNAME)
            RegisterHandler.register_next_step(message, self._ask_link)

    @Base._cancel_function
    async def _ask_count(self, _, message):
        await self._ask_count_validate(message, ENTER_NICKNAME_OR_ID, self._ask_link)

    async def start(self):
        await super(SpamToChat, self).start()
