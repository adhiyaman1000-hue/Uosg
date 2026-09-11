 import os
import re
import sqlite3
import time
import threading
from datetime import datetime
from collections import Counter
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
CEO_CHAT_ID = 8631720591  
ADMIN_ID = 8631720591
bot = telebot.TeleBot(TOKEN)

# Separate Databases for Filters and Media files
FILTER_DB = "filters.db"
MEDIA_DB = "media_database.db"

def init_db():
    try:
        conn = sqlite3.connect(FILTER_DB)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS filters (keyword TEXT, response TEXT)")
        cursor.execute("CREATE TABLE IF NOT EXISTS restricted_words (word TEXT UNIQUE)")
        conn.commit()
        conn.close()

        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS files (name TEXT, id TEXT, chat TEXT, msg INT)")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")

init_db()

activity_logs = []

def handle_auto_delete_and_warning(bot, chat_id, sent_message_ids, delay_seconds=10000):
    time.sleep(delay_seconds)
    for msg_id in sent_message_ids:
        try:
            bot.delete_message(chat_id, msg_id)
        except:
            pass

# Today Stats Command
@bot.message_handler(commands=['today'])
def today_stats(message):
    if message.from_user.id != ADMIN_ID:
        return
    
    today_str = datetime.now().strftime('%Y-%m-%d')
    today_entries = [log for log in activity_logs if log['timestamp'].strftime('%Y-%m-%d') == today_str]
    
    total_queries = len(today_entries)
    unique_users = len(set(log['user_id'] for log in today_entries))
    all_queries_text = [log['query'] for log in today_entries]
    common_queries = Counter(all_queries_text).most_common(5)
    
    report = (
        f"📊 **Today's Activity Report ({today_str})** 🌸\n\n"
        f"🔹 Total Searches: `{total_queries}`\n"
        f"🔹 Unique Users: `{unique_users}`\n\n"
        f"🔥 **Top Searches Today:**\n"
    )
    
    if common_queries:
        for q, count in common_queries:
            report += f"• `{q}` : {count} times\n"
    else:
        report += "• No search activity recorded yet today.\n"
        
    bot.reply_to(message, report, parse_mode="Markdown")

