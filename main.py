import os
import requests
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler

# Configuration - அனைத்து டோக்கன்களும் நேரடியாக இணைக்கப்பட்டுள்ளன
TELEGRAM_BOT_TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
GOOGLE_API_KEY = "AIzaSyBXWXOvvUxLiEY7_gEXn0z6SrDvrzTGEm8"
SEARCH_ENGINE_ID = "5788d738584a240fa"

# Render-ன் உன்னுடைய தற்போதைய URL
RENDER_URL = "https://uosg-kg1t.onrender.com"

app = Flask(__name__)

# Telegram Application Setup
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

@app.route('/')
def home():
    return "𝑻𝒉𝒆 𝑼𝒏𝒊𝒗𝒆𝒓𝒔𝒆 𝒐𝒇 𝑺𝒆𝒓𝒊𝒆𝒔 𝑮𝒓𝒐𝒖𝒑 Bot is active and running via Webhook!"

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
    search_status = "❌ துண்டிக்கப்பட்டுள்ளது"
    try:
        test_res = requests.get("https://www.googleapis.com/customsearch/v1", params={
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'q': 'test'
        }, timeout=5)
        if test_res.status_code == 200:
            search_status = "✅ Connected in Google Search"
        else:
            search_status = f"⚠️ Error Code: {test_res.status_code}"
    except Exception:
        search_status = "❌ இணைப்பு கிடைக்கவில்லை"

    keyboard = [
        [InlineKeyboardButton("🔍 டிராமா தேட (/s)", callback_data="help_search")],
        [InlineKeyboardButton("📶 பாட் ஸ்டேட்டஸ் பரிசோதிக்க (/ping)", callback_data="check_status")],
        [InlineKeyboardButton("💎 𝓚𝓒 𝔁 𝒟𝓇𝒶𝓂𝒶 𝒲ℴ𝓇𝓁𝒹", url="https://t.me/KC_X_DRAMA_WORLD")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        f"🌟 **வணக்கம் நண்பா! 𝑻𝒉𝒆 𝑼𝒏𝒊𝒗𝒆𝒓𝒔𝒆 𝒐𝒇 𝑺𝒆𝒓𝒊𝒆𝒔 𝑮𝒓𝒐𝒖𝒑 பாட் இயக்கத்தில் உள்ளது.**\n\n"
        f"🟢 **பாட் நிலை:** ONLINE (Webhook மூலம்)\n"
        f"🌐 **Google Search API:** {search_status}\n\n"
        f"📌 **இந்த பாட் என்னென்ன செய்யும்?**\n"
        f"• `/s [டிராமா பெயர்]` என அனுப்பினால் கூகுள் சர்ச் மூலம் டிராமாவின் கதைக்களம் (Plot), வெளியான ஆண்டு மற்றும் மொழி விவரங்களை ஆட்டோமேட்டிக்காகத் தரும்.\n"
        f"• `/ping` என அனுப்பினால் பாட் மற்றும் கூகுள் சர்ச் கனெக்ஷனைச் சோதித்துச் சொல்லும்."
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def ping_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    search_status = "❌ துண்டிக்கப்பட்டுள்ளது"
    try:
        test_res = requests.get("https://www.googleapis.com/customsearch/v1", params={
            'key': GOOGLE_API_KEY,
            'cx': SEARCH_ENGINE_ID,
            'q': 'test'
        }, timeout=5)
        if test_res.status_code == 200:
            search_status = "✅ Connected in Google Search"
        else:
            search_status = f"⚠️ Error Code: {test_res.status_code}"
    except Exception:
        search_status = "❌ இணைப்பு கிடைக்கவில்லை"

    ping_text = (
        f"🟢 **பாட் ஸ்டேட்டஸ்: ONLINE**\n\n"
        f"🌐 **Google Search API Status:** {search_status}\n"
        f"👑 **Group:** 𝑻𝒉𝒆 𝑼𝒏𝒊𝒗𝒆𝒓𝒔𝒆 𝒐𝒇 𝑺𝒆𝒓𝒊𝒆𝒔 𝑮𝒓𝒐𝒖𝒑"
    )
    await update.message.reply_text(ping_text)

async def search_drama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ நண்பா, டிராமாவின் பெயரையும் சேர்த்து அனுப்பவும்.\nஎடுத்துக்காட்டு: `/s Twinkling Watermelon`")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 '{query}' டிராமாவின் முழு விவரங்களையும் கூகுள் சர்ச் மூலம் தேடிக்கொண்டிருக்கிறேன் நண்பா...")

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
            
            keyboard = [
                [InlineKeyboardButton("🔗 முழு விவரங்களைப் பார்க்க", url=link)],
                [InlineKeyboardButton("👑 CEO Bot Approval", callback_data=f"approve_{query[:15]}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            reply_text = (
                f"✅ **Connected in Google Search: SUCCESS**\n\n"
                f"🎬 **டிராமா தகவல் அறிக்கை**\n\n"
                f"📌 **தலைப்பு & ஆண்டு:** {title}\n\n"
                f"📖 **கதைக்களம் & விவரங்கள் (Plot):**\n{snippet}\n\n"
                f"🌐 **மொழி நிலை:** தமிழ் டப்பிங் / பிற விவரங்கள் இணையத்தில் தேடப்பட்டுள்ளது."
            )
            await update.message.reply_text(reply_text, reply_markup=reply_markup)
        else:
            reply_text = (
                f"⚠️ **Google Search Connected, ஆனால் தகவல் இல்லை**\n\n"
                f"மன்னிக்கவும் நண்பா, '{query}' டிராமா பற்றிய தகவல்கள் வெப்பில் கிடைக்கவில்லை."
            )
            await update.message.reply_text(reply_text)
            
    except Exception as e:
        await update.message.reply_text("⚠️ கூகுள் சர்ச்சுடன் இணைப்பதில் சிறு தடை ஏற்பட்டுள்ளது நண்பா. சற்று கழித்து முயற்சிக்கவும்.")

def setup_webhook():
    webhook_url = f"{RENDER_URL}/{TELEGRAM_BOT_TOKEN}"
    requests.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(CommandHandler("ping", ping_command))
telegram_app.add_handler(CommandHandler("status", ping_command))
telegram_app.add_handler(CommandHandler("s", search_drama_command))
telegram_app.add_handler(CommandHandler("search", search_drama_command))

if __name__ == '__main__':
    setup_webhook()
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
