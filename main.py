import os
import asyncio
import logging
from datetime import datetime, timedelta

from telegram import Update, ChatMemberUpdated
from telegram.ext import Application, CommandHandler, ChatMemberHandler, ContextTypes
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_IDS = list(map(int, os.getenv("CHANNEL_IDS", "").split(",")))
user_data = {}

async def id_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"Chat ID: {chat_id}")

async def track_join(update: ChatMemberUpdated, context: ContextTypes.DEFAULT_TYPE):
    chat = update.chat
    member = update.new_chat_member

    if member.status == "member":
        join_date = datetime.utcnow()
        chat_users = user_data.setdefault(chat.id, {})
        chat_users[member.user.id] = join_date
        logger.info(f"User {member.user.id} joined {chat.id} at {join_date}")

async def check_and_remove():
    while True:
        now = datetime.utcnow()
        for chat_id in CHANNEL_IDS:
            chat_users = user_data.get(chat_id, {})
            to_remove = [
                user_id for user_id, join_date in chat_users.items()
                if now - join_date > timedelta(days=90)
            ]
            for user_id in to_remove:
                try:
                    await application.bot.ban_chat_member(chat_id, user_id)
                    await application.bot.unban_chat_member(chat_id, user_id)
                    logger.info(f"Removed user {user_id} from {chat_id}")
                    del chat_users[user_id]
                except Exception as e:
                    logger.warning(f"Failed to remove user {user_id}: {e}")
        await asyncio.sleep(3600)

async def main():
    global application
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("id", id_command))
    application.add_handler(ChatMemberHandler(track_join, ChatMemberHandler.CHAT_MEMBER))

    asyncio.create_task(check_and_remove())

    logger.info("Bot started...")
    await application.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
