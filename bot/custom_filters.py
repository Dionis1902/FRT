from pyrogram import filters


def is_session_file():
    async def wrapper(_, __, query):
        if query.document and query.document.file_name.endswith('.session') and query.document.mime_type == 'application/vnd.sqlite3':
            return True
    return filters.create(wrapper)
