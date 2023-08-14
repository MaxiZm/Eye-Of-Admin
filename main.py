import configparser
import asyncio
import tools
import aiogram.utils.exceptions
import database
import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.filters import Command, ChatTypeFilter, AdminFilter, IsReplyFilter
from aiogram import types
from datetime import datetime, timedelta
import pickle

config = configparser.ConfigParser()
config.read("config.ini")

bot = Bot(token=config["BOT"]["TOKEN"])
dp = Dispatcher(bot)

db = database.db


@dp.message_handler(commands=["start"])
async def start(msg):
    await database.update_db(msg, bot)
    if msg.chat.id > 0:
        await msg.reply("привет! я работаю в группах")
        return

    await bot.send_message(msg.chat.id, "Привет! Я помощник и помогаю администаторам данного чата!")


@dp.message_handler(Command("ban") | Command("dban"),
                    ChatTypeFilter(types.ChatType.GROUP) | ChatTypeFilter(types.ChatType.SUPERGROUP),
                    AdminFilter(True), IsReplyFilter(True))
async def ban(msg):
    await database.update_db(msg, bot)
    user_data = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
    if not user_data["can_restrict_members"]:
        await msg.reply("вы не админ!")
        return

    if await tools.is_admin(msg.chat.id, msg.reply_to_message.from_user.id, bot):
        await msg.reply(f"забанить не выйдет, так как @{msg.reply_to_message.from_user.username} - админ")
        return

    await asyncio.gather(bot.ban_chat_member(msg.chat.id, msg.reply_to_message.from_user.id),
                         bot.send_message(msg.chat.id, "мне тебя жаль 😢"))
    if msg.text.startswith("/dban"):
        await asyncio.gather(bot.delete_message(msg.chat.id, msg.reply_to_message.message_id),
                             bot.delete_message(msg.chat.id, msg.message_id))


@dp.message_handler(Command("unban"),
                    ChatTypeFilter(types.ChatType.GROUP) | ChatTypeFilter(types.ChatType.SUPERGROUP),
                    AdminFilter(True), IsReplyFilter(True))
async def unban(msg):
    await database.update_db(msg, bot)
    user_data = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
    if not user_data["can_restrict_members"]:
        await msg.reply("вы не админ!")
        return
    await bot.unban_chat_member(msg.chat.id, msg.reply_to_message.from_user.id)
    try:
        await bot.send_message(msg.reply_to_message.from_user.id, (await bot.get_chat(msg.chat.id))["invite_link"])
    except (aiogram.utils.exceptions.BotBlocked, aiogram.utils.exceptions.CantInitiateConversation) as e:
        await bot.send_message(msg.chat.id,
                               "отправьте ему кто-нибудь ссылку на вступление -> " + (await bot.get_chat(msg.chat.id))[
                                   "invite_link"])
    await bot.send_message(msg.chat.id, "ура!!!")


@dp.message_handler(commands=['мут', 'mute'], commands_prefix='./', is_chat_admin=True)
async def mute(msg):
    await database.update_db(msg, bot)

    rep = lambda: msg.reply(
        f'<b>замутил:</b> {name1}\n<b>анскилл:</b> <a href="tg://user?id={msg.reply_to_message.from_user.id}">{msg.reply_to_message.from_user.first_name}</a>\n<b>срок наказания:</b> {muteint} {mutetype}\n<b>причина:</b> {comment}',
        parse_mode='html')

    name1 = msg.from_user.get_mention(as_html=True)
    user_data = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
    if not user_data["can_restrict_members"]:
        await msg.reply("вы не админ!")
        return
    if not msg.reply_to_message:
        await msg.reply("эта команда должна быть ответом на сообщение!")
        return

    if await tools.is_admin(msg.chat.id, msg.reply_to_message.from_user.id, bot):
        await msg.reply(f"замутить не выйдет, так как @{msg.reply_to_message.from_user.username} - админ")
        return

    try:
        muteint = int(msg.text.split()[1])
        mutetype = msg.text.split()[2]
        comment = " ".join(msg.text.split()[3:])
    except IndexError:
        await msg.reply('не хватает аргументов!\nПример:\n`/мут 1 ч причина`')
        return
    if mutetype == "ч" or mutetype == "часов" or mutetype == "час":
        dt = datetime.now() + timedelta(hours=muteint)
        timestamp = dt.timestamp()
        await bot.restrict_chat_member(msg.chat.id, msg.reply_to_message.from_user.id,
                                       types.ChatPermissions(False), until_date=timestamp)
        await rep()
    elif mutetype == "м" or mutetype == "минут" or mutetype == "минуты":
        dt = datetime.now() + timedelta(minutes=muteint)
        timestamp = dt.timestamp()
        await bot.restrict_chat_member(msg.chat.id, msg.reply_to_message.from_user.id,
                                       types.ChatPermissions(False), until_date=timestamp)
        await rep()
    elif mutetype == "д" or mutetype == "дней" or mutetype == "день":
        dt = datetime.now() + timedelta(days=muteint)
        timestamp = dt.timestamp()
        await bot.restrict_chat_member(msg.chat.id, msg.reply_to_message.from_user.id,
                                       types.ChatPermissions(False), until_date=timestamp)
        await rep()


@dp.message_handler(Command("event"), ChatTypeFilter(types.ChatType.GROUP) | ChatTypeFilter(types.ChatType.SUPERGROUP),
                    AdminFilter(True))
async def create_event(msg):
    await database.update_db(msg, bot)

    if len(msg.text.split()) < 5:
        await msg.reply("неверное число параметров в сообщении")

    event_type = msg.text.split()[1]
    num = int(msg.text.split()[2])
    time_type = msg.text.split()[3]
    info = " ".join(msg.text.split()[4:])

    if event_type == "changeTitle":
        date = datetime.now()
        if time_type in ["д", "дней", "день"]:
            date += timedelta(days=num)

        elif time_type in ["ч", "часов", "час"]:
            date += timedelta(hours=num)

        elif time_type in ["м", "минут", "минута"]:
            date += timedelta(minutes=num)

        add_info = pickle.dumps(str(info))

        await db.execute("INSERT INTO events (chat_id, user_id, event, additional_info, date_of_execution) VALUES "
                         "(?, ?, ?, ?, ?);", (msg.chat.id, msg.from_user.id, event_type, add_info, date))
        await db.commit()

        await msg.reply(f"прекрасно! создал событие <b>{event_type}</b> через {num} {time_type}.", parse_mode='html')


@dp.message_handler(ChatTypeFilter(types.ChatType.GROUP) | ChatTypeFilter(types.ChatType.SUPERGROUP))
async def other(msg):
    await database.update_db(msg, bot)


async def event_handler():
    while True:
        for event in await (
                await db.execute("SELECT event_id, chat_id, user_id, event, additional_info, date_of_execution FROM "
                                 "events WHERE date_of_execution <= ?;",
                                 (datetime.now(),))).fetchall():
            result = await tools.execute_event(event_id=event[0], chat_id=event[1], user_id=event[2], event_type=event[3],
                                               additional_info=pickle.loads(event[4]), execution_time=event[5], bot=bot)
            if result:
                await db.execute("DELETE FROM events WHERE event_id=?", (event[0],))
        await asyncio.sleep(1)


async def main():
    await database.get_db_ready()
    await asyncio.gather(dp.start_polling(),
                         event_handler())


if __name__ == "__main__":
    asyncio.run(main())
