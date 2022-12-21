import asyncio
import re
import random
from pyrogram.types import Message, KeyboardButton
from bot.functions.base import Base
from bot.language import *
from bot.utils import RegisterHandler
from bot.functions.spam_to_chat import SpamToChat


class SpamToComments(SpamToChat):
    async def __start(self, *args):
        client, data, group_id, post_id = args
        post: Message = await self._try_execute(client.get_discussion_message(group_id, int(post_id)))
        if not post:
            return
        message = random.choice(data.messages)
        comment = await self._try_execute(self._send_message_by_client(client, post.chat.id, message, by_group=data.by_group,
                                                                       reply_to_message_id=post.id))
        if not comment:
            return
        self._logger.info(f'Group ID : {post.sender_chat.id}, Post ID: {post_id}, Comment ID : {comment.id}')
        await asyncio.sleep(.1)

    @Base._log_function('spam_to_comments')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        for _ in range(data.repeat_count if data.account_counts != 1 else 1):
            async for client in self._get_accounts(data.account_counts, timeout=data.timeout, only_premium=data.by_group):
                for [[group_id, post_id]] in data.links:
                    for _ in range(data.repeat_count if data.account_counts == 1 else 1):
                        await self.__start(client, data, group_id, post_id)

    @Base._cancel_function
    async def _ask_link(self, _, message):
        link_data = re.findall(r'^https://t.me/([^/]*)/(\d*)$', message.text or '')
        links = []
        if message.document and message.document.mime_type == 'text/plain':
            links = await self._get_file_content(message, func=lambda x: re.findall(r'^https://t.me/([^/]*)/(\d*)$', x))
            if not links:
                await self._send_message(NO_ONE_LINK_TO_POST_IN_FILE)
                RegisterHandler.register_next_step(message, self._ask_link)
                return
        elif link_data:
            links = [link_data]

        if links:
            await self._send_message(ENTER_MESSAGE, reply_markup=[[KeyboardButton(DEAD_STICKER)]])
            RegisterHandler.register_next_step(message, self._ask_message, links=links)
        else:
            await self._send_message(INVALID_LINK_TO_POST)
            RegisterHandler.register_next_step(message, self._ask_link)

    @Base._cancel_function
    async def _ask_count(self, _, message):
        await self._ask_count_validate(message, ENTER_LINK_TO_POST, self._ask_link)
