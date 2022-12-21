from bot.utils.database import Client


class Whitelist:
    __USERS = []
    __is_loaded = False
    __db = Client.get_db()

    @staticmethod
    async def add(id_):
        if id_ not in Whitelist.__USERS:
            Whitelist.__USERS.append(id_)
            await Whitelist.__db.whitelist.insert_one(dict(id=id_))

    @staticmethod
    async def get():
        if not Whitelist.__is_loaded:
            Whitelist.__USERS = [document['id'] async for document in Whitelist.__db.whitelist.find()]
            Whitelist.__is_loaded = True
        return Whitelist.__USERS
