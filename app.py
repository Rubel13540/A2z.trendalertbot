import os
import asyncio
import urllib.parse
import feedparser
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

# ট্রেডার এবং ক্রিয়েটরদের জন্য স্মার্ট এনালাইসিস জেনারেটর
def analyze_trend(traffic_str):
    try:
        clean_num = int(traffic_str.replace(',', '').replace('+', '').strip())
    except:
        clean_num = 0

    if clean_num >= 50000:
        return "📈 *ট্রেন্ড লেভেল:* 🚨 ULTRA HIGH (ভাইরাল)\n⏱️ *স্থায়িত্ব:* ২৪ - ৪৮ ঘণ্টা\n🎯 *পরামর্শ:* এখনই ট্রেন্ডিং নিউজ/কন্টেন্ট বানান বা শেয়ার মার্কেটে ইমপ্যাক্ট চেক করুন।"
    elif clean_num >= 10000:
        return "📈 *ট্রেন্ড লেভেল:* 🔥 HIGH\n⏱️ *স্থায়িত্ব:* ১২ - ২৪ ঘণ্টা\n🎯 *পরামর্শ:* ট্রেডিং এটেনশন ও শর্ট কন্টেন্টের জন্য ভালো।"
    else:
        return "📈 *ট্রেন্ড লেভেল:* ⚡ MODERATE\n⏱️ *স্থায়িত্ব:* ৬ - ১২ ঘণ্টা\n🎯 *পরামর্শ:* অর্গানিক সার্চ এনগেজমেন্টের জন্য উপযুক্ত।"

# Google Trends ডেটা ও ডাইরেক্ট লিঙ্ক প্রসেসিং
def fetch_trends(geo="BD"):
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url)
    trends = []
    
    for entry in feed.entries[:5]:
        title = entry.get("title", "No title")
        traffic = entry.get("ht_approx_traffic", entry.get("ht:approx_traffic", "100+"))
        
        # গুগল সার্চের লিঙ্ক তৈরি
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(title)}"
        analysis = analyze_trend(traffic)
        
        text = (
            f"📌 *[{title}]({search_url})*\n"
            f"📊 *সার্চ ভলিউম:* `{traffic}`\n"
            f"{analysis}\n"
            f"───────────────"
        )
        trends.append(text)
        
    return "\n\n".join(trends) if trends else "⚠️ কোনো ট্রেন্ড তথ্য পাওয়া যায়নি।"

# দেশের বাটন (Inline Keyboard)
def get_inline_keyboard():
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
            InlineKeyboardButton("🔄 রিফ্রেশ ডেটা (BD)", callback_data="trend_BD")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

# স্থায়ী নিচে থাকা মেনু বাটন (Reply Keyboard)
def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("🔥 আজকের ট্রেন্ডস"), KeyboardButton("🏠 মূল মেনু")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

# /start হ্যান্ডলার
async def start(update, context):
    welcome_text = (
        "🚀 *স্মার্ট ট্রেন্ডস ও ট্রেডিং এনালাইজার বটে স্বাগতম!*\n\n"
        "এখানে রিয়েল-টাইম সার্চ ট্রেন্ডের পাশাপাশি কন্টেন্ট ও মার্কেট ইমপ্যাক্ট এনালাইসিস দেখতে পাবেন।\n\n"
        "👇 নিচের বাটন থেকে দেশ নির্বাচন করুন অথবা কিবোর্ড ব্যবহার করুন:"
    )
    # স্থায়ী কিবোর্ড চালু করা
    await update.message.reply_text("কিবোর্ড অপশন চালু করা হয়েছে।", reply_markup=get_reply_keyboard())
    
    # ইনলাইন মেনু দেখানো
    await update.message.reply_text(
        welcome_text, 
        reply_markup=get_inline_keyboard(), 
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

# টেক্সট বটনের মেসেজ হ্যান্ডলার
async def handle_message(update, context):
    text = update.message.text
    if text in ["🏠 মূল মেনু", "🔥 আজকের ট্রেন্ডস"]:
        await start(update, context)

# বাটন ক্লিক ইভেন্ট
async def button_click(update, context):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("trend_"):
        geo = query.data.split("_")[1]
        await query.edit_message_text("⏳ *অ্যানালাইসিস ডেটা প্রসেসিং করা হচ্ছে...*", parse_mode='Markdown')
        
        trend_text = fetch_trends(geo)
        response = f"📊 *দেশ:* `{geo}` (রিয়েল-টাইম মার্কেট ট্রেন্ড)\n───────────────\n\n{trend_text}"
        
        await query.edit_message_text(
            response, 
            reply_markup=get_inline_keyboard(), 
            parse_mode='Markdown',
            disable_web_page_preview=True
        )

# মেইন লুপ
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN পাওয়া যায়নি!")
        return

    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Render Server Health
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, server.serve_forever)

    print("বট সফলভাবে চালু হয়েছে...")
    async with application:
        await application.start()
        await application.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
