import random

from pyrogram.errors import UsernameNotOccupied, UsernameInvalid, UserPrivacyRestricted, UserNotMutualContact, UserIsBlocked

from functions.base_function import Base
from functions.utils import Field, Types


class Function(Base):
    """Spam messages to private messages"""

    __id__ = 'spam_pm'
    __function_name__ = 'Spam PM'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts', with_spam_block=False),
                 users: Field(Types.INPUTS, label_name='Users',
                              pattern=r'^@\\w{5,32}|https://t.me/\\w{5,32}$',
                              placeholder='@username'),
                 messages: Field(Types.TEXTAREA, label_name='Messages',
                                 placeholder='Hello, how are you?'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, settings)
        self._users = users
        self._messages = messages
        self._skip = []

    def _is_need_finish(self):
        is_need_finish = len(self._skip) == len(self._users)
        if is_need_finish:
            self._logger.error('No one valid username')
        return is_need_finish

    @Base._check_for_flood
    async def _send_message(self, user, client, account):
        username = user.rstrip('/').replace('https://t.me/', '')

        if user in self._skip:
            self._logger.error(f'The username @{username} is not occupied by anyone')
            return True

        try:
            message = random.choice(self._messages)
            await client.send_message(username, message)
            self._logger.info(f'Success send message to @{username}, message "{message}"', extra=dict(user_id=account.user_id))
        except (UserPrivacyRestricted, UserNotMutualContact, UserIsBlocked) as e:
            self._logger.error(f'Some troubles with user @{username}, details "{e.__doc__}"')
            self._skip.append(user)
        except (UsernameNotOccupied, UsernameInvalid):
            self._logger.error(f'The username @{username} is not occupied by anyone')
            self._skip.append(user)
        return True

    async def _run(self, client, account):
        for user in self._users:
            if not (await self._send_message(user, client, account)):
                break
            await self._wait(user != self._users[-1])
