import telebot
from telebot import types
from flask import Flask, request
import os, json

# === Token va bot ===
TOKEN = "8227719581:AAG0urV7wYg9DRB2am-xknjqTsY2z3Tr2js"
bot = telebot.TeleBot(TOKEN)
ADMIN_ID = 7530173398

# === Flask app ===
app = Flask(__name__)

# === Fayllar ===
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

# === Webhook handler ===
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "", 200

# === Telegram komandalar ===
@bot.message_handler(commands=["start"])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 O'zbek raqam olish"), types.KeyboardButton("🌍 Chet el raqam olish"))
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin panel"))
    bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

# === Qolgan bot funksiyalaring shu yerda bo‘ladi (raqam ko‘rsatish, to‘lov, admin panel) ===

# === Appni ishga tushurish va webhook o‘rnatish ===
if __name__ == "__main__":
    WEBHOOK_URL = f"https://telegram-bot-2-lbu8.onrender.com/{TOKEN}"  # Renderdagi URL bo‘yicha tuzilgan

    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
