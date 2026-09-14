import os
import random
import asyncio
import threading
import requests
from io import BytesIO
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Real Visitor Traffic Bot is Running!"

# ----------------- রিয়েল ব্রাউজার হেডার -----------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.80 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
]

REFERRERS = [
    "https://www.google.com/",
    "https://www.facebook.com/",
    "https://t.co/",
    "https://www.bing.com/",
    "https://duckduckgo.com/"
]

user_data = {}
active_tests = {}

# ----------------- স্ক্রিনশট ও ট্রাফিক জেনারেটর -----------------
def capture_and_visit(url, headers):
    session = requests.Session()
    session.headers.update(headers)
    
    # মোট ২ ধাপে রিকোয়েস্ট (কুকি ও আসল পেজ লোড বাইপাস)
    res = session.get(url, timeout=20, allow_redirects=True)
    
    # ফ্রি API ব্যবহার করে লাইভ স্ক্রিনশট প্রুফ তৈরি
    shot_url = f"https://render-tron.appspot.com/screenshot/{url}"
    img_res = requests.get(shot_url, timeout=15)
    
    img_data = BytesIO(img_res.content) if img_res.status_code == 200 else None
    return res.status_code, img_data

async def run_traffic_process(url, chat_id, context, total_runs, delay_mode):
    stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Test Now", callback_data="stop_test")]])
    
    delay = 2 if delay_mode == "fast" else (5 if delay_mode == "medium" else 10)
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🚀 *Traffic Test Started!*\n🔗 **URL:** `{url}`\n📊 **Target Visits:** `{total_runs}`\n⚡ **Mode:** `{delay_mode.upper()}`\n\n_থামাতে চাইলে নিচের বাটনটি চাপুন।_",
        reply_markup=stop_keyboard,
        parse_mode='Markdown'
    )

    success_count = 0
    fail_count = 0
    screenshot_sent = False

    loop = asyncio.get_event_loop()

    for i in range(1, total_runs + 1):
        if active_tests.get(chat_id) == False:
            await context.bot.send_message(chat_id=chat_id, text=f"⏹️ *Test Stopped by User!*\n\n🟢 Success: {success_count}\n🔴 Failed: {fail_count}", parse_mode='Markdown')
            return

        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Referer": random.choice(REFERRERS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1"
        }

        try:
            status, img_data = await loop.run_in_executor(None, capture_and_visit, url, headers)

            if status == 200:
                success_count += 1
                
                # প্রথম সফল ভিজিটের স্ক্রিনশট প্রমাণ হিসেবে পাঠানো
                if img_data and not screenshot_sent:
                    screenshot_sent = True
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=img_data,
                        caption="📸 *Live Proof:* আপনার ওয়েবসাইটে সফলভাবে প্রবেশ করা হয়েছে এবং পেজ লোড হয়েছে!",
                        parse_mode='Markdown'
                    )
            else:
                fail_count += 1
        except Exception:
            fail_count += 1

        # প্রতি ৫টি ভিজিটে আপডেট পাঠানো
        if i % 5 == 0 or i == total_runs:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔄 *Progress:* `{i}/{total_runs}` visits sent.\n🟢 Success: {success_count} | 🔴 Failed: {fail_count}",
                reply_markup=stop_keyboard,
                parse_mode='Markdown'
            )

        await asyncio.sleep(random.uniform(delay - 0.5, delay + 2.0))

    active_tests[chat_id] = False
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ *Traffic Test Completed Successfully!*\n\n🎯 **Total Target:** {total_runs}\n🟢 **Success Count:** {success_count}\n🔴 **Failed Count:** {fail_count}",
        parse_mode='Markdown'
    )

# ----------------- কিবোর্ড ও ইনলাইন মেনু -----------------

def get_count_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("30 Visits", callback_data="count_30"), InlineKeyboardButton("50 Visits", callback_data="count_50")],
        [InlineKeyboardButton("100 Visits", callback_data="count_100")]
    ])

def get_speed_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Fast (2s)", callback_data="speed_fast"), InlineKeyboardButton("🚶 Medium (5s)", callback_data="speed_medium")],
        [InlineKeyboardButton("🛡️ Human Like (10s)", callback_data="speed_human")]
    ])

# ----------------- হ্যান্ডলারস -----------------

async def start(update, context):
    active_tests[update.message.chat_id] = False
    welcome = (
        "🤖 *Advanced Traffic Simulation Bot*\n\n"
        "এই বটের মাধ্যমে রিয়েল ইউজার-এজেন্ট ব্যবহার করে ওয়েবসাইটের ভিজিটর টেস্ট করা যায়।\n\n"
        "👇 শুরু করতে নিচে **🚀 Start Traffic Test** এ চাপ দিন।"
    )
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🚀 Start Traffic Test")],
        [KeyboardButton("🛑 Stop Current Test")]
    ], resize_keyboard=True)
    
    await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode='Markdown')

async def handle_message(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    if text == "🚀 Start Traffic Test":
        user_data[user_id] = {"state": "WAITING_FOR_URL"}
        await update.message.reply_text("🔗 **দয়া করে আপনার ওয়েবসাইটের লিংক (URL) পাঠান:**\n*(উদাহরণ: `https://example.com`)*", parse_mode='Markdown')

    elif text == "🛑 Stop Current Test":
        active_tests[chat_id] = False
        await update.message.reply_text("🛑 **রানিং টেস্ট বন্ধ করা হয়েছে!**")

    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_URL":
        if text.startswith("http://") or text.startswith("https://"):
            user_data[user_id]["url"] = text
            user_data[user_id]["state"] = "WAITING_FOR_COUNT"
            await update.message.reply_text("📊 **কতবার ভিজিট করাতে চান?**", reply_markup=get_count_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ **অবৈধ লিংক!** সঠিক URL দিন (http:// বা https:// সহ)।")

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    await query.answer()

    if query.data == "stop_test":
        active_tests[chat_id] = False
        await query.edit_message_text("🛑 **টেস্ট সাথে সাথে বন্ধ করা হয়েছে!**")

    elif query.data.startswith("count_"):
        count = int(query.data.split("_")[1])
        user_data[user_id]["count"] = count
        user_data[user_id]["state"] = "WAITING_FOR_SPEED"
        await query.edit_message_text("⚡ **ভিজিটের গতি (Speed / Delay) বেছে নিন:**", reply_markup=get_speed_keyboard(), parse_mode='Markdown')

    elif query.data.startswith("speed_"):
        speed_mode = query.data.split("_")[1]
        if user_data.get(user_id, {}).get("url") and user_data.get(user_id, {}).get("count"):
            url = user_data[user_id]["url"]
            count = user_data[user_id]["count"]
            user_data[user_id] = None
            active_tests[chat_id] = True
            
            await query.edit_message_text(f"✅ **{count} Visits ({speed_mode.upper()} Mode) Selected.** Starting...", parse_mode='Markdown')
            asyncio.create_task(run_traffic_process(url, chat_id, context, count, speed_mode))

# ----------------- সার্ভার রানার -----------------
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    server.serve_forever()

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        threading.Thread(target=run_flask, daemon=True).start()
        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        application.run_polling()
