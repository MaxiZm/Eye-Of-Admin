import asyncio
import tools
import aiosqlite


db = aiosqlite.connect("identifier.sqlite")

async def create_chat_user_tables():
    await db.execute("CREATE TABLE IF NOT EXISTS chats ("
                     "chat_id INT PRIMARY KEY"
                     ");")

    await db.execute("CREATE TABLE IF NOT EXISTS users ("
                     "chat_id INT, "
                     "user_id INT, "
                     "username TEXT, "
                     "admin_level INT, "
                     "chat_user_hash BLOB PRIMARY KEY, "
                     "FOREIGN KEY (chat_id) REFERENCES chats(chat_id)"
                     ");")

    await db.execute("CREATE TABLE IF NOT EXISTS events ("
                      "event_id INTEGER PRIMARY KEY AUTOINCREMENT, "
                      "chat_id INT, "
                      "user_id INT, "
                      "event TEXT, "
                      "additional_info BLOB, "
                      "date_of_execution TIMESTAMP"
                      ");")

    await db.commit()


async def get_db_ready():
    global db
    db = await db
    await asyncio.gather(create_chat_user_tables())


async def update_db(msg, bot):
    await db.execute("REPLACE INTO chats (chat_id)"
                     "VALUES (?);", (msg.chat.id, ))

    level = (await bot.get_chat_member(msg.chat.id, msg.from_user.id))["status"]
    if level == "administrator":
        level = 1
    elif level == "creator":
        level = 2
    else:
        level = 0

    hash_value = hash(str(msg.chat.id) + str(msg.from_user.id) + str(msg.from_user.username))

    await db.execute("REPLACE INTO users (chat_id, user_id, username, admin_level, chat_user_hash) "
                     "VALUES (?, ?, ?, ?, ?);", (msg.chat.id, msg.from_user.id, msg.from_user.username, level, hash_value))

    await db.commit()