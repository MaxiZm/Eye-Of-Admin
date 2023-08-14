import asyncio
import aiogram


async def is_admin(chatid, userid, bot):
    for i in await bot.get_chat_administrators(chat_id=chatid):
        if i["user"]["id"] == userid:
            return True

    return False


async def execute_event(event_id, chat_id, user_id, event_type, additional_info, execution_time, bot):
    if event_type == "changeTitle":
        await bot.set_chat_title(chat_id, additional_info)
        return True