# Group Handler for Custom Filters, Restricted Words and Media Search
@bot.message_handler(func=lambda m: True, content_types=['text'])
def group_handler(message):
    if not message.text or message.text.startswith('/'):
        return
        
    query = message.text.lower().strip()
    query_words = query.split()
    
    if len(query_words) < 2:
        return

    hardcoded_restricted = [
        'download', 'downloads', 'episode', 'episodes', 'ep', 'season', 'seasons',
        'tamil', 'telugu', 'hindi', 'malayalam', 'kannada', 'english', 'dubbed',
        'sub', 'subs', 'subtitles', 'movie', 'movies', 'series', 'show', 'shows',
        'link', 'links', 'file', 'files', 'watch', 'online', 'telegram', 'tg'
    ]
    if any(r_word in query_words for r_word in hardcoded_restricted):
        return

    try:
        # Check Custom Filters Database
        conn = sqlite3.connect(FILTER_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT keyword, response FROM filters")
        all_filters = cursor.fetchall()
        conn.close()

        filter_matched = False
        clean_words = [word.strip('.,!?()[]{}\'\"') for word in query_words]
        
        for kw, resp in all_filters:
            if kw:
                kw_clean = kw.strip().lower()
                if kw_clean in clean_words:
                    bot.reply_to(message, resp)
                    filter_matched = True
                    break
        if filter_matched:
            return

        # Check Restricted Words Database
        conn = sqlite3.connect(FILTER_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT word FROM restricted_words")
        restricted_rows = cursor.fetchall()
        restricted_words_list = [row[0] for row in restricted_rows]
        conn.close()

        if any(r_word in query_words for r_word in restricted_words_list):
            return

        # Search Media Database
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        cursor.execute("SELECT name, id, chat, msg FROM files")
        rows = cursor.fetchall()
        conn.close()

        found_count = 0
        seen_msg_ids = set()
        sent_message_ids = []
        sent_file_names = []

        for name, fid, chat, msg in rows:
            if name and chat and msg:
                db_name = name.lower()
                if query in db_name:
                    if msg in seen_msg_ids:
                        continue
                    try:
                        sent_msg = bot.copy_message(
                            chat_id=message.chat.id,
                            from_chat_id=int(chat),
                            message_id=int(msg)
                        )
                        sent_message_ids.append(sent_msg.message_id)
                        sent_file_names.append(name)
                        seen_msg_ids.add(msg)
                        found_count += 1
                        time.sleep(2.0)
                    except Exception as err:
                        print(f"Copy Error: {err}")

        if found_count > 0:
            try:
                bot.reply_to(
                    message,
                    f"🌸 **Files Found Successfully!** 📂\n\n"
                    f"Hi there, I have successfully found and sent all your requested files right above! ✨\n"
                    f"👑 **Administrative Power & CEOs:**\n"
                    f"👉 @LegendUOSG\n"
                    f"👉 @Adhiyaman1000\n\n"
                    f"Have a wonderful time enjoying your media! 🌸",
                    parse_mode="Markdown"
                )
            except Exception as reply_err:
                print(f"Reply Error: {reply_err}")
        else:
            try:
                bot.reply_to(
                    message,
                    f"🥺 **Oops, No Files Found Here...** 🌸\n\n"
                    f"Sorry, I couldn't find that file right now. But don't worry! If you contact our CEOs personally, your requested files will be added soon.\n"
                    f"👑 **For personal requests and support, contact our only two supreme admins:**\n"
                    f"👉 @LegendUOSG\n"
                    f"👉 @Adhiyaman1000\n\n"
                    f"Stay connected with us! 🌸",
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"No match reply error: {e}")

        now_time = datetime.now()
        user_obj = message.from_user
        activity_logs.append({
            'timestamp': now_time,
            'time_str': now_time.strftime('%H:%M:%S'),
            'user_id': user_obj.id,
            'username': user_obj.first_name if user_obj.first_name else "Unknown",
            'user_tag': f"@{user_obj.username}" if user_obj.username else "No Username",
            'query': query,
            'files_count': found_count,
            'files_list': sent_file_names
        })

        threading.Thread(target=handle_auto_delete_and_warning, args=(bot, message.chat.id, sent_message_ids, 10000)).start()

    except Exception as c:
        print(f"Group Handler Error: {c}")

# Channel Post Handler for Auto-Indexing Media
@bot.channel_post_handler(content_types=["document", "video", "audio", "photo"])
def index_files(message):
    fid = None
    file_name_from_doc = None

    if message.document:
        fid = message.document.file_id
        file_name_from_doc = message.document.file_name
    elif message.video:
        fid = message.video.file_id
        file_name_from_doc = message.video.file_name
    elif message.audio:
        fid = message.audio.file_id
        file_name_from_doc = message.audio.file_name
    elif message.photo:
        fid = message.photo[-1].file_id
        file_name_from_doc = f"Photo_{message.message_id}"

    if not fid:
        return

    raw_name = ""
    if message.caption:
        raw_name = message.caption

    branding_texts = [
        "UOSG - The Unlimited Universe",
        "UOSG",
        "The Universe of Series Group",
        "The Universe of Dramas"
    ]

    for brand in branding_texts:
        raw_name = raw_name.replace(brand, "")

    raw_name = re.sub(r'[@#]', '', raw_name)
    raw_name = raw_name.strip()

    if not raw_name:
        if file_name_from_doc:
            raw_name = file_name_from_doc
        else:
            raw_name = f"File_{message.message_id}"

    clean_name = raw_name.lower()
    clean_name = re.sub(r'[\s_.-]+', ' ', clean_name)
    clean_name = " ".join(clean_name.split())

    if not clean_name:
        clean_name = f"file_{message.message_id}"

    try:
        conn = sqlite3.connect(MEDIA_DB)
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS files (name TEXT, id TEXT, chat TEXT, msg INT)")
        cursor.execute(
            "INSERT INTO files (name, id, chat, msg) VALUES (?, ?, ?, ?)",
            (clean_name, fid, str(message.chat.id), int(message.message_id))
        )
        conn.commit()
        conn.close()
        print(f"[INDEXED] Successfully Saved -> {clean_name}", flush=True)
    except Exception as e:
        print(f"[INDEX ERROR] {e}", flush=True)

# Start Command
@bot.message_handler(commands=['start'])
def send_start(message):
    welcome_text = (
        f"✨ **Welcome {message.from_user.first_name}** 🌸\n\n"
        f"I am your advanced File & Filter Bot! 🎬\n"
        f"We are here to manage your group files, save custom filters, and keep everything organized effortlessly. ✨"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

# Ping Command
@bot.message_handler(commands=['ping'])
def ping_check(message):
    try:
        response_text = (
            "🌸 Hey there! Bot is active, online, and blooming with energy! 🚀✨\n"
            "Status: Online & ready to vibe with the music!"
        )
        bot.reply_to(message, response_text)
    except Exception as e:
        print(f"Ping Error: {e}")

print("✨ Telegram File & Filter Bot is ONLINE ✨")
bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
                       
    
