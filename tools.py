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
    if event_type == "unbanDelay":
        await bot.unban_chat_member(chat_id, additional_info)
        try:
            await bot.send_message(additional_info, (await bot.get_chat(chat_id))["invite_link"])
        except (aiogram.utils.exceptions.BotBlocked, aiogram.utils.exceptions.CantInitiateConversation) as e:
            await bot.send_message(chat_id,
                                   f'отправьте <a href="tg://user?id={additional_info}">ему</a> кто-нибудь ссылку на вступление -> ' +
                                   (await bot.get_chat(chat_id))[
                                       "invite_link"], parse_mode="html")
        await bot.send_message(chat_id, f'<a href="tg://user?id={additional_info}">человек</a> разбанен',
                               parse_mode="html")
        return True


