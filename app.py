import os
import asyncio
import random
import threading
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from playwright.async_api import async_playwright
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Ultra-Stealth Traffic Bot is Running!"

@app.route('/health')
def health():
    return "OK"

# ----------------- রিয়েল ট্রাফিকের অ্যান্টি-ডিটেকশন কনফিগারেশন -----------------

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

# ----------------- ট্রাফিক সিমুলেটর লজিক -----------------

async def simulate_traffic(url, chat_id, context, total_runs):
    await context.bot.send_message(
        chat_id=chat_id, 
        text=f"🚀 *Traffic Test Started!*\n🔗 **URL:** `{url}`\n📊 **Target Visits:** `{total_runs}`\n🛡️ **Stealth Mode:** Enabled",
        parse_mode='Markdown'
    )
    
    success_count = 0
    fail_count = 0

    async with async_playwright() as p:
        for i in range(1, total_runs + 1):
            try:
                # ব্রাউজার লঞ্চিং উইথ অ্যান্টি-বোট ফ্ল্যাগ
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-infobars'
                    ]
                )
                
                # অর্গানিক ট্রাফিক হেডারের মতো সাজানো
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

                # Anti-Bot Evasion JavaScript Injections
                await page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                    window.chrome = { runtime: {} };
                    Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3]});
                """)

                # ওয়েবসাইটে প্রবেশ
                await page.goto(url, timeout=35000, wait_until="domcontentloaded")
                
                # ১০ সেকেন্ড হিউম্যানাইজড অ্যাক্টিভিটি (র্যান্ডম স্ক্রোল ও মাউস মুভমেন্ট)
                start_time = asyncio.get_event_loop().time()
                while asyncio.get_event_loop().time() - start_time < 10:
                    # মাউস জিটার (মানুষের মতো মাউস নাড়ানো)
                    if not is_mobile:
                        await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                    
                    # মানুষের মতো স্ক্রোল করা
                    scroll_y = random.randint(200, 500)
                    await page.mouse.wheel(0, scroll_y)
                    await asyncio.sleep(random.uniform(1.5, 3.2)) # পজ

                await browser.close()
                success_count += 1

                # প্রতি ৫টি বা শেষ ভিজিটে স্ট্যাটাস আপডেট
                if i % 5 == 0 or i == total_runs:
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🔄 *Progress:* `{i}/{total_runs}` visits completed.\n🟢 Success: {success_count} | 🔴 Stuck/Failed: {fail_count}",
                        parse_mode='Markdown'
                    )

                # ৫ সেকেন্ড বিরতি (র্যান্ডমাইজড)
                await asyncio.sleep(random.uniform(4.5, 6.5))

            except Exception as e:
                fail_count += 1
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚠️ *Visit #{i} Stuck/Failed!* Retrying next...\nError: `{str(e)[:40]}`",
                    parse_mode='Markdown'
                )
                await asyncio.sleep(3)

    # কাজ শেষে ফাইনাল মেসেজ
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"✅ *Traffic Test Completed!*\n\n🎯 **Total Target:** {total_runs}\n🟢 **Success:** {success_count}\n🔴 **Failed/Stuck:** {fail_count}",
        parse_mode='Markdown'
    )

# ----------------- কিবোর্ড ও ইনলাইন মেনু -----------------

def get_count_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("30 Visits", callback_data="count_30"), InlineKeyboardButton("50 Visits", callback_data="count_50")],
        [InlineKeyboardButton("100 Visits", callback_data="count_100")]
    ])

# ----------------- টেলিগ্রাম হ্যান্ডলারস -----------------

async def start(update, context):
    welcome = (
        "🤖 *Real Human-Like Traffic Bot*\n\n"
        "এই বটের সাহায্যে আপনি অ্যান্টি-ডিটেকশন মোডে ওয়েবসাইটের ট্রাফিক টেস্ট করতে পারবেন।\n\n"
        "👇 শুরু করতে নিচে **🚀 Start Traffic Test** এ ক্লিক করুন।"
    )
    keyboard = ReplyKeyboardMarkup([[KeyboardButton("🚀 Start Traffic Test")]], resize_keyboard=True)
    await update.message.reply_text(welcome, reply_markup=keyboard, parse_mode='Markdown')

async def handle_message(update, context):
    user_id = update.message.from_user.id
    text = update.message.text

    if text == "🚀 Start Traffic Test":
        user_data[user_id] = {"state": "WAITING_FOR_URL"}
        await update.message.reply_text("🔗 **দয়া করে আপনার ওয়েবসাইটের লিংক (URL) পাঠান:**\n\n*(উদাহরণ: `https://example.com`)*", parse_mode='Markdown')
        
    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_URL":
        if text.startswith("http://") or text.startswith("https://"):
            user_data[user_id]["url"] = text
            user_data[user_id]["state"] = "WAITING_FOR_COUNT"
            await update.message.reply_text("📊 **কতবার ভিজিট করাতে চান?**\n\nনিচের বাটন থেকে নির্বাচন করুন অথবা সংখ্যাটি ম্যানুয়ালি লিখে পাঠান:", reply_markup=get_count_keyboard(), parse_mode='Markdown')
        else:
            await update.message.reply_text("⚠️ **অবৈধ লিংক!** সঠিক URL দিন (http:// বা https:// সহ)।")
            
    elif user_data.get(user_id, {}).get("state") == "WAITING_FOR_COUNT":
        if text.isdigit() and int(text) > 0:
            url = user_data[user_id]["url"]
            count = int(text)
            user_data[user_id] = None
            asyncio.create_task(simulate_traffic(url, update.message.chat_id, context, total_runs=count))
        else:
            await update.message.reply_text("⚠️ **অবৈধ সংখ্যা!** কেবল সঠিক সংখ্যা লিখে পাঠান (যেমন: 20, 50, 100)।")

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    if query.data.startswith("count_"):
        count = int(query.data.split("_")[1])
        if user_data.get(user_id, {}).get("url"):
            url = user_data[user_id]["url"]
            user_data[user_id] = None
            await query.edit_message_text(f"✅ **{count} Visits Selected.** Process Starting...", parse_mode='Markdown')
            asyncio.create_task(simulate_traffic(url, query.message.chat_id, context, total_runs=count))
        else:
            await query.edit_message_text("⚠️ **সেশন এক্সপায়ার হয়েছে!** নতুন করে `/start` দিন।")

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
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Traffic Bot চালু হয়েছে...")
        application.run_polling()
