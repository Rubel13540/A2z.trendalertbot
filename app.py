import os
import random
import asyncio
import threading
import requests
from bs4 import BeautifulSoup
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Ultra Headless Engine is Active!"

# ----------------- ফোরেনসিক লেভেল ডিভাইস ও ব্রাউজার ফিঙ্গারপ্রিন্টিং -----------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
]

REFERRERS = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://l.facebook.com/",
    "https://t.co/",
    "https://www.pinterest.com/pin/",
    "https://www.linkedin.com/feed/"
]

user_data = {}
active_tests = {}

# ----------------- হিউম্যান বিহেভিওরাল সিমুলেটর -----------------
def execute_stealth_browser_emulation(url):
    session = requests.Session()
    
    # র্যান্ডম সিকিউরিটি ও ফিঙ্গারপ্রিন্ট হেডার্স
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERRERS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Ch-Ua": '"Not/A)Brand";v="8", "Chromium";v="126"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "cross-site",
        "Sec-Fetch-User": "?1"
    }
    
    # ১. প্রাইমারি পেজ লোডিং
    res = session.get(url, headers=headers, timeout=25, allow_redirects=True)
    status_code = res.status_code
    
    # ২. ইন্টারনাল পেজ স্ক্রলিং ও রিসোর্স লোডার (হিউম্যান বিহেভিওরাল সিমুলেশন)
    if status_code == 200:
        try:
            soup = BeautifulSoup(res.text, 'html.parser')
            # পেজের স্ক্রিপ্ট ও এসেট ফেচিং (GA4 & Analytics Tracking)
            assets = [elem.get('src') for elem in soup.find_all(['script', 'img', 'link'], src=True)[:5]]
            for asset in assets:
                if asset.startswith("http"):
                    headers["Sec-Fetch-Dest"] = "script" if asset.endswith(".js") else "image"
                    session.get(asset, headers=headers, timeout=5)
        except Exception:
            pass

    return status_code

async def run_traffic_process(url, chat_id, context, total_runs, stay_time):
    stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Simulation", callback_data="stop_test")]])
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚡ *Stealth Engine V3 Active!*\n\n🌐 **Target:** `{url}`\n📊 **Sessions:** `{total_runs}`\n⏱️ **Duration:** `{stay_time}s per session`\n🎭 **Emulation:** Full DOM & Fingerprint Spoofing",
        reply_markup=stop_keyboard,
        parse_mode='Markdown'
    )

    success_count = 0
    fail_count = 0
    loop = asyncio.get_event_loop()

    for i in range(1, total_runs + 1):
        if not active_tests.get(chat_id, False):
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"⏹️ *Process Aborted by User!*\n\n🟢 **Success:** `{success_count}` | 🔴 **Failed:** `{fail_count}`",
                parse_mode='Markdown'
            )
            return

        try:
            status = await loop.run_in_executor(None, execute_stealth_browser_emulation, url)
            if status in [200, 301, 302]:
                success_count += 1
            else:
                fail_count += 1
        except Exception:
            fail_count += 1

        # ১ম ভিজিটের প্রুফ স্ন্যাপশট
        if i == 1:
            screenshot_api = f"https://api.screenshotmachine.com?key=free&url={url}&dimension=1024x768"
            try:
                await context.bot.send_photo(
                    chat_id=chat_id,
                    photo=screenshot_api,
                    caption=f"📸 *Visual Proof Snapshot*\nStatus Response: `{status}`",
                    parse_mode='Markdown'
                )
            except Exception:
                pass

        # প্রতি ৫ ভিজিটে টেলিগ্রাম মেসেজ আপডেট
        if i % 5 == 0 or i == total_runs:
            percent = int((i / total_runs) * 100)
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"🔄 *Progress:* `{i}/{total_runs}` ({percent}%)\n🟢 **Success:** `{success_count}` | 🔴 **Errors:** `{fail_count}`",
                reply_markup=stop_keyboard,
                parse_mode='Markdown'
            )

        # ১ সেকেন্ডের স্মার্ট স্টপ চেক
        total_delay = stay_time + random.uniform(1.0, 3.0)
        for _ in range(int(total_delay)):
            if not active_tests.get(chat_id, False):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⏹️ *Process Aborted by User!*\n\n🟢 **Success:** `{success_count}` | 🔴 **Failed:** `{fail_count}`",
                    parse_mode='Markdown'
                )
                return
            await asyncio.sleep(1)

    active_tests[chat_id] = False
    
    # অ্যাডভান্সড ফাইনাল ড্যাশবোর্ড রিপোর্ট
    summary_text = (
        f"🏆 *ADVANCED TRAFFIC COMPLETED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **Domain:** `{url}`\n"
        f"🔢 **Total Requested:** `{total_runs}`\n"
        f"🟢 **Successful Sessions:** `{success_count}`\n"
        f"🔴 **Failed Requests:** `{fail_count}`\n"
        f"⏱️ **Session Time:** `{stay_time}s`\n"
        f"🛡️ **Security Protocol:** Stealth Passed\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await context.bot.send_message(chat_id=chat_id, text=summary_text, parse_mode='Markdown')

# ----------------- ইনলাইন ও কাস্টম কিবোর্ড -----------------
def get_count_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("50 Visits", callback_data="count_50"), InlineKeyboardButton("100 Visits", callback_data="count_100")],
        [InlineKeyboardButton("250 Visits", callback_data="count_250"), InlineKeyboardButton("✏️ Custom Count", callback_data="count_custom")]
    ])

