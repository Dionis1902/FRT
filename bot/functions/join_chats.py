import asyncio
import re
from bot.functions.base import Base
from bot.language import *
from bot.utils import RegisterHandler


class JoinChats(Base):
    @Base._log_function('join_chats')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        async for client in self._get_accounts(data.account_counts, timeout=data.timeout):
            for link in data.links:
                group = await self._try_execute(self._join_and_get(client, link))
                if not group:
                    continue
                self._logger.info(f'Group ID : {group.id}')
                await asyncio.sleep(.1)

    @Base._cancel_function
    async def _ask_time_out(self, _, message):
        if message.text and message.text.isdigit() and int(message.text) >= 0:
            RegisterHandler.update(message, timeout=int(message.text))
            await self._start(message)
        else:
            await self._send_message(ENTER_VALID_NUMBER)
            RegisterHandler.register_next_step(message, self._ask_time_out)

    @Base._cancel_function
    async def _ask_link(self, _, message):
        link_data = re.findall(r'^https://t.me/.*$', message.text or '')
        links = []
        if message.document and message.document.mime_type == 'text/plain':
            links = await self._get_file_content(message, filter_=lambda x: re.findall(r'^https://t.me/.*$', x))
            if not links:
                await self._send_message(NO_ONE_LINK_TO_CHAT_IN_FILE)
                RegisterHandler.register_next_step(message, self._ask_link)
                return
        elif link_data:
            links = link_data

        if links:
            await self._send_message(ENTER_TIMEOUT)
            RegisterHandler.register_next_step(message, self._ask_time_out, links=links)
        else:
            await self._send_message(INVALID_LINK_TO_CHAT)
            RegisterHandler.register_next_step(message, self._ask_link)

    @Base._cancel_function
    async def _ask_count(self, _, message):
        await self._ask_count_validate(message, ENTER_LINK_TO_CHAT, self._ask_link)
