import datetime
import os
import re
import sqlite3
import threading
import time
import telebot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup
from flask import Flask

# Bot Configuration
TOKEN = "8988853898:AAGoQ6fkETdCp4jOr-i58l3j-QsVzR7ZIxk"
ADMIN_ID = 8631720591

bot = telebot.TeleBot(TOKEN)

# In-memory activity logs and seen message caches
activity_logs = []
seen_msg_ids = set()

# Database setup for the bot
DB_NAME = "drama_filters.db"


def init_db():
  conn = sqlite3.connect(DB_NAME)
  cursor = conn.cursor()
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS files (
            name TEXT,
            id TEXT,
            chat TEXT,
            msg TEXT
        )
    """
  )
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS filters (
            keyword TEXT,
            response TEXT
        )
    """
  )
  cursor.execute(
      """
        CREATE TABLE IF NOT EXISTS restricted_words (
            word TEXT
        )
    """
  )
  conn.commit()
  conn.close()


init_db()


# Channel Post Handler (Indexing files automatically with Caption Priority & Cleaning)
@bot.channel_post_handler(
    content_types=["document", "video", "audio", "photo"]
)
def index_files(n):
  fid = None
  file_name_from_doc = None

  if n.document:
    fid = n.document.file_id
    file_name_from_doc = n.document.file_name
  elif n.video:
    fid = n.video.file_id
    file_name_from_doc = n.video.file_name
  elif n.audio:
    fid = n.audio.file_id
    file_name_from_doc = n.audio.file_name
  elif n.photo:
    fid = n.photo[-1].file_id
    file_name_from_doc = f"photo_{n.message_id}"

  if not fid:
    return

  raw_name = ""
  if n.caption:
    raw_name = n.caption
  elif file_name_from_doc:
    raw_name = file_name_from_doc
  else:
    raw_name = f"file_{n.message_id}"

  branding_texts = [
      "UOSG - The Unlimited Universe",
      "UOSG",
      "_The Universe of Series Group_",
      "_The Universe of Dramas_",
  ]

  for brand in branding_texts:
    raw_name = raw_name.replace(brand, "")

  raw_name = re.sub(r"@\w+", "", raw_name)
  raw_name = re.sub(r"#\w+", "", raw_name)

  clean_name = raw_name.lower()
  clean_name = re.sub(r"[^a-z0-9\s]", " ", clean_name)
  clean_name = " ".join(clean_name.split())

  if not clean_name:
    clean_name = f"file_{n.message_id}"

  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO files (name, id, chat, msg) VALUES (?, ?, ?, ?)",
        (clean_name, fid, str(n.chat.id), str(n.message_id)),
    )
    conn.commit()
    conn.close()
    print(f"✅ [INDEXED] Successfully Saved -> {clean_name}", flush=True)

    try:
      markup = InlineKeyboardMarkup()
      markup.add(InlineKeyboardButton("🗑️ Clear Update", callback_data="clear_update"))
      
      admin_msg_text = (
          f"📥 **New File Indexed Successfully!**\n\n"
          f"📂 **Saved Name:** `{clean_name}`\n"
          f"📢 **Source Chat ID:** `{n.chat.id}`\n"
          f"🆔 **Message ID:** `{n.message_id}`"
      )
      bot.send_message(ADMIN_ID, admin_msg_text, parse_mode="Markdown", reply_markup=markup)
    except Exception as admin_err:
      print(f"Admin Notification Error: {admin_err}")

  except Exception as e:
    print(f"❌ Index Error: {e}", flush=True)


# Callback query handler for Clear Update button
@bot.callback_query_handler(func=lambda call: call.data == "clear_update")
def clear_update_callback(call):
  try:
    bot.delete_message(call.message.chat.id, call.message.message_id)
  except Exception as e:
    print(f"Delete update error: {e}")


