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

# Get bot token from environment variable
TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')

# --- Database Setup ---
def init_database():
    """Initialize SQLite database with required tables."""
    conn = sqlite3.connect('user_data.db')
    c = conn.cursor()
    
    # Create table for storing user information
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
    
    # Create table for user settings (optional)
    c.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'en',
            notification_enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# --- Database Helper Functions ---
def save_info(user_id: int, key: str, value: str) -> bool:
    """Save or update information for a user."""
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        
        # Check if key exists
        c.execute('SELECT id FROM user_info WHERE user_id = ? AND key_name = ?', (user_id, key))
        exists = c.fetchone()
        
        if exists:
            # Update existing record
            c.execute('''
                UPDATE user_info 
                SET value = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? AND key_name = ?
            ''', (value, user_id, key))
        else:
            # Insert new record
            c.execute('''
                INSERT INTO user_info (user_id, key_name, value) 
                VALUES (?, ?, ?)
            ''', (user_id, key, value))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Error saving info: {e}")
        return False

def get_info(user_id: int, key: str) -> str:
    """Retrieve information for a user."""
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('SELECT value, updated_at FROM user_info WHERE user_id = ? AND key_name = ?', (user_id, key))
        result = c.fetchone()
        conn.close()
        
        if result:
            return result[0]  # Return the value
        return None
    except Exception as e:
        logger.error(f"Error getting info: {e}")
        return None

def get_all_keys(user_id: int) -> list:
    """Get all keys for a user."""
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('SELECT key_name, value, updated_at FROM user_info WHERE user_id = ? ORDER BY key_name', (user_id,))
        results = c.fetchall()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"Error getting all keys: {e}")
        return []

def delete_info(user_id: int, key: str) -> bool:
    """Delete information for a user."""
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM user_info WHERE user_id = ? AND key_name = ?', (user_id, key))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error(f"Error deleting info: {e}")
        return False

def delete_all_info(user_id: int) -> bool:
    """Delete all information for a user."""
    try:
        conn = sqlite3.connect('user_data.db')
        c = conn.cursor()
        c.execute('DELETE FROM user_info WHERE user_id = ?', (user_id,))
        conn.commit()
        affected = c.rowcount
        conn.close()
        return affected > 0
    except Exception as e:
        logger.error(f"Error deleting all info: {e}")
        return False

# --- Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with instructions."""
    user_name = update.effective_user.first_name
    
    welcome_text = f"""
👋 Hello {user_name}! I'm your **Information Keeper Bot**!

I can store and retrieve information for you. Here's how:

📌 **Commands:**
/save <key> <value> - Save information
/get <key> - Retrieve information
/list - List all your saved keys
/delete <key> - Delete specific information
/clear - Delete ALL your information
/search <text> - Search through your saved info
/stats - See your storage statistics
/help - Show this help

📝 **Examples:**
/save password mySecret123 - Save password
/get password - Retrieve it
/save birthday Jan 15, 1990 - Save birthday

🔒 Your data is private - only you can access it!
"""
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message."""
    help_text = """
❓ **Help - How to use this bot**

**Save Information:**
/save <key> <value>
Example: `/save phone 123-456-7890`

**Retrieve Information:**
/get <key>
Example: `/get phone`

**List All Keys:**
/list
Shows all your saved information

**Delete Information:**
/delete <key>
Example: `/delete phone`

**Clear All Data:**
/clear
⚠️ This will delete ALL your saved information!

**Search Information:**
/search <text>
Finds keys or values containing the search text

**View Statistics:**
/stats
Shows how many items you have saved

---
💡 **Tips:**
• Keys are case-sensitive
• You can save any type of text as value
• Data is stored in a secure database
• Updates to existing keys will overwrite old data
"""
    await update.message.reply_text(help_text)

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save information."""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 2:
        await update.message.reply_text(
            "❌ Please provide both a key and a value.\n"
            "Format: `/save <key> <value>`\n"
            "Example: `/save city New York`"
        )
        return
    
    key = args[0]
    value = ' '.join(args[1:])  # Join all remaining arguments as value
    
    if len(key) > 50:
        await update.message.reply_text("❌ Key is too long! Maximum 50 characters.")
        return
    
    if len(value) > 1000:
        await update.message.reply_text("❌ Value is too long! Maximum 1000 characters.")
        return
    
    if save_info(user_id, key, value):
        await update.message.reply_text(f"✅ Information saved!\n\n📌 **Key:** {key}\n📝 **Value:** {value}")
    else:
        await update.message.reply_text("❌ Failed to save information. Please try again.")

