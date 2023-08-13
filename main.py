import configparser
import asyncio

import aiogram.utils.exceptions

import database
import aiosqlite
from aiogram import Bot, Dispatcher
from aiogram.dispatcher.filters import Command, ChatTypeFilter, AdminFilter, IsReplyFilter
from aiogram import types


config = configparser.ConfigParser()
config.read("config.ini")

bot = Bot(token=config["BOT"]["TOKEN"])
dp = Dispatcher(bot)

db = database.db


async def main():
    await database.get_db_ready()


@dp.message_handler(commands=["start"])
async def start(msg):
    if msg.chat.id > 0:
        await msg.reply("недопустимый чат")
        return

    await bot.send_message(msg.chat.id, "Привет! Я помощник и помогаю администаторам данного чата!")


@dp.message_handler(Command("ban"),
                    ChatTypeFilter(types.ChatType.GROUP) | ChatTypeFilter(types.ChatType.SUPERGROUP),
                    AdminFilter(True), IsReplyFilter(True))
async def ban(msg):
    user_data = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
    if not user_data["can_restrict_members"]:
        return

    await bot.ban_chat_member(msg.chat.id, msg.reply_to_message.from_user.id)
    await bot.send_message(msg.chat.id, "мне тебя жаль 😢")


@dp.message_handler(Command("unban"),
                    ChatTypeFilter(types.ChatType.GROUP) | ChatTypeFilter(types.ChatType.SUPERGROUP),
                    AdminFilter(True), IsReplyFilter(True))
async def unban(msg):
    user_data = await bot.get_chat_member(msg.chat.id, msg.from_user.id)
    if not user_data["can_restrict_members"]:
        return

    await bot.unban_chat_member(msg.chat.id, msg.reply_to_message.from_user.id)
    try:
        await bot.send_message(msg.reply_to_message.from_user.id, (await bot.get_chat(msg.chat.id))["invite_link"])
    except (aiogram.utils.exceptions.BotBlocked, aiogram.utils.exceptions.CantInitiateConversation) as e:
        await bot.send_message(msg.chat.id, "отправьте ему кто-нибудь ссылку на вступление -> "+(await bot.get_chat(msg.chat.id))["invite_link"])
    await bot.send_message(msg.chat.id, "ура!!!")


if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(dp.start_polling())
