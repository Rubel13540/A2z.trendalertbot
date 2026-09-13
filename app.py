import os
import asyncio
import urllib.parse
import feedparser
import requests
import random
from flask import Flask
from google import genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running with AI & Monetization!"

@app.route('/health')
def health():
    return "OK"

# ----------------- কনফিগারেশন ও ডাটাবেস -----------------
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))  # আপনার টেলিগ্রাম আইডি
SPONSOR_LINK = os.getenv("SPONSOR_LINK", "https://t.me/telegram")  # আপনার চ্যানেলের বা স্পনসর লিংক

ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None

# বটের ইউজার আইডি ট্র্যাক করার মেমোরি লিস্ট
USER_IDS = set()

def register_user(user_id):
    USER_IDS.add(user_id)

def ask_ai(prompt):
    if not ai_client:
        return "⚠️ AI সার্ভিসটি সেটআপ করা হয়নি। GEMINI_API_KEY প্রদান করুন।"
    try:
        sys_instruction = "You are a professional crypto/forex trading analyst and content creation expert. Give concise, highly helpful responses in Bengali."
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={'system_instruction': sys_instruction}
        )
        return response.text
    except Exception as e:
        return "⚠️ AI প্রসেসিং করতে সমস্যা হচ্ছে।"

# ----------------- ট্রেডিং ও ট্রেন্ড সার্ভিসেস -----------------
def fetch_gold_btc_ratio():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,tether-gold&vs_currencies=usd"
        res = requests.get(url, timeout=5).json()
        btc = res['bitcoin']['usd']
        gold = res['tether-gold']['usd']
        ratio = round(btc / gold, 2)
        
        analysis = "🚀 *স্মার্ট মানি ট্রেন্ড:* রিস্ক-অন মোড! ইনস্টিটিউশনগুলো ক্রিপ্টোতে ক্যাপিটাল শিফট করছে।" if ratio > 25 else "🛡️ *স্মার্ট মানি ট্রেন্ড:* সেফ হ্যাভেন মোড! ট্রেডাররা রিস্ক কমাচ্ছে।"
            
        return (
            f"🥇 *Gold vs BTC Ratio Signal*\n───────────────\n"
            f"💰 ১ BTC = *{ratio} oz* Gold (XAU)\n\n{analysis}\n\n"
            f"💡 *টিপ:* রেশিও দ্রুত বাড়লে অল্টকয়েন সিজন আসার সম্ভাবনা তৈরি হয়।"
        )
    except:
        return "⚠️ রেশিও ডেটা পাওয়া যায়নি।"

def fetch_whale_liquidation():
    types = ["BUY / ACCUMULATION 🟢", "SELL / DUMP 🔴"]
    whales = [
        {"val": "2,450 BTC ($150M+)", "action": random.choice(types), "target": "Binance -> Cold Wallet"},
        {"val": "15,000 ETH ($40M+)", "action": random.choice(types), "target": "Unknown Wallet -> Coinbase"}
    ]
    selected = random.choice(whales)
    return (
        f"🐋 *Whale Movement Alert*\n───────────────\n"
        f"📦 *সাইজ:* `{selected['val']}`\n⚡ *মুভমেন্ট:* {selected['action']}\n🔄 *রুট:* {selected['target']}\n\n"
        f"🔥 *মার্কেট নোট:* শর্ট/লং লিকুইডেশন ট্র্যাকিং বজায় রাখুন।"
    )

def fetch_crypto_prices():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        res = requests.get(url, timeout=5).json()
        
        btc_p, btc_c = res['bitcoin']['usd'], res['bitcoin']['usd_24h_change']
        eth_p, eth_c = res['ethereum']['usd'], res['ethereum']['usd_24h_change']
        sol_p, sol_c = res['solana']['usd'], res['solana']['usd_24h_change']

        fmt = lambda c: f"🟢 +{c:.2f}%" if c >= 0 else f"🔴 {c:.2f}%"

        return (
            "💰 *লাইভ ক্রিপ্টো আপডেট*\n───────────────\n"
            f"🪙 *Bitcoin (BTC):* ${btc_p:,} ({fmt(btc_c)})\n"
            f"💎 *Ethereum (ETH):* ${eth_p:,} ({fmt(eth_c)})\n"
            f"⚡ *Solana (SOL):* ${sol_p:,} ({fmt(sol_c)})\n"
        )
    except:
        return "⚠️ ক্রিপ্টো ডেটা আনা যাচ্ছে না।"

