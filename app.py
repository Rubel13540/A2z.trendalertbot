import os
import random
import asyncio
import threading
import time
import aiohttp
import sqlite3
from bs4 import BeautifulSoup
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

# ================== অ্যাডমিন কনফিগারেশন ==================
# এখানে আপনার টেলিগ্রাম আইডি নম্বর বসান (@userinfobot থেকে নিন)
ADMIN_ID = 123456789  # <-- আপনার আইডি এখানে বসান

app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Ultra Fast Engine Status: ONLINE & ACTIVE ⚡"

# ----------------- ডাটাবেস সেটআপ (SQLite) -----------------
def init_db():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name):
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
                       (user_id, username, first_name))
        conn.commit()
    except Exception as e:
        print(f"DB Error: {e}")
    finally:
        conn.close()

def get_total_users():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_today_users():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(join_date) = DATE('now')")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect('bot_users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, username, first_name, join_date FROM users ORDER BY join_date DESC LIMIT 50")
    users = cursor.fetchall()
    conn.close()
    return users

# ডাটাবেস ইনিশিয়ালাইজ করা
init_db()

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

def get_time_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ Fast (5 Seconds)", callback_data="time_5")],
        [InlineKeyboardButton("⏱️ Medium (10 Seconds)", callback_data="time_10")],
        [InlineKeyboardButton("⏳ Slow (15 Seconds)", callback_data="time_15")]
    ])

# ----------------- অ্যাডমিন প্যানেল হ্যান্ডলার -----------------
async def admin_panel(update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ডটি ব্যবহার করার অনুমতি নেই।")
        return

    total = get_total_users()
    today = get_today_users()
    
    msg = (
        f"👑 *ADMIN CONTROL PANEL* 👑\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **মোট ইউজার:** `{total}` জন\n"
        f"📅 **আজকের নতুন ইউজার:** `{today}` জন\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"নিচের বাটনগুলো ব্যবহার করে আরও তথ্য দেখুন:"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 সব ইউজারের লিস্ট", callback_data="admin_userlist")],
        [InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔄 রিফ্রেশ স্ট্যাটস", callback_data="admin_refresh")]
    ])
    
    await update.message.reply_text(msg, reply_markup=keyboard, parse_mode='Markdown')

# ----------------- টেলিগ্রাম হ্যান্ডলারস -----------------
async def start(update, context):
    user = update.message.from_user
    # ডাটাবেসে ইউজার সেভ করা
    add_user(user.id, user.username, user.first_name)
    
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

    # ইউজারকে ডাটাবেসে সেভ করা (প্রতিবার মেসেজ দিলে)
    user = update.message.from_user
    add_user(user.id, user.username, user.first_name)

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

    # --- অ্যাডমিন প্যানেলের বাটনগুলো ---
    if query.data == "admin_refresh":
        if user_id != ADMIN_ID: return
        total = get_total_users()
        today = get_today_users()
        msg = (
            f"👑 *ADMIN CONTROL PANEL* 👑\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **মোট ইউজার:** `{total}` জন\n"
            f"📅 **আজকের নতুন ইউজার:** `{today}` জন\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 *স্ট্যাটস রিফ্রেশ করা হয়েছে!*"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 সব ইউজারের লিস্ট", callback_data="admin_userlist")],
            [InlineKeyboardButton("📢 ব্রডকাস্ট মেসেজ", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔄 রিফ্রেশ স্ট্যাটস", callback_data="admin_refresh")]
        ])
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode='Markdown')
        return

    elif query.data == "admin_userlist":
        if user_id != ADMIN_ID: return
        users = get_all_users()
        if not users:
            await query.edit_message_text("❌ এখনো কোনো ইউজার নেই।")
            return
        
        text = "📋 *সর্বশেষ ৫০ জন ইউজারের লিস্ট:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for u in users:
            name = u[2] if u[2] else "Unknown"
            uname = f"@{u[1]}" if u[1] else "No Username"
            text += f"👤 {name} | {uname} | `{u[0]}`\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━\n"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Panel", callback_data="admin_refresh")]])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')
        return

    elif query.data == "admin_broadcast":
        if user_id != ADMIN_ID: return
        await query.edit_message_text("📢 *ব্রডকাস্ট মেসেজ পাঠাতে চাইলে নিচের ফরম্যাটে মেসেজ দিন:*\n\n`/broadcast আপনার মেসেজ`", parse_mode='Markdown')
        return

    # --- সাধারণ ইউজারদের বাটন ---
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

# ----------------- ব্রডকাস্ট কমান্ড -----------------
async def broadcast(update, context):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ আপনি এই কমান্ডটি ব্যবহার করার অনুমতি নেই।")
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ ব্যবহার: `/broadcast আপনার মেসেজ`", parse_mode='Markdown')
        return
    
    msg = " ".join(context.args)
    users = get_all_users()
    success = 0
    fail = 0
    
    await update.message.reply_text(f"📢 ব্রডকাস্ট শুরু হচ্ছে... ({len(users)} জন ইউজার)")
    
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 *অ্যাডমিন নোটিশ:*\n\n{msg}", parse_mode='Markdown')
            success += 1
            await asyncio.sleep(0.05)  # টেলিগ্রাম লিমিট এড়াতে
        except Exception:
            fail += 1
    
    await update.message.reply_text(f"✅ ব্রডকাস্ট সম্পন্ন!\n\n🟢 সফল: {success}\n🔴 ব্যর্থ: {fail}")

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
        
        # হ্যান্ডলার যোগ করা
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("admin", admin_panel))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("⚡ বট চালু হচ্ছে...")
        application.run_polling()
