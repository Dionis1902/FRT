import random
from pyrogram.errors import MsgIdInvalid, ChatWriteForbidden, UserBannedInChannel, UsernameInvalid, UsernameNotOccupied
from functions.base_function import Base
from functions.utils import Field, Types


class Function(Base):
    """Spam comments to post"""

    __id__ = 'spam_comments'
    __function_name__ = 'Spam comments'

    def __init__(self, accounts: Field(Types.ACCOUNTS, label_name='Accounts'),
                 posts: Field(Types.INPUTS, label_name='Posts',
                              pattern=r'^https://t.me/\\w{5,32}/[0-9]{1,}$',
                              placeholder='https://t.me/simple_post/22121'),
                 comments: Field(Types.TEXTAREA, label_name='Comments',
                                 placeholder='Hello world!'),
                 settings: Field(Types.SETTINGS, label_name='Settings')):
        super().__init__(accounts, settings)
        self._posts = posts
        self._comments = comments
        self._skip = []

    def _is_need_finish(self):
        is_need_finish = len(self._skip) == len(self._posts)
        if is_need_finish:
            self._logger.error('No one valid post')
        return is_need_finish

    async def _send_comment(self, client, post):
        return await post.reply(random.choice(self._comments))

    @Base._check_for_flood
    async def _try_send_comment(self, post_url, client, account):
        if post_url in self._skip:
            self._logger.error(f'The post {post_url} is invalid')
            return True
        channel, post_id = post_url.rstrip('/').split('/')[-2:]
        try:
            post = await client.get_discussion_message(channel, int(post_id))
            comment = await self._send_comment(client, post)
            self._logger.info(f'Success send comment https://t.me/{channel}/{post_id}?comment={comment.id}',
                              extra=dict(user_id=account.user_id))
        except MsgIdInvalid:
            self._logger.error(f'The post is invalid {post_url}')
            self._skip.append(post_url)
        except (UsernameNotOccupied, UsernameInvalid):
            self._logger(f'Channel @{channel} don\'t exist')
            self._skip.append(post_url)
        except (ChatWriteForbidden, UserBannedInChannel) as e:
            self._logger.error(f'Can\'t write comment to post {post_url}, details "{e.__doc__}"', extra=dict(user_id=account.user_id))
        return True

    async def _run(self, client, account):
        for post in self._posts:
            if not (await self._try_send_comment(post, client, account)):
                break
            await self._wait(post != self._posts[-1])

