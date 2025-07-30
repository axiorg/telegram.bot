import telebot from telebot import types from flask import Flask, request import json import os

=== Token va bot ===

TOKEN = "8227719581:AAG0urV7wYg9DRB2am-xknjqTsY2z3Tr2js" bot = telebot.TeleBot(TOKEN) ADMIN_ID = 7530173398

=== Flask app ===

app = Flask(name)

=== Fayllar ===

NUMBERS_FILE = "numbers.json" SETTINGS_FILE = "settings.json"

if not os.path.exists(NUMBERS_FILE): with open(NUMBERS_FILE, "w") as f: json.dump({"uzbek": [], "foreign": []}, f)

if not os.path.exists(SETTINGS_FILE): with open(SETTINGS_FILE, "w") as f: json.dump({"card_number": "5614681914238039", "card_name": "Nasriddinova.M"}, f)

=== Webhook endpoint ===

@app.route(f"/{TOKEN}", methods=["POST"]) def webhook(): update = telebot.types.Update.de_json(request.stream.read().decode("utf-8")) bot.process_new_updates([update]) return "", 200

=== /start komandasi ===

@bot.message_handler(commands=['start']) def start_handler(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add(types.KeyboardButton("📱 O'zbek raqam olish"), types.KeyboardButton("🌍 Chet el raqam olish")) if message.from_user.id == ADMIN_ID: markup.add(types.KeyboardButton("⚙️ Admin panel")) bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

=== Raqamlarni ko'rsatish ===

@bot.message_handler(func=lambda message: message.text in ["📱 O'zbek raqam olish", "🌍 Chet el raqam olish"]) def show_numbers(message): category = "uzbek" if "O'zbek" in message.text else "foreign" with open(NUMBERS_FILE, "r") as f: data = json.load(f) numbers = data.get(category, []) if not numbers: bot.send_message(message.chat.id, "Hozircha bu bo‘limda raqam yo‘q.") return for item in numbers: btn = types.InlineKeyboardMarkup() btn.add(types.InlineKeyboardButton(f"💳 Sotib olish - {item['price']} so'm", callback_data=f"buy_{item['number']}")) bot.send_message(message.chat.id, f"📞 {item['number']} — {item['price']} so'm", reply_markup=btn)

=== To'lov bosilganda ===

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_")) def process_payment(call): number = call.data.split("", 1)[1] with open(SETTINGS_FILE, "r") as f: settings = json.load(f) markup = types.InlineKeyboardMarkup() markup.add(types.InlineKeyboardButton("📤 To‘lov qildim", callback_data=f"paid{number}")) bot.send_message(call.message.chat.id, f"💳 To‘lov uchun karta:\n\n{settings['card_number']}\nIsm: {settings['card_name']}\n\nTo‘lovni amalga oshirgach 'To‘lov qildim' tugmasini bosing.", reply_markup=markup)

=== Chek so'rash ===

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_")) def ask_for_receipt(call): bot.send_message(call.message.chat.id, "🧾 Chek rasmini yuboring.") bot.register_next_step_handler(call.message, handle_receipt, call.data.split("_", 1)[1])

=== Chekni adminlarga yuborish ===

def handle_receipt(message, number): if not message.photo: bot.send_message(message.chat.id, "Rasm yuboring.") return caption = f"🧾 Chek keldi!\n\n📞 Raqam: {number}\n👤 @{message.from_user.username or message.from_user.first_name}\nID: {message.from_user.id}" markup = types.InlineKeyboardMarkup() markup.add( types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{message.from_user.id}{number}"), types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject{message.from_user.id}_{number}") ) bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup) bot.send_message(message.chat.id, "✅ Chekingiz yuborildi. Iltimos kuting.")

=== Admin tasdiqlashi ===

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data.startswith("reject_")) def handle_admin_action(call): action, user_id, number = call.data.split("_") user_id = int(user_id) if action == "confirm": bot.send_message(user_id, f"✅ To‘lovingiz tasdiqlandi!\n📞 {number}") else: bot.send_message(user_id, "❌ To‘lovingiz rad etildi.") bot.answer_callback_query(call.id, "Xabar yuborildi.")

=== Webhookni sozlash va serverni ishga tushurish ===

if name == "main": webhook_url = f"https://telegram-bot-2-lbu8.onrender.com/{TOKEN}" bot.remove_webhook() bot.set_webhook(webhook_url) port = int(os.environ.get("PORT", 5000)) app.run(host="0.0.0.0", port=port)

  
