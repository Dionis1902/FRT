import asyncio
from bot.functions import Functions
from bot.language import *


async def callback_handler(client, callback_query):
    if callback_query.data.startswith('task_'):
        task_name = callback_query.data[5:]
        task = [task for task in asyncio.all_tasks() if task.get_name() == task_name]
        if task:
            task[0].cancel()
            await callback_query.message.delete()
            await client.answer_callback_query(callback_query.id, text=SUCCESS_STOP_TASK)
        else:
            await client.answer_callback_query(callback_query.id, text=TASK_NOT_FOUND)

    else:
        await client.answer_callback_query(callback_query.id)
        func = getattr(Functions, callback_query.data, None)

        if func and callable(func):
            await func(client, callback_query.message.chat.id)
