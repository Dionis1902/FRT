from pyrogram.errors import BadRequest, InviteHashExpired, UsernameNotOccupied, UsernameInvalid
from pyrogram.types import ChatPreview

from functions.base_function import Base
from functions.utils import Field, Types


class Function(Base):
    """Join selected groups"""

    __id__ = 'join_groups'
    __function_name__ = 'Join groups'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts'),
                 groups: Field(Types.INPUTS, label_name='Groups link',
                               pattern=r'^https://t.me/(\\w{5,32}|\\+\\w+|joinchat/\\w+)$',
                               placeholder='https://t.me/simple_chat'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, settings)
        self._groups = groups
        self._skip = []

    def _is_need_finish(self):
        is_need_finish = len(self._skip) == len(self._groups)
        if is_need_finish:
            self._logger.error('No one valid link')
        return is_need_finish

    @Base._check_for_flood
    async def _join_group(self, link, client, account):
        if link in self._skip:
            self._logger.error(f'Skipping {link} as it invalid')
            return True
        try:
            if 'joinchat/' in link or '+' in link:
                chat = await client.get_chat(link)
                if isinstance(chat, ChatPreview):
                    try:
                        await client.join_chat(link)
                        self._logger.info(f'Success joined to {link}', extra=dict(user_id=account.user_id))
                    except BadRequest as e:
                        if 'INVITE_REQUEST_SENT' in e.value:
                            self._logger.info(f'Request to join chat or channel has been successfully sent to {link}', extra=dict(user_id=account.user_id))
                        else:
                            raise e
                else:
                    self._logger.info(f'Already joined to {link}', extra=dict(user_id=account.user_id))
            else:
                await client.join_chat(link.split('/')[-1])
                self._logger.info(f'Success joined to {link}', extra=dict(user_id=account.user_id))
        except (UsernameNotOccupied, UsernameInvalid, InviteHashExpired):
            self._logger.error(f'Link {link} is invalid and will be skipped in the future')
            self._skip.append(link)
        return True

    async def _run(self, client, account):
        for link in self._groups:
            if not (await self._join_group(link.rstrip('/'), client, account)):
                break
            await self._wait(link != self._groups[-1])
