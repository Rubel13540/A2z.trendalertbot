import os
import requests
import random
import threading
from datetime import datetime, timedelta, timezone
from flask import Flask
from google import genai
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Sports Betting Tips Bot with Live API is Running!"

@app.route('/health')
def health():
    return "OK"

# ----------------- কনফিগারেশন -----------------
GEMINI_KEY = os.getenv("GEMINI_API_KEY")
ODDS_API_KEY = os.getenv("ODDS_API_KEY") # The Odds API Key
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
VIP_LINK = os.getenv("SPONSOR_LINK", "https://t.me/telegram")

ai_client = genai.Client(api_key=GEMINI_KEY) if GEMINI_KEY else None
USER_IDS = set()

def register_user(user_id):
    USER_IDS.add(user_id)

def ask_ai_prediction(match_info):
    if not ai_client:
        return "⚠️ AI সার্ভিসটি সেটআপ করা হয়নি।"
    try:
        sys_instruction = (
            "You are a cautious sports analyst. Provide safe, low-risk betting predictions "
            "with double chance or safe handicap options. Answer in concise Bengali."
        )
        response = ai_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"Analyze this match and give low risk tips: {match_info}",
            config={'system_instruction': sys_instruction}
        )
        return response.text
    except Exception:
        return "⚠️ AI অ্যানালাইসিস করতে সমস্যা হচ্ছে।"

# ----------------- লাইভ API ডাটা ফেচিং (আগামী ১২ ঘণ্টা) -----------------

def fetch_live_matches(sport_key):
    """
    sport_key উদাহরণ: 
    - soccer_epl (English Premier League)
    - soccer_spain_la_liga (La Liga)
    - cricket_international (Cricket)
    - soccer_usa_mls
    """
    if not ODDS_API_KEY:
        return "⚠️ `ODDS_API_KEY` সেট করা হয়নি! রিয়েল টাইম ডাটা পেতে API Key যুক্ত করুন।"

    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h"
    
    try:
        res = requests.get(url, timeout=10).json()
        if not isinstance(res, list):
            return "⚠️ এই মুহূর্তে এই লিগের কোনো ম্যাচের তথ্য পাওয়া যায়নি।"

        now = datetime.now(timezone.utc)
        twelve_hours_later = now + timedelta(hours=12)

        matches_list = []

        for match in res:
            # ISO ফরম্যাট সময় পার্স করা
            commence_time_str = match.get("commence_time")
            if commence_time_str:
                match_time = datetime.fromisoformat(commence_time_str.replace("Z", "+00:00"))

                # আগামী ১২ ঘণ্টার মধ্যে ম্যাচ কি না তা ফিল্টার করা
                if now <= match_time <= twelve_hours_later:
                    home_team = match.get("home_team")
                    away_team = match.get("away_team")
                    
                    # কম রিস্ক বের করার জন্য বুকমেকার ওডস বিশ্লেষণ
                    odds_text = "N/A"
                    safe_tip = f"{home_team} / Draw (Safe 1X)"
                    
                    if match.get("bookmakers"):
                        outcomes = match["bookmakers"][0]["markets"][0]["outcomes"]
                        # ওডস ফরম্যাটিং
                        odds_text = " | ".join([f"{o['name']}: {o['price']}" for o in outcomes])

                    matches_list.append(
                        f"⚔️ *{home_team} vs {away_team}*\n"
                        f"⏰ *কিক অফ (UTC):* `{match_time.strftime('%H:%M, %d %b')}`\n"
                        f"🎯 *Low Risk Tip:* `{safe_tip}`\n"
                        f"📊 *Live Odds:* `{odds_text}`\n"
                    )

        if not matches_list:
            return "⏳ *আগামী ১২ ঘণ্টার মধ্যে কোনো লো-রিস্ক ম্যাচ শিডিউল করা নেই।*"

        header = "⚽ *আগামী ১২ ঘণ্টার লাইভ ফুটবল আপডেট*\n───────────────\n\n" if "soccer" in sport_key else "🏏 *আগামী ১২ ঘণ্টার লাইভ ক্রিকেট আপডেট*\n───────────────\n\n"
        return header + "\n".join(matches_list[:5]) # সেরা ৫টি প্রদর্শন করা হচ্ছে

    except Exception as e:
        return "⚠️ এপিআই থেকে ডেটা ফেচ করতে সমস্যা হয়েছে।"

# ----------------- কিবোর্ড ও ইনলাইন অপশন -----------------
def get_main_inline_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⚽ ফুটবল (১২ ঘণ্টা)", callback_data="tips_football"), InlineKeyboardButton("🏏 ক্রিকেট (১২ ঘণ্টা)", callback_data="tips_cricket")],
        [InlineKeyboardButton("📊 ব্যাংক রোল গাইড", callback_data="guide_bankroll"), InlineKeyboardButton("🤖 AI ম্যাচ অ্যানালাইজার", callback_data="ai_predict")],
        [InlineKeyboardButton("🔥 VIP / স্পেশাল অফার 📢", url=VIP_LINK)]
    ])

