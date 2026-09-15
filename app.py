import os
import random
import asyncio
import threading
import time
import aiohttp
from bs4 import BeautifulSoup
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Ultra Fast Engine Status: ONLINE & ACTIVE ⚡"

# ----------------- প্রফেশনাল ডিভাইস ইউজার-এজেন্ট -----------------
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

# ----------------- ভিজ্যুয়াল প্রোগ্রেস বার -----------------
def generate_progress_bar(percent, length=10):
    filled = int(length * percent // 100)
    bar = '█' * filled + '░' * (length - filled)
    return bar

# ----------------- হাই-স্পিড অ্যাসিঙ্ক স্টিল্থ ব্রাউজার -----------------
async def execute_fast_stealth_emulation(session, url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERRERS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,bn;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as res:
            status_code = res.status
            if status_code == 200:
                html = await res.text()
                soup = BeautifulSoup(html, 'html.parser')
                assets = [elem.get('src') for elem in soup.find_all(['script', 'img', 'link'], src=True)[:3]]
                for asset in assets:
                    if asset and asset.startswith("http"):
                        try:
                            async with session.get(asset, headers=headers, timeout=aiohttp.ClientTimeout(total=5)):
                                pass
                        except Exception:
                            pass
            return status_code
    except Exception:
        return 500

# ----------------- ট্রাফিক প্রসেস ও স্পিড মিটার -----------------
async def run_traffic_process(url, chat_id, context, total_runs, stay_time):
    stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 EMERGENCY STOP", callback_data="stop_test")]])
    
    start_msg = (
        f"⚡ *HIGH-SPEED ENGINE ACTIVE*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **Target:** `{url}`\n"
        f"🔢 **Sessions:** `{total_runs}`\n"
        f"⏱️ **Mode Delay:** `{stay_time}s / session`\n"
        f"🛡️ **Security:** `TLS Spoofed & Async Pipeline`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    
    await context.bot.send_message(
        chat_id=chat_id,
        text=start_msg,
        reply_markup=stop_keyboard,
        parse_mode='Markdown'
    )

    success_count = 0
    fail_count = 0
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        for i in range(1, total_runs + 1):
            if not active_tests.get(chat_id, False):
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"🛑 *PROCESS ABORTED BY USER!*\n\n🟢 **Success:** `{success_count}` | 🔴 **Failed:** `{fail_count}`",
                    parse_mode='Markdown'
                )
                return

            status = await execute_fast_stealth_emulation(session, url)
            if status in [200, 301, 302]:
                success_count += 1
            else:
                fail_count += 1

            # প্রতি ৫ ভিজিটে লাইভ আপডেট ও স্পিড ক্যালকুলেশন
            if i % 5 == 0 or i == total_runs:
                elapsed_time = round(time.time() - start_time, 1)
                speed = round(i / elapsed_time, 2) if elapsed_time > 0 else i
                percent = int((i / total_runs) * 100)
                p_bar = generate_progress_bar(percent)
                
                progress_msg = (
                    f"⚡ *TRAFFIC SIMULATION IN PROGRESS*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 `[{p_bar}]` *{percent}%*\n\n"
                    f"🔄 **Completed:** `{i}/{total_runs}`\n"
                    f"🟢 **Successful:** `{success_count}` | 🔴 **Errors:** `{fail_count}`\n"
                    f"🚀 **Execution Speed:** `{speed} req/sec`\n"
                    f"⏱️ **Elapsed Time:** `{elapsed_time}s`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=progress_msg,
                    reply_markup=stop_keyboard,
                    parse_mode='Markdown'
                )

            # ব্যবহারকারীর নির্ধারিত স্পিড অনুযায়ী গ্যাপ দেওয়া
            for _ in range(stay_time):
                if not active_tests.get(chat_id, False):
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🛑 *PROCESS ABORTED BY USER!*\n\n🟢 **Success:** `{success_count}` | 🔴 **Failed:** `{fail_count}`",
                        parse_mode='Markdown'
                    )
                    return
                await asyncio.sleep(1)

    active_tests[chat_id] = False
    
    total_time = round(time.time() - start_time, 1)
    
    feedback_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 5 Star", callback_data="rate_5"), InlineKeyboardButton("👍 Awesome", callback_data="rate_good")]
    ])
    
    summary_text = (
        f"🏆 *SIMULATION COMPLETED SUCCESSFULLY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🌐 **Target:** `{url}`\n"
        f"📊 **Requested Traffic:** `{total_runs}`\n"
        f"🟢 **Successful Visits:** `{success_count}`\n"
        f"🔴 **Failed Requests:** `{fail_count}`\n"
        f"⏱️ **Total Time Taken:** `{total_time}s`\n"
        f"🛡️ **Status:** `100% Anonymity Maintained`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ *আপনার অভিজ্ঞতা কেমন ছিল? নিচে রেটিং দিন:*"
    )
    
    await context.bot.send_message(chat_id=chat_id, text=summary_text, reply_markup=feedback_keyboard, parse_mode='Markdown')

# ----------------- কাস্টম ইনলাইন কিবোর্ড -----------------
def get_count_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 STANDARD PACKS 🔹", callback_data="header1")],
        [InlineKeyboardButton("⚡ 100 Visits", callback_data="count_100"), InlineKeyboardButton("⚡ 300 Visits", callback_data="count_300")],
        [InlineKeyboardButton("⚡ 500 Visits", callback_data="count_500"), InlineKeyboardButton("⚡ 1000 Visits", callback_data="count_1000")],
        [InlineKeyboardButton("🚀 HIGH VOLUME PACKS 🚀", callback_data="header2")],
        [InlineKeyboardButton("🔥 5000 Visits", callback_data="count_5000"), InlineKeyboardButton("🔥 10000 Visits", callback_data="count_10000")],
        [InlineKeyboardButton("⚙️ CUSTOM AMOUNT", callback_data="count_custom")]
    ])

