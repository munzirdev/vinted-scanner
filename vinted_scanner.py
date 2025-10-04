#!/usr/bin/env python3
import sys
import time
import json
import Config
import smtplib
import logging
import requests
import email.utils
from datetime import datetime
from email.message import EmailMessage
from logging.handlers import RotatingFileHandler


# Configure a rotating file handler to manage log files
handler = RotatingFileHandler("vinted_scanner.log", maxBytes=5000000, backupCount=5)

logging.basicConfig(handlers=[handler], 
                    format="%(asctime)s - %(filename)s - %(funcName)10s():%(lineno)s - %(levelname)s - %(message)s", 
                    level=logging.INFO)

# Timeout configuration for the requests
timeoutconnection = 30

# List to keep track of already analyzed items
list_analyzed_items = []

# Flag to track if startup notification has been sent
startup_notification_sent = False

# Function to send restart notification
def send_restart_notification():
    if Config.telegram_bot_token:
        try:
            restart_message = "🔄 VintedScanner restarted and is running again!"
            url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
            
            # Send to multiple chat IDs if configured, otherwise use single chat ID
            chat_ids = getattr(Config, 'telegram_chat_ids', [Config.telegram_chat_id])
            
            for chat_id in chat_ids:
                params = {
                    "chat_id": chat_id,
                    "text": restart_message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, params=params, headers=headers)
                if response.status_code == 200:
                    logging.info(f"Restart notification sent to chat {chat_id}")
                else:
                    logging.error(f"Failed to send restart notification to chat {chat_id}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error sending restart notification: {e}")

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:128.0) Gecko/20100101 Firefox/128.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/png,image/svg+xml,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "cross-site",
    "Sec-GPC": "1",
    "Priority": "u=0, i",
    "Pragma": "no-cache",
    "Cache-Control": "no-cache",
}

# Load previously analyzed item hashes to avoid duplicates
def load_analyzed_item():
    try:
        with open("vinted_items.txt", "r", errors="ignore") as f:
            for line in f:
                if line:
                    list_analyzed_items.append(line.rstrip())
    except FileNotFoundError:
        logging.info("vinted_items.txt not found, starting with empty list")
    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()

# Save a new analyzed item to prevent repeated alerts
def save_analyzed_item(hash):
    try:
        with open("vinted_items.txt", "a") as f:
            f.write(str(hash) + "\n")
    except IOError as e:
        logging.error(e, exc_info=True)
        sys.exit()

# Send notification e-mail when a new item is found
def send_email(item_title, item_price, item_url, item_image):
    try:
        # Create the e-mail message
        msg = EmailMessage()
        msg["To"] = Config.smtp_toaddrs
        msg["From"] = email.utils.formataddr(("Vinted Scanner", Config.smtp_username))
        msg["Subject"] = "Vinted Scanner - New Item"
        msg["Date"] = email.utils.formatdate(localtime=True)
        msg["Message-ID"] = email.utils.make_msgid()

        # Format message content
        body = f"{item_title}\n{item_price}\n🔗 {item_url}\n📷 {item_image}"

        msg.set_content(body)
        
        # Securely opening the SMTP connection
        with smtplib.SMTP(Config.smtp_server, 587) as smtpserver:
            smtpserver.ehlo()
            smtpserver.starttls()
            smtpserver.ehlo()

            # Authentication
            smtpserver.login(Config.smtp_username, Config.smtp_psw)
            
            # Sending the message
            smtpserver.send_message(msg)
            logging.info("E-mail sent")
    
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error sending email: {e}", exc_info=True)
    except Exception as e:
        logging.error(f"Error sending email: {e}", exc_info=True)


# Send a Slack message when a new item is found
def send_slack_message(item_title, item_price, item_url, item_image):
    webhook_url = Config.slack_webhook_url 

    # Format message content
    message = f"*{item_title}*\n🏷️ {item_price}\n🔗 {item_url}\n📷 {item_image}"
    slack_data = {"text": message}

    try:
        response = requests.post(
            webhook_url, 
            data=json.dumps(slack_data),
            headers={"Content-Type": "application/json"},
            timeout=timeoutconnection
        )

        if response.status_code != 200:
            logging.error(f"Slack notification failed: {response.status_code}, {response.text}")
        else:
            logging.info("Slack notification sent")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Slack message: {e}")

# Send a Telegram message when a new item is found
def send_telegram_message(item_title, item_price, item_url, item_image):
    # Format message content
    message = f"<b>{item_title}</b>\n🏷️ {item_price}\n🔗 {item_url}"

    try:
        # Send to multiple chat IDs if configured, otherwise use single chat ID
        chat_ids = getattr(Config, 'telegram_chat_ids', [Config.telegram_chat_id])
        
        for chat_id in chat_ids:
            # First send the photo
            photo_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendPhoto"
            photo_params = {
                "chat_id": chat_id,
                "photo": item_image,
                "caption": message,
                "parse_mode": "HTML"
            }
            
            photo_response = requests.post(photo_url, params=photo_params, headers=headers)
            if photo_response.status_code != 200:
                logging.error(f"Telegram photo failed for chat {chat_id}. Status code: {photo_response.status_code}, Response: {photo_response.text}")
                # Fallback to text message if photo fails
                text_url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
                text_params = {
                    "chat_id": chat_id,
                    "text": f"{message}\n📷 {item_image}",
                    "parse_mode": "HTML"
                }
                text_response = requests.post(text_url, params=text_params, headers=headers)
                if text_response.status_code == 200:
                    logging.info(f"Telegram text notification sent to chat {chat_id}")
                else:
                    logging.error(f"Telegram text notification failed for chat {chat_id}")
            else:
                logging.info(f"Telegram photo notification sent to chat {chat_id}")

    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending Telegram message: {e}")

