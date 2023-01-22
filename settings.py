import pickle

from sqlalchemy.dialects.postgresql import insert

from db.models import settings

from db import database


class Settings:
    _DATA = {
        'username': 'root',
        'password': 'roottoor',
        'flood_wait': 60
    }

    @staticmethod
    def set_many(data: dict):
        Settings._DATA.update(data)

    @staticmethod
    def set(name, value):
        Settings._DATA[name] = value

    @staticmethod
    def get(key, default=None):
        return Settings._DATA.get(key, default)

    @staticmethod
    def get_all():
        return Settings._DATA

    @staticmethod
    async def save():
        query = insert(settings)
        update_query = query.on_conflict_do_update(
            index_elements=['name'],
            set_=dict(value=query.excluded.value)
        )
        await database.execute_many(update_query, [dict(name=name, value=pickle.dumps(value)) for name, value in Settings._DATA.items()])

    @staticmethod
    async def load():
        data = await database.fetch_all(settings.select())
        for i in data:
            Settings._DATA[i.name] = pickle.loads(i.value)