def get_time_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ 10 Seconds", callback_data="time_10"), InlineKeyboardButton("⏱️ 30 Seconds", callback_data="time_30")],
        [InlineKeyboardButton("⏳ 60 Seconds", callback_data="time_60")]
    ])

# ----------------- টেলিগ্রাম বটের হ্যান্ডলার -----------------
async def start(update, context):
    active_tests[update.message.chat_id] = False
    welcome = "🤖 *Stealth Engine V3 Simulator*\n\nপ্যানেল খুলতে নিচের **🚀 Start Traffic Test** বাটনে ক্লিক করুন।"
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("🚀 Start Traffic Test")], [KeyboardButton("🛑 Stop Current Test")]], resize_keyboard=True)
    await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode='Markdown')

async def handle_message(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    if text == "🚀 Start Traffic Test":
        user_data[user_id] = {"state": "WAITING_FOR_URL"}
        await update.message.reply_text("🔗 **আপনার ওয়েবসাইটের লিংক (URL) পাঠান:**", parse_mode='Markdown')

    elif text == "🛑 Stop Current Test":
        active_tests[chat_id] = False
        await update.message.reply_text("🛑 **টেস্ট সাথে সাথে বন্ধ করা হয়েছে!**")

    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_URL":
        if text.startswith("http://") or text.startswith("https://"):
            user_data[user_id]["url"] = text
            user_data[user_id]["state"] = "WAITING_FOR_COUNT"
            await update.message.reply_text("📊 **ভিজিট সংখ্যা নির্ধারণ করুন:**", reply_markup=get_count_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ **অবৈধ লিংক!** দয়া করে http:// বা https:// সহ সঠিক লিংক দিন।")

    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_CUSTOM_COUNT":
        if text.isdigit() and int(text) > 0:
            user_data[user_id]["count"] = int(text)
            user_data[user_id]["state"] = "WAITING_FOR_TIME"
            await update.message.reply_text("⏱️ **প্রতি ভিজিটের Stay Duration কত সেকেন্ড হবে?**", reply_markup=get_time_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ **ভুল ইনপুট!** একটি সঠিক সংখ্যা লিখুন।")

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    await query.answer()

    if query.data == "stop_test":
        active_tests[chat_id] = False
        await query.edit_message_text("🛑 **টেস্ট সাথে সাথে বন্ধ করা হয়েছে!**")

    elif query.data == "count_custom":
        user_data[user_id]["state"] = "WAITING_FOR_CUSTOM_COUNT"
        await query.edit_message_text("✏️ **আপনি কতগুলো ভিজিট পাঠাতে চান তা সংখ্যায় লিখে পাঠান:**", parse_mode='Markdown')

    elif query.data.startswith("count_"):
        count = int(query.data.split("_")[1])
        if user_id in user_data:
            user_data[user_id]["count"] = count
            user_data[user_id]["state"] = "WAITING_FOR_TIME"
            await query.edit_message_text("⏱️ **প্রতি ভিজিটের Stay Duration কত সেকেন্ড হবে?**", reply_markup=get_time_keyboard(), parse_mode='Markdown')

    elif query.data.startswith("time_"):
        stay_time = int(query.data.split("_")[1])
        if user_data.get(user_id, {}).get("url") and user_data.get(user_id, {}).get("count"):
            url = user_data[user_id]["url"]
            count = user_data[user_id]["count"]
            user_data[user_id] = None
            
            active_tests[chat_id] = True
            await query.edit_message_text(f"✅ Configured: **{count} Visits** | **{stay_time}s Stay**\nInitiating Advanced Session Engine...", parse_mode='Markdown')
            asyncio.create_task(run_traffic_process(url, chat_id, context, count, stay_time))

# ----------------- SERVER BOOTSTRAP -----------------
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
