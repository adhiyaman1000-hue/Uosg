import os
import re
import sqlite3
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
CEO_CHAT_ID = 8631720591  # உன்னுடைய பிரைவேட் சாட் ஐடி
bot = telebot.TeleBot(TOKEN)

# Database Initialization
def init_db():
    conn = sqlite3.connect("filters.db")
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS files (
                        clean_name TEXT, 
                        file_name TEXT, 
                        file_id TEXT, 
                        chat_id TEXT, 
                        message_id TEXT,
                        file_type TEXT
                    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS custom_filters (
                        keyword TEXT UNIQUE, 
                        response_text TEXT
                    )''')
    conn.commit()
    conn.close()

init_db()

def clean_file_search_name(filename):
    if not filename:
        return ""
    name_wo_ext = os.path.splitext(filename)[0]
    cleaned = name_wo_ext.replace('_', ' ').replace('.', ' ')
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned.lower()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message,
        "✨ **@LegendUOSG Bot is Active!** ✨",
        parse_mode="Markdown"
    )

# 1. Custom Filter Command: /filter keyword | response text
@bot.message_handler(commands=['filter'])
def save_custom_filter(message):
    try:
        parts = message.text.replace("/filter", "").split("|", 1)
        if len(parts) < 2:
            bot.reply_to(message, "⚠️ Format: `/filter keyword | response text`", parse_mode="Markdown")
            return
        
        keyword = parts[0].strip().lower()
        response_text = parts[1].strip()
        
        conn = sqlite3.connect("filters.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO custom_filters (keyword, response_text) VALUES (?, ?)", (keyword, response_text))
        conn.commit()
        conn.close()
        
        bot.reply_to(message, f"✨ Filter saved for: `{keyword}` 📂", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error: {e}")

# 2. Channel Auto-Save Files
@bot.message_handler(content_types=['document', 'video', 'audio', 'photo'])
def auto_save_channel_files(m):
    if m.chat.type not in ['channel', 'supergroup']:
        return
        
    try:
        file_name = ""
        file_id = ""
        file_type = "document"
        
        if m.document:
            file_name = m.document.file_name
            file_id = m.document.file_id
            file_type = "document"
        elif m.video:
            file_name = m.video.file_name if m.video.file_name else f"Video_{m.message_id}"
            file_id = m.video.file_id
            file_type = "video"
        elif m.audio:
            file_name = m.audio.file_name if m.audio.file_name else f"Audio_{m.message_id}"
            file_id = m.audio.file_id
            file_type = "audio"
        elif m.photo:
            file_name = f"Photo_{m.message_id}"
            file_id = m.photo[-1].file_id
            file_type = "photo"
            
        if not file_name or not file_id:
            return
            
        clean_name = clean_file_search_name(file_name)
        
        conn = sqlite3.connect("filters.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (clean_name, file_name, file_id, chat_id, message_id, file_type) VALUES (?, ?, ?, ?, ?, ?)",
            (clean_name, file_name, file_id, str(m.chat.id), str(m.message_id), file_type)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Save Error: {e}")

# 3. Group Search Handler (NO BUTTONS IN GROUP - Clean Text and Media Only)
@bot.message_handler(func=lambda message: True, content_types=['text'])
def group_search_handler(message):
    text = message.text.strip()
    if not text or text.startswith('/'):
        return
        
    query = text.lower()
    query_cleaned = re.sub(r'[\s_.-]+', ' ', query).strip()
    
    try:
        conn = sqlite3.connect("filters.db")
        cursor = conn.cursor()
        
        # Check Custom Filters first
        cursor.execute("SELECT response_text FROM custom_filters WHERE keyword LIKE ?", (f"%{query}%",))
        custom_res = cursor.fetchone()
        if custom_res:
            conn.close()
            # No buttons sent to group, only text reply
            bot.reply_to(message, custom_res[0], parse_mode="Markdown")
            return

        # Search Media Files
        cursor.execute("SELECT file_name, file_id, file_type FROM files WHERE clean_name LIKE ? LIMIT 5", (f"%{query_cleaned}%",))
        results = cursor.fetchall()
        conn.close()
        
        if results:
            for f_name, f_id, f_type in results:
                response_text = (
                    f"✨ **File Found!** 📂\n\n"
                    f"🎬 **Name:** `{f_name}`\n\n"
                    f"👑 **Contact Admin:**\n"
                    f"👉 @LegendUOSG"
                )
                # Sends response and media without any buttons in the group
                sent_msg = bot.reply_to(message, response_text, parse_mode="Markdown")
                try:
                    if f_type == "video":
                        bot.send_video(chat_id=message.chat.id, video=f_id, reply_to_message_id=sent_msg.message_id)
                    elif f_type == "document":
                        bot.send_document(chat_id=message.chat.id, document=f_id, reply_to_message_id=sent_msg.message_id)
                    elif f_type == "audio":
                        bot.send_audio(chat_id=message.chat.id, audio=f_id, reply_to_message_id=sent_msg.message_id)
                    elif f_type == "photo":
                        bot.send_photo(chat_id=message.chat.id, photo=f_id, reply_to_message_id=sent_msg.message_id)
                except Exception as media_err:
                    print(f"Media Send Error: {media_err}")
        else:
            bot.reply_to(
                message,
                f"🥺🌸 Sorry dear, no files found for `{text}`!\n\n"
                f"👑 **Contact Admin:**\n👉 @LegendUOSG",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Search Error: {e}")

# 4. Auto Join Requests Handler (Buttons sent ONLY to Private Chat - CEO)
@bot.chat_join_request_handler()
def handle_join_request(request):
    user = request.from_user
    chat = request.chat
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("✅ Approve", callback_data=f"approve_{chat.id}_{user.id}"),
        InlineKeyboardButton("❌ Decline", callback_data=f"decline_{chat.id}_{user.id}")
    )
    
    text = (
        f"🔔 **New Join Request!**\n\n"
        f"👤 **User:** {user.first_name} (`{user.id}`)\n"
        f"🏷️ **Username:** @{user.username if user.username else 'None'}\n"
        f"👥 **Group/Channel:** {chat.title}"
    )
    
    try:
        bot.send_message(CEO_CHAT_ID, text, parse_mode="Markdown", reply_markup=markup)
    except Exception as e:
        print(f"Join Request Error: {e}")

# 5. Callback Handler for Private Chat Buttons
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    try:
        data = call.data
        if data.startswith("approve_") or data.startswith("decline_"):
            parts = data.split("_")
            action = parts[0]
            chat_id = int(parts[1])
            user_id = int(parts[2])
            
            if action == "approve":
                bot.approve_chat_join_request(chat_id, user_id)
                bot.answer_callback_query(call.id, "✅ Approved!")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"✅ **Status:** Join Request Approved! 🎉",
                    parse_mode="Markdown"
                )
            elif action == "decline":
                bot.decline_chat_join_request(chat_id, user_id)
                bot.answer_callback_query(call.id, "❌ Declined!")
                bot.edit_message_text(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=f"❌ **Status:** Join Request Declined! 🚫",
                    parse_mode="Markdown"
                )
    except Exception as e:
        print(f"Callback Error: {e}")

print("✨ @LegendUOSG Bot is running smoothly with private buttons!")
bot.infinity_polling()
