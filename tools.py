import asyncio
import aiogram


async def is_admin(chatid, userid, bot):
    for i in await bot.get_chat_administrators(chat_id=chatid):
        if i["user"]["id"] == userid:
            return True

    return False
