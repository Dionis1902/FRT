import asyncio
import logging
import os.path
import random

from pyrogram.errors import SessionExpired, SessionRevoked, UserDeactivated, UserDeactivatedBan, FloodWait
from sqlalchemy.sql.expression import func

from add_accounts.custom_client import CustomClient
from db import database
from db.models import accounts as accounts_model, tasks, Status
from db.utils import delete_account
from functions.live_logger import WebsocketHandler, SystemLogFilter
from settings import Settings
from utils import proxy_to_dict


class Base:
    __function_name__ = 'Base function'

    _TASKS = {}

    def __init__(self, accounts_data, settings):
        self._accounts = accounts_data.get('ids', 1)
        self._accounts_params = accounts_data.get('params', {})
        self._settings = settings

        self._task_id = None
        self._accounts_data = []
        self._websocket_handler = None
        self._logger = None

    async def _run(self, client, account):
        pass

    def _is_need_finish(self):
        pass

    async def start(self):
        try:
            need_accounts = self._accounts if isinstance(self._accounts, int) else 0
            used_accounts = 0
            for account in self._accounts_data:
                if self._is_need_finish() or (need_accounts and need_accounts == used_accounts):
                    break

                self._logger.info(f'Using account {account.first_name} {account.last_name or ""} with id {account.user_id}')

                client = CustomClient('client', api_id=Settings.get('api_id'), api_hash=Settings.get('api_hash'),
                                      session_string=account.session_string, proxy=proxy_to_dict(account.proxy or Settings.get('proxy')),
                                      no_updates=True)
                try:
                    await client.start()
                except (SessionExpired, SessionRevoked, UserDeactivated, UserDeactivatedBan) as e:
                    await delete_account(account)
                    self._logger.error(f'Account {account.first_name} {account.last_name or ""} with id {account.user_id} is invalid "{e.__doc__}"')
                    if not self._settings.get('replace_account', True):
                        used_accounts += 1
                    continue
                try:
                    await self._run(client, account)
                except Exception as e:
                    self._logger.exception(e)
                finally:
                    if client.is_initialized:
                        await client.stop()
                    used_accounts += 1
                    if account == self._accounts_data[-1] or (need_accounts and need_accounts == used_accounts):
                        continue
                    timeout = random.uniform(*self._settings.get('account_timeout', [1, 3]))
                    self._logger.debug(f'Sleep {timeout:.2f} seconds between change accounts')
                    await asyncio.sleep(timeout)

            self._logger.info(f'Task #{self._task_id} finished')
            await database.execute(tasks.update().values(status=Status.FINISHED.value).where(tasks.c.id == self._task_id))
        except Exception as e:
            self._logger.exception(e)
            await database.execute(tasks.update().values(status=Status.ERROR.value).where(tasks.c.id == self._task_id))
        self._websocket_handler.clear()

    async def save_task(self):
        self._task_id = await database.execute(tasks.insert().values(name=self.__function_name__))

        if isinstance(self._accounts, str):
            query = accounts_model.select()
        elif isinstance(self._accounts, list):
            query = accounts_model.select().where(accounts_model.c.user_id.in_(self._accounts))
        else:
            query = accounts_model.select().order_by(func.random())
        if self._accounts_params.get('only_premium', False):
            query = query.where(accounts_model.c.is_premium)

        if not self._accounts_params.get('with_spam_block', True):
            query = query.where(accounts_model.c.spam_block == 'No')

        self._accounts_data = await database.fetch_all(query)
        user_ids = [account.user_id for account in self._accounts_data][:self._accounts if isinstance(self._accounts, int) else None]

        await database.execute(tasks.update()
                               .values(accounts=user_ids)
                               .where(tasks.c.id == self._task_id))

        self._logger = logging.getLogger(f'task_{self._task_id}')
        self._logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(user_id)s %(message)s',
                                      '%m-%d-%Y %H:%M:%S')

        self._logger.addFilter(SystemLogFilter())

        path = os.path.join(os.getcwd(), 'data', 'logs')

        if not os.path.isdir(path):
            os.makedirs(path, exist_ok=True)

        file_handler = logging.FileHandler(os.path.join(path, f'task_{self._task_id}.log'), encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

        self._websocket_handler = WebsocketHandler(self._task_id)
        self._websocket_handler.setFormatter(formatter)
        self._websocket_handler.setLevel(logging.DEBUG)
        self._logger.addHandler(self._websocket_handler)
        Base._TASKS[self._task_id] = asyncio.create_task(self.start())
        self._logger.info(f'Task #{self._task_id} {self.__function_name__} started')
        return self._task_id

    @staticmethod
    async def stop(task_id):
        task = Base._TASKS.get(task_id)
        if task and not task.done() and not task.cancelled():
            WebsocketHandler(task_id).clear()
            task.cancel()
            await database.execute(tasks.update().values(status=Status.STOPPED.value).where(tasks.c.id == task_id and tasks.c.status == Status.PROGRESS.value))
            return True
        return False

    @staticmethod
    def _check_for_flood(function):
        async def wrapper(self, *args, **kwargs):
            try:
                return await function(self, *args, **kwargs)
            except FloodWait as e:
                self._logger.warning(f'Got banned for flooding on {e.value} seconds')
                flood_wait = Settings.get('flood_wait')
                if e.value < flood_wait:
                    self._logger.info('Since the ban time is less than the maximum allowed, we wait')
                    await asyncio.sleep(e.value)
                    return await function(self, *args, **kwargs)
                else:
                    self._logger.error('Since the ban time is more than the maximum allowed, we skip this account')
                    return False
            except Exception as e:
                print(e, type(e), e.__dict__)
                self._logger.error(f'Some troubles, details "{e.__doc__}"')
            return True

        return wrapper

    async def _wait(self, is_need_wait):
        if is_need_wait:
            timeout = random.uniform(*self._settings.get('action_timeout', [1, 3]))
            self._logger.debug(f'Sleep {timeout:.2f} seconds between actions')
            await asyncio.sleep(timeout)
