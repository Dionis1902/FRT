from settings import Settings
from web.connection_manager import ConnectionManager


class AddAccount:
    _IN_PROGRESS = False
    _PROGRESS = {'total_count': 0, 'success_added': 0, 'already_added': 0, 'error_added': 0}

    _INSTANCE = None

    def __new__(cls, *args, **kwargs):
        if AddAccount._INSTANCE or (not Settings.get('api_id') or not Settings.get('api_hash')):
            return None
        AddAccount._IN_PROGRESS = True
        AddAccount._INSTANCE = super(AddAccount, cls).__new__(cls)
        return AddAccount._INSTANCE

    async def _on_disconnect(self):
        pass

    def __init__(self, tab_id):
        self._api_id = Settings.get('api_id')
        self._api_hash = Settings.get('api_hash')
        self._manager = ConnectionManager('/accounts', tab_id, on_disconnect=self._on_disconnect)

    @staticmethod
    def in_progress():
        return AddAccount._IN_PROGRESS

    @staticmethod
    def progress():
        return AddAccount._PROGRESS

    async def _end(self):
        await self._manager.broadcast(lock_buttons=False)
        AddAccount._IN_PROGRESS = False
        AddAccount._INSTANCE = None
