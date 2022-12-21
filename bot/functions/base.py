import asyncio
import datetime
import random
from pyrogram import Client

from bot.language import *
from bot.utils import AccountsManager, RegisterHandler, random_string, get_logger
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, ChatPreview, Chat, InlineKeyboardMarkup, InlineKeyboardButton


class Base:
    def __init__(self, bot, chat_id):
        self._bot = bot
        self._chat_id = chat_id
        self._logger, self._file = get_logger()

        self._accounts = None

    async def _ask_count(self, _, message):
        pass

    async def _ask_count_validate(self, message, text, func):
        if message.text and message.text.isdigit() and int(message.text) > 0:
            await self._send_message(text)
            RegisterHandler.register_next_step(message, func, account_counts=int(message.text))
        else:
            await self._send_message(ENTER_VALID_NUMBER)
            RegisterHandler.register_next_step(message, self._ask_count)

    async def start(self):
        count = (await AccountsManager.get_count())['count']
        if not count:
            await self._bot.send_message(self._chat_id, NO_ACCOUNTS_IN_DB)
            return
        message = await self._send_message(HOW_MANY_ACCOUNTS_USE.format(count=count))
        RegisterHandler.register_next_step(message, self._ask_count)

    async def _get_accounts(self, count, timeout=0, only_premium=False):
        if self._accounts is None:
            self._accounts = await AccountsManager.get()
            random.shuffle(self._accounts)

        accounts_used = 0
        for i, data in enumerate(self._accounts):
            if only_premium and not data['is_premium']:
                continue
            self._logger.update_account(data['user_id'])
            client = Client('client', session_string=data['session_string'], in_memory=True)
            try:
                await client.start()
            except (Exception,):
                await AccountsManager.delete(data['user_id'])
                self._logger.error('Problem with account, deleting this account from data base')
                await self._bot.send_message(self._chat_id, PROBLEM_WITH_ACCOUNT.format(id=data['user_id']))
                del self._accounts[i]
                continue
            accounts_used += 1
            yield client
            await client.stop()
            if accounts_used == count:
                break
            await asyncio.sleep(timeout)

    async def _try_execute(self, func):
        try:
            return await func
        except Exception as e:
            self._logger.error(e)

    async def _send_message(self, text, reply_markup=None):
        reply_markup = ReplyKeyboardMarkup([[KeyboardButton(CANCEL)], *(reply_markup if isinstance(reply_markup, list) else [])],
                                           resize_keyboard=True)
        return await self._bot.send_message(self._chat_id, text, reply_markup=reply_markup)

    @staticmethod
    async def _get_file_content(message, func=None, filter_=None):
        document = await message.download('data', in_memory=True)
        return list(filter(filter_, [func(line.strip()) if func else line.strip() for line in document.getvalue().decode().split('\n')]))

    @staticmethod
    def _cancel_function(func):
        async def wrapper(*args, **kwargs):
            if args[2].text == CANCEL:
                RegisterHandler.delete(args[2])
                await args[1].send_message(args[2].chat.id, CANCELED, reply_markup=ReplyKeyboardRemove())
            else:
                await func(*args, **kwargs)

        return wrapper

    @staticmethod
    async def _join_and_get(client, group):
        if group.startswith('http') and ('t.me/joinchat/' in group or '+' in group):
            chat = await client.get_chat(group)
            if isinstance(chat, ChatPreview):
                chat = await client.join_chat(group)
            if isinstance(chat, Chat):
                return chat
        else:
            return await client.join_chat(group.replace('https://t.me/', '').replace('/', ''))

    @staticmethod
    def _log_function(function):
        text = FUNCTIONS[function].split(' ', 1)[1]

        def decorator(func):
            async def wrapper(self: Base, message):
                task_name = random_string()
                self._logger.info('Function started')
                main_message = await self._bot.send_message(self._chat_id, FUNCTION_START.format(text=text), reply_markup=ReplyKeyboardRemove())
                delete_message = await self._bot.send_message(self._chat_id, CANCEL_FUNCTION,
                                                              reply_markup=InlineKeyboardMarkup(
                                                                  [[InlineKeyboardButton(CANCEL, callback_data='task_' + task_name)]]
                                                              ),
                                                              reply_to_message_id=main_message.id)
                start = datetime.datetime.now()
                emoji, end_text = SUCCESS_EMOJI, SUCCESS_END
                try:
                    task = asyncio.create_task(func(self, message), name=task_name)
                    try:
                        await task
                    except asyncio.CancelledError:
                        emoji, end_text = STOPPED_EMOJI, STOPPED_END
                    except Exception as e:
                        self._logger.exception(e)
                        emoji, end_text = ERROR_EMOJI, ERROR_END
                finally:
                    self._logger.update_account(0)
                    self._logger.info('Function ended')
                    await delete_message.delete()
                    await self._bot.send_document(self._chat_id, self._file,
                                                  caption=FUNCTION_END.format(emoji=emoji, text=text,
                                                                              end_text=end_text, time_used=datetime.datetime.now() - start),
                                                  reply_to_message_id=main_message.id)

            return wrapper

        return decorator
