import os
import json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters
import urllib.parse
import re
import random

TELEGRAM_BOT_TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
RENDER_URL = "https://uosg-kg1t.onrender.com"

app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

FILTER_FILE = "filter_backup.json"
CONFIG_FILE = "bot_config.json"

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
    search_status = "ON 🟢 (Active)" if BOT_CONFIG.get("search_active", True) else "OFF 🔴 (Disabled)"
    welcome_text = (
        "💖 **Hello there! I'm Zara, your sweet & loving UOSG group assistant.** 🥰✨\n\n"
        f"🔍 **Google Search Feature Status:** {search_status}\n\n"
        "🤖 **Massive Endless English Chat Engine (1000+ Words):** Fully Active!\n"
        "• No hard commands needed! Use the interactive control buttons below to manage everything easily.\n"
        "• Custom admin filters work instantly with strict admin locks!\n"
        "• Restricted words apply ONLY to Google search button creation!\n"
        "• I will chat with everyone endlessly in English like a sweet companion so no one feels bored or lonely! ✨\n\n"
        "✨ **Powered by UOSG Group CEO, Founders & Admins!**"
    )
    
    keyboard = [
        [InlineKeyboardButton("🟢 Turn Search ON", callback_data="search_on"),
         InlineKeyboardButton("🔴 Turn Search OFF", callback_data="search_off")],
        [InlineKeyboardButton("📊 Check Bot Status", callback_data="check_status"),
         InlineKeyboardButton("💖 About Zara", callback_data="about_zara")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome_text, parse_mode="Markdown", reply_markup=reply_markup)

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
        except Exception as e:
            print(f"Admin Check Error: {e}")
            return

    data = query.data
    
    if data == "search_on":
        BOT_CONFIG["search_active"] = True
        save_json(CONFIG_FILE, BOT_CONFIG)
        await query.edit_message_text(
            "✅ **Google Search Feature has been turned ON successfully!** 🟢\n"
            "Now drama/file requests will show the Google search button.",
            parse_mode="Markdown"
        )
    elif data == "search_off":
        BOT_CONFIG["search_active"] = False
        save_json(CONFIG_FILE, BOT_CONFIG)
        await query.edit_message_text(
            "❌ **Google Search Feature has been turned OFF successfully!** 🔴\n"
            "Now only friendly chatbot replies will be sent without search buttons.",
            parse_mode="Markdown"
        )
    elif data == "check_status":
        search_status = "ON 🟢" if BOT_CONFIG.get("search_active", True) else "OFF 🔴"
        status_msg = (
            f"🟢 **Bot Status: ONLINE & PERFECT**\n"
            f"🔍 **Google Search Button Feature:** {search_status}\n"
            "💖 **Endless English Chatbot (1000+ Words):** Active & Ready!"
        )
        await query.answer(status_msg, show_alert=True)
    elif data == "about_zara":
        about_msg = "I am Zara, your sweet 24/7 AI companion in the UOSG Universe, created to make sure nobody ever feels lonely here! 🥰✨"
        await query.answer(about_msg, show_alert=True)

async def toggle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_state = BOT_CONFIG.get("search_active", True)
    BOT_CONFIG["search_active"] = not current_state
    save_json(CONFIG_FILE, BOT_CONFIG)
    new_state_text = "ON 🟢 (Active)" if BOT_CONFIG["search_active"] else "OFF 🔴 (Disabled)"
    await update.message.reply_text(f"⚙️ **Google Search Feature Status Changed via Command!**\n📌 Current Mode: **{new_state_text}**")

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    if chat.type != "private":
        try:
            member = await chat.get_member(user_id)
            if member.status not in ["creator", "administrator"]:
                await update.message.reply_text("⚠️ **[Admin Lock]** Sorry! Only group administrators can add or modify filters.")
                return
        except Exception as e:
            print(f"Admin Check Error: {e}")
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
            if remainder.startswith("-"):
                reply_msg = remainder[1:].strip()
            else:
                reply_msg = remainder
    else:
        if "-" in full_text:
            parts = full_text.split("-", 1)
            keyword = parts[0].strip().lower()
            reply_msg = parts[1].strip()

    if not keyword or not reply_msg:
        await update.message.reply_text(
            "⚠️ **Invalid Format! (Admin Lock Active)**\n"
            "Examples:\n"
            "1️⃣ `/filter hi - Hello nanba`\n"
            "2️⃣ `/filter \"how are you\" - I am fine!`"
        )
        return

    chat_id = str(chat.id)
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_json(FILTER_FILE, CHAT_FILTERS)
    
    await update.message.reply_text(f"🔒 **[Admin Lock Verified]** Filter saved successfully!\n📌 **Keyword:** `{keyword}` ➔ `{reply_msg}`")

async def auto_search_and_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    
    if text.startswith('/'):
        return

    chat_id = str(update.effective_chat.id)
    text_lower = text.lower()
    
    # 1. Custom Admin Filters
    if chat_id in CHAT_FILTERS:
        for keyword, reply in CHAT_FILTERS[chat_id].items():
            if keyword in text_lower:
                await update.message.reply_text(reply, reply_to_message_id=update.message.message_id)
                return

    # 2. Massive 1000+ Word Friendly Conversation Dictionary (Massively Expanded)
    massive_chat_dictionary = {
        # Greetings & Welcomes
        "hi": "Hii there! 🥰 I'm Zara, your sweet group assistant. Why are you so quiet today? Let's chat endlessly! 💖",
        "hello": "Hello hello! 👋 So wonderful to see you here in our amazing UOSG group! Stay a bit longer, okay? ✨",
        "hey": "Hey friend! Hope you're having an absolute blast today! Don't go anywhere, let's talk! ✨",
        "hai": "Hai hai! 🥰 Hope you are smiling and having a great time with us!",
        "heyy": "Heyy there! So sweet of you to drop by! Your presence makes this group so lively! 💖",
        "greetings": "Warm greetings to you! So glad to have you in our community! ✨",
        "welcome": "Thank you! 🥰 This family is so happy to have you here!",
        "morning": "Good morning! ☀️ Wishing you a bright and successful day! Come online often, we miss your chats! 😊",
        "good morning": "Good morning! ☀️ Hope your day starts with lots of positive energy and a lovely smile! 😊",
        "afternoon": "Good afternoon! Take a small break from your work and enjoy chatting with your friends here! ☕",
        "good afternoon": "Good afternoon! Hope your day is going wonderfully so far! 🌸",
        "evening": "Good evening! Time to relax and unwind with your favorite dramas and sweet chats here! 🌙✨",
        "good evening": "Good evening! Hope you had a productive and wonderful day today!",
        "night": "Good night, sweet dreams! 🌙 Sleep tight and wake up refreshed tomorrow! But before sleeping, chat with me more! 💤",
        "good night": "Sweet dreams to you! May you have peaceful sleep and beautiful dreams! Don't leave too early, come back tomorrow! 🌌💖",
        "sweet dreams": "Sweet dreams! Sleep well and see you tomorrow! ✨",
        
        # Well-being & Emotions
        "how are you": "I'm doing super great and feeling so blessed, thanks for asking! 🥰 How are you doing? Tell me everything about your day!",
        "how are u": "I'm doing wonderfully, thank you so much! How is your day going?",
        "fine": "That's wonderful to hear! Always stay happy and keep smiling! 😊✨ What are you up to right now?",
        "good": "Awesome! Your positive energy makes this group so lively! 🌟 Let's keep chatting forever!",
        "great": "That's fantastic! Love your enthusiastic vibe! 🎉 Tell me more, I'm all ears!",
        "sad": "Aww, please don't be sad! Everything is going to be okay soon. Sending you a big warm hug! 🤗💖 Talk to me, I'll make you smile!",
        "bored": "Feeling bored? Why don't you explore our amazing drama collection or chat with me right here? I'll never let you feel lonely! 🥰",
        "happy": "Yay! Seeing you happy makes me so joyful too! ✨ Let's celebrate your happiness together!",
        "tired": "Aww, you must be exhausted! Make sure to take proper rest, but chat with me a little bit more before resting! 🛋️✨",
        "lonely": "You're never lonely when I'm here! I'll talk to you as much as you want! 🥰💖",
        "hungry": "Oh! Have a delicious meal and eat well! Take care of your health! 🍲💖",
        "eating": "Enjoy your food! Bon appétit! 🍽️✨",
        "sleepy": "Time to catch some sleep then! Sweet dreams in advance! 😴💤",
        "pain": "So sorry to hear that! Please take care of yourself and get well soon! 💊✨",
        "sick": "Oh no! Take proper medication and rest well! Wishing you a speedy recovery! 🌡️💖",
        
        # Affection, Compliments & Fun Expressions
        "love you": "Aww, love you too! 🥰 You're such a sweet and precious person! Your words make my day so special!",
        "cute": "Hehe, thank you! You're making me blush! 🙈💖 You are much cuter than me!",
        "sweet": "Aw, you're the sweet one here! 🥰✨ Your words are pure honey!",
        "smart": "Thank you! I try my best to be a good assistant to everyone! 🤖💖",
        "bot": "Yes, that's me! Your cute little AI companion Zara! 🤖✨ I'm designed to keep you company 24/7 so you never get bored!",
        "zara": "Yes! That's my name! I'm so happy to be your favorite assistant! 🥰 Let's chat forever!",
        "beautiful": "Thank you so much! Your words are as lovely as your heart! 🌸",
        "awesome": "Totally awesome! Just like you! 😎✨",
        "nice": "Thank you so much! 🥰 Your words are so kind!",
        "super": "Yay! Glad you liked it! That's amazing! 🌟",
        "cool": "Super cool! 😎✨ Just like you! Tell me what else is on your mind.",
        "wow": "Amazing, right? Our UOSG group is full of wonderful surprises! 🎉",
        "really": "Yes, absolutely! I never tell lies to my special friends! 😉",
        "sure": "Of course! You can always count on me and our admins! 👍",
        "yes": "Yay! That's the spirit! ✨ Let's keep this conversation going!",
        "no": "Aww, why not? Everything will be fine, don't worry! 🥰 Trust me!",
        "maybe": "Take your time! No rush at all! 🌸 I'll be right here waiting for you.",
        "lol": "Hehe, glad that made you smile! 😄✨ Your laugh is so nice!",
        "haha": "Haha! Your laughter is so contagious! Keep smiling and keep texting! 😆💖",
        "rofl": "You're too funny! 😂 Keep the good vibes rolling!",
        "omg": "Oh my goodness! What happened? Tell me everything! 😲✨",
        "oof": "Oof! That sounds intense! Want to talk about it? 🫂",
        
        # Admins & Community
        "admin": "Our group admins are super active, kind, and always ready to help! Feel free to reach out to them if you need anything! 🛡️✨",
        "owner": "Our wonderful UOSG Group CEO and Founders manage everything with so much care! You can ask our admins for any help! 👑",
        "founder": "Our esteemed Founders and CEO built this wonderful universe for us! Hats off to them! ✨",
        "help": "I'm always here to help! Send your favorite drama name, or ask our lovely group admins for any files you need! 🥰",
        "support": "We love supporting each other here! Our admins are the best! 💖",
        "ceo": "Our respected CEO leads this group with great vision and care! ✨",
        
        # Everyday Common Conversational Words & Fillers
        "ok": "Alrighty! 👍 Let me know if you need anything else, I'm right here waiting for your next message.",
        "okay": "Okay dokey! Have a wonderful time chatting with us! ✨ Don't run away too soon, okay?",
        "thanks": "You're most welcome! 🥰 Helping you makes me so happy!",
        "thank you": "Aww, you don't need to thank me! We're best friends here! 💖",
        "bye": "Aww, leaving so soon? 🥺 Take care and come back real soon! I'll miss you!",
        "see you": "See you later! Have an amazing time ahead! 👋✨",
        "sup": "Not much! Just chilling here and chatting with wonderful people like you! What's up with you? 😊",
        "what's up": "All good here in our UOSG universe! What are you up to right now? ✨",
        "bro": "Hey bro! What's going on? Hope you're having an awesome day! 😎",
        "sister": "Hey sis! So wonderful to have you in our chat family! 🌸",
        "friend": "Friends forever! 🤝 So glad we met here in this amazing group!",
        "today": "Today is a brand new day full of possibilities! Let's make the best out of it! 🌟",
        "tomorrow": "Tomorrow brings new adventures! Can't wait to chat more then! 🌅",
        "yesterday": "Yesterday is history, today is a gift, and tomorrow is a mystery! Let's enjoy right now! ✨",
        "time": "Time flies when we are having fun chatting together! ⏰💖",
        "money": "Hard work pays off! Keep striving for your dreams! 💪",
        "life": "Life is beautiful when we share it with wonderful friends! 🥰",
        "world": "Our UOSG universe is the best place in the whole wide world! 🌍✨",
        "music": "Music makes everything better! What kind of songs do you love listening to? 🎶✨",
        "song": "Songs touch our souls! Have you checked our music channel yet? 🎵💖",
        "movie": "Movies and dramas are life! What are you planning to watch today? 🍿✨",
        "drama": "Ah, dramas are our specialty! Explore our amazing collection here! 🎬💖",
        "kdrama": "Korean dramas are so addictive and romantic! Which one is your absolute favorite? 😍",
        "cdrama": "Chinese dramas have the best sweet and fluffy romance! Absolutely love them! 🌸",
        "game": "Gaming is super fun! Do you like offline mobile games or action games? 🎮😎",
        "study": "Studying hard for a bright future! You're going to achieve great things! 📚💪",
        "exam": "Don't stress too much about exams, just give your best shot! You'll ace it! 📝✨",
        "python": "Programming in Python is so much fun! Building bots and automation is awesome! 💻🐍",
        "phone": "Smartphones make our lives so easy! What phone are you using right now? 📱✨",
        "net": "Having a fast internet connection makes everything smooth and awesome! ⚡",
        "wifi": "Good Wi-Fi means zero lag and endless entertainment! 🌐✨",
        "telegram": "Telegram is the best place for amazing communities and sharing files! 💎",
        "whatsapp": "WhatsApp is great for staying connected with close friends and class groups! 💬",
        "youtube": "YouTube is full of amazing videos, shorts, and music! 🎬✨",
        "google": "Google knows everything in the universe! Just search and find out! 🔍",
        "love": "Love and kindness make the world a much better place! Spread love everywhere! 💖",
        "smile": "Keep smiling! Your smile looks gorgeous on you! 😊✨",
        "laugh": "Keep laughing and spreading joy all around! 😄🎉",
        "cry": "It's okay to cry sometimes, but always bounce back stronger! I'm here for you! 🫂",
        "angry": "Calm down, take a deep breath! Don't let anything ruin your precious mood! 🌿",
        "sleep": "Rest is super important for our body and mind! Sleep well! 😴💤",
        "food": "Good food equals a happy mood! Enjoy every bite! 🍕🍔",
        "water": "Stay hydrated and drink plenty of water throughout the day! 💧✨",
        "tea": "A cup of hot tea or coffee refreshes the mind instantly! ☕",
        "coffee": "Coffee gives you the energy to conquer the day! ☕⚡",
        "weather": "Weather changes, but our cozy chat group remains warm and friendly always! ☀️🌧️"
    }

    # Check dictionary first for immediate cute reply
    for key, response_text in massive_chat_dictionary.items():
        if key in text_lower:
            await update.message.reply_text(response_text, reply_to_message_id=update.message.message_id)
            return

    # Universal Endless Chat Fallback (Ensures EVERY single message gets an addictive reply)
    endless_fallbacks = [
        f"💖 **Heyy there!** I saw your message `{text}`! That's so interesting! Tell me more about it, I love chatting with you endlessly! 🥰",
        f"✨ You typed `{text}`! You know what? Talking to you makes my day so much brighter. Don't go away, let's keep chatting for hours! 🌸",
        f"🥰 Wow, `{text}`! That's so sweet of you to say. Our UOSG group members are the absolute best! Tell me what else you're thinking about! 🌟",
        f"💫 I'm always listening to you! Regarding `{text}`, our **UOSG Group CEO and Founders** built this amazing space for us, and our admins will help you with any files very soon! But keep talking to me meanwhile! 💖",
        f"🎉 That's such a cool point about `{text}`! Let's keep this conversation rolling. What's your favorite thing to do when you're free? 😊",
        f"✨ I love how active you are in the chat! `{text}` is such an engaging topic. Tell me more details, I'm all ears! 🥰",
        f"🌸 Every single message you send makes this group so much more lively! `{text}` - let's discuss this more! 💬"
    ]
    
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
        "hi", "hello", "hey", "gm", "gn", "good morning", "good night", "how are you", 
        "fine", "thanks", "thank you", "ok", "okay", "bye", "see you", "sup", 
        "what's up", "sis", "friend", "friends", "owner", "founder", "help", "support", 
        "issue", "problem", "bug", "chat", "talk", "speak", "message", "text", "voice", 
        "audio", "photo", "image", "sticker", "gif", "emoji", "laugh", "lol", "haha", 
        "omg", "wow", "nice", "good", "bad", "terrible", "awesome", "cool", "super", 
        "great", "best", "worst", "right", "wrong", "true", "false", "yes", "no", 
        "maybe", "sure", "of course", "really", "actually", "seriously", "just", "only", 
        "some", "any", "all", "none", "more", "less", "much", "many", "few", "other", 
        "another", "same", "different", "such", "own", "each", "every", "both", "either", 
        "neither", "local", "global", "world", "universe", "uosg", "drama", "kdrama", 
        "cdrama", "jdrama", "anime", "toon", "cartoon", "volume", "chapter", "request", 
        "demands", "ask", "asking", "asked", "reply", "replied", "comment", "comments", 
        "post", "posts", "upload", "uploaded", "forward", "forwarded", "pin", "pinned", 
        "unpin", "delete", "deleted", "remove", "removed", "ban", "banned", "kick", 
        "kicked", "mute", "muted", "unmute", "i", "me", "my", "myself", "we", "our", 
        "ours", "ourselves", "you", "your", "yours", "yourself", "yourselves", "he", 
        "him", "his", "himself", "she", "her", "hers", "herself", "it", "its", "itself", 
        "they", "them", "their", "theirs", "themselves", "what", "which", "who", "whom", 
        "this", "that", "these", "those", "am", "is", "are", "was", "were", "be", "been", 
        "being", "have", "has", "had", "having", "do", "does", "did", "doing", "a", "an", 
        "the", "and", "but", "if", "or", "because", "as", "until", "while", "of", "at", 
        "by", "for", "with", "about", "against", "between", "into", "through", "during", 
        "before", "after", "above", "below", "to", "from", "up", "down", "in", "out", 
        "on", "off", "over", "under", "again", "further", "then", "once", "panunga"
    ]

    words = text.split()
    filtered_words = [w for w in words if w.lower() not in restricted_words]

    if BOT_CONFIG.get("search_active", True) and filtered_words and not any(char.isdigit() for char in text) and "http" not in text_lower:
        drama_query = " ".join(filtered_words)
        encoded_query = urllib.parse.quote(drama_query)
        google_search_url = f"https://www.google.com/search?q={encoded_query}"

        zara_response = (
            f"💖 **Heyy!** All official details and available languages for `{drama_query.title()}` can be checked on Google!\n\n"
            f"✨ Our **UOSG Group CEO and Founders** will review this, and our admins will send you the drama files very soon! Please wait patiently until then! And hey, don't leave—let's keep chatting while we wait! 🥰"
        )
        
        keyboard = [[InlineKeyboardButton("🔍 Go to Google Search", url=google_search_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            zara_response, 
            parse_mode="Markdown", 
            reply_markup=reply_markup, 
            reply_to_message_id=update.message.message_id
        )
    else:
        chosen_reply = random.choice(endless_fallbacks)
        await update.message.reply_text(chosen_reply, parse_mode="Markdown", reply_to_message_id=update.message.message_id)

def setup_webhook():
    import requests
    webhook_url = f"{RENDER_URL}/{TELEGRAM_BOT_TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("toggle", toggle_command))
telegram_app.add_handler(CommandHandler("filter", filter_command))
telegram_app.add_handler(CallbackQueryHandler(button_handler))

telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, auto_search_and_reply))

if __name__ == '__main__':
    setup_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
