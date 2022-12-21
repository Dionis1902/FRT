import asyncio
import random
import re

from pyrogram.types import KeyboardButton

from bot.functions.base import Base
from bot.language import *
from bot.utils import RegisterHandler

REACTIONS = ['👍', '😴', '😁', '🤯', '🥱', '👻', '🤮', '🥰', '🍌', '🌭', '👏', '🙏', '💋', '🤬', '🎃', '🤔', '🎉', '🍓', '🤓', '🤝', '🔥', '🥴', '😭', '🤣',
             '🤡', '😍', '😱', '🖕', '✍', '😇', '💯', '😐', '😨', '\U0001fae1', '🤗', '💔', '👌', '🏆', '🌚', '🙈', '❤', '❤\u200d🔥', '👎', '⚡', '🤨', '😢',
             '💩', '🐳', '👀', '🤩', '😈', '👨\u200d💻', '🕊', '🍾', RANDOM_REACTION]


class ReactionRaid(Base):
    @Base._log_function('reaction_raid')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        block_groups = []
        async for client in self._get_accounts(data.account_counts, timeout=data.timeout):
            for [[group_id, post_id]] in data.links:
                if group_id in block_groups:
                    continue
                group = await self._try_execute(client.get_chat(group_id))
                if not group:
                    continue
                available_reactions = []
                if group.available_reactions:
                    if group.available_reactions.all_are_enabled:
                        available_reactions = REACTIONS[:-1]
                    else:
                        available_reactions = [i.emoji for i in group.available_reactions.reactions]
                if available_reactions:
                    reaction = data.reaction
                    if data.reaction == RANDOM_REACTION:
                        reaction = random.choice(available_reactions)
                    if await client.send_reaction(group.id, int(post_id), reaction):
                        self._logger.info(f'Group ID : {group.id}, Message ID : {post_id}, Reaction : {reaction}')
                else:
                    block_groups.append(group_id)
                    self._logger.error(f'Group ID : {group.id} don\'t have available reactions')
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
    async def _ask_reaction(self, _, message):
        if message.text in REACTIONS:
            await self._send_message(ENTER_TIMEOUT)
            RegisterHandler.register_next_step(message, self._ask_time_out, reaction=message.text)
        else:
            await self._send_message(ENTER_REACTION, reply_markup=[[KeyboardButton(RANDOM_REACTION)]])
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
            await self._send_message(ENTER_REACTION, reply_markup=[[KeyboardButton(RANDOM_REACTION)]])
            RegisterHandler.register_next_step(message, self._ask_reaction, links=links)
        else:
            await self._send_message(INVALID_LINK_TO_POST_OR_MESSAGE)
            RegisterHandler.register_next_step(message, self._ask_link)

    @Base._cancel_function
    async def _ask_count(self, _, message):
        await self._ask_count_validate(message, ENTER_LINK_TO_POST_OR_MESSAGE, self._ask_link)