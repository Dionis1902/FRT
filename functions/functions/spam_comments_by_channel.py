import random

from pyrogram.errors import BadRequest

from functions.functions.spam_comments import Function as SpamComments
from functions.utils import Field, Types
from utils import random_string


class Function(SpamComments):
    """Spam comments to post on behalf of the channel"""

    __id__ = 'spam_comments_by_channel'
    __function_name__ = 'Spam comments by channel'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts', only_premium=True),
                 posts: Field(Types.INPUTS, label_name='Posts',
                              pattern=r'^https://t.me/\\w{5,32}/[0-9]{1,}$',
                              placeholder='https://t.me/simple_post/22121'),
                 comments: Field(Types.TEXTAREA, label_name='Comments',
                                 placeholder='Hello world!'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, posts, comments, settings)

    async def _send_comment(self, client, post):
        channel = await client.create_channel(random_string())
        await client.set_chat_username(channel.id, random_string(32))
        try:
            await client.set_send_as_chat(post.chat.id, channel.id)
        except BadRequest as e:
            await client.delete_channel(channel.id)
            raise e
        post = await post.reply(random.choice(self._comments))
        await client.delete_channel(channel.id)
        return post