# Group Handler (Search & Filter Response)
@bot.message_handler(func=lambda m: True)
def group_handler(m):
  if not m.text or m.text.startswith("/"):
    return

  query = m.text.lower().strip()
  query_words = query.split()

  if len(query_words) < 2:
    return

  hardcoded_restricted = [
      "download", "downloads", "episode", "episodes", "ep", "season", "seasons",
      "tamil", "telugu", "hindi", "malayalam", "kannada", "english", "dubbed",
      "sub", "subs", "subtitles", "movie", "movies", "series", "show", "shows",
      "link", "links", "file", "files", "watch", "online", "telegram", "tg",
  ]

  if any(r_word in query_words for r_word in hardcoded_restricted):
    return

  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT keyword, response FROM filters")
    all_filters = cursor.fetchall()

    filter_matched = False
    clean_words = [word.strip(".,!?:;()[]{}") for word in query_words]

    for kw, resp in all_filters:
      if kw:
        kw_clean = kw.strip().lower()
        if kw_clean in clean_words:
          bot.reply_to(m, resp)
          filter_matched = True
          break

    if filter_matched:
      conn.close()
      return

    cursor.execute("SELECT word FROM restricted_words")
    restricted_rows = cursor.fetchall()
    restricted_words_list = [row[0] for row in restricted_rows]

    if any(r_word in query_words for r_word in restricted_words_list):
      conn.close()
      return

    cursor.execute("SELECT name, id, chat, msg FROM files")
    rows = cursor.fetchall()
    conn.close()

    found_count = 0
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
                chat_id=m.chat.id,
                from_chat_id=int(chat),
                message_id=int(msg),
            )
            sent_message_ids.append(sent_msg.message_id)
            sent_file_names.append(name)
            seen_msg_ids.add(msg)
            found_count += 1
            time.sleep(2.0)
          except Exception as err:
            print(f"Copy Error: {err}")

    if found_count > 0:
      print(f"[SENT] Total {found_count} files for query: {query}")
      try:
        bot.reply_to(
            m,
            (
                "🌸 **Files Sent Successfully, Sweetie!** 🌸\n\n"
                "💖 **Hey dear, I have successfully found and sent all your requested files!** 💖\n\n"
                "👑 **Full Administrative Powers & CEOs:** 👑\n"
                "👉 @LegendUOSG\n"
                "👉 @Adhiyaman1000\n\n"
                "✨ **Have a wonderful time enjoying your media!** ✨"
            ),
            parse_mode="Markdown",
        )
      except Exception as reply_err:
        print(f"Reply Error: {reply_err}")
    else:
      try:
        bot.reply_to(
            m,
            (
                "🌸 **Oops, No Files Found Here...** 🌸\n\n"
                "💔 **Sorry dear, I couldn't find that file right now. But don't worry!** 💔\n\n"
                "👑 **Full Administrative Powers & CEOs:** 👑\n"
                "👉 @LegendUOSG\n"
                "👉 @Adhiyaman1000\n\n"
                "✨ **If you need help, contact our admin:** @Adhiyaman1000 ✨"
            ),
            parse_mode="Markdown",
        )
      except Exception as e:
        print(f"No match reply error: {e}")

    now_time = datetime.datetime.now()
    user_obj = m.from_user
    activity_logs.append({
        "timestamp": now_time,
        "time_str": now_time.strftime("%H:%M:%S"),
        "user_id": user_obj.id,
        "user_name": user_obj.first_name if user_obj.first_name else "Unknown",
        "username": (
            f"@{user_obj.username}" if user_obj.username else "No Username"
        ),
        "query": query,
        "files_count": found_count,
        "files_list": sent_file_names,
    })

    def handle_auto_delete_and_warning(
        bot_instance, chat_id, sent_message_ids, delay_seconds=300
    ):
      time.sleep(delay_seconds)
      for msg_id in sent_message_ids:
        try:
          bot_instance.delete_message(chat_id, msg_id)
        except Exception:
          pass

    threading.Thread(
        target=handle_auto_delete_and_warning,
        args=(bot, m.chat.id, sent_message_ids, 300),
    ).start()

  except Exception as c:
    print(f"Group Handler Error: {c}")