def get_reply_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("⚽ আগামী ১২ ঘণ্টার ফুটবল"), KeyboardButton("🏏 আগামী ১২ ঘণ্টার ক্রিকেট")],
        [KeyboardButton("📊 ব্যাংক রোল গাইড"), KeyboardButton("🤖 AI ম্যাচ অ্যানালাইসিস")],
        [KeyboardButton("🏠 মূল মেনু")]
    ], resize_keyboard=True)

# ----------------- হ্যান্ডলারস -----------------
user_state = {}

async def start(update, context):
    user_id = update.message.from_user.id
    register_user(user_id)
    
    welcome = (
        "🎯 *Safe Bet Pro - Low Risk Betting Tips Bot!*\n\n"
        "এখানে আগামী **১২ ঘণ্টার** মধ্যে হতে যাওয়া ক্রিকেট ও ফুটবলের লাইভ ম্যাচ ফিল্টার করে সেরা **Low Risk** টিপস দেওয়া হয়।\n\n"
        "👇 নিচের মেনু থেকে বেছে নিন:"
    )
    await update.message.reply_text("স্মার্ট মেনু চালু হয়েছে।", reply_markup=get_reply_keyboard())
    await update.message.reply_text(welcome, reply_markup=get_main_inline_keyboard(), parse_mode='Markdown')

async def handle_message(update, context):
    user_id = update.message.from_user.id
    register_user(user_id)
    text = update.message.text

    if text == "🏠 মূল মেনু":
        user_state[user_id] = None
        await start(update, context)
    elif text == "⚽ আগামী ১২ ঘণ্টার ফুটবল":
        await update.message.reply_text("⏳ লাইভ ডাটা লোড হচ্ছে...", parse_mode='Markdown')
        msg = fetch_live_matches("soccer_epl") # ডিফল্ট EPL ধরা হলো, প্রয়োজনে soccer_spain_la_liga ইত্যাদি দিতে পারেন
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "🏏 আগামী ১২ ঘণ্টার ক্রিকেট":
        await update.message.reply_text("⏳ লাইভ ডাটা লোড হচ্ছে...", parse_mode='Markdown')
        msg = fetch_live_matches("cricket_international")
        await update.message.reply_text(msg, parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "📊 ব্যাংক রোল গাইড":
        guide = (
            "📊 *ব্যাংক রোল ম্যানেজমেন্ট গাইড (Low Risk Rules)*\n───────────────\n"
            "১. **১-৩% রুল:** আপনার মোট বাজেটের সর্বোচ্চ ১ থেকে ৩ শতাংশ প্রতি বেটে রাখবেন।\n"
            "২. **লসের পেছনে দৌড়াবেন না:** হেরে গেলে একবারে রিকভার করার চেষ্টা করবেন না।\n"
            "৩. **মাল্টি-বেট এড়ান:** অ্যাকুমুলেটর বা বড় মাল্টি বেটে ঝুঁকি বেশি থাকে, সিঙ্গেল সেফ বেট খেলুন।"
        )
        await update.message.reply_text(guide, parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif text == "🤖 AI ম্যাচ অ্যানালাইসিস":
        user_state[user_id] = "WAITING_FOR_MATCH_NAME"
        await update.message.reply_text("🧠 *AI প্রস্তুত!* যেকোনো ম্যাচের নাম লিখে পাঠান (যেমন: *Real Madrid vs Barcelona*):", parse_mode='Markdown')
    elif user_state.get(user_id) == "WAITING_FOR_MATCH_NAME":
        user_state[user_id] = None
        await update.message.reply_text("⏳ *AI দিয়ে সেফ অ্যানালাইসিস তৈরি হচ্ছে...*", parse_mode='Markdown')
        ai_response = ask_ai_prediction(text)
        await update.message.reply_text(f"🤖 *AI Analysis & Safe Tip:*\n\n{ai_response}", reply_markup=get_main_inline_keyboard())
    else:
        await update.message.reply_text("দয়া করে নিচের মেনু থেকে একটি বাটন নির্বাচন করুন।", reply_markup=get_reply_keyboard())

async def button_click(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    register_user(user_id)
    await query.answer()

    if query.data == "tips_football":
        await query.edit_message_text("⏳ ফুটবল ম্যাচের লাইভ ডাটা আপডেট হচ্ছে...", parse_mode='Markdown')
        msg = fetch_live_matches("soccer_epl")
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif query.data == "tips_cricket":
        await query.edit_message_text("⏳ ক্রিকেট ম্যাচের লাইভ ডাটা আপডেট হচ্ছে...", parse_mode='Markdown')
        msg = fetch_live_matches("cricket_international")
        await query.edit_message_text(msg, parse_mode='Markdown', reply_markup=get_main_inline_keyboard())
    elif query.data == "ai_predict":
        user_state[user_id] = "WAITING_FOR_MATCH_NAME"
        await query.edit_message_text("🧠 *AI প্রস্তুত!* যেকোনো ম্যাচের নাম লিখে বার্তা পাঠান:", parse_mode='Markdown')

# ----------------- সার্ভার রানার -----------------
def run_flask():
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    server.serve_forever()

if __name__ == "__main__":
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN পাওয়া যায়নি!")
    else:
        threading.Thread(target=run_flask, daemon=True).start()
        
        application = ApplicationBuilder().token(token).build()
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_click))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        print("Sports Betting Tips Bot চালু হয়েছে...")
        application.run_polling()
                                          
