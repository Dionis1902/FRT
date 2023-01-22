import random

from pyrogram.errors import UsernameNotOccupied, UsernameInvalid

from functions.base_function import Base
from functions.utils import Field, Types

all_reactions = ['☃', '⚡', '✍', '❤', '❤\u200d🔥', '🆒', '🌚', '🌭', '🍌', '🍓', '🍾', '🎃', '🎄', '🎅', '🎉', '🏆', '🐳', '👀', '👌', '👎', '👏', '👨\u200d💻',
                 '👻', '💅', '💋', '💔', '💩', '💯', '🔥', '🕊', '🖕', '🗿', '😁', '😇', '😈', '😍', '😐', '😢', '😨', '😭', '😱', '😴', '🙈', '🙏', '🤓', '🤔', '🤗',
                 '🤝', '🤡', '🤣', '🤨', '🤩', '🤪', '🤬', '🤮', '🤯', '🥰', '🥱', '🥴', '\U0001fae1']


class Function(Base):
    """Add reaction to message or post"""

    __id__ = 'reaction_raid'
    __function_name__ = 'Reaction raid'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts'),
                 posts: Field(Types.INPUTS, label_name='Posts',
                              pattern=r'^https://t.me/\\w{5,32}/[0-9]{1,}$',
                              placeholder='https://t.me/simple_post/22121'),
                 reactions: Field(Types.REACTIONS, label_name='Reactions'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, settings)
        self._posts = posts
        self._reactions = reactions
        self._skip = []

    async def _reaction(self, post_url, client, account):
        if post_url in self._skip:
            self._logger.error(f'The post {post_url} is invalid')
            return True
        channel, post_id = post_url.rstrip('/').split('/')[-2:]
        try:
            group = await client.get_chat(channel)
        except (UsernameNotOccupied, UsernameInvalid):
            self._logger.error(f'Channel @{channel} don\'t exist')
            self._skip.append(post_url)
            return True

        if not group.available_reactions:
            self._logger.error(f'Reaction don\'t available in this channel @{channel}')
            self._skip.append(post_url)
            return True

        if group.available_reactions.all_are_enabled:
            available_reactions = self._reactions if isinstance(self._reactions, list) else all_reactions
        else:
            available_reactions = [i.emoji for i in group.available_reactions.reactions]
            if isinstance(self._reactions, list):
                available_reactions = list(set(available_reactions) & set(self._reactions))
        if not available_reactions:
            self._logger.error(f'Reactions you selected are not available in channel @{channel}')
            self._skip.append(post_url)
            return True
        reaction = random.choice(available_reactions)
        await client.send_reaction(group.id, int(post_id), reaction)
        self._logger.info(f'Success add reaction {reaction} to {post_url}', extra=dict(user_id=account.user_id))
        return True

    async def _run(self, client, account):
        for post in self._posts:
            if not (await self._reaction(post, client, account)):
                break
            await self._wait(post != self._posts[-1])
