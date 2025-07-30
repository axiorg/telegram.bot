import telebot from telebot import types from flask import Flask, request import os, json

=== Asosiy sozlamalar ===

TOKEN = "8227719581:AAG0urV7wYg9DRB2am-xknjqTsY2z3Tr2js" bot = telebot.TeleBot(TOKEN) ADMIN_ID = 7530173398

app = Flask(name)

=== Fayl yo‘llari ===

NUMBERS_FILE = "numbers.json" SETTINGS_FILE = "settings.json"

=== Fayllarni yaratish (agar mavjud bo‘lmasa) ===

if not os.path.exists(NUMBERS_FILE): with open(NUMBERS_FILE, "w") as f: json.dump({"uzbek": [], "foreign": []}, f)

if not os.path.exists(SETTINGS_FILE): with open(SETTINGS_FILE, "w") as f: json.dump({ "card_number": "5614681914238039", "card_name": "Nasriddinova.M" }, f)

=== Webhook route ===

@app.route(f"/{TOKEN}", methods=['POST']) def webhook(): update = telebot.types.Update.de_json(request.stream.read().decode("utf-8")) bot.process_new_updates([update]) return '', 200

@app.before_first_request def set_webhook(): url = f"https://telegram-bot-2-lbu8.onrender.com/{TOKEN}" bot.remove_webhook() bot.set_webhook(url)

=== Bot komandalar ===

@bot.message_handler(commands=['start']) def start_handler(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add(types.KeyboardButton("\ud83d\udcf1 O'zbek raqam olish"), types.KeyboardButton("\ud83c\udf0d Chet el raqam olish")) if message.from_user.id == ADMIN_ID: markup.add(types.KeyboardButton("\u2699\ufe0f Admin panel")) bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text in ["\ud83d\udcf1 O'zbek raqam olish", "\ud83c\udf0d Chet el raqam olish"]) def show_numbers(message): category = "uzbek" if "O'zbek" in message.text else "foreign" with open(NUMBERS_FILE, "r") as f: data = json.load(f) numbers = data.get(category, []) if not numbers: bot.send_message(message.chat.id, "Hozircha bu bo‘limda raqam yo‘q.") return for item in numbers: number = item["number"] price = item["price"] btn = types.InlineKeyboardMarkup() btn.add(types.Inline


