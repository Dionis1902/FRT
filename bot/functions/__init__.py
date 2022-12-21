from bot.functions.reaction_raid import ReactionRaid
from bot.functions.spam_to_comments import SpamToComments
from bot.functions.spam_to_chat import SpamToChat
from bot.functions.spam_to_pp import SpamToPP
from bot.functions.join_chats import JoinChats
from bot.functions.leave_chat import LeaveChat
from bot.functions.vote_poll import VotePoll


class Functions:
    @staticmethod
    async def spam_to_comments(client, chat_id):
        await SpamToComments(client, chat_id).start()

    @staticmethod
    async def spam_to_chat(client, chat_id):
        await SpamToChat(client, chat_id).start()

    @staticmethod
    async def spam_to_pp(client, chat_id):
        await SpamToPP(client, chat_id).start()

    @staticmethod
    async def join_chats(client, chat_id):
        await JoinChats(client, chat_id).start()

    @staticmethod
    async def leave_chats(client, chat_id):
        await LeaveChat(client, chat_id).start()

    @staticmethod
    async def reaction_raid(client, chat_id):
        await ReactionRaid(client, chat_id).start()

    @staticmethod
    async def vote_poll(client, chat_id):
        await VotePoll(client, chat_id).start()
