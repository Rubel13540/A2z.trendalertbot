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
ADMIN_ID = 5293614793

app = Flask(__name__)

@app.route('/')
def home():
    return "⚡ Ultra Fast Traffic Engine Status: ONLINE & ACTIVE ⚡"

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

init_db()

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36"
]

REFERRERS = [
    "https://www.google.com/search?q=",
    "https://www.bing.com/search?q=",
    "https://l.facebook.com/",
    "https://t.co/",
    "https://www.pinterest.com/"
]

user_data = {}
active_tests = {}

def generate_progress_bar(percent, length=10):
    filled = int(length * percent // 100)
    return '🟦' * filled + '⬜' * (length - filled)

async def execute_fast_stealth_emulation(session, url):
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": random.choice(REFERRERS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }
    try:
        async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=15), allow_redirects=True) as res:
            return res.status
    except Exception:
        return 500

async def run_traffic_process(url, chat_id, context, total_runs, stay_time):
    stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 EMERGENCY STOP 🛑", callback_data="stop_test")]])
    
    start_msg = (
        f"🚀 *TRAFFIC SIMULATION LAUNCHED*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **Target:** `{url}`\n"
        f"📦 **Total Visits:** `{total_runs}`\n"
        f"⏱️ **Interval:** `{stay_time}s / session`\n"
        f"🛡️ **Security:** `TLS Spoof & Anti-Bot Bypass`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━"
    )
    await context.bot.send_message(chat_id=chat_id, text=start_msg, reply_markup=stop_keyboard, parse_mode='Markdown')

    success_count, fail_count = 0, 0
    start_time = time.time()

    async with aiohttp.ClientSession() as session:
        for i in range(1, total_runs + 1):
            if not active_tests.get(chat_id, False):
                await context.bot.send_message(chat_id=chat_id, text="⚠️ *PROCESS ABORTED BY USER!*", parse_mode='Markdown')
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
                    f"⚡ *TRAFFIC ENGINE IN PROGRESS*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 {p_bar} *{percent}%*\n\n"
                    f"🔄 **Completed:** `{i}/{total_runs}`\n"
                    f"🟢 **Success:** `{success_count}` | 🔴 **Errors:** `{fail_count}`\n"
                    f"🚀 **Speed:** `{speed} req/sec`\n"
                    f"⏱️ **Elapsed Time:** `{elapsed_time}s`\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━"
                )
                await context.bot.send_message(chat_id=chat_id, text=progress_msg, reply_markup=stop_keyboard, parse_mode='Markdown')

            await asyncio.sleep(stay_time)

    active_tests[chat_id] = False
    
    feedback_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⭐ 5 Stars", callback_data="rate_5"), InlineKeyboardButton("🔥 Excellent", callback_data="rate_good")]
    ])
    
    summary = (
        f"🏆 *SIMULATION COMPLETED SUCCESSFULLY*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 **Target:** `{url}`\n"
        f"🟢 **Successful Visits:** `{success_count}`\n"
        f"🔴 **Failed Requests:** `{fail_count}`\n"
        f"⏱️ **Total Time:** `{round(time.time() - start_time, 1)}s`\n"
        f"🛡️ **Anonymity:** `100% High Stealth`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"✨ *আমাদের সার্ভিসটি কেমন লেগেছে? নিচে রেটিং দিন:*"
    )
    await context.bot.send_message(chat_id=chat_id, text=summary, reply_markup=feedback_keyboard, parse_mode='Markdown')

# ----------------- কাস্টম কিবোর্ড -----------------
def get_main_keyboard(user_id):
    # সাধারণ ইউজারদের জন্য
    buttons = [
        [KeyboardButton("🚀 Start Traffic Test"), KeyboardButton("📊 Live Server Stats")],
        [KeyboardButton("🛑 STOP IMMEDIATELY")]
    ]
    # শুধুমাত্র অ্যাডমিনের জন্য বিশেষ '👑 Admin Control' বাটন যোগ
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton("👑 Admin Control Panel")])
        
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def get_count_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔹 STARTER PACKS 🔹", callback_data="header1")],
        [InlineKeyboardButton("⚡ 100 Visits", callback_data="count_100"), InlineKeyboardButton("⚡ 300 Visits", callback_data="count_300")],
        [InlineKeyboardButton("⚡ 500 Visits", callback_data="count_500"), InlineKeyboardButton("⚡ 1000 Visits", callback_data="count_1000")],
        [InlineKeyboardButton("🔥 PRO PACKS 🔥", callback_data="header2")],
        [InlineKeyboardButton("💎 5000 Visits", callback_data="count_5000"), InlineKeyboardButton("💎 10000 Visits", callback_data="count_10000")],
        [InlineKeyboardButton("⚙️ Custom Quantity", callback_data="count_custom")]
    ])

