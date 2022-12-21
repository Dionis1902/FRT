import asyncio
import random
import re
from pyrogram.types import KeyboardButton
from bot.functions import ReactionRaid
from bot.functions.base import Base
from bot.language import *
from bot.utils import RegisterHandler


class VotePoll(ReactionRaid):
    @Base._log_function('vote_poll')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        no_poll = []
        async for client in self._get_accounts(data.account_counts, timeout=data.timeout):
            for [[group_id, post_id]] in data.links:
                if (group_id, post_id) in no_poll:
                    continue
                message_ = await self._try_execute(client.get_messages(group_id, int(post_id)))
                if not message_:
                    continue
                if not message_.poll:
                    no_poll.append((group_id, post_id))
                    self._logger.error(f'Group : {group_id}, Message ID : {post_id} is not poll')
                    continue
                max_options = len(message_.poll.options) - 1
                if data.poll == RANDOM_POLL:
                    option = random.randint(0, max_options)
                else:
                    option = int(data.poll) - 1
                    if option > max_options:
                        option = max_options
                await client.vote_poll(group_id, int(post_id), option)
                self._logger.info(f'Group : {group_id}, Message ID : {post_id} voted for option {option}')
                await asyncio.sleep(.1)

    @Base._cancel_function
    async def _ask_reaction(self, _, message):
        if message.text == RANDOM_POLL or (message.text and message.text.isdigit() and 1 <= int(message.text) <= 10):
            await self._send_message(ENTER_TIMEOUT)
            RegisterHandler.register_next_step(message, self._ask_time_out, poll=message.text)
        else:
            await self._send_message(ENTER_POLL, reply_markup=[[KeyboardButton(RANDOM_POLL)]])
            RegisterHandler.register_next_step(message, self._ask_reaction)

    @Base._cancel_function
    async def _ask_link(self, _, message):
        link_data = re.findall(r'^https://t.me/([^/]*)/(\d*)$', message.text or '')
        links = []
        if message.document and message.document.mime_type == 'text/plain':
            links = await self._get_file_content(message, func=lambda x: re.findall(r'^https://t.me/([^/]*)/(\d*)$', x))
            if not links:
                await self._send_message(NO_ONE_LINK_TO_POST_OR_MESSAGE_IN_FILE)
                RegisterHandler.register_next_step(message, self._ask_link)
                return
        elif link_data:
            links = [link_data]

        if links:
            await self._send_message(ENTER_POLL, reply_markup=[[KeyboardButton(RANDOM_POLL)]])
            RegisterHandler.register_next_step(message, self._ask_reaction, links=links)
        else:
            await self._send_message(INVALID_LINK_TO_POST_OR_MESSAGE)
            RegisterHandler.register_next_step(message, self._ask_link)
