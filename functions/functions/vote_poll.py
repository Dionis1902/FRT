import random

from pyrogram.errors import UsernameInvalid, UsernameNotOccupied

from functions.base_function import Base
from functions.utils import Field, Types


class Function(Base):
    """Vote in poll"""

    __id__ = 'vote_poll'
    __function_name__ = 'Vote poll'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts'),
                 polls: Field(Types.POLL, label_name='Polls',
                              pattern=r'^https://t.me/\\w{5,32}/[0-9]{1,}$',
                              placeholder='https://t.me/simple_post/22121'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, settings)
        self._polls = polls
        self._skip = []

    def _is_need_finish(self):
        is_need_finish = len(self._skip) == len(self._polls)
        if is_need_finish:
            self._logger.error('No one valid link')
        return is_need_finish

    @Base._check_for_flood
    async def _vote_poll(self, link, option, client, account):
        if link in self._skip:
            self._logger.error(f'Skipping {link} as it invalid or not poll')
            return True

        group, post_id = link.rstrip('/').split('/')[-2:]
        try:
            message = await client.get_messages(group, int(post_id))
        except (UsernameNotOccupied, UsernameInvalid):
            self._logger(f'Group @{group} don\'t exist')
            self._skip.append(link)
            return True

        if not message or not message.poll:
            self._logger.error(f'Skipping {link} as it invalid or not poll')
            self._skip.append(link)
            return True
        max_options = len(message.poll.options) - 1
        if option == 'random':
            option = random.randint(0, max_options)
        else:
            option = int(option) - 1
            if option > max_options:
                option = max_options
        await client.vote_poll(group, int(post_id), option)
        self._logger.info(f'Voted in {link} for option "{message.poll.options[option].text}"', extra=dict(user_id=account.user_id))
        return True

    async def _run(self, client, account):
        links = list(self._polls.keys())
        for link, option in self._polls.items():
            if not (await self._vote_poll(link, option, client, account)):
                break
            await self._wait(link != links[-1])
