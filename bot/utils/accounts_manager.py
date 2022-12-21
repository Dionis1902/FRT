from bot.language import *
from bot.utils.database import Client
from pyrogram.types import ReplyKeyboardRemove


class AccountsManager:
    __db = Client.get_db()

    @staticmethod
    async def add(session_string, user):
        data = dict(user_id=user.id, session_string=session_string, is_premium=user.is_premium)
        document = await AccountsManager.__db.accounts.find_one({'user_id': data['user_id']})
        if document:
            if document['session_string'] == data['session_string']:
                return False
            else:
                await AccountsManager.__db.accounts.update_one({'user_id': data['user_id']}, {'$set': data})
        else:
            await AccountsManager.__db.accounts.insert_one(data)
        return True

    @staticmethod
    async def get():
        return [document async for document in AccountsManager.__db.accounts.find()]

    @staticmethod
    async def delete(id_):
        await AccountsManager.__db.accounts.delete_one({'user_id': id_})

    @staticmethod
    async def get_count():
        return {'count': await AccountsManager.__db.accounts.count_documents({}),
                'premium': await AccountsManager.__db.accounts.count_documents({'is_premium': True})}

    @staticmethod
    async def change_premium_status(id_, status):
        await AccountsManager.__db.accounts.update_one({'user_id': id_}, {'$set': {'is_premium': status}})

    @staticmethod
    async def add_user(client, message, app, reply=True):
        user = await app.get_me()
        status = await AccountsManager.add(await app.export_session_string(), user)
        if status:
            await client.send_message(message.chat.id, SUCCESS_ADD_ACCOUNT.format(user_id=user.id, first_name=user.first_name,
                                                                                  last_name=(user.last_name and user.last_name) or "",
                                                                                  phone_number=user.phone_number, is_premium=["❌", "✅"][user.is_premium]),
                                      reply_to_message_id=reply and message.id,
                                      reply_markup=ReplyKeyboardRemove())
        else:
            await client.send_message(message.chat.id, ACCOUNT_ALREADY_IN_DB.format(user_id=user.id), reply_to_message_id=reply and message.id,
                                      reply_markup=ReplyKeyboardRemove())
