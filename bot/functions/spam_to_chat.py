import asyncio
import re
import random
from pyrogram.errors import BadRequest
from pyrogram.types import KeyboardButton, Sticker, ReplyKeyboardRemove
from bot.functions.base import Base
from bot.language import *
from bot.utils import RegisterHandler, AccountsManager, random_string, DEAD_STICKER_ID


class SpamToChat(Base):
    async def _create_channel(self, client, chat_id):
        channel = await client.create_channel(random_string())
        await client.set_chat_username(channel.id, random_string(32))
        try:
            await client.set_send_as_chat(chat_id, channel.id)
            return channel
        except BadRequest:
            await AccountsManager.change_premium_status(client.me.id, False)
            self._logger.warning('Account don\'t have premium')
            await client.delete_channel(channel.id)

    async def _send_message_by_client(self, client, *args, **kwargs):
        channel = None
        by_group = kwargs.pop('by_group', None)
        if by_group:
            channel = await self._create_channel(client, args[0])
            if not channel:
                return
        message = None
        try:
            if isinstance(args[1], Sticker):
                message = await client.send_sticker(args[0], args[1].file_id, **kwargs)
            elif args[1] == DEAD_STICKER:
                message = await client.send_sticker(args[0], DEAD_STICKER_ID, **kwargs)
            else:
                message = await client.send_message(*args, **kwargs)
        except Exception as e:
            self._logger.error(e)

        if by_group:
            await client.delete_channel(channel.id)

        return message

    async def __start(self, *args):
        client, data, link = args
        group = await self._try_execute(self._join_and_get(client, link))
        if not group:
            return
        message_text = random.choice(data.messages)
        message = await self._try_execute(self._send_message_by_client(client, group.id, message_text, by_group=data.by_group))
        if not message:
            return
        self._logger.info(f'Group ID : {group.id}, Message ID : {message.id}')
        await asyncio.sleep(.1)

    @Base._log_function('spam_to_chat')
    async def _start(self, message):
        data = RegisterHandler.get_data(message)
        for _ in range(data.repeat_count if data.account_counts != 1 else 1):
            async for client in self._get_accounts(data.account_counts, timeout=data.timeout, only_premium=data.by_group):
                for link in data.links:
                    for _ in range(data.repeat_count if data.account_counts == 1 else 1):
                        await self.__start(client, data, link)

    @Base._cancel_function
    async def _ask_repeat_count(self, _, message):
        if message.text and message.text.isdigit() and int(message.text) >= 1:
            RegisterHandler.update(message, repeat_count=int(message.text))
            await self._start(message)
        else:
            await self._send_message(ENTER_VALID_NUMBER)
            RegisterHandler.register_next_step(message, self._ask_repeat_count)

    @Base._cancel_function
    async def _ask_time_out(self, _, message):
        if message.text and message.text.isdigit() and int(message.text) >= 0:
            await self._send_message(HOW_MANY_TIMES_REPEAT)
            RegisterHandler.register_next_step(message, self._ask_repeat_count, timeout=int(message.text))
        else:
            await self._send_message(ENTER_VALID_NUMBER)
            RegisterHandler.register_next_step(message, self._ask_time_out)

    @Base._cancel_function
    async def _ask_message(self, _, message):
        if message.document and message.document.mime_type == 'text/plain':
            messages = await self._get_file_content(message, func=lambda x: x.replace('\\n', '\n'))
            if not messages:
                await self._send_message(EMPTY_FILE)
                RegisterHandler.register_next_step(message, self._ask_message)
                return
        elif message.sticker:
            messages = [message.sticker]
        else:
            messages = [message.text]

        await self._send_message(ENTER_TIMEOUT)
        RegisterHandler.register_next_step(message, self._ask_time_out, messages=messages)

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
            await self._send_message(ENTER_MESSAGE, reply_markup=[[KeyboardButton(DEAD_STICKER)]])
            RegisterHandler.register_next_step(message, self._ask_message, links=links)
        else:
            await self._send_message(INVALID_LINK_TO_CHAT)
            RegisterHandler.register_next_step(message, self._ask_link)

    @Base._cancel_function
    async def _ask_count(self, _, message):
        await self._ask_count_validate(message, ENTER_LINK_TO_CHAT, self._ask_link)

    @Base._cancel_function
    async def _ask_spam_type(self, _, message):
        if message.text not in [BY_USER, BY_CHANNEL]:
            await self._send_message(SPAM_BY, reply_markup=[[KeyboardButton(BY_USER)], [KeyboardButton(BY_CHANNEL)]])
            RegisterHandler.register_next_step(message, self._ask_spam_type)
        else:
            by_group = message.text == BY_CHANNEL
            account_count = await AccountsManager.get_count()
            count = account_count['premium'] if by_group else account_count['count']
            if not count:
                await self._bot.send_message(self._chat_id, NO_ACCOUNTS_IN_DB, reply_markup=ReplyKeyboardRemove())
                return
            message = await self._send_message(HOW_MANY_ACCOUNTS_USE.format(count=count))
            RegisterHandler.register_next_step(message, self._ask_count, by_group=by_group)

    async def start(self):
        count = (await AccountsManager.get_count())['count']
        if not count:
            await self._bot.send_message(self._chat_id, NO_ACCOUNTS_IN_DB)
            return
        message = await self._send_message(SPAM_BY, reply_markup=[[KeyboardButton(BY_USER)], [KeyboardButton(BY_CHANNEL)]])
        RegisterHandler.register_next_step(message, self._ask_spam_type)
