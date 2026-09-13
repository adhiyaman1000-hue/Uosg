import os
import json
requests = __import__('requests')
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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
    return "𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝐞𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩 AI Bot is running perfectly!"

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
        f"🌟 **வணக்கம் நண்பா! 𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝒆𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩 AI Bot இயக்கத்தில் உள்ளது.**\n\n"
        f"🟢 **பாட் நிலை:** ONLINE & AI MODE READY\n\n"
        f"📌 **பயன்படுத்தும் முறை:**\n"
        f"• ஒரே வார்த்தை ஃபில்டர்: `/filter hi - வணக்கம்`\n"
        f"• பல வார்த்தை ஃபில்டர்: `/filter \"good morning\" - இனிய காலை வணக்கம்`\n"
        f"• `/s [டிராமா பெயர்]` - உலகளாவிய தேடல் மற்றும் AI மோட் சுருக்கம் பெற.\n"
        f"• `/ping` - பாட் நிலையைச் சோதிக்க."
    )
    await update.message.reply_text(welcome_text)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ping_text = (
        f"🟢 **பாட் ஸ்டேட்டஸ்: ONLINE (AI Mode Active)**\n"
        f"📂 **Auto-Filter Backup:** Active & Safe\n"
        f"👑 **Group:** 𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝒆𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩"
    )
    await update.message.reply_text(ping_text)

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    full_text = " ".join(context.args)
    
    if "-" not in full_text:
        await update.message.reply_text(
            "⚠️ முறை தவறு நண்பா!\n"
            "சரியான வடிவம்:\n"
            "• `/filter வார்த்தை - பதில்`\n"
            "• `/filter \"பல வார்த்தைகள்\" - பதில்`"
        )
        return
    
    parts = full_text.split("-", 1)
    raw_keyword = parts[0].strip()
    reply_msg = parts[1].strip()
    
    if raw_keyword.startswith('"') and raw_keyword.endswith('"'):
        keyword = raw_keyword[1:-1].strip().lower()
    else:
        keyword = raw_keyword.lower()
    
    if not keyword or not reply_msg:
        await update.message.reply_text("⚠️ வார்த்தை அல்லது பதில் காலியாக இருக்கக்கூடாது நண்பா!")
        return

    chat_id = str(update.effective_chat.id)
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_filters(CHAT_FILTERS)
    
    await update.message.reply_text(f"✅ ஃபில்டர் வெற்றிகரமாக சேமிக்கப்பட்டது!\n📌 **கீவர்டு:** `{keyword}`\n💬 **பதில்:** `{reply_msg}`")

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
    await update.message.reply_text(f"🤖 **AI Mode:** உலகளாவிய வலையில் இருந்து '{query}' பற்றிய விவரங்களைத் தேடுகிறது நண்பா...")

    try:
        # உலகளாவிய தேடலுக்கான API (DuckDuckGo Instant Answer / Search API)
        search_api_url = f"https://api.duckduckgo.com/?q={query}+drama+Tamil+dubbed&format=json&no_html=1&skip_disambig=1"
        res = requests.get(search_api_url, timeout=10).json()
        
        abstract = res.get("AbstractText", "")
        abstract_url = res.get("FirstURL", "")
        
        if not abstract:
            # Related topics-ல் இருந்து தகவல் தேடுதல்
            related = res.get("RelatedTopics", [])
            for topic in related:
                if "Text" in topic:
                    abstract = topic["Text"]
                    abstract_url = topic.get("FirstURL", "")
                    break
                    
        if abstract:
            main_google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}+drama+Tamil+dubbed"
            keyboard = [
                [InlineKeyboardButton("🔗 முழு மூலத் தகவல் (Source)", url=abstract_url)],
                [InlineKeyboardButton("🌍 மெயின் கூகுளில் மேலும் தேட", url=main_google_url)]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            ai_response = (
                f"✨ **AI Mode Overview: {query}**\n\n"
                f"📖 {abstract}\n\n"
                f"💡 *இது உலகளாவிய வலையிலிருந்து AI மூலம் தொகுக்கப்பட்ட சுருக்கமாகும் நண்பா!*"
            )
            await update.message.reply_text(ai_response, reply_markup=reply_markup)
        else:
            # ஒருவேளை சுருக்கம் கிடைக்கவில்லை என்றால் நேரடி கூகுள் சர்ச் ரிசல்ட் காட்டுவது
            main_google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}+drama+Tamil+dubbed"
            keyboard = [[InlineKeyboardButton("🌍 மெயின் கூகுளில் நேரடியாகத் தேட", url=main_google_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"⚠️ '{query}' பற்றிய நேரடி AI சுருக்கம் கிடைக்கவில்லை நண்பா. கீழே உள்ள மெயின் கூகுள் சர்ச் பட்டனைப் பயன்படுத்தவும்:",
                reply_markup=reply_markup
            )
    except Exception as e:
        main_google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}+drama+Tamil+dubbed"
        keyboard = [[InlineKeyboardButton("🌍 மெயின் கூகுளில் தேட", url=main_google_url)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("⚠️ தேடுவதில் சிறு தொழில்நுட்பத் தடை ஏற்பட்டுள்ளது நண்பா. கூகுள் லிங்க் இதோ:", reply_markup=reply_markup)

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