# Admin Commands: /today and /date
@bot.message_handler(commands=["today", "date"])
def get_activity_stats(message):
  if message.from_user.id != ADMIN_ID:
    bot.reply_to(message, "❌ This command is restricted for admin only!")
    return

  try:
    cmd_parts = message.text.split(" ", 1)
    command_name = cmd_parts[0].lower()
    target_date_str = ""
    now = datetime.datetime.now()

    if "/today" in command_name:
      target_date_str = now.strftime("%d-%m-%Y")
    else:
      if len(cmd_parts) < 2:
        bot.reply_to(
            message,
            "⚠️ Please use format:\n`/date DD, MM, YYYY`",
            parse_mode="Markdown",
        )
        return
      command_text = cmd_parts[1].strip()
      parts = [p.strip() for p in command_text.split(",")]
      if len(parts) != 3:
        bot.reply_to(
            message,
            "❌ Invalid format! Use: `/date DD, MM, YYYY`",
            parse_mode="Markdown",
        )
        return
      day, month, year = parts
      target_date_str = f"{day.zfill(2)}-{month.zfill(2)}-{year}"

    matching_logs = []
    for log in activity_logs:
      log_date_str = log["timestamp"].strftime("%d-%m-%Y")
      if log_date_str == target_date_str:
        if "/today" in command_name:
          start_of_day = now.replace(
              hour=0, minute=0, second=0, microsecond=0
          )
          if log["timestamp"] >= start_of_day:
            matching_logs.append(log)
        else:
          matching_logs.append(log)

    total_searches = len(matching_logs)
    total_files_sent = sum(log["files_count"] for log in matching_logs)
    unique_users = len(set(log["user_id"] for log in matching_logs))

    if total_searches == 0:
      report_text = (
          f"📊 **Activity Report ({target_date_str})**📊 \n\n"
          f"👥 Total Users Searched: `0`\n"
          f"🔍 Total Search Queries: `0`\n"
          f"📁 Total Files Sent: `0`\n\n"
          f"🌸 *No search activities recorded for this date (0 0 0).* 🌸"
      )
      bot.send_message(ADMIN_ID, report_text, parse_mode="Markdown")
    else:
      summary_text = (
          f"📊 **Activity Report ({target_date_str})**📊 \n\n"
          f"👥 Unique Users: `{unique_users}`\n"
          f"🔍 Total Searches: `{total_searches}`\n"
          f"📁 Total Files Sent: `{total_files_sent}`"
      )
      bot.send_message(ADMIN_ID, summary_text, parse_mode="Markdown")

      for idx, log in enumerate(matching_logs, 1):
        block_text = (
            f"📦 **User Activity Block #{idx}**📦\n\n"
            f"👤 **Name:** {log['user_name']}\n"
            f"🌐 **Username:** {log['username']}\n"
            f"🆔 **User ID:** `{log['user_id']}`\n"
            f"🔍 **Query:** `{log['query']}`\n"
            f"📁 **Files Sent:** `{log['files_count']}`\n"
            f"⏰ **Time:** `{log['time_str']}`"
        )
        bot.send_message(ADMIN_ID, block_text, parse_mode="Markdown")
        time.sleep(0.3)

  except Exception as e:
    print(f"Stats Error: {e}")
    bot.reply_to(message, f"❌ Error: {e}")


# Check file in Database command: /check
@bot.message_handler(commands=["check"])
def check_file_in_db(message):
  try:
    parts = message.text.split(" ", 1)
    if len(parts) < 2:
      bot.reply_to(
          message,
          "⚠️ Please provide a name to check!\nExample: `/check my girlfriend is an alien`",
          parse_mode="Markdown",
      )
      return

    search_query = parts[1].lower().strip()

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM files")
    rows = cursor.fetchall()
    conn.close()

    matches = [name for (name,) in rows if search_query in name]

    if matches:
      response = (
          f"✅ **Found {len(matches)} match(es) in Database:**\n"
          f"🌸 *(Already saved, no need to re-upload!)*\n"
      )
      for i, m_name in enumerate(matches[:5], 1):
        response += f"`{i}`. {m_name}\n"
      if len(matches) > 5:
        response += f"...and {len(matches) - 5} more matches."
    else:
      response = (
          f"❌ **Not found in Database!**\n*(This file is missing, you can upload it.)*"
      )

    bot.reply_to(message, response, parse_mode="Markdown")
  except Exception as e:
    print(f"Check Error: {e}")


# User ID command: /id
@bot.message_handler(commands=["id"])
def get_user_id(message):
  try:
    user_id = message.from_user.id
    bot.reply_to(
        message,
        f"🆔 **Your Telegram User ID:** `{user_id}`",
        parse_mode="Markdown",
    )
  except Exception as e:
    print(f"ID Error: {e}")


