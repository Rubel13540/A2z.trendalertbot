import os
import threading
import feedparser
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler

# === Render-এর Environment Variables থেকে টোকেন নেবে ===
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")

# Flask অ্যাপ তৈরি (Render-এর পোর্ট চেক পাস করার জন্য)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running"

@app.route('/health')
def health():
    return "OK"

# ============ বটের ফাংশন ============
def fetch_trends(geo="BD"):
    """Google Trends RSS থেকে ট্রেন্ডিং ডেটা আনে"""
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url)
    trends = []
    for entry in feed.entries[:5]:
        title = entry.get("title", "No title")
        traffic = entry.get("ht:approx_traffic", "N/A")
        trends.append(f"🔥 {title}\n   📊 সার্চ: {traffic}")
    return "\n\n".join(trends) if trends else "এখন কোনো ট্রেন্ড নেই।"

async def start(update, context):
    """বটে /start দিলে এই ফাংশন চলবে"""
    await update.message.reply_text(
        "🇧🇩 হ্যালো! আমি বাংলাদেশ ট্রেন্ড অ্যালার্ট বট।\n\n"
        "📌 কমান্ডগুলো:\n"
        "/trends — বাংলাদেশের ট্রেন্ড\n"
        "/trends US — আমেরিকার ট্রেন্ড\n"
        "/trends IN — ভারতের ট্রেন্ড\n\n"
        "যেকোনো দেশের দুই-অক্ষরের কোড দিতে পারবেন।"
    )

async def trends_command(update, context):
    """বটে /trends দিলে এই ফাংশন চলবে"""
    geo = "BD"  # ডিফল্ট বাংলাদেশ
    if context.args:
        geo = context.args[0].upper()
    
    await update.message.reply_text(f"⏳ {geo} এর ট্রেন্ড আনা হচ্ছে...")
    trend_text = fetch_trends(geo)
    await update.message.reply_text(trend_text)

# ============ বট চালু ============
def run_bot():
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("trends", trends_command))
    print("বট চালু হচ্ছে...")
    application.run_polling()

# মূল ব্লক
if __name__ == "__main__":
    # বটকে আলাদা থ্রেডে চালান
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()
    
    # Flask সার্ভার চালান (Render-এর পোর্ট চেকের জন্য)
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
