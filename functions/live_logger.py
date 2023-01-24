import asyncio
import os
from logging import StreamHandler, Filter

import aiofiles

from web.connection_manager import ConnectionManager


class WebsocketHandler(StreamHandler):
    _INSTANCES = {}

    def __new__(cls, task_id):
        if not WebsocketHandler._INSTANCES.get(f'/tasks/{task_id}'):
            WebsocketHandler._INSTANCES[f'/tasks/{task_id}'] = super(WebsocketHandler, cls).__new__(cls)
        return WebsocketHandler._INSTANCES[f'/tasks/{task_id}']

    def __init__(self, task_id):
        StreamHandler.__init__(self)
        self._task_id = task_id
        self._manager = ConnectionManager(f'/tasks/{task_id}')
        self._messages = []

    @ConnectionManager.handler('init_logs', self=lambda path: WebsocketHandler._INSTANCES.get(path))
    async def _innit_logs(self, manager, task_id):
        log_file = os.path.join(os.getcwd(), 'data', 'logs', f'task_{task_id}.log')
        if not self and os.path.isfile(log_file):
            async with aiofiles.open(log_file, 'r', encoding='utf8') as f:
                await manager.send_data(logging_message=await f.readlines())
            return
        elif not self:
            return
        await manager.send_data(logging_message=self._messages)

    def emit(self, record):
        msg = self.format(record)
        self._messages.append(msg)
        asyncio.create_task(self._manager.broadcast(logging_message=msg))

    def clear(self):
        WebsocketHandler._INSTANCES.pop(f'/tasks/{self._task_id}', None)
        self._messages.clear()


class SystemLogFilter(Filter):
    def filter(self, record):
        if not hasattr(record, 'user_id'):
            record.user_id = ''
        else:
            record.user_id = f'{record.user_id} |'
        return True