# Welcome Message for New Chat Members
@bot.message_handler(content_types=["new_chat_members"])
def elite_welcome_message(message):
  try:
    for user in message.new_chat_members:
      welcome_text = (
          "✨🌸 ─── ⋆⋅ ✧ ⋅⋆ ─── 🌸✨\n"
          "   **WELCOME TO THE UNIVERSE OF DRAMAS**\n"
          "✨🌸 ─── ⋆⋅ ✧ ⋅⋆ ─── 🌸✨\n\n"
          f"👋 **Hello {user.first_name}**, A warm welcome to our exclusive community!\n"
          "🎬 *Step into the ultimate world of Asian dramas, where endless entertainment awaits.*\n"
          "🔍 `To find any drama, simply type the name of your favorite show!`\n"
          "📌 **Important Guidelines for Members:**\n"
          "• Keep the chat clean, respectful, and friendly for everyone.\n"
          "• Avoid spamming links, promotions, or irrelevant messages.\n"
          "• Follow the group rules to maintain a wonderful environment.\n"
          "💖 **Let's create an amazing space together. Enjoy your stay and happy watching!**"
      )

      sent_msg = bot.send_message(
          message.chat.id, welcome_text, parse_mode="Markdown"
      )

      def delete_later(chat_id, msg_id):
        try:
          time.sleep(300)
          bot.delete_message(chat_id, msg_id)
        except Exception as err:
          print(f"Auto Delete Error: {err}")

      threading.Thread(
          target=delete_later, args=(message.chat.id, sent_msg.message_id)
      ).start()
  except Exception as e:
    print(f"Welcome Error: {e}")


# Bot Statistics command: /total
@bot.message_handler(commands=["total"])
def database_stats(message):
  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM files")
    total_files = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM filters")
    total_filters = cursor.fetchone()[0]
    conn.close()

    response = (
        f"📊 **Bot Database Statistics:**\n\n"
        f"📁 **Total Files Saved:** `{total_files}`\n"
        f"🔍 **Total Custom Filters:** `{total_filters}`\n\n"
        f"✨*(All systems are running smoothly!)*"
    )
    bot.reply_to(message, response, parse_mode="Markdown")
  except Exception as e:
    print(f"Stats Error: {e}")


# Export Database Files list command: /list
@bot.message_handler(commands=["list"])
def export_database_files(message):
  try:
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM files")
    rows = cursor.fetchall()
    conn.close()

    if not rows:
      bot.reply_to(message, "⚠️ No files found in the database to export!")
      return

    file_path = "database_files_list.txt"
    with open(file_path, "w", encoding="utf-8") as f:
      for i, (name,) in enumerate(rows, 1):
        f.write(f"{i}. {name}\n")

    with open(file_path, "rb") as f:
      bot.send_document(
          message.chat.id,
          f,
          caption=(
              f"📂 **Here is your database backup!**\nTotal Files: {len(rows)}"
          ),
          parse_mode="Markdown",
      )
  except Exception as e:
    print(f"Export Error: {e}")


# Get Photo File ID helper
@bot.message_handler(content_types=["photo"])
def get_file_id(message):
  try:
    photo_file_id = message.photo[-1].file_id
    print(f"Photo File ID: {photo_file_id}")
    bot.reply_to(
        message,
        f"✅ **Photo File ID:**\n`{photo_file_id}`",
        parse_mode="Markdown",
    )
  except Exception as e:
    print(f"Error getting file_id: {e}")


# --- Flask Mini Web Server to satisfy Render Port requirement ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is active and running smoothly!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
  print("=" * 50)
  print(" 🚀 TELEGRAM FILE & FILTER BOT IS ONLINE 🌸 ")
  print("=" * 50)
  
  # Start Flask web server in a separate background thread
  flask_thread = threading.Thread(target=run_flask)
  flask_thread.daemon = True
  flask_thread.start()

  while True:
    try:
      bot.infinity_polling(skip_pending=True, timeout=60, long_polling_timeout=60)
    except Exception as e:
      print(f"[Connection Error]: {e}")
      print("[Reconnecting in 5 seconds...]")
      time.sleep(5)
