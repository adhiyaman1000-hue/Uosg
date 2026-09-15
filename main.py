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
        "Join our news channel to get information on all the latest updates.\n\n"
        "Check /privacy to view the privacy policy, and interact with your data."
    )
    
    keyboard = [
        [InlineKeyboardButton("Add me to your chat!", url=f"https://t.me/{context.bot.username}?startgroup=true"),
         InlineKeyboardButton("Get your own Rose!", url="https://t.me/MissRose_bot")],
        [InlineKeyboardButton("🟢 Turn Search ON", callback_data="search_on"),
         InlineKeyboardButton("🔴 Turn Search OFF", callback_data="search_off")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(start_text, reply_markup=reply_markup)

# --- /help COMMAND WITH ALL 27 BUTTONS GRID ---

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_status = "ON 🟢" if BOT_CONFIG.get("search_active", True) else "OFF 🔴"
    help_text = (
        "<b>Help & Usage Guide</b>\n\n"
        "Hey! My name is UOSG Rose. I am a group management bot, here to help you get around and keep order!\n\n"
        f"<b>Google Search Status:</b> {search_status}\n\n"
        "<b>Core Commands:</b>\n"
        " • /start - Starts the bot\n"
        " • /help - Shows this help menu\n"
        " • /toggle - Toggle Google Search trigger ON/OFF\n"
        " • /filter [keyword] - [reply] - Save a custom text filter (Example: /filter hi - Hello Nanba)\n"
        " • /setwelcome [message] - Save custom welcome greeting for new users\n"
        " • /getwelcome - View current group welcome message\n"
        " • /ban - Reply to user message to ban\n"
        " • /unban - Reply to unban user\n"
        " • /mute - Reply to mute user\n"
        " • /unmute - Reply to unmute user\n"
        " • /pin - Reply to pin message\n"
        " • /id - Get user or group ID\n\n"
        "<b>All commands can be used with: / or !</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton("Admin", callback_data="help_admin"), InlineKeyboardButton("Antiflood", callback_data="help_antiflood"), InlineKeyboardButton("AntiRaid", callback_data="help_antiraid")],
        [InlineKeyboardButton("Approval", callback_data="help_approval"), InlineKeyboardButton("Bans", callback_data="help_bans"), InlineKeyboardButton("Blocklists", callback_data="help_blocklists")],
        [InlineKeyboardButton("CAPTCHA", callback_data="help_captcha"), InlineKeyboardButton("Clean Comms", callback_data="help_cleancomms"), InlineKeyboardButton("Clean Service", callback_data="help_cleanservice")],
        [InlineKeyboardButton("Connections", callback_data="help_connections"), InlineKeyboardButton("Disabling", callback_data="help_disabling"), InlineKeyboardButton("Federations", callback_data="help_federations")],
        [InlineKeyboardButton("Filters", callback_data="help_filters"), InlineKeyboardButton("Formatting", callback_data="help_formatting"), InlineKeyboardButton("Greetings", callback_data="help_greetings")],
        [InlineKeyboardButton("Import/Export", callback_data="help_importexport"), InlineKeyboardButton("Languages", callback_data="help_languages"), InlineKeyboardButton("Locks", callback_data="help_locks")],
        [InlineKeyboardButton("Log Channels", callback_data="help_logchannels"), InlineKeyboardButton("Misc", callback_data="help_misc"), InlineKeyboardButton("Notes", callback_data="help_notes")],
        [InlineKeyboardButton("Pin", callback_data="help_pin"), InlineKeyboardButton("Privacy", callback_data="help_privacy"), InlineKeyboardButton("Purges", callback_data="help_purges")],
        [InlineKeyboardButton("Reports", callback_data="help_reports"), InlineKeyboardButton("Rules", callback_data="help_rules"), InlineKeyboardButton("Topics", callback_data="help_topics")],
        [InlineKeyboardButton("Warnings", callback_data="help_warnings"), InlineKeyboardButton("⭐ Custom Instances", callback_data="help_custominstances")],
        [InlineKeyboardButton("🌐 Docs Website", url="https://core.telegram.org/bots/api"), InlineKeyboardButton("🔍 Toggle Search", callback_data="toggle_search_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(help_text, parse_mode="HTML", reply_markup=reply_markup)

# --- CALLBACK QUERY HANDLER FOR BUTTONS ---

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    chat = query.message.chat
    
    if chat.type != "private":
        try:
            member = await chat.get_member(user_id)
            if member.status not in ["creator", "administrator"]:
                await query.answer("⚠️ [Admin Lock] Only group administrators can use these control buttons!", show_alert=True)
                return
        except Exception:
            return

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
    elif data.startswith("help_"):
        feature = data.split("_")[1].replace("help", "").capitalize()
        await query.answer(f"📂 Module [{feature}] is active and ready!", show_alert=True)

# --- CUSTOM FILTER SYSTEM (/filter) ---

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type != "private":
        try:
            member = await chat.get_member(user.id)
            if member.status not in ["creator", "administrator"]:
                await update.message.reply_text("⚠️ **[Admin Lock]** Only administrators can set filters!")
                return
        except Exception:
            return

    full_text = " ".join(context.args)
    match = re.findall(r'"([^"]*)"', full_text)
    
    keyword = ""
    reply_msg = ""
    
    if len(match) >= 1:
        keyword = match[0].strip().lower()
        parts = full_text.split('"', 2)
        if len(parts) >= 3:
            remainder = parts[2].strip()
            reply_msg = remainder[1:].strip() if remainder.startswith("-") else remainder
    else:
        if "-" in full_text:
            parts = full_text.split("-", 1)
            keyword = parts[0].strip().lower()
            reply_msg = parts[1].strip()

    if not keyword or not reply_msg:
        await update.message.reply_text("⚠️ **Invalid Format!** Use like this:\n`/filter keyword - Reply message here`", parse_mode="Markdown")
        return

    chat_id = str(chat.id)
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_json(FILTER_FILE, CHAT_FILTERS)
    
    await update.message.reply_text(f"🔒 **[Filter Saved Successfully]**\nKeyword: `{keyword}`\nReply: `{reply_msg}`", parse_mode="Markdown")

# --- CUSTOM WELCOME SYSTEM (/setwelcome & /getwelcome) ---

async def set_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    
    if chat.type == "private":
        await update.message.reply_text("⚠️ This command can only be used inside groups!")
        return
        
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"]:
            await update.message.reply_text("⚠️ **[Admin Lock]** Only administrators can change welcome settings!")
            return
    except Exception:
        return

    welcome_msg = " ".join(context.args)
    if not welcome_msg:
        await update.message.reply_text("⚠️ **Usage:** `/setwelcome Hello {first}, welcome to {title}!`\nUse `{first}` for user name and `{title}` for group title.", parse_mode="Markdown")
        return

    chat_id = str(chat.id)
    WELCOME_MESSAGES[chat_id] = welcome_msg
    save_json(WELCOME_FILE, WELCOME_MESSAGES)
    
    await update.message.reply_text(f"✅ **[Welcome Message Saved]**\n`{welcome_msg}`", parse_mode="Markdown")

async def get_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    chat_id = str(chat.id)
    
    if chat_id in WELCOME_MESSAGES:
        await update.message.reply_text(f"📌 **Current Group Welcome Message:**\n\n`{WELCOME_MESSAGES[chat_id]}`", parse_mode="Markdown")
    else:
        await update.message.reply_text("ℹ️ No custom welcome set yet. Use `/setwelcome [message]` to configure one.", parse_mode="Markdown")

async def track_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for member in update.message.new_chat_members:
        if member.id == context.bot.id:
            await update.message.reply_text("👋 Thanks for adding me to your group! Use /help to see all features.")
            continue
            
        chat_id = str(update.effective_chat.id)
        welcome_template = WELCOME_MESSAGES.get(chat_id, "Welcome {first} to the group!")
        
        personalized_msg = welcome_template.replace("{first}", member.first_name).replace("{title}", update.effective_chat.title)
        
        keyboard = [[InlineKeyboardButton("Rules & Info", url="https://t.me/RoseSupportChannel")]]
        await update.message.reply_text(personalized_msg, reply_markup=InlineKeyboardMarkup(keyboard))

# --- MODERATION & UTILITIES ---

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_state = BOT_CONFIG.get("search_active", True)
    BOT_CONFIG["search_active"] = not current_state
    save_json(CONFIG_FILE, BOT_CONFIG)
    new_state_text = "ON 🟢 (Active)" if BOT_CONFIG["search_active"] else "OFF 🔴 (Disabled)"
    await update.message.reply_text(f"⚙️ **Google Search Status Changed!**\n📌 Current Mode: **{new_state_text}**")

async def privacy_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    privacy_text = (
        "🔒 **Privacy Policy & Data Interaction**\n\n"
        "This bot stores custom filters, welcomes, and configurations locally for group moderation. No personal media or private chat histories are logged."
    )
    await update.message.reply_text(privacy_text, parse_mode="Markdown")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"]:
            return
    except Exception:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to the user you want to ban!")
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await chat.ban_member(target_user.id)
        await update.message.reply_text(f"🔨 Banned user {target_user.first_name} successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"]:
            return
    except Exception:
        return

    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Please reply to the user you want to unban!")
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await chat.unban_member(target_user.id)
        await update.message.reply_text(f"🔓 Unbanned user {target_user.first_name} successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def mute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"]:
            return
    except Exception:
        return

    if not update.message.reply_to_message:
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await chat.restrict_member(target_user.id, permissions=ChatPermissions(can_send_messages=False))
        await update.message.reply_text(f"🔇 Muted {target_user.first_name} successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def unmute_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"]:
            return
    except Exception:
        return

    if not update.message.reply_to_message:
        return

    target_user = update.message.reply_to_message.from_user
    try:
        await chat.restrict_member(
            target_user.id, 
            permissions=ChatPermissions(
                can_send_messages=True, can_send_media_messages=True, 
                can_send_other_messages=True, can_add_web_page_previews=True
            )
        )
        await update.message.reply_text(f"🔊 Unmuted {target_user.first_name} successfully.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def pin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    if chat.type == "private":
        return
    try:
        member = await chat.get_member(user.id)
        if member.status not in ["creator", "administrator"]:
            return
    except Exception:
        return

    if not update.message.reply_to_message:
        return

    try:
        await context.bot.pin_chat_message(chat_id=chat.id, message_id=update.message.reply_to_message.message_id)
        await update.message.reply_text("📌 Message pinned successfully!")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def get_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        await update.message.reply_text(f"🆔 **User ID:** `{target.id}`\n👤 **Name:** {target.first_name}", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🆔 **Group ID:** `{chat.id}`\n📌 **Chat Type:** {chat.type}", parse_mode="Markdown")

# --- GOOGLE SEARCH TRIGGER HANDLER ---

async def auto_search_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    if text.startswith('/'):
        return

    chat_id = str(update.effective_chat.id)
    text_lower = text.lower()
    
    # 1. Custom Filters Check
    if chat_id in CHAT_FILTERS:
        for keyword, reply in CHAT_FILTERS[chat_id].items():
            if keyword in text_lower:
                await update.message.reply_text(reply, reply_to_message_id=update.message.message_id)
                return

    # 2. Restricted Words List for Google Search Button Trigger
    restricted_words = [
        "bro", "send", "send panunga", "send me", "link", "links", "episode", "episodes", 
        "dubbed", "subbed", "tamil", "telugu", "hindi", "english", "download", "file", 
        "files", "movie", "movies", "series", "season", "seasons", "part", "parts", 
        "video", "videos", "watch", "online", "telegram", "channel", "group", "admin", 
        "please", "pls", "plz", "give", "share", "get", "got", "find", "search", 
        "telegram link", "drive link", "mega link", "zip", "rar", "apk", "mod", 
        "full movie", "full series", "all episodes", "hd", "bluray", "webrip", "hdtv", 
        "camrip", "torrent", "magnet", "bot", "bots", "hi bro", "hey bro", "bro send", 
        "send link", "need link", "want link", "any link", "fast", "slow", "server", 
        "working", "not working", "error", "hello bro", "dear bro", "bro give", "give me", 
        "can you send", "i want", "i need", "anybody", "anyone", "here", "there", "when", 
        "where", "how", "why", "who", "what", "site", "website", "app", "application", 
        "play", "stop", "start", "restart", "update", "new", "old", "latest", "upcoming",
        "drama", "kdrama", "cdrama", "jdrama", "anime", "panunga"
    ]

    words = text.split()
    filtered_words = [w for w in words if w.lower() not in restricted_words]

    if BOT_CONFIG.get("search_active", True) and filtered_words and not any(char.isdigit() for char in text) and "http" not in text_lower:
        has_restricted = any(rw in text_lower for rw in restricted_words)
        if has_restricted:
            drama_query = " ".join(filtered_words)
            encoded_query = urllib.parse.quote(drama_query)
            google_search_url = f"https://www.google.com/search?q={encoded_query}"

            search_response_text = (
                f"🔍 **Search Query:** `{drama_query.title()}`\n\n"
            )
            
            keyboard = [[InlineKeyboardButton("🔍 Open Google Search", url=google_search_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await update.message.reply_text(
                search_response_text, 
                parse_mode="Markdown", 
                reply_markup=reply_markup, 
                reply_to_message_id=update.message.message_id
            )

def setup_webhook():
    import requests
    webhook_url = f"{RENDER_URL}/{TELEGRAM_BOT_TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}")

# --- HANDLERS REGISTRATION ---
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("help", help_command))
telegram_app.add_handler(CommandHandler("toggle", toggle_command))
telegram_app.add_handler(CommandHandler("privacy", privacy_command))
telegram_app.add_handler(CommandHandler("filter", filter_command))
telegram_app.add_handler(CommandHandler("setwelcome", set_welcome))
telegram_app.add_handler(CommandHandler("getwelcome", get_welcome))
telegram_app.add_handler(CommandHandler("ban", ban_user))
telegram_app.add_handler(CommandHandler("unban", unban_user))
telegram_app.add_handler(CommandHandler("mute", mute_user))
telegram_app.add_handler(CommandHandler("unmute", unmute_user))
telegram_app.add_handler(CommandHandler("pin", pin_message))
telegram_app.add_handler(CommandHandler("id", get_id))

telegram_app.add_handler(CallbackQueryHandler(button_handler))
telegram_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, track_new_members))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_search_and_reply))

if __name__ == '__main__':
    setup_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