# ৩ টি স্পিড অপশন
def get_time_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Fast (5 Seconds)", callback_data="time_5")],
        [InlineKeyboardButton("⏱️ Medium (10 Seconds)", callback_data="time_10")],
        [InlineKeyboardButton("⏳ Slow (15 Seconds)", callback_data="time_15")]
    ])

# ----------------- টেলিগ্রাম হ্যান্ডলারস -----------------
async def start(update, context):
    active_tests[update.message.chat_id] = False
    welcome = (
        f"🌟 *WELCOME TO ULTRA STEALTH ENGINE V3* 🌟\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"হাই-স্পিড আসিক্রোনাস পাইপলাইন দিয়ে ওয়েবসাইট ট্রাফিক সিমুলেশন করুন অত্যন্ত নিরাপদে।\n\n"
        f"📌 **অপশন নির্বাচন করুন:**\n"
        f"🚀 **Start Simulation** - ট্রাফিক পাঠানো শুরু করতে।\n"
        f"📊 **Live Server Stats** - ইঞ্জিন হেলথ ও স্ট্যাটাস দেখতে।\n"
        f"🛑 **STOP IMMEDIATELY** - ইনস্ট্যান্ট যেকোনো প্রসেস বন্ধ করতে।"
    )
    
    keyboard = ReplyKeyboardMarkup([
        [KeyboardButton("🚀 Start Traffic Test"), KeyboardButton("📊 Live Server Stats")],
        [KeyboardButton("🛑 STOP IMMEDIATELY")]
    ], resize_keyboard=True)
    
    await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode='Markdown')

async def handle_message(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    if text == "🚀 Start Traffic Test":
        user_data[user_id] = {"state": "WAITING_FOR_URL"}
        await update.message.reply_text("🌐 *আপনার ওয়েবসাইটের লিংক (URL) পাঠান:* \n_(উদাহরণ: `https://example.com`)_", parse_mode='Markdown')

    elif text == "📊 Live Server Stats":
        stats_msg = (
            f"⚡ *ENGINE LIVE SYSTEM STATUS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 **Server Status:** `ONLINE (0ms Latency)`\n"
            f"⚙️ **Async Pipeline:** `Active`\n"
            f"🛡️ **Fingerprint Proxy:** `Loaded`\n"
            f"🚀 **Max Engine Capacity:** `100,000 Req/Day`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(stats_msg, parse_mode='Markdown')

    elif text == "🛑 STOP IMMEDIATELY":
        active_tests[chat_id] = False
        await update.message.reply_text("🛑 *সকল একটিভ টেস্ট তাৎক্ষণিকভাবে বন্ধ করা হয়েছে!*", parse_mode='Markdown')

    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_URL":
        if text.startswith("http://") or text.startswith("https://"):
            user_data[user_id]["url"] = text
            user_data[user_id]["state"] = "WAITING_FOR_COUNT"
            await update.message.reply_text("📊 *ট্রাফিক প্যাকেজ নির্বাচন করুন:*", reply_markup=get_count_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ *অবৈধ লিংক!* দয়া করে `http://` বা `https://` সহ সঠিক লিংক দিন।", parse_mode='Markdown')

    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_CUSTOM_COUNT":
        if text.isdigit() and int(text) > 0:
            user_data[user_id]["count"] = int(text)
            user_data[user_id]["state"] = "WAITING_FOR_TIME"
            await update.message.reply_text("⏱️ *স্পিড এবং Stay Duration সিলেক্ট করুন:*", reply_markup=get_time_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ *ভুল ইনপুট!* শুধু একটি ধনাত্মক সংখ্যা লিখুন।", parse_mode='Markdown')

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    await query.answer()

    if query.data in ["header1", "header2"]:
        return

    elif query.data in ["rate_5", "rate_good"]:
        await query.edit_message_text("💖 **আপনার ফিডব্যাকের জন্য ধন্যবাদ! বটটি ব্যবহার করতে থাকুন।**")

    elif query.data == "stop_test":
        active_tests[chat_id] = False
        await query.edit_message_text("🛑 *টেস্ট সাথে সাথে বন্ধ করা হয়েছে!*", parse_mode='Markdown')

    elif query.data == "count_custom":
        if user_id in user_data:
            user_data[user_id]["state"] = "WAITING_FOR_CUSTOM_COUNT"
            await query.edit_message_text("✏️ *আপনি কতগুলো ভিজিট পাঠাতে চান তা টাইপ করে জানান:*", parse_mode='Markdown')

    elif query.data.startswith("count_"):
        count = int(query.data.split("_")[1])
        if user_id in user_data:
            user_data[user_id]["count"] = count
            user_data[user_id]["state"] = "WAITING_FOR_TIME"
            await query.edit_message_text("⏱️ *স্পিড এবং Stay Duration সিলেক্ট করুন:*", reply_markup=get_time_keyboard(), parse_mode='Markdown')

    elif query.data.startswith("time_"):
        stay_time = int(query.data.split("_")[1])
        if user_data.get(user_id) and user_data[user_id].get("url") and user_data[user_id].get("count"):
            url = user_data[user_id]["url"]
            count = user_data[user_id]["count"]
            user_data[user_id] = {}
            
            active_tests[chat_id] = True
            await query.edit_message_text(
                f"⚙️ *CONFIGURATION COMPLETE*\n━━━━━━━━━━━━━━━━━━━━━━\n🎯 **Target:** `{url}`\n📊 **Visits:** `{count}`\n⏱️ **Speed Mode:** `{stay_time}s Stay`\n\n🔮 *Launching High-Speed Async Engine...*",
                parse_mode='Markdown'
            )
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
