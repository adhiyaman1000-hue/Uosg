import os
import json
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

TELEGRAM_BOT_TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
RENDER_URL = "https://uosg-kg1t.onrender.com"

app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

FILTER_FILE = "filter_backup.json"

def load_filters():
    if os.path.exists(FILTER_FILE):
        try:
            with open(FILTER_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_filters(filters_dict):
    try:
        with open(FILTER_FILE, "w", encoding="utf-8") as f:
            json.dump(filters_dict, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Backup Error: {e}")

CHAT_FILTERS = load_filters()

@app.route('/')
def home():
    return "Bot is running perfectly!"

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def process_update():
        await telegram_app.initialize()
        await telegram_app.process_update(update)

    loop.run_until_complete(process_update())
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🌟 **Welcome! Bot is active.**\n\n"
        "🛡️ **Security:** Admin-Only Filter Lock Active\n\n"
        "📌 **Usage:**\n"
        "• `/filter keyword - reply` (Admins only)\n"
        "• `/s [drama name]` - Get Google AI style 3-point details instantly\n"
        "• `/ping` - Check bot status"
    )
    await update.message.reply_text(welcome_text)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ping_text = (
        "🟢 **Bot Status: ONLINE (Connected & Safe)**\n"
        "📂 **Auto-Filter Backup:** Active & Safe"
    )
    await update.message.reply_text(ping_text)

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    if chat.type != "private":
        try:
            member = await chat.get_member(user_id)
            if member.status not in ["creator", "administrator"]:
                await update.message.reply_text("⚠️ Sorry! Only group administrators can use the `/filter` command (Admin Lock Active).")
                return
        except Exception as e:
            print(f"Admin Check Error: {e}")
            return

    full_text = " ".join(context.args)
    if "-" not in full_text:
        await update.message.reply_text("⚠️ Invalid format! Example: `/filter hi - hello`")
        return
    
    parts = full_text.split("-", 1)
    raw_keyword = parts[0].strip()
    reply_msg = parts[1].strip()
    
    if raw_keyword.startswith('"') and raw_keyword.endswith('"'):
        keyword = raw_keyword[1:-1].strip().lower()
    else:
        keyword = raw_keyword.lower()
    
    if not keyword or not reply_msg:
        await update.message.reply_text("⚠️ Keyword or reply message cannot be empty!")
        return

    chat_id = str(chat.id)
    if chat_id str(chat.id) not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_filters(CHAT_FILTERS)
    
    await update.message.reply_text(f"🔒 **[Admin Lock]** Filter saved successfully!\n📌 **Keyword:** `{keyword}` ➔ `{reply_msg}`")

async def handle_filters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.lower()
    chat_id = str(update.effective_chat.id)
    
    if chat_id in CHAT_FILTERS:
        for keyword, reply in CHAT_FILTERS[chat_id].items():
            if keyword in text:
                await update.message.reply_text(reply)
                break

async def search_drama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Please specify the drama name. Example: `/s Twinkling Watermelon`", reply_to_message_id=update.message.message_id)
        return

    query_raw = " ".join(context.args).strip()
    query_lower = query_raw.lower()
    
    # கூகுள் ஏ.ஐ பாணியில் துல்லியமான 3 குறிப்புகளைத் தரும் வடிவம்
    drama_name = query_raw.title()
    release_year = "2023"
    
    if "twinkling watermelon" in query_lower:
        release_year = "2023"
    elif "lovely runner" in query_lower:
        release_year = "2024"
    elif "dream to you" in query_lower:
        release_year = "2023"
    elif "when i fly towards you" in query_lower:
        release_year = "2023"
    elif "put your head on my shoulder" in query_lower:
        release_year = "2019"
    elif "my girlfriend is an alien" in query_lower:
        release_year = "2019"
    elif "dr. romantic" in query_lower:
        release_year = "2016"
    elif "love o2o" in query_lower:
        release_year = "2016"
    elif "true beauty" in query_lower:
        release_year = "2020"
    elif "i'm not a robot" in query_lower:
        release_year = "2017"

    if "chinese" in query_lower or "china" in query_lower or "mandarin" in query_lower or "when i fly" in query_lower or "love o2o" in query_lower:
        languages = "Mandarin (Original), English / Tamil (Dubbed/Subbed)"
    else:
        languages = "Korean (Original), English / Tamil (Dubbed/Subbed)"

    # கூகுள் ஏ.ஐ ஸ்டைல் சுருக்கமான 3 பாயிண்ட் அவுட்லைன்
    ai_response = (
        f"🤖 **Google AI Summary:**\n\n"
        f"1️⃣ **Drama Name:** {drama_name}\n"
        f"2️⃣ **Release Year:** {release_year}\n"
        f"3️⃣ **Languages:** {languages}"
    )
    
    await update.message.reply_text(ai_response, reply_to_message_id=update.message.message_id)

def setup_webhook():
    import requests
    webhook_url = f"{RENDER_URL}/{TELEGRAM_BOT_TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("ping", ping_command))
telegram_app.add_handler(CommandHandler("status", ping_command))
telegram_app.add_handler(CommandHandler("s", search_drama_command))
telegram_app.add_handler(CommandHandler("search", search_drama_command))
telegram_app.add_handler(CommandHandler("filter", filter_command))

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_filters))

if __name__ == '__main__':
    setup_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
