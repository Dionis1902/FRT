import asyncio
from collections import defaultdict
from types import FunctionType

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionManager:
    _ACTIVE_CONNECTIONS: dict[str, list[WebSocket]] = defaultdict(list)
    _ACTIVE_TABS: dict[str, WebSocket] = {}
    _HANDLERS = {}
    _ON_DISCONNECT = {}

    def __init__(self, path, tab_id=None, websocket=None, on_disconnect=None):
        self._path = path
        self._tab_id = tab_id
        self._websocket = websocket
        if tab_id and on_disconnect:
            ConnectionManager._ON_DISCONNECT[tab_id] = on_disconnect

        if websocket is not None:
            self._ACTIVE_CONNECTIONS[path].append(websocket)
            self._ACTIVE_TABS[tab_id] = websocket
        elif tab_id is not None:
            self._websocket = self._ACTIVE_TABS.get(tab_id, None)

    @staticmethod
    def handler(key, self=None):
        def decorator(func):
            data = dict(func=func)
            if self:
                data['self'] = self
            ConnectionManager._HANDLERS[key] = data

        return decorator

    async def broadcast(self, **data):
        for connection in self._ACTIVE_CONNECTIONS[self._path]:
            try:
                await connection.send_json(data)
            except WebSocketDisconnect:
                self._ACTIVE_CONNECTIONS[self._path].remove(connection)

    async def alert(self, message, message_type='success'):
        await self.send_data(alert=dict(message=message, type=message_type))

    async def send_data(self, **data):
        if not self._websocket:
            return
        try:
            await self._websocket.send_json(data)
        except (Exception,):
            self._websocket = None

    async def broadcast_data(self):
        if not self._tab_id:
            return
        while True:
            data = await self._websocket.receive_json()
            if 'handler' in data and isinstance(data['handler'], dict):
                task = self._HANDLERS.get(data['handler']['func'])
                if task and isinstance(task['func'], FunctionType):
                    _self = task.get('self')
                    params = data['handler'].get('data', {})

                    if 'manager' in params:
                        params['manager'] = self
                    if _self.__code__.co_varnames:
                        params['self'] = _self(self._path)
                    elif _self:
                        params['self'] = _self()
                    asyncio.create_task(task['func'](**params))

    async def disconnect(self):
        if not self._tab_id:
            return
        self._ACTIVE_TABS.pop(self._tab_id, None)
        if self._websocket in self._ACTIVE_CONNECTIONS[self._path]:
            self._ACTIVE_CONNECTIONS[self._path].remove(self._websocket)
        if ConnectionManager._ON_DISCONNECT.get(self._tab_id):
            await ConnectionManager._ON_DISCONNECT[self._tab_id]()