def main():
    global startup_notification_sent
    
    # Send startup notification only once
    if not startup_notification_sent and Config.telegram_bot_token:
        try:
            startup_message = "🚀 VintedScanner started successfully!"
            url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
            
            # Send to multiple chat IDs if configured, otherwise use single chat ID
            chat_ids = getattr(Config, 'telegram_chat_ids', [Config.telegram_chat_id])
            
            for chat_id in chat_ids:
                params = {
                    "chat_id": chat_id,
                    "text": startup_message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, params=params, headers=headers)
                if response.status_code == 200:
                    logging.info(f"Startup notification sent to chat {chat_id}")
                else:
                    logging.error(f"Failed to send startup notification to chat {chat_id}: {response.status_code}")
            
            startup_notification_sent = True
        except Exception as e:
            logging.error(f"Error sending startup notification: {e}")

    # Load the list of previously analyzed items
    load_analyzed_item()

    # Initialize session and obtain session cookies from Vinted
    session = requests.Session()
    session.post(Config.vinted_url, headers=headers, timeout=timeoutconnection)
    cookies = session.cookies.get_dict()
    
    # Send search notification
    if Config.telegram_bot_token:
        try:
            search_message = "🔍 Conducting Vinted search..."
            url = f"https://api.telegram.org/bot{Config.telegram_bot_token}/sendMessage"
            
            # Send to multiple chat IDs if configured, otherwise use single chat ID
            chat_ids = getattr(Config, 'telegram_chat_ids', [Config.telegram_chat_id])
            
            for chat_id in chat_ids:
                params = {
                    "chat_id": chat_id,
                    "text": search_message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, params=params, headers=headers)
                if response.status_code == 200:
                    logging.info(f"Search notification sent to chat {chat_id}")
                else:
                    logging.error(f"Failed to send search notification to chat {chat_id}: {response.status_code}")
        except Exception as e:
            logging.error(f"Error sending search notification: {e}")

    # Loop through each search query defined in Config.py
    for params in Config.queries:
        # Request items from the Vinted API based on the search parameters
        logging.info(f"Searching with params: {params}")
        response = requests.get(f"{Config.vinted_url}/api/v2/catalog/items", params=params, cookies=cookies, headers=headers)
        logging.info(f"API Response status: {response.status_code}")
        
        data = response.json()
        logging.info(f"Found {len(data.get('items', []))} items in response")
        
        # Log the first few items for debugging
        if data.get('items'):
            for i, item in enumerate(data['items'][:3]):  # Show first 3 items
                logging.info(f"Item {i+1}: {item.get('title', 'No title')} - {item.get('price', {}).get('amount', 'No price')} {item.get('price', {}).get('currency_code', '')}")
        else:
            logging.warning("No items found in API response")
            logging.info(f"Full API response: {data}")

        if data:
            # Process only the first 5 items (most recent)
            items_to_process = data["items"][:5]
            logging.info(f"Processing {len(items_to_process)} most recent items")
            
            for item in items_to_process:
                item_id = str(item["id"])
                item_title = item["title"]
                item_url = item["url"]
                item_price = f'{item["price"]["amount"]} {item["price"]["currency_code"]}'
                item_image = item["photo"]["full_size_url"]

                # Check if the item has already been analyzed to prevent duplicates
                if item_id not in list_analyzed_items:

                    # Send e-mail notifications if configured
                    if Config.smtp_username and Config.smtp_server:
                        send_email(item_title, item_price,item_url, item_image)

                    # Send Slack notifications if configured
                    if Config.slack_webhook_url:
                        send_slack_message(item_title, item_price, item_url, item_image)

                    # Send Telegram notifications if configured
                    if Config.telegram_bot_token and Config.telegram_chat_id:
                        send_telegram_message(item_title, item_price, item_url, item_image)

                    # Mark item as analyzed and save it
                    list_analyzed_items.append(item_id)
                    save_analyzed_item(item_id)

if __name__ == "__main__":
    # Send restart notification when script starts
    send_restart_notification()
    
    while True:
        try:
            main()
            # Wait 2 minutes before next scan
            logging.info("Scan completed. Waiting 2 minutes before next scan...")
            time.sleep(120)  # 2 minutes = 120 seconds
        except KeyboardInterrupt:
            logging.info("Scanner stopped by user")
            break
        except Exception as e:
            logging.error(f"Error in main loop: {e}", exc_info=True)
            # Send restart notification when recovering from error
            send_restart_notification()
            logging.info("Waiting 2 minutes before retry...")
            time.sleep(120)  # Wait 2 minutes before retry
