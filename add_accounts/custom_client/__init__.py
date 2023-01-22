from pyrogram import Client, raw
from pyrogram.errors import Unauthorized

from add_accounts.custom_client.session import CustomSession


class CustomClient(Client):
    async def connect(self) -> bool:
        if self.is_connected:
            raise ConnectionError('Client is already connected')

        await self.load_session()

        self.session = CustomSession(
            self, await self.storage.dc_id(),
            await self.storage.auth_key(), await self.storage.test_mode()
        )

        await self.session.start()

        self.is_connected = True

        return bool(await self.storage.user_id())

    async def start(self):
        is_authorized = await self.connect()

        try:
            if not is_authorized:
                raise Unauthorized

            if not await self.storage.is_bot() and self.takeout:
                self.takeout_id = (await self.invoke(raw.functions.account.InitTakeoutSession())).id

            await self.invoke(raw.functions.updates.GetState())
        except (Exception, KeyboardInterrupt):
            await self.disconnect()
            raise
        else:
            self.me = await self.get_me()
            await self.initialize()

            return self

    async def start_after_connect(self):
        try:
            if not await self.storage.is_bot() and self.takeout:
                self.takeout_id = (await self.invoke(raw.functions.account.InitTakeoutSession())).id

            await self.invoke(raw.functions.updates.GetState())
        except (Exception, KeyboardInterrupt):
            await self.disconnect()
            raise
        else:
            self.me = await self.get_me()
            await self.initialize()

            return self
