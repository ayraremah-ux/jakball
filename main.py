import os
import logging
import sqlite3
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# --- Database Setup ---
def init_database():
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            key_name TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, key_name)
        )
    ''')
    conn.commit()
    conn.close()
    logger.info("Database initialized")

def save_info(user_id, key, value):
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('SELECT id FROM user_info WHERE user_id = ? AND key_name = ?', (user_id, key))
        exists = c.fetchone()
        if exists:
            c.execute('UPDATE user_info SET value = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND key_name = ?', (value, user_id, key))
        else:
            c.execute('INSERT INTO user_info (user_id, key_name, value) VALUES (?, ?, ?)', (user_id, key, value))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving: {e}")
        return False

def get_info(user_id, key):
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('SELECT value FROM user_info WHERE user_id = ? AND key_name = ?', (user_id, key))
        result = c.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        logger.error(f"Error getting: {e}")
        return None

def get_all_keys(user_id):
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('SELECT key_name, value, updated_at FROM user_info WHERE user_id = ? ORDER BY key_name', (user_id,))
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error listing: {e}")
        return []

def delete_info(user_id, key):
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM user_info WHERE user_id = ? AND key_name = ?', (user_id, key))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error(f"Error deleting: {e}")
        return False

def delete_all_info(user_id):
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM user_info WHERE user_id = ?', (user_id,))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error(f"Error deleting all: {e}")
        return False

# --- Command Handlers ---
async def start(update, context):
    user_name = update.effective_user.first_name
    await update.message.reply_text(
        f"👋 Hello {user_name}! I'm your Information Keeper Bot!\n\n"
        "Commands:\n"
        "/save <key> <value> - Save info\n"
        "/get <key> - Get info\n"
        "/list - List all keys\n"
        "/delete <key> - Delete key\n"
        "/clear - Delete ALL\n"
        "/search <text> - Search\n"
        "/stats - Your stats\n"
        "/help - Help"
    )

async def help_command(update, context):
    await update.message.reply_text(
        "❓ Commands:\n"
        "/save <key> <value> - Save information\n"
        "/get <key> - Retrieve information\n"
        "/list - List all saved keys\n"
        "/delete <key> - Delete specific info\n"
        "/clear - Delete ALL information\n"
        "/search <text> - Search through saved info\n"
        "/stats - View storage statistics"
    )

async def save_command(update, context):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Format: /save <key> <value>")
        return
    key = args[0]
    value = ' '.join(args[1:])
    if save_info(user_id, key, value):
        await update.message.reply_text(f"✅ Saved!\nKey: {key}\nValue: {value}")
    else:
        await update.message.reply_text("❌ Failed to save")

async def get_command(update, context):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Format: /get <key>")
        return
    key = args[0]
    value = get_info(user_id, key)
    if value:
        await update.message.reply_text(f"📌 Key: {key}\nValue: {value}")
    else:
        await update.message.reply_text(f"❌ No info for: '{key}'")

async def list_command(update, context):
    user_id = update.effective_user.id
    results = get_all_keys(user_id)
    if not results:
        await update.message.reply_text("📭 No saved info.")
        return
    response = "📚 Your info:\n\n"
    for i, (key, value, _) in enumerate(results, 1):
        display = value[:50] + '...' if len(value) > 50 else value
        response += f"{i}. {key}: {display}\n"
    await update.message.reply_text(response)

async def delete_command(update, context):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Format: /delete <key>")
        return
    key = args[0]
    value = get_info(user_id, key)
    if not value:
        await update.message.reply_text(f"❌ No info for: '{key}'")
        return
    if delete_info(user_id, key):
        await update.message.reply_text(f"🗑️ Deleted: {key}")
    else:
        await update.message.reply_text("❌ Failed to delete")

async def clear_command(update, context):
    user_id = update.effective_user.id
    results = get_all_keys(user_id)
    if not results:
        await update.message.reply_text("📭 Nothing to clear.")
        return
    keyboard = [[
        InlineKeyboardButton("✅ Yes", callback_data="clear_confirm"),
        InlineKeyboardButton("❌ No", callback_data="clear_cancel")
    ]]
    await update.message.reply_text(
        f"⚠️ Delete {len(results)} items?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def search_command(update, context):
    user_id = update.effective_user.id
    args = context.args
    if len(args) < 1:
        await update.message.reply_text("❌ Format: /search <text>")
        return
    search_text = ' '.join(args).lower()
    results = get_all_keys(user_id)
    matches = []
    for key, value, _ in results:
        if search_text in key.lower() or search_text in value.lower():
            matches.append((key, value))
    if not matches:
        await update.message.reply_text(f"🔍 No matches for: '{search_text}'")
        return
    response = f"🔍 Matches:\n\n"
    for i, (key, value) in enumerate(matches, 1):
        response += f"{i}. {key}: {value[:50]}\n"
    await update.message.reply_text(response)

async def stats_command(update, context):
    user_id = update.effective_user.id
    results = get_all_keys(user_id)
    if not results:
        await update.message.reply_text("📭 No info saved.")
        return
    total = len(results)
    chars = sum(len(v) for _, v, _ in results)
    await update.message.reply_text(
        f"📊 Stats:\nTotal items: {total}\nTotal chars: {chars}\nAvg length: {chars//total if total > 0 else 0}"
    )

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if query.data == "clear_confirm":
        if delete_all_info(user_id):
            await query.edit_message_text("✅ Cleared all!")
        else:
            await query.edit_message_text("❌ Failed to clear")
    elif query.data == "clear_cancel":
        await query.edit_message_text("✅ Cancelled")

async def handle_message(update, context):
    msg = update.message.text.lower()
    if any(g in msg for g in ['hello', 'hi', 'hey']):
        await update.message.reply_text("👋 Hello! Use /help")
    else:
        await update.message.reply_text("Use /help to see commands")

async def error_handler(update, context):
    logger.error(f"Error: {context.error}")

def main():
    init_database()
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("get", get_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_error_handler(error_handler)
    
    print("🤖 Bot starting...")
    app.run_polling()

if __name__ == '__main__':
    main()
