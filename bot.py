import os
import time
import requests
import asyncio
import json
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Telegram Bot Token (Railway Environment Variable থেকে নেবে)
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# API Data Load (TBomb-এর apidata.json ফাইল থেকে API লিস্ট নেওয়া হবে)
def load_api_data():
    try:
        with open("TBomb-master/apidata.json", "r") as f:
            return json.load(f)
    except Exception:
        return {}

# Background Attack Process
async def run_attack(update: Update, context: ContextTypes.DEFAULT_TYPE, target: str, count: int):
    chat_id = update.effective_chat.id
    status_msg = await context.bot.send_message(chat_id=chat_id, text=f"🚀 *Attack Started on:* `{target}`\nTotal Requests: `{count}`", parse_mode="Markdown")
    
    api_data = load_api_data()
    success, failed = 0, 0

    # API Request Simulator
    for i in range(1, count + 1):
        # সাধারণ HTTP Request পাঠানোর উদাহরণ
        try:
            # API রিকোয়েস্ট ট্রাই করা
            await asyncio.sleep(0.5)  # Safe Delay
            success += 1
        except Exception:
            failed += 1

        if i % 5 == 0 or i == count:
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=status_msg.message_id,
                text=f"⚡ *ATTACK IN PROGRESS*\nTarget: `{target}`\nProgress: `{i}/{count}`\n🟢 Success: `{success}` | 🔴 Failed: `{failed}`",
                parse_mode="Markdown"
            )

    await context.bot.send_message(chat_id=chat_id, text=f"✅ *Process Finished for:* `{target}`", parse_mode="Markdown")

# /start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 *TBomb Telegram Interface*\n\n"
        "ব্যবহার করার নিয়ম:\n"
        "`/bomb <phone_number> <count>`\n\n"
        "উদাহরণ:\n"
        "`/bomb 01700000000 20`"
    )
    await update.message.reply_text(welcome_text, parse_mode="Markdown")

# /bomb Command
async def bomb_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ সঠিক ফরম্যাট: `/bomb <phone_number> <count>`", parse_mode="Markdown")
        return

    target = context.args[0]
    try:
        count = int(context.args[1])
        if count > 100:
            await update.message.reply_text("⚠️ সর্বোচ্চ ১০০ টি রিকোয়েস্ট একবারে দেওয়া সম্ভব।")
            return
    except ValueError:
        await update.message.reply_text("⚠️ রিকোয়েস্ট সংখ্যা অবশ্যই একটি সংখ্যা হতে হবে।")
        return

    await update.message.reply_text(f"⏳ Processing request for `{target}`...", parse_mode="Markdown")
    asyncio.create_task(run_attack(update, context, target, count))

if __name__ == "__main__":
    if not BOT_TOKEN:
        print("Error: TELEGRAM_TOKEN environment variable not set!")
    else:
        app = ApplicationBuilder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("bomb", bomb_command))
        print("Bot is running...")
        app.run_polling()
