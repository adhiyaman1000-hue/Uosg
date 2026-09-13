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
        f"🌟 **வணக்கம் நண்பா! 𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝒆𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩 பாட் இயக்கத்தில் உள்ளது.**\n\n"
        f"🛡️ **பாதுகாப்பு:** Admin-Only Filter Lock Active\n\n"
        f"📌 **பயன்படுத்தும் முறை:**\n"
        f"• `/filter வார்த்தை - பதில்` (அட்மின்கள் மட்டும்)\n"
        f"• `/s [டிராமா பெயர்]` - ஆண்டு, மொழி மற்றும் கூகுள் லிங்க் பெற\n"
        f"• `/ping` - பாட் நிலையைச் சோதிக்க."
    )
    await update.message.reply_text(welcome_text)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ping_text = (
        f"🟢 **பாட் ஸ்டேட்டஸ்: ONLINE (Connected & Safe)**\n"
        f"📂 **Auto-Filter Backup:** Active & Safe\n"
        f"👑 **Group:** 𝑻𝒉𝒆 𝐔𝐧𝐢𝐯𝒆𝐫𝐬𝐞 𝐨𝐟 𝐒𝐞𝐫𝐢𝐞𝐬 𝐆𝐫𝐨𝐮𝐩"
    )
    await update.message.reply_text(ping_text)

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat = update.effective_chat
    
    if chat.type != "private":
        try:
            member = await chat.get_member(user_id)
            if member.status not in ["creator", "administrator"]:
                await update.message.reply_text("⚠️ மன்னிக்கவும் நண்பா! இந்த `/filter` கமாண்டை குரூப் அட்மின்கள் மட்டுமே பயன்படுத்த முடியும் (Admin Lock Active).")
                return
        except Exception as e:
            print(f"Admin Check Error: {e}")
            return

    full_text = " ".join(context.args)
    if "-" not in full_text:
        await update.message.reply_text("⚠️ முறை தவறு நண்பா! எ.கா: `/filter hi - வணக்கம்` அல்லது `/filter \"good morning\" - பதில்`")
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

    chat_id = str(chat.id)
    if chat_id not in CHAT_FILTERS:
        CHAT_FILTERS[chat_id] = {}
        
    CHAT_FILTERS[chat_id][keyword] = reply_msg
    save_filters(CHAT_FILTERS)
    
    await update.message.reply_text(f"🔒 **[Admin Lock]** ஃபில்டர் வெற்றிகரமாகச் சேமிக்கப்பட்டது!\n📌 **கீவர்டு:** `{keyword}` ➔ `{reply_msg}`")

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
    
    # முன்பைப்போலவே மிகத் துல்லியமான நேரடி கூகுள் தேடல் லிங்க் உருவாக்கம்
    main_google_url = f"https://www.google.com/search?q={query.replace(' ', '+')}+drama+release+year+languages+Tamil+dubbed"
    keyboard = [[InlineKeyboardButton("🌍 மெயின் கூகுளில் முழு விவரம் காண", url=main_google_url)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    response_text = (
        f"🎬 **டிராமா பெயர்:** {query.title()}\n\n"
        f"📅 **வெளியான ஆண்டு & மொழிகள்:**\n"
        f"• இந்தத் டிராமாவின் அதிகாரப்பூர்வ **வெளியீட்டு ஆண்டு**, **இயக்குநர்/நடிப்பாட்டாளர்கள்** மற்றும் **தமிழ் (Tamil) / ஒரிஜினல் மொழிகள்** பற்றிய முழுமையான தகவல்களைத் தெரிந்து கொள்ள கீழே உள்ள கூகுள் லிங்க்கை அழுத்தவும் நண்பா!\n\n"
        f"🔗 *நேரடி மற்றும் வேகமான இணைப்பு உருவாக்கப்பட்டுள்ளது.*"
    )
    await update.message.reply_text(response_text, reply_markup=reply_markup)

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