async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve information."""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "❌ Please provide a key.\n"
            "Format: `/get <key>`\n"
            "Example: `/get city`"
        )
        return
    
    key = args[0]
    value = get_info(user_id, key)
    
    if value:
        await update.message.reply_text(f"📌 **Key:** {key}\n📝 **Value:** {value}")
    else:
        await update.message.reply_text(f"❌ No information found for key: '{key}'")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all saved information."""
    user_id = update.effective_user.id
    results = get_all_keys(user_id)
    
    if not results:
        await update.message.reply_text("📭 You haven't saved any information yet.")
        return
    
    # Format the list
    response = "📚 **Your Saved Information:**\n\n"
    for i, (key, value, updated_at) in enumerate(results, 1):
        # Truncate long values
        display_value = value[:50] + '...' if len(value) > 50 else value
        response += f"{i}. **{key}**: {display_value}\n"
    
    # Add note if there are more items
    if len(results) > 20:
        response += f"\n... and {len(results) - 20} more items."
    
    await update.message.reply_text(response)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete specific information."""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "❌ Please provide a key to delete.\n"
            "Format: `/delete <key>`\n"
            "Example: `/delete city`"
        )
        return
    
    key = args[0]
    
    # Check if key exists first
    value = get_info(user_id, key)
    if not value:
        await update.message.reply_text(f"❌ No information found for key: '{key}'")
        return
    
    if delete_info(user_id, key):
        await update.message.reply_text(f"🗑️ Deleted: **{key}**\n\nPrevious value: {value}")
    else:
        await update.message.reply_text("❌ Failed to delete information. Please try again.")

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete all information for a user."""
    user_id = update.effective_user.id
    results = get_all_keys(user_id)
    
    if not results:
        await update.message.reply_text("📭 You don't have any information to clear.")
        return
    
    # Ask for confirmation
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes, clear everything", callback_data="clear_confirm"),
            InlineKeyboardButton("❌ No, cancel", callback_data="clear_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ **Are you sure?**\n\nYou have {len(results)} saved items.\n\nThis action cannot be undone!",
        reply_markup=reply_markup
    )

async def search_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search through saved information."""
    user_id = update.effective_user.id
    args = context.args
    
    if len(args) < 1:
        await update.message.reply_text(
            "❌ Please provide search text.\n"
            "Format: `/search <text>`\n"
            "Example: `/search birthday`"
        )
        return
    
    search_text = ' '.join(args).lower()
    results = get_all_keys(user_id)
    
    if not results:
        await update.message.reply_text("📭 You haven't saved any information yet.")
        return
    
    # Filter results
    matches = []
    for key, value, updated_at in results:
        if search_text in key.lower() or search_text in value.lower():
            matches.append((key, value))
    
    if not matches:
        await update.message.reply_text(f"🔍 No matches found for: '{search_text}'")
        return
    
    response = f"🔍 **Search Results for '{search_text}':**\n\n"
    for i, (key, value) in enumerate(matches, 1):
        display_value = value[:50] + '...' if len(value) > 50 else value
        response += f"{i}. **{key}**: {display_value}\n"
    
    await update.message.reply_text(response)

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show statistics about saved information."""
    user_id = update.effective_user.id
    results = get_all_keys(user_id)
    
    if not results:
        await update.message.reply_text("📭 You haven't saved any information yet.")
        return
    
    # Calculate statistics
    total_items = len(results)
    total_chars = sum(len(value) for _, value, _ in results)
    avg_len = total_chars // total_items if total_items > 0 else 0
    
    # Find most recent
    most_recent = max(results, key=lambda x: x[2])
    
    response = f"""
📊 **Your Storage Statistics**

📌 Total items: {total_items}
📝 Total characters: {total_chars}
📏 Average length: {avg_len} characters
🔄 Most recent: **{most_recent[0]}** ({most_recent[2][:10]})

💾 Storage used: ~{total_chars / 1024:.2f} KB
"""
    await update.message.reply_text(response)

# --- Callback Query Handler ---
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data = query.data
    
    if data == "clear_confirm":
        if delete_all_info(user_id):
            await query.edit_message_text("✅ All your information has been cleared!")
        else:
            await query.edit_message_text("❌ Failed to clear information. Please try again.")
    
    elif data == "clear_cancel":
        await query.edit_message_text("✅ Clear operation cancelled. Your data is safe.")

# --- Message Handler ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle regular text messages (non-commands)."""
    user_message = update.message.text
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    # Simple greetings
    if any(greeting in user_message.lower() for greeting in ['hello', 'hi', 'hey']):
        await update.message.reply_text(f"👋 Hey {user_name}! Use /help to see what I can do.")
    elif "thank" in user_message.lower():
        await update.message.reply_text("🙌 You're welcome! Let me know if you need anything else.")
    elif "help" in user_message.lower():
        await update.message.reply_text("Type /help to see all my commands!")
    else:
        await update.message.reply_text(
            f"I'll remember that for you! Try using:\n"
            f"• /save key value\n"
            f"• /get key\n"
            f"• /help for more commands"
        )

# --- Error Handler ---
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong. Please try again or use /help for support."
        )

# --- Main Function ---
def main():
    """Start the bot."""
    # Initialize database
    init_database()
    
    # Create the Application
    app = Application.builder().token(TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("get", get_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("search", search_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Register callback and message handlers
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Register error handler
    app.add_error_handler(error_handler)

    # Start the bot
    print("🤖 Bot is starting with database storage...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