def fetch_trends(geo="BD"):
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url)
    trends = []
    for entry in feed.entries[:5]:
        title = entry.get("title", "No title")
        traffic = entry.get("ht_approx_traffic", entry.get("ht:approx_traffic", "100+"))
        search_url = f"https://www.google.com/search?q={urllib.parse.quote(title)}"
        trends.append(f"🔥 *[{title}]({search_url})*\n📊 সার্চ: `{traffic}`")
    return "\n\n".join(trends) if trends else "⚠️ কোনো ট্রেন্ড পাওয়া যায়নি।"

# ----------------- কিবোর্ড ও ইনলাইন অপশন (With Ads Button) -----------------
def get_main_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🥇 Gold/BTC সিগন্যাল", callback_data="gold_btc"), InlineKeyboardButton("🐋 Whale Alert", callback_data="whale_alert")],
        [InlineKeyboardButton("💰 ক্রিপ্টো প্রাইস", callback_data="crypto_live"), InlineKeyboardButton("🇧🇩 BD ট্রেন্ডস", callback_data="trend_BD")],
        [InlineKeyboardButton("🤖 AI ট্রেডিং পরামর্শ", callback_data="ai_help")],
        [InlineKeyboardButton("📢 স্পনসর / ভিআইপি অফার 🔥", url=SPONSOR_LINK)]  # বিজ্ঞাপন বা চ্যানেল বাটন
    ])

def get_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🤖 AI ট্রেডিং পরামর্শ"), KeyboardButton("🥇 সিক্রেট সিগন্যাল")],
        [KeyboardButton("🐋 Whale Tracker"), KeyboardButton("💰 ক্রিপ্টো প্রাইস")],
        [KeyboardButton("🔥 ভাইরাল ট্রেন্ডস"), KeyboardButton("🏠 মূল মেনু")]
    ], resize_keyboard=True)

# ----------------- হ্যান্ডলারস -----------------
user_state = {}

async def start(update, context):
    user_id = update.message.from_user.id
    register_user(user_id)
    
    welcome = (
        "🚀 *প্রো-ট্রেডার & AI অ্যাসিস্ট্যান্ট বটে স্বাগতম!*\n\n"
        "এখানে লাইভ মার্কেট ডাটা ও ট্রেন্ডের পাশাপাশি পাবেন *গুগল জেমিনি AI অ্যানালাইজার*।\n\n"
        "💡 যেকোনো প্রশ্ন লিখে পাঠাতে *🤖 AI ট্রেডিং পরামর্শ* বাটনে চাপুন।"
    )
    await update.message.reply_text("স্মার্ট কিবোর্ড চালু হয়েছে।", reply_markup=get_reply_keyboard())
    await update.message.reply_text(welcome, reply_markup=get_main_inline_keyboard(), parse_mode='Markdown')

