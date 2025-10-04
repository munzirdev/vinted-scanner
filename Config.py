import os

# SMTP Settings for e-mail notification
smtp_username = os.getenv("SMTP_USERNAME", "")
smtp_psw = os.getenv("SMTP_PASSWORD", "")
smtp_server = os.getenv("SMTP_SERVER", "")
smtp_toaddrs = os.getenv("SMTP_TOADDRS", "User <example@example.com>").split(",")

# Slack WebHook for notification
slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")

# Telegram Token and ChatIDs for notification
telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "8373369489:AAH5G4FqpuzDsCTLZAMLrc7iGJsX4U9QoC0")
# Single chat ID (for backward compatibility)
telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "203591317")
# Multiple chat IDs (list format)
telegram_chat_ids = os.getenv("TELEGRAM_CHAT_IDS", "203591317").split(",")  # Comma-separated list

# Vinted URL: change the TLD according to your country (.fr, .es, etc.)
vinted_url = "https://www.vinted.de"

# Vinted queries for research
# "page", "per_page" and "order" you may not edit them
# "search_text" is the free search field, this field may be empty if you wish to search for the entire brand.
# "catalog_ids" is the category in which to eventually search, if the field is empty it will search in all categories. Vinted assigns a numeric ID to each category, e.g. 2996 is the ID for e-Book Reader
# "brand_ids" if you want to search by brand. Vinted assigns a numeric ID to each brand, e.g. 417 is the ID for Louis Vuitton
# "order" you can change it to relevance, newest_first, price_high_to_low, price_low_to_high

queries = [
    {
        'page': '1',
        'per_page': '96',
        'search_text': 'Amouage',
        'catalog_ids': '',
        'brand_ids' : '',
        'order': 'newest_first',
    },
]
