from pyrogram import raw
from pyrogram.connection import Connection
from pyrogram.errors import RPCError, AuthKeyDuplicated
from pyrogram.raw.all import layer
from pyrogram.session import Session


class CustomSession(Session):
    async def start(self):
        for _ in range(3):
            self.connection = Connection(
                self.dc_id,
                self.test_mode,
                self.client.ipv6,
                self.client.proxy,
                self.is_media
            )
            try:
                await self.connection.connect()

                self.network_task = self.loop.create_task(self.network_worker())
                await self.send(raw.functions.Ping(ping_id=0), timeout=self.START_TIMEOUT)
                if not self.is_cdn:
                    await self.send(
                        raw.functions.InvokeWithLayer(
                            layer=layer,
                            query=raw.functions.InitConnection(
                                api_id=await self.client.storage.api_id(),
                                app_version=self.client.app_version,
                                device_model=self.client.device_model,
                                system_version=self.client.system_version,
                                system_lang_code=self.client.lang_code,
                                lang_code=self.client.lang_code,
                                lang_pack="",
                                query=raw.functions.help.GetConfig(),
                            )
                        ),
                        timeout=self.START_TIMEOUT
                    )

                self.ping_task = self.loop.create_task(self.ping_worker())

            except AuthKeyDuplicated as e:
                await self.stop()
                raise e
            except (OSError, TimeoutError, RPCError):
                await self.stop()
            except Exception as e:
                await self.stop()
                raise e
            else:
                break
        else:
            raise TimeoutError
        self.is_connected.set()
