import telebot
from telebot import types
from flask import Flask, request
import os, json

# === Asosiy sozlamalar ===
TOKEN = "8227719581:AAG0urV7wYg9DRB2am-xknjqTsY2z3Tr2js"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 7530173398

app = Flask(__name__)

# === Fayl yo‘llari ===
NUMBERS_FILE = "numbers.json"
SETTINGS_FILE = "settings.json"

# === Fayllarni yaratish (agar mavjud bo‘lmasa) ===
if not os.path.exists(NUMBERS_FILE):
    with open(NUMBERS_FILE, "w") as f:
        json.dump({"uzbek": [], "foreign": []}, f)

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "card_number": "5614681914238039",
            "card_name": "Nasriddinova.M"
        }, f)

# === Webhook route ===
@app.route(f"/{TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return '', 200

@app.before_first_request
def set_webhook():
    url = f"https://telegram-bot-2-lbu8.onrender.com/{TOKEN}"  # Render dagi URL'ing shu bo‘lishi mumkin
    bot.remove_webhook()
    bot.set_webhook(url)

# === Bot komandalar ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 O'zbek raqam olish"), types.KeyboardButton("🌍 Chet el raqam olish"))
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin panel"))
    bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

# === Raqam ko‘rsatish, to‘lov jarayoni, admin paneli funksiyalari shu yerdan pastga qoladi ===
# Oldingi kodda yozilgan qismlar — ularni bu yerga joylab ketamiz, agar kerak bo‘lsa yana qo‘shib beraman

