import asyncio

import aiosqlite


db = aiosqlite.connect("identifier.sqlite")

async def create_chat_user_tables():
    await db.execute("CREATE TABLE IF NOT EXISTS chats ("
                     "chat_id INT PRIMARY KEY"
                     ");")

    await db.execute("CREATE TABLE IF NOT EXISTS users ("
                     "chat_id INT, "
                     "user_id INT, "
                     "admin_level INT, "
                     "FOREIGN KEY (chat_id) REFERENCES chats(chat_id)"
                     ");")

    await db.commit()


async def get_db_ready():
    global db
    db = await db
    await asyncio.gather(create_chat_user_tables())

