# Information Keeper Telegram Bot

A Telegram bot that stores and retrieves information using SQLite database, deployed on Railway.

## Features

- ✅ Save information with custom keys
- ✅ Retrieve saved information
- ✅ List all saved items
- ✅ Delete specific items
- ✅ Clear all data with confirmation
- ✅ Search through saved information
- ✅ View storage statistics
- ✅ Private data per user
- ✅ Persistent storage with SQLite

## Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/start` | Welcome message | `/start` |
| `/help` | Show help | `/help` |
| `/save <key> <value>` | Save information | `/save phone 123-456-7890` |
| `/get <key>` | Retrieve information | `/get phone` |
| `/list` | List all saved keys | `/list` |
| `/delete <key>` | Delete specific info | `/delete phone` |
| `/clear` | Delete ALL information | `/clear` |
| `/search <text>` | Search through saved info | `/search birthday` |
| `/stats` | View storage statistics | `/stats` |

## Deployment

### 1. Get Bot Token
- Open Telegram and search for `@BotFather`
- Send `/newbot` and follow instructions
- Copy your bot token

### 2. Deploy on Railway
1. Create a GitHub repository with these files
2. Go to [Railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Add environment variable:
   - Key: `TELEGRAM_BOT_TOKEN`
   - Value: Your bot token from BotFather

### 3. Test Your Bot
- Open Telegram and find your bot
- Send `/start`
- Try saving and retrieving information

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `TELEGRAM_BOT_TOKEN` | Your bot token from BotFather | Yes |

## Tech Stack

- Python 3.x
- python-telegram-bot
- SQLite3
- Railway

## License

MIT
