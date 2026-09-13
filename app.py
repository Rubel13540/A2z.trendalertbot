import os
import asyncio
import feedparser
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

# Google Trends থেকে ডেটা সংগ্রহের ফাংশন
def fetch_trends(geo="BD"):
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url)
    trends = []
    
    for entry in feed.entries[:5]:
        title = entry.get("title", "No title")
        traffic = entry.get("ht_approx_traffic", entry.get("ht:approx_traffic", None))
        
        text = f"🔥 *{title}*"
        if traffic:
            text += f"\n📊 সার্চ: `{traffic}`"
        
        trends.append(text)
        
    return "\n\n".join(trends) if trends else "⚠️ কোনো ট্রেন্ড তথ্য পাওয়া যায়নি।"

# সুন্দর বাটন তৈরি করার লেআউট
def get_main_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("🇧🇩 বাংলাদেশ", callback_data="trend_BD"),
            InlineKeyboardButton("🇺🇸 আমেরিকা", callback_data="trend_US"),
        ],
        [
            InlineKeyboardButton("🇮🇳 ভারত", callback_data="trend_IN"),
            InlineKeyboardButton("🇬🇧 যুক্তরাজ্য", callback_data="trend_GB"),
        ],
        [
            InlineKeyboardButton("🔄 রিফ্রেশ (BD)", callback_data="trend_BD")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# /start কমান্ড হ্যান্ডলার
async def start(update, context):
    welcome_text = (
        "✨ *ওয়েলকাম টু ট্রেন্ড অ্যালার্ট বট!* ✨\n\n"
        "এখানে আপনি যেকোনো দেশের লেটেস্ট গুগল সার্চ ট্রেন্ড এক ক্লিকে দেখতে পাবেন।\n\n"
        "👇 নিচে দেশের বাটনে ক্লিক করুন অথবা মেনু ব্যবহার করুন:"
    )
    await update.message.reply_text(
        welcome_text, 
        reply_markup=get_main_keyboard(), 
        parse_mode='Markdown'
    )

# /trends কমান্ড হ্যান্ডলার
async def trends_command(update, context):
    geo = "BD"
    if context.args:
        geo = context.args[0].upper()
    
    msg = await update.message.reply_text(f"⏳ *{geo}* এর ট্রেন্ডিং ডেটা আনা হচ্ছে...", parse_mode='Markdown')
    trend_text = fetch_trends(geo)
    
    response = f"📌 *দেশ:* {geo}\n-------------------------\n{trend_text}"
    await msg.edit_text(response, reply_markup=get_main_keyboard(), parse_mode='Markdown')

# বাটন ক্লিকের ইভেন্ট হ্যান্ডলার
async def button_click(update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("trend_"):
        geo = query.data.split("_")[1]
        await query.edit_message_text(f"⏳ *{geo}* এর আপডেট তথ্য আনা হচ্ছে...", parse_mode='Markdown')
        
        trend_text = fetch_trends(geo)
        response = f"📌 *দেশ:* {geo}\n-------------------------\n{trend_text}"
        
        await query.edit_message_text(
            response, 
            reply_markup=get_main_keyboard(), 
            parse_mode='Markdown'
        )

# মূল অ্যাসিনক্রোনাস লুপ ও সার্ভিস
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN পাওয়া যায়নি!")
        return

    application = ApplicationBuilder().token(token).build()
    
    # হ্যান্ডলার যুক্ত করা
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("trends", trends_command))
    application.add_handler(CallbackQueryHandler(button_click))

    # Web Server for Render Health Check
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, server.serve_forever)

    # Polling Start
    print("বট সফলভাবে চালু হয়েছে...")
    async with application:
        await application.start()
        await application.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
