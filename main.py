import os
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_API_KEY = "AIzaSyBXWXOvvUxLiEY7_gEXn0z6SrDvrzTGEm8"
SEARCH_ENGINE_ID = "5788d738584a240fa"

app = Flask(__name__)

@app.route('/')
def home():
    return "𝑻𝒉𝒆 𝑼𝒏𝒊𝒗𝒆𝒓𝒔𝒆 𝒐𝒇 𝑺𝒆𝒓𝒊𝒆𝒔 𝑮𝒓𝒐𝒖𝒑 Bot is active and running!"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔍 டிராமா தேட (/s)", callback_data="help_search")],
        [InlineKeyboardButton("💎 𝓚𝓒 𝔁 𝒟𝓇𝒶𝓂𝒶 𝒲ℴ𝓇𝓁𝒹", url="https://t.me/KC_X_DRAMA_WORLD")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "வணக்கம் நண்பா! 𝑻𝒉𝒆 𝑼𝒏𝒊𝒗𝒆𝒓𝒔𝒆 𝒐𝒇 𝑺𝒆𝒓𝒊𝒆𝒔 𝑮𝒓𝒐𝒖𝒑 பாட் தயார் நிலையிலுள்ளது.\n"
        "`/s [டிராமா பெயர்]` என அனுப்பி அதன் கதைக்களம், ஆண்டு மற்றும் மொழி விவரங்களைப் பெற்றுக்கொள்ளலாம்.",
        reply_markup=reply_markup
    )

async def search_drama_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ நண்பா, கமெண்டுடன் டிராமாவின் பெயரையும் சேர்த்து அனுப்பவும்.\nஎடுத்துக்காட்டு: `/s Twinkling Watermelon`")
        return

    query = " ".join(context.args)
    await update.message.reply_text(f"🔍 '{query}' டிராமாவின் முழு விவரங்களையும் (Plot, Year, Languages) கூகுள் மூலம் தேடிக்கொண்டிருக்கிறேன் நண்பா...")

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
            
            # Interactive Buttons
            keyboard = [
                [InlineKeyboardButton("🔗 முழு விவரங்களைப் பார்க்க", url=link)],
                [InlineKeyboardButton("👑 CEO Bot Approval", callback_data=f"approve_{query[:15]}")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            reply_text = (
                f"🎬 **டிராமா தகவல் அறிக்கை**\n\n"
                f"📌 **தலைப்பு & ஆண்டு:** {title}\n\n"
                f"📖 **கதைக்களம் & விவரங்கள் (Plot):**\n{snippet}\n\n"
                f"🌐 **மொழி நிலை:** தமிழ் / பிற மொழிகளில் இணையத்தில் தேடப்பட்டுள்ளது."
            )
            await update.message.reply_text(reply_text, reply_markup=reply_markup)
        else:
            reply_text = (
                f"❌ **ஸ்டேட்டஸ்: NOT AVAILABLE**\n\n"
                f"மன்னிக்கவும் நண்பா, '{query}' டிராமா பற்றிய தகவல்கள் வெப்பில் கிடைக்கவில்லை."
            )
            await update.message.reply_text(reply_text)
            
    except Exception as e:
        await update.message.reply_text("⚠️ தேடுவதில் சிறு தொழில்நுட்பத் தடை ஏற்பட்டுள்ளது நண்பா. சற்று கழித்து முயற்சிக்கவும்.")

def main():
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram Token missing!")
        return

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("s", search_drama_command))
    application.add_handler(CommandHandler("search", search_drama_command))

    application.run_polling()

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)
