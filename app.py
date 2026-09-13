import os
import asyncio
import feedparser
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler
from werkzeug.serving import make_server

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

@app.route('/health')
def health():
    return "OK"

def fetch_trends(geo="BD"):
    url = f"https://trends.google.com/trending/rss?geo={geo}"
    feed = feedparser.parse(url)
    trends = []
    for entry in feed.entries[:5]:
        title = entry.get("title", "No title")
        traffic = entry.get("ht:approx_traffic", "N/A")
        trends.append(f"🔥 {title}\n   📊 সার্চ: {traffic}")
    return "\n\n".join(trends) if trends else "এখন কোনো ট্রেন্ড নেই।"

async def start(update, context):
    await update.message.reply_text(
        "🇧🇩 হ্যালো! আমি বাংলাদেশ ট্রেন্ড অ্যালার্ট বট।\n\n"
        "📌 কমান্ডগুলো:\n"
        "/trends — বাংলাদেশের ট্রেন্ড\n"
        "/trends US — আমেরিকার ট্রেন্ড\n"
        "/trends IN — ভারতের ট্রেন্ড"
    )

async def trends_command(update, context):
    geo = "BD"
    if context.args:
        geo = context.args[0].upper()
    await update.message.reply_text(f"⏳ {geo} এর ট্রেন্ড আনা হচ্ছে...")
    trend_text = fetch_trends(geo)
    await update.message.reply_text(trend_text)

async def main():
    token = os.getenv("TELEGRAM_TOKEN")
    if not token:
        print("Error: TELEGRAM_TOKEN পাওয়া যায়নি!")
        return

    application = ApplicationBuilder().token(token).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("trends", trends_command))

    # Run Flask Web Server
    port = int(os.environ.get("PORT", 8080))
    server = make_server("0.0.0.0", port, app)
    loop = asyncio.get_running_loop()
    loop.run_in_executor(None, server.serve_forever)

    # Start Telegram Polling
    print("বট সফলভাবে চালু হয়েছে...")
    async with application:
        await application.start()
        await application.updater.start_polling()
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
        
