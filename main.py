import os
import json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ChatPermissions
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import urllib.parse
import re

TELEGRAM_BOT_TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
RENDER_URL = "https://uosg-kg1t.onrender.com"

app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

FILTER_FILE = "filter_backup.json"
CONFIG_FILE = "bot_config.json"
WELCOME_FILE = "welcome_backup.json"

def load_json(filename, default_val):
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default_val
    return default_val

def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Save Error ({filename}): {e}")

CHAT_FILTERS = load_json(FILTER_FILE, {})
BOT_CONFIG = load_json(CONFIG_FILE, {"search_active": True})
WELCOME_MESSAGES = load_json(WELCOME_FILE, {})

@app.route('/')
def home():
    return "UOSG Advanced Rose Bot is running perfectly!"

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.method == "POST":
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

# --- /start COMMAND ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    start_text = (
        "Hey there! My name is UOSG Rose - I'm here to help you manage your groups! "
        "Use /help to find out how to use me to my full potential.\n\n"
        "Join our news channel to get information on all the latest updates."
    )
    
    keyboard = [
        [InlineKeyboardButton("Add me to your chat!", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("🟢 Turn Search ON", callback_data="search_on"),
         InlineKeyboardButton("🔴 Turn Search OFF", callback_data="search_off")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(start_text, reply_markup=reply_markup)

# --- /help COMMAND WITH ALL BUTTONS GRID ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_status = "ON 🟢" if BOT_CONFIG.get("search_active", True) else "OFF 🔴"
    help_text = (
        "<b>Help & Usage Guide</b>\n\n"
        "Hey! My name is UOSG Rose. I am a group management bot, here to help you keep order!\n\n"
        f"<b>Google Search Status:</b> {search_status}\n\n"
        "<b>Core Commands:</b>\n"
        " • /start - Starts the bot\n"
        " • /help - Shows this help menu\n"
        " • /toggle - Toggle Google Search trigger ON/OFF\n"
        " • /filter [keyword] - [reply] - Save custom text filter\n"
        " • /setwelcome [message] - Save custom welcome greeting\n"
        " • /ban /unban /mute /unmute /pin /id"
    )
    
    keyboard = [
        [InlineKeyboardButton("Admin", callback_data="help_admin"), InlineKeyboardButton("Antiflood", callback_data="help_antiflood")],
        [InlineKeyboardButton("Bans", callback_data="help_bans"), InlineKeyboardButton("Filters", callback_data="help_filters")],
        [InlineKeyboardButton("Greetings", callback_data="help_greetings"), InlineKeyboardButton("Locks", callback_data="help_locks")],
        [InlineKeyboardButton("Notes", callback_data="help_notes"), InlineKeyboardButton("Warnings", callback_data="help_warnings")],
        [InlineKeyboardButton("🔍 Toggle Search", callback_data="toggle_search_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, parse_mode="HTML", reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    
    if data == "search_on":
        BOT_CONFIG["search_active"] = True
        save_json(CONFIG_FILE, BOT_CONFIG)
        await query.answer("✅ Google Search Feature turned ON!", show_alert=True)
    elif data == "search_off":
        BOT_CONFIG["search_active"] = False
        save_json(CONFIG_FILE, BOT_CONFIG)
        await query.answer("❌ Google Search Feature turned OFF!", show_alert=True)
    elif data == "toggle_search_menu":
        current = BOT_CONFIG.get("search_active", True)
        status_txt = "Active (ON 🟢)" if current else "Disabled (OFF 🔴)"
        await query.answer(f"Google Search Status: {status_txt}", show_alert=True)

# --- CUSTOM FILTER SYSTEM (/filter) ---

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    full_text = " ".join(context.args)
    if "-" not in full_text:
        await update.message.reply_text("⚠️ **Format:** `/filter keyword - Reply message`", parse_mode="Markdown")
        return
    
    parts = full_text.split("-", 1)
    keyword = parts[0].strip().lower()
    reply_msg = parts[1].strip()

    chat_id = str(chat.id)
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_json(FILTER_FILE, CHAT_FILTERS)
    await update.message.reply_text(f"🔒 **Filter Saved Successfully!**\nKeyword: `{keyword}`", parse_mode="Markdown")

# --- WELCOME SYSTEM ---

async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    welcome_msg = " ".join(context.args)
    if not welcome_msg:
        await update.message.reply_text("⚠️ **Usage:** `/setwelcome Hello {first}!`", parse_mode="Markdown")
        return

    chat_id = str(chat.id)
    WELCOME_MESSAGES[chat_id] = welcome_msg
    save_json(WELCOME_FILE, WELCOME_MESSAGES)
    await update.message.reply_text("✅ **Welcome Message Saved!**", parse_mode="Markdown")

async def track_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            continue
        chat_id = str(update.effective_chat.id)
        welcome_template = WELCOME_MESSAGES.get(chat_id, "Welcome {first} to the group!")
        personalized_msg = welcome_template.replace("{first}", member.first_name).replace("{title}", update.effective_chat.title)
        await update.message.reply_text(personalized_msg)

# --- UTILITIES & SEARCH ---

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    BOT_CONFIG["search_active"] = not BOT_CONFIG.get("search_active", True)
    save_json(CONFIG_FILE, BOT_CONFIG)
    await update.message.reply_text(f"⚙️ Search Status: {BOT_CONFIG['search_active']}")

async def auto_search_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    if text.startswith('/'):
        return

    chat_id = str(update.effective_chat.id)
    text_lower = text.lower()
    
    if chat_id in CHAT_FILTERS:
        for keyword, reply in CHAT_FILTERS[chat_id].items():
            if keyword in text_lower:
                await update.message.reply_text(reply, reply_to_message_id=update.message.message_id)
                return

    restricted_words = ["bro", "send", "link", "download", "movie", "series", "drama", "kdrama", "cdrama", "episode"]
    if BOT_CONFIG.get("search_active", True) and any(rw in text_lower for rw in restricted_words):
        encoded_query = urllib.parse.quote(text)
        google_search_url = f"https://www.google.com/search?q={encoded_query}"
        keyboard = [[InlineKeyboardButton("🔍 Open Google Search", url=google_search_url)]]
        await update.message.reply_text(f"🔍 **Search Query:** `{text}`", parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard), reply_to_message_id=update.message.message_id)

def setup_webhook():
    import requests
    webhook_url = f"{RENDER_URL}/{TELEGRAM_BOT_TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}")

# Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("toggle", toggle_command))
telegram_app.add_handler(CommandHandler("filter", filter_command))
telegram_app.add_handler(CommandHandler("setwelcome", set_welcome))
telegram_app.add_handler(CallbackQueryHandler(button_handler))
telegram_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_members))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_search_and_reply))

if __name__ == '__main__':
    setup_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
