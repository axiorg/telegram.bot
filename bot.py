import telebot
from telebot import types
import json
import os

TOKEN = "SENING_BOT_TOKENING"  # O'zgartir: o'z tokeningni qo'y
bot = telebot.TeleBot(TOKEN)

ADMIN_ID = 123456789  # O'zgartir: o'z Telegram ID'ingni yoz

NUMBERS_FILE = "numbers.json"
SETTINGS_FILE = "settings.json"

if not os.path.exists(NUMBERS_FILE):
    with open(NUMBERS_FILE, "w") as f:
        json.dump({"uzbek": [], "foreign": []}, f)

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "card_number": "5614681914238039",
            "card_name": "Nasriddinova.M"
        }, f)
