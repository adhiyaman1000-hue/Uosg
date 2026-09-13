import os
import json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters
import urllib.parse

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
        "💖 **Hello there! I'm Zara, your UOSG group assistant.**\n\n"
        "🛡️ **Security:** 300+ Restricted Words Filter & Inline Button Search Active\n\n"
        "📌 **Info:**\n"
        "• Send your drama message, and I will filter out casual words to provide a cute Google Search button!"
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
                await update.message.reply_text("⚠️ Sorry! Only group administrators can use the `/filter` command.")
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
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_filters(CHAT_FILTERS)
    
    await update.message.reply_text(f"🔒 **[Admin Lock]** Filter saved successfully!\n📌 **Keyword:** `{keyword}` ➔ `{reply_msg}`")

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
                await update.message.reply_text(reply)
                return

    # 🚫 300+ Comprehensive Restricted / Ignored Words List
    restricted_words = [
        "bro", "send", "send panunga", "send me", "link", "links", "episode", "episodes", 
        "dubbed", "subbed", "tamil", "telugu", "hindi", "english", "download", "file", 
        "files", "movie", "movies", "series", "season", "seasons", "part", "parts", 
        "video", "videos", "watch", "online", "telegram", "channel", "group", "admin", 
        "please", "pls", "plz", "give", "share", "get", "got", "find", "search", 
        "telegram link", "drive link", "mega link", "zip", "rar", "apk", "mod", 
        "full movie", "full series", "all episodes", "hd", "1080p", "720p", "480p", 
        "bluray", "webrip", "hdtv", "camrip", "torrent", "magnet", "bot", "bots", 
        "hi bro", "hey bro", "bro send", "send link", "need link", "want link", 
        "any link", "fast", "slow", "server", "working", "not working", "error", 
        "hello bro", "dear bro", "bro give", "give me", "can you send", "i want", 
        "i need", "anybody", "anyone", "here", "there", "when", "where", "how", 
        "why", "who", "what", "site", "website", "app", "application", "play", 
        "stop", "start", "restart", "update", "new", "old", "latest", "upcoming",
        "hi", "hello", "hey", "gm", "gn", "good morning", "good night", "how are you", 
        "fine", "thanks", "thank you", "ok", "okay", "bye", "see you", "sup", 
        "what's up", "sis", "friend", "friends", "owner", "founder", 
        "help", "support", "issue", "problem", "bug", "chat", "talk", "speak", 
        "message", "text", "voice", "audio", "photo", "image", "sticker", "gif", 
        "emoji", "laugh", "lol", "haha", "omg", "wow", "nice", "good", "bad", 
        "terrible", "awesome", "cool", "super", "great", "best", "worst", "right", 
        "wrong", "true", "false", "yes", "no", "maybe", "sure", "of course", 
        "really", "actually", "seriously", "just", "only", "some", "any", "all", 
        "none", "more", "less", "much", "many", "few", "other", "another", "same", 
        "different", "such", "own", "each", "every", "both", "either", "neither", 
        "local", "global", "world", "universe", "uosg", "drama", "kdrama", 
        "cdrama", "jdrama", "anime", "toon", "cartoon", "volume", "chapter", 
        "request", "demands", "ask", "asking", "asked", "reply", "replied", 
        "comment", "comments", "post", "posts", "upload", "uploaded", "forward", 
        "forwarded", "pin", "pinned", "unpin", "delete", "deleted", "remove", 
        "removed", "ban", "banned", "kick", "kicked", "mute", "muted", "unmute",
        "i", "me", "my", "myself", "we", "our", "ours", "ourselves", "you", "your", 
        "yours", "yourself", "yourselves", "he", "him", "his", "himself", "she", "her", 
        "hers", "herself", "it", "its", "itself", "they", "them", "their", "theirs", 
        "themselves", "what", "which", "who", "whom", "this", "that", "these", "those", 
        "am", "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", 
        "having", "do", "does", "did", "doing", "a", "an", "the", "and", "but", "if", 
        "or", "because", "as", "until", "while", "of", "at", "by", "for", "with", "about", 
        "against", "between", "into", "through", "during", "before", "after", "above", 
        "below", "to", "from", "up", "down", "in", "out", "on", "off", "over", "under", 
        "again", "further", "then", "once", "panunga"
    ]

    words = text.split()
    filtered_words = [w for w in words if w.lower() not in restricted_words]

    if not filtered_words:
        return

    drama_query = " ".join(filtered_words)
    encoded_query = urllib.parse.quote(drama_query)
    google_search_url = f"https://www.google.com/search?q={encoded_query}"

    zara_response = (
        f"💖 **Heyy!** All official details and available languages for `{drama_query.title()}` can be checked on Google!\n\n"
        f"✨ Our **UOSG Group CEO and Founders** will review this, and our admins will send you the drama files very soon! Please wait patiently until then! 🥰"
    )
    
    # அழகிய இன்லைன் பட்டன் அமைப்பு (Inline Keyboard Button)
    keyboard = [[InlineKeyboardButton("🔍 Go to Google Search", url=google_search_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        zara_response, 
        parse_mode="Markdown", 
        reply_markup=reply_markup, 
        reply_to_message_id=update.message.message_id
    )

def setup_webhook():
    import requests
    webhook_url = f"{RENDER_URL}/{TELEGRAM_BOT_TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("ping", ping_command))
telegram_app.add_handler(CommandHandler("status", ping_command))
telegram_app.add_handler(CommandHandler("filter", filter_command))

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_search_and_reply))

if __name__ == '__main__':
    setup_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
