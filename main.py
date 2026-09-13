import os
import json
requests = __import__('requests')
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, MessageHandler, filters

# Re-verified Configuration Tokens
TELEGRAM_BOT_TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
GOOGLE_API_KEY = "AIzaSyBXWXOvvUxLiEY7_gEXn0z6SrDvrzTGEm8"
SEARCH_ENGINE_ID = "5788d738584a240fa"
RENDER_URL = "https://uosg-kg1t.onrender.com"

app = Flask(__name__)
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Persistent Backup Filter System
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
    return "𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝐞𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩 Bot is running perfectly!"

@app.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, telegram_app.bot)
    
    async def process_update():
        await telegram_app.initialize()
        await telegram_app.process_update(update)

    import asyncio
    asyncio.run(process_update())
    return "OK"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        f"🌟 **வணக்கம் நண்பா! 𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝒆𝐫𝐬𝐞 𝐨𝐟 𝐒𝒆𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩 பாட் இயக்கத்தில் உள்ளது.**\n\n"
        f"🟢 **பாட் நிலை:** ONLINE & SECURED\n\n"
        f"📌 **பயன்படுத்தும் முறை:**\n"
        f"• `/filter [வார்த்தை] [பதில்]` - புதிய ஃபில்டர் சேர்க்க.\n"
        f"• `/s [டிராமா பெயர்]` - டிராமா விவரங்கள் தேட.\n"
        f"• `/ping` - பாட் நிலையைச் சோதிக்க."
    )
    await update.message.reply_text(welcome_text)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ping_text = (
        f"🟢 **பாட் ஸ்டேட்டஸ்: ONLINE (Perfect)**\n"
        f"📂 **Auto-Filter Backup:** Active & Safe\n"
        f"👑 **Group:** 𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝒆𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩"
    )
    await update.message.reply_text(ping_text)

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ பயன்பாட்டு முறை தவறு நண்பா!\nஎடுத்துக்காட்டு: `/filter hi வணக்கம் நண்பா`")
        return
    
    keyword = context.args[0].lower()
    reply_msg = " ".join(context.args[1:])
    
    chat_id = str(update.effective_chat.id)
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_filters(CHAT_FILTERS)
    
    await update.message.reply_text(f"✅ ஃபில்டர் வெற்றிகரமாக சேமிக்கப்பட்டது: `{keyword}`")

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
        await update.message.reply_text("⚠️ நண்பா, டிராமாவின் பெயரைக் குறிப்பிடவும். எ.கா: `/s Twinkling Watermelon`")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 '{query}' தேடிக்கொண்டிருக்கிறேன் நண்பா...")

    search_url = "https://www.googleapis.com/customsearch/v1"
    params = {
        'key': GOOGLE_API_KEY,
        'cx': SEARCH_ENGINE_ID,
        'q': f"{query} drama details release year plot Tamil dubbed"
    }

    try:
        response = requests.get(search_url, params=params)
        result = response.json()

        if 'items' in result and len(result['items']) > 0:
            top_result = result['items'][0]
            title = top_result.get('title', '')
            snippet = top_result.get('snippet', '')
            link = top_result.get('link', '')
            
            keyboard = [[InlineKeyboardButton("🔗 முழு விவரங்களைப் பார்க்க", url=link)]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            reply_text = (
                f"🎬 **டிராமா தகவல்**\n\n"
                f"📌 **தலைப்பு:** {title}\n\n"
                f"📖 **கதைக்களம்:**\n{snippet}"
            )
            await update.message.reply_text(reply_text, reply_markup=reply_markup)
        else:
            await update.message.reply_text(f"⚠️ '{query}' டிராமா பற்றிய தகவல்கள் கிடைக்கவில்லை.")
            
    except Exception as e:
        await update.message.reply_text("⚠️ இணைப்பில் சிறு தடை ஏற்பட்டுள்ளது நண்பா.")

def setup_webhook():
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