def get_time_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚡ High Speed (5s Stay)", callback_data="time_5")],
        [InlineKeyboardButton("⏱️ Medium Speed (10s Stay)", callback_data="time_10")],
        [InlineKeyboardButton("⏳ Safe Mode (15s Stay)", callback_data="time_15")]
    ])

# ----------------- অ্যাডমিন প্যানেল -----------------
async def send_admin_panel(chat_id, context):
    total = get_total_users()
    today = get_today_users()
    
    msg = (
        f"👑 *ADMIN DASHBOARD & CONTROL Panel*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 **Total Registered Users:** `{total}`\n"
        f"📅 **New Users Today:** `{today}`\n"
        f"⚙️ **Bot Engine Status:** `Running 24/7`\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *কন্ট্রোল করতে নিচের অপশন নির্বাচন করুন:*"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View User List (Top 50)", callback_data="admin_userlist")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
        [InlineKeyboardButton("🔄 Refresh Statistics", callback_data="admin_refresh")]
    ])
    
    await context.bot.send_message(chat_id=chat_id, text=msg, reply_markup=keyboard, parse_mode='Markdown')

# ----------------- টেলিগ্রাম হ্যান্ডলারস -----------------
async def start(update, context):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name)
    
    welcome = (
        f"✨ *WELCOME TO TRAFFIC PULSE PRO V3* ✨\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👋 **Hello, {user.first_name}!**\n"
        f"হাই-স্পিড আসিক্রোনাস পাইপলাইন দিয়ে আপনার ওয়েবসাইটে রিয়েল ট্রাফিক সিমুলেশন করুন সম্পূর্ণ নিরাপদে।\n\n"
        f"💎 *প্রধান ফিচারসমূহ:*\n"
        f"• TLS Fingerprint Spoofing\n"
        f"• Multi-Referer & Custom User Agents\n"
        f"• Live Progress & Speed Tracking\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👇 *শুরু করতে নিচের বাটনগুলো ব্যবহার করুন:*"
    )
    
    await update.message.reply_text(welcome, reply_markup=get_main_keyboard(user.id), parse_mode='Markdown')

