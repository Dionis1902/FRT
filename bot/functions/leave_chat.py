import asyncio

from pyrogram.types import Chat

from bot.functions.base import Base
from bot.functions.join_chats import JoinChats
from bot.utils import RegisterHandler


class LeaveChat(JoinChats):
    @staticmethod
    async def _join_and_get(client, group):
        if group.startswith('http') and ('t.me/joinchat/' in group or '+' in group):
            chat = await client.get_chat(group)
            if isinstance(chat, Chat):
                return chat
        else:
            return await client.get_chat(group.replace('https://t.me/', '').replace('/', ''))

    @Base._log_function('leave_chats')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        async for client in self._get_accounts(data.account_counts, timeout=data.timeout):
            for link in data.links:
                group = await self._try_execute(self._join_and_get(client, link))
                if not group:
                    continue
                await self._try_execute(client.leave_chat(group.id))
                self._logger.info(f'Group ID : {group.id}')
                await asyncio.sleep(.1)
