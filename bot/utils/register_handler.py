from pyrogram import filters


class Data:
    pass


class RegisterHandler:
    __DATA = {}

    @staticmethod
    def register_next_step(message, func, **kwargs):
        data = RegisterHandler.get_data(message)
        for key, value in kwargs.items():
            setattr(data, key, value)
        RegisterHandler.__DATA[message.chat.id] = dict(func=func, data=data)

    @staticmethod
    def filter():
        async def wrapper(_, __, query):
            return query.chat.id in RegisterHandler.__DATA

        return filters.create(wrapper)

    @staticmethod
    def get_data(message):
        return RegisterHandler.__DATA.get(message.chat.id, {}).get('data', Data)

    @staticmethod
    def delete(message):
        RegisterHandler.__DATA.pop(message.chat.id, None)

    @staticmethod
    async def handler(client, message):
        data = RegisterHandler.__DATA.get(message.chat.id)
        if data:
            RegisterHandler.delete(message)
            await data['func'](client, message)

    @staticmethod
    def update(message, **kwargs):
        data = RegisterHandler.get_data(message)
        for key, value in kwargs.items():
            setattr(data, key, value)
