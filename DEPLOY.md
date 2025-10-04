# VintedScanner - Render Deployment Guide

## Prerequisites
- GitHub account
- Render account (free at render.com)
- Telegram bot token

## Deployment Steps

### 1. Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/vinted-scanner.git
git push -u origin main
```

### 2. Deploy on Render

1. Go to [render.com](https://render.com) and sign up
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: vinted-scanner
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python vinted_scanner.py`

### 3. Set Environment Variables

In Render dashboard, go to Environment tab and add:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
TELEGRAM_CHAT_IDS=chat_id_1,chat_id_2
```

### 4. Get Your Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Get your bot token
4. Get your chat ID by messaging [@get_id_bot](https://t.me/get_id_bot)

### 5. Deploy

Click "Create Web Service" and wait for deployment.

## Configuration

The scanner will:
- Search for Amouage items on Vinted.de
- Send notifications every 2 minutes
- Send the 5 most recent items as photo messages
- Track items to avoid duplicates

## Monitoring

- Check logs in Render dashboard
- Bot will send restart notifications when deployed
- Search notifications every 2 minutes

## Free Tier Limitations

- Service sleeps after 15 minutes of inactivity
- 750 hours per month
- Automatic wake-up when accessed

## Troubleshooting

- Check Render logs for errors
- Verify environment variables are set
- Ensure bot token is correct
- Check chat ID is valid