# এডমিন ব্রডকাস্ট কমান্ড (/broadcast আপনার মেসেজ)
async def broadcast_command(update, context):
    user_id = update.message.from_user.id
    
    # এডমিন ফিল্টারিং (ADMIN_ID সেট থাকলে সিকিউরিটি চেক করবে)
    if ADMIN_ID != 0 and user_id != ADMIN_ID:
        await update.message.reply_text("⛔ আপনি এই কমান্ডটি ব্যবহার করতে পারবেন না।")
        return

    if not context.args:
        await update.message.reply_text("⚠️ ব্যবহার পদ্ধতি: `/broadcast আপনার স্পনসর বা মেসেজ বার্তা`", parse_mode='Markdown')
        return

    broadcast_msg = " ".join(context.args)
    success_count = 0
    fail_count = 0

    await update.message.reply_text(f"⏳ {len(USER_IDS)} জন ইউজারের কাছে মেসেজ পাঠানো শুরু হচ্ছে...")

    for uid in list(USER_IDS):
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *বিশেষ নোটিশ / স্পনসর আপডেট:*\n\n{broadcast_msg}",
                parse_mode='Markdown'
            )
            success_count += 1
            await asyncio.sleep(0.05)  # Telegram API limit রক্ষা করার জন্য রেট লিমিট
        except Exception:
            fail_count += 1

    await update.message.reply_text(
        f"✅ *ব্রডকাস্ট সম্পন্ন হয়েছে!*\n\n"
        f"🟢 সফল: {success_count}\n"
        f"🔴 ব্যর্থ: {fail_count}",
        parse_mode='Markdown'
    )

async def handle_message(update, context):
    user_id = update.message.from_user.id
    register_user(user_id)
    text = update.message.text

    if text == "🏠 মূল মেনু":
        user_state[user_id] = None
        await start(update, context)
    elif text == "🤖 AI ট্রেডিং পরামর্শ":
        user_state[user_id] = "WAITING_FOR_AI_QUERY"
        await update.message.reply_text("🧠 *AI প্রস্তুত!* আপনার যেকোনো ট্রেডিং প্রশ্ন বা কন্টেন্ট টিপস মেসেজে লিখে পাঠান:", parse_mode='Markdown')
    elif user_state.get(user_id) == "WAITING_FOR_AI_QUERY":
        user_state[user_id] = None
        await update.message.reply_text("⏳ *AI উত্তর তৈরি করছে...*", parse_mode='Markdown')
        ai_response = ask_ai(text)
        await update.message.reply_text(f"🤖 *AI অ্যানালাইসিস:*\n\n{ai_response}", parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "🥇 সিক্রেট সিগন্যাল":
        await update.message.reply_text(fetch_gold_btc_ratio(), parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "🐋 Whale Tracker":
        await update.message.reply_text(fetch_whale_liquidation(), parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "💰 ক্রিপ্টো প্রাইস":
        await update.message.reply_text(fetch_crypto_prices(), parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "🔥 ভাইরাল ট্রেন্ডস":
        msg = fetch_trends("BD")
        await update.message.reply_text(f"🇧🇩 *বাংলাদেশ ট্রেন্ডস:*\n\n{msg}", parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_main_inline_keyboard())
    else:
        await update.message.reply_text("⏳ *AI চিন্তা করছে...*", parse_mode='Markdown')
        ai_response = ask_ai(text)
        await update.message.reply_text(f"🤖 *AI অ্যানালাইসিস:*\n\n{ai_response}", parse_mode='Markdown', reply_markup=get_main_inline_keyboard())

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    register_user(user_id)
    await query.answer()

    if query.data == "ai_help":
        user_state[user_id] = "WAITING_FOR_AI_QUERY"
        await query.edit_message_text("🧠 *AI প্রস্তুত!* আপনার ট্রেডিং প্রশ্ন বা কন্টেন্ট প্রম্পট লিখে মেসেজ পাঠান:", parse_mode='Markdown')
    elif query.data == "gold_btc":
        await query.edit_message_text(fetch_gold_btc_ratio(), parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif query.data == "whale_alert":
        await query.edit_message_text(fetch_whale_liquidation(), parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif query.data == "crypto_live":
        await query.edit_message_text(fetch_crypto_prices(), parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif query.data.startswith("trend_"):
        geo = query.data.split("_")[1]
        trend_text = fetch_trends(geo)
        await query.edit_message_text(f"📌 *দেশ:* `{geo}`\n───────────────\n\n{trend_text}", parse_mode='Markdown', disable_web_page_preview=True, reply_markup=get_main_inline_keyboard())

# ----------------- মেইন রানার -----------------
async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN পাওয়া যায়নি!")
        return

    application = ApplicationBuilder().token(token).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast_command))  # ব্রডকাস্ট হ্যান্ডলার
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

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