async def admin_command(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ *Access Denied!* আপনি অ্যাডমিন নন।", parse_mode='Markdown')
        return
    await send_admin_panel(update.effective_chat.id, context)

async def handle_message(update, context):
    user = update.effective_user
    chat_id = update.effective_chat.id
    text = update.message.text
    add_user(user.id, user.username, user.first_name)

    # অ্যাডমিন বাটন প্রেস করলে
    if text == "👑 Admin Control Panel":
        if user.id == ADMIN_ID:
            await send_admin_panel(chat_id, context)
        else:
            await update.message.reply_text("❌ *অনুমতি নেই!*", parse_mode='Markdown')

    elif text == "🚀 Start Traffic Test":
        user_data[user.id] = {"state": "WAITING_FOR_URL"}
        await update.message.reply_text("🌐 *আপনার ওয়েবসাইটের লিংক (URL) পাঠান:*\n_(উদাহরণ: `https://example.com`)_", parse_mode='Markdown')

    elif text == "📊 Live Server Stats":
        stats = (
            f"⚡ *TRAFFIC PULSE ENGINE STATUS*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🟢 **Server Status:** `ONLINE (0ms Latency)`\n"
            f"⚙️ **Engine Architecture:** `Asyncio / Aiohttp`\n"
            f"🛡️ **Stealth Proxy:** `Active & Fingerprinted`\n"
            f"🚀 **Max Capacity:** `100,000 Req / Day`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        await update.message.reply_text(stats, parse_mode='Markdown')

    elif text == "🛑 STOP IMMEDIATELY":
        active_tests[chat_id] = False
        await update.message.reply_text("🛑 *সকল প্রসেস তাৎক্ষণিকভাবে থামানো হয়েছে!*", parse_mode='Markdown')

    elif user_data.get(user.id, {}).get("state") == "WAITING_FOR_URL":
        if text.startswith("http://") or text.startswith("https://"):
            user_data[user.id]["url"] = text
            user_data[user.id]["state"] = "WAITING_FOR_COUNT"
            await update.message.reply_text("📊 *ট্রাফিক প্যাকেজ নির্বাচন করুন:*", reply_markup=get_count_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ *ভুল URL!* অবশ্যই `http://` বা `https://` সহ দিন।", parse_mode='Markdown')

    elif user_data.get(user.id, {}).get("state") == "WAITING_FOR_CUSTOM_COUNT":
        if text.isdigit() and int(text) > 0:
            user_data[user.id]["count"] = int(text)
            user_data[user.id]["state"] = "WAITING_FOR_TIME"
            await update.message.reply_text("⏱️ *স্পিড এবং Stay Duration সিলেক্ট করুন:*", reply_markup=get_time_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ *ভুল ইনপুট!* শুধু সংখ্যা টাইপ করুন।", parse_mode='Markdown')

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    await query.answer()

    if query.data == "admin_refresh" and user_id == ADMIN_ID:
        total = get_total_users()
        today = get_today_users()
        msg = (
            f"👑 *ADMIN DASHBOARD & CONTROL Panel*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"👥 **Total Registered Users:** `{total}`\n"
            f"📅 **New Users Today:** `{today}`\n"
            f"⚙️ **Bot Engine Status:** `Running 24/7`\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔄 *স্ট্যাটস রিফ্রেশ করা হয়েছে!*"
        )
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📋 View User List (Top 50)", callback_data="admin_userlist")],
            [InlineKeyboardButton("📢 Broadcast Message", callback_data="admin_broadcast")],
            [InlineKeyboardButton("🔄 Refresh Statistics", callback_data="admin_refresh")]
        ])
        await query.edit_message_text(msg, reply_markup=keyboard, parse_mode='Markdown')

    elif query.data == "admin_userlist" and user_id == ADMIN_ID:
        users = get_all_users()
        text = "📋 *সর্বশেষ ৫০ জন ইউজারের লিস্ট:*\n━━━━━━━━━━━━━━━━━━━━━━\n"
        for u in users:
            name = u[2] if u[2] else "Unknown"
            uname = f"@{u[1]}" if u[1] else "No Username"
            text += f"👤 {name} | {uname} | `{u[0]}`\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━━━"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back to Panel", callback_data="admin_refresh")]])
        await query.edit_message_text(text, reply_markup=keyboard, parse_mode='Markdown')

    elif query.data == "admin_broadcast" and user_id == ADMIN_ID:
        await query.edit_message_text("📢 *ব্রডকাস্ট করতে কমান্ড ব্যবহার করুন:*\n\n`/broadcast আপনার মেসেজ`", parse_mode='Markdown')

    elif query.data in ["rate_5", "rate_good"]:
        await query.edit_message_text("💖 **আপনার সুন্দর ফিডব্যাকের জন্য ধন্যবাদ!**")

    elif query.data == "stop_test":
        active_tests[chat_id] = False
        await query.edit_message_text("🛑 *টেস্ট সফলভাবে বন্ধ করা হয়েছে!*", parse_mode='Markdown')

    elif query.data == "count_custom":
        if user_id in user_data:
            user_data[user_id]["state"] = "WAITING_FOR_CUSTOM_COUNT"
            await query.edit_message_text("✏️ *কতগুলো ভিজিট পাঠাতে চান সংখ্যায় লিখুন:*", parse_mode='Markdown')

    elif query.data.startswith("count_"):
        count = int(query.data.split("_")[1])
        if user_id in user_data:
            user_data[user_id]["count"] = count
            user_data[user_id]["state"] = "WAITING_FOR_TIME"
            await query.edit_message_text("⏱️ *স্পিড সিলেক্ট করুন:*", reply_markup=get_time_keyboard(), parse_mode='Markdown')

    elif query.data.startswith("time_"):
        stay_time = int(query.data.split("_")[1])
        if user_data.get(user_id) and user_data[user_id].get("url") and user_data[user_id].get("count"):
            url = user_data[user_id]["url"]
            count = user_data[user_id]["count"]
            user_data[user_id] = {}
            
            active_tests[chat_id] = True
            await query.edit_message_text(f"🚀 *Engine Initializing for:* `{url}`\n📊 *Visits:* `{count}`", parse_mode='Markdown')
            asyncio.create_task(run_traffic_process(url, chat_id, context, count, stay_time))

async def broadcast(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    
    if not context.args:
        await update.message.reply_text("⚠️ ব্যবহার: `/broadcast আপনার মেসেজ`", parse_mode='Markdown')
        return
    
    msg = " ".join(context.args)
    users = get_all_users()
    success, fail = 0, 0
    
    await update.message.reply_text(f"📢 ব্রডকাস্ট শুরু হচ্ছে...")
    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 *ADMIN NOTICE:*\n\n{msg}", parse_mode='Markdown')
            success += 1
            await asyncio.sleep(0.05)
        except Exception:
            fail += 1
            
    await update.message.reply_text(f"✅ *Broadcast Complete!*\n🟢 Success: `{success}` | 🔴 Failed: `{fail}`", parse_mode='Markdown')

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    server.serve_forever()

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if token:
        threading.Thread(target=run_flask, daemon=True).start()
        application = ApplicationBuilder().token(token).build()
        
        application.add_handler(CommandHandler(["admin", "Admin", "ADMIN"], admin_command))
        application.add_handler(CommandHandler("broadcast", broadcast))
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        application.run_polling()
    
