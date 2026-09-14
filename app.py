import os
import sys
import asyncio
import random
import threading
import subprocess
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from playwright.async_api import async_playwright
from werkzeug.serving import make_server

# ----------------- ব্রাউজার অটো-ইনস্টলেশন (এরর রিমুভাল) -----------------
print("Checking and installing Playwright Chromium binaries...")
try:
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
    subprocess.run([sys.executable, "-m", "playwright", "install-deps", "chromium"], check=True)
    print("Chromium installed successfully!")
except Exception as e:
    print(f"Browser installation warning: {e}")

app = Flask(__name__)

@app.route('/')
def home():
    return "Ultra-Stealth Traffic Bot with Stop Control is Running!"

@app.route('/health')
def health():
    return "OK"

# ----------------- অ্যান্টি-ডিটেকশন কনফিগারেশন -----------------
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.80 Mobile Safari/537.36"
]

REFERRERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://t.co/",
    "https://www.facebook.com/",
    "https://duckduckgo.com/"
]

user_data = {}
running_tasks = {} # স্টপ বাটনের জন্য টাস্ক ট্র্যাক করার ডিকশনারি

# ----------------- ট্রাফিক সিমুলেটর লজিক -----------------
async def simulate_traffic(url, chat_id, context, total_runs):
    stop_keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🛑 Stop Test Now", callback_data="stop_test")]])
    
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"🚀 *Traffic Test Started!*\n🔗 **URL:** `{url}`\n📊 **Target Visits:** `{total_runs}`\n🛡️ **Stealth Mode:** Enabled\n\n_যেকোনো সময় বন্ধ করতে নিচের স্টপ বাটনে চাপ দিন।_",
        reply_markup=stop_keyboard,
        parse_mode='Markdown'
    )
    
    success_count = 0
    fail_count = 0

    async with async_playwright() as p:
        for i in range(1, total_runs + 1):
            # স্টপ কমান্ড চেক
            if running_tasks.get(chat_id) == "STOP":
                await context.bot.send_message(chat_id=chat_id, text=f"⏹️ *Test Cancelled by User!*\n\n🟢 Total Completed: {success_count}\n🔴 Total Failed: {fail_count}", parse_mode='Markdown')
                running_tasks[chat_id] = None
                return

            try:
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox', '--disable-blink-features=AutomationControlled']
                )
                
                selected_ua = random.choice(USER_AGENTS)
                is_mobile = "Mobile" in selected_ua or "iPhone" in selected_ua

                context_browser = await browser.new_context(
                    user_agent=selected_ua,
                    viewport={'width': 390 if is_mobile else random.choice([1366, 1920, 1440]), 
                              'height': 844 if is_mobile else random.choice([768, 1080, 900])},
                    is_mobile=is_mobile,
                    has_touch=is_mobile,
                    extra_http_headers={"Referer": random.choice(REFERRERS)}
                )
                
                page = await context_browser.new_page()

                # Anti-Bot Script Injection
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                """)

                await page.goto(url, timeout=35000, wait_until="domcontentloaded")
                
                # র্যান্ডম সময় অবস্থান ও মানুষের মতো স্ক্রোলিং (৮-১৫ সেকেন্ড)
                stay_duration = random.randint(8, 15)
                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < stay_duration:
                    if not is_mobile:
                        await page.mouse.move(random.randint(100, 600), random.randint(100, 600))
                    
                    await page.mouse.wheel(0, random.randint(200, 500))
                    await asyncio.sleep(random.uniform(1.5, 3.0))

                await browser.close()
                success_count += 1

                # প্রতি ৫ ভিজিটে আপডেট পাঠানো
                if i % 5 == 0 or i == total_runs:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🔄 *Progress:* `{i}/{total_runs}` completed.\n🟢 Success: {success_count} | 🔴 Stuck: {fail_count}",
                        reply_markup=stop_keyboard,
                        parse_mode='Markdown'
                    )

                await asyncio.sleep(random.uniform(3.5, 5.5))

            except Exception as e:
                fail_count += 1
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ *Visit #{i} Error:* `{str(e)[:40]}` - Retrying next...",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(2)

    running_tasks[chat_id] = None
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ *Traffic Test Completed Successfully!*\n\n🎯 **Total Target:** {total_runs}\n🟢 **Success:** {success_count}\n🔴 **Failed:** {fail_count}",
        parse_mode='Markdown'
    )

# ----------------- টেলিগ্রাম মেনু ও হ্যান্ডলার -----------------
def get_count_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("30 Visits", callback_data="count_30"), InlineKeyboardButton("50 Visits", callback_data="count_50")],
        [InlineKeyboardButton("100 Visits", callback_data="count_100")]
    ])

async def start(update, context):
    welcome = (
        "🤖 *Advanced Real Human-Like Traffic Bot*\n\n"
        "নতুন অ্যান্টি-ডিটেকশন টেকনোলজি এবং রিয়েল ইউজার এজেন্ট সহ ট্রাফিক টেস্ট করার সুবিধা রয়েছে।\n\n"
        "👇 শুরু করতে **🚀 Start Traffic Test** এ চাপ দিন।"
    )
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("🚀 Start Traffic Test")], [KeyboardButton("🛑 Stop Current Test")]], resize_keyboard=True)
    await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode='Markdown')

async def handle_message(update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    text = update.message.text

    if text == "🚀 Start Traffic Test":
        user_data[user_id] = {"state": "WAITING_FOR_URL"}
        await update.message.reply_text("🔗 **দয়া করে আপনার ওয়েবসাইটের লিংক (URL) পাঠান:**", parse_mode='Markdown')
        
    elif text == "🛑 Stop Current Test":
        running_tasks[chat_id] = "STOP"
        await update.message.reply_text("🛑 **টেস্ট বন্ধের রিকোয়েস্ট পাঠানো হয়েছে...**")

    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_URL":
        if text.startswith("http://") or text.startswith("https://"):
            user_data[user_id]["url"] = text
            user_data[user_id]["state"] = "WAITING_FOR_COUNT"
            await update.message.reply_text("📊 **কতবার ভিজিট করাতে চান?**\n\nবাটন থেকে বেছে নিন বা ম্যানুয়ালি সংখ্যা লিখে পাঠান:", reply_markup=get_count_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ **অবৈধ লিংক!** সঠিক URL দিন (http:// বা https:// সহ)।")
            
    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_COUNT":
        if text.isdigit() and int(text) > 0:
            url = user_data[user_id]["url"]
            count = int(text)
            user_data[user_id] = None
            running_tasks[chat_id] = "RUNNING"
            asyncio.create_task(simulate_traffic(url, chat_id, context, total_runs=count))
        else:
            await update.message.reply_text("⚠️ **অবৈধ সংখ্যা!** কেবল সঠিক সংখ্যা লিখে পাঠান।")

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    await query.answer()

    if query.data == "stop_test":
        running_tasks[chat_id] = "STOP"
        await query.edit_message_text("🛑 **টেস্ট বন্ধ করা হচ্ছে...**")
        
    elif query.data.startswith("count_"):
        count = int(query.data.split("_")[1])
        if user_data.get(user_id, {}).get("url"):
            url = user_data[user_id]["url"]
            user_data[user_id] = None
            running_tasks[chat_id] = "RUNNING"
            await query.edit_message_text(f"✅ **{count} Visits Selected.** Process Starting...", parse_mode='Markdown')
            asyncio.create_task(simulate_traffic(url, chat_id, context, total_runs=count))
        else:
            await query.edit_message_text("⚠️ **সেশন এক্সপায়ার হয়েছে!** নতুন করে শুরু করুন।")

# ----------------- সার্ভার রানার -----------------
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    server.serve_forever()

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN পাওয়া যায়নি!")
    else:
        threading.Thread(target=run_flask, daemon=True).start()
        
        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("stop", start))
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Bot is Running...")
        application.run_polling()
    
