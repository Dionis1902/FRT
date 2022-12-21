import os

import motor.motor_asyncio


class Client:
    __instance = None

    @staticmethod
    def get_db():
        if not Client.__instance:
            Client.__instance = motor.motor_asyncio.AsyncIOMotorClient(os.getenv('MONGO_URI'))
        return Client.__instance.frt_data
