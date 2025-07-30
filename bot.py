import telebot
from telebot import types
import json
import os
from flask import Flask, request
#=== Sozlamalar ===

TOKEN = "822771958:AAG0urV7wYg9DRB2am-xknjqTsY2z3Tr2js"
WEBHOOK_URL = "https://telegram-bot-2-lbu8.onrender.com"
ADMIN_ID = 7530173398
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

NUMBERS_FILE = "numbers.json"
SETTINGS_FILE = "settings.json"

#=== Fayllarni yaratish ===

if not os.path.exists(NUMBERS_FILE): with open(NUMBERS_FILE, "w") as f: json.dump({"uzbek": [], "foreign": []}, f)

if not os.path.exists(SETTINGS_FILE): with open(SETTINGS_FILE, "w") as f: json.dump({"card_number": "5614681914238039", "card_name": "Nasriddinova.M"}, f)

#=== /start ===

@bot.message_handler(commands=['start']) def start_handler(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add(types.KeyboardButton("\ud83d\udcf1 O'zbek raqam olish"), types.KeyboardButton("\ud83c\udf0d Chet el raqam olish")) if message.from_user.id == ADMIN_ID: markup.add(types.KeyboardButton("\u2699\ufe0f Admin panel")) bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

# === Raqamlarni ko'rsatish ===

@bot.message_handler(func=lambda m: m.text in ["\ud83d\udcf1 O'zbek raqam olish", "\ud83c\udf0d Chet el raqam olish"]) def show_numbers(message): category = "uzbek" if "O'zbek" in message.text else "foreign" with open(NUMBERS_FILE, "r") as f: data = json.load(f) numbers = data.get(category, []) if not numbers: bot.send_message(message.chat.id, "Hozircha bu bo'limda raqam yo'q.") return for item in numbers: number = item["number"] price = item["price"] btn = types.InlineKeyboardMarkup() btn.add(types.InlineKeyboardButton(f"\ud83d\udcb3 Sotib olish - {price} so'm", callback_data=f"buy_{number}")) bot.send_message(message.chat.id, f"\ud83d\udcde {number} — {price} so'm", reply_markup=btn)

#=== Sotib olish ===

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_")) def process_payment(call): number = call.data.split("", 1)[1] with open(SETTINGS_FILE, "r") as f: settings = json.load(f) card = settings["card_number"] card_name = settings["card_name"] markup = types.InlineKeyboardMarkup() markup.add(types.InlineKeyboardButton("\ud83d\udce4 To'lov qildim", callback_data=f"paid{number}")) bot.send_message(call.message.chat.id, f"\ud83d\udcb3 To'lov uchun karta:\n\n{card}\nIsm: {card_name}\n\nTo'lovni amalga oshirgach 'To'lov qildim' tugmasini bosing.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_")) def ask_for_receipt(call): bot.send_message(call.message.chat.id, "\ud83e\uddfe Chek rasmini yuboring.") bot.register_next_step_handler(call.message, handle_receipt, call.data.split("_", 1)[1])

def handle_receipt(message, number): if not message.photo: bot.send_message(message.chat.id, "Iltimos, chekni rasm sifatida yuboring.") return caption = f"\ud83e\uddfe Chek keldi!\n\n\ud83d\udcde Raqam: {number}\n\ud83d\udc64 Foydalanuvchi: @{message.from_user.username or message.from_user.first_name}\nID: {message.from_user.id}" markup = types.InlineKeyboardMarkup() markup.add( types.InlineKeyboardButton("\u2705 Tasdiqlash", callback_data=f"confirm_{message.from_user.id}{number}"), types.InlineKeyboardButton("\u274c Rad etish", callback_data=f"reject{message.from_user.id}_{number}") ) bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup) bot.send_message(message.chat.id, "✅ Chekingiz yuborildi. Iltimos kuting.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data.startswith("reject_")) def handle_admin_action(call): parts = call.data.split("_") action, user_id, number = parts[0], int(parts[1]), parts[2] if action == "confirm": bot.send_message(user_id, f"\u2705 To'lovingiz tasdiqlandi!\n\ud83d\udcde {number}") else: bot.send_message(user_id, f"\u274c To'lovingiz rad etildi. Iltimos, qayta yuboring.") bot.answer_callback_query(call.id, "Xabar yuborildi.")

#=== Admin panel ===

@bot.message_handler(func=lambda m: m.text == "\u2699\ufe0f Admin panel" and m.from_user.id == ADMIN_ID) def admin_panel(message): markup = types.ReplyKeyboardMarkup(resize_keyboard=True) markup.add( types.KeyboardButton("\u2795 Raqam qo'shish"), types.KeyboardButton("\u2796 Raqam o'chirish"), types.KeyboardButton("\ud83d\udcc2 Raqamlar ro'yxati"), types.KeyboardButton("\ud83d\udcb3 Karta ma'lumotlarini o'zgartirish"), types.KeyboardButton("\u2b05\ufe0f Orqaga") ) bot.send_message(message.chat.id, "Admin panelga xush kelibsiz!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Raqam qo'shish" and m.from_user.id == ADMIN_ID) def add_number(message): bot.send_message(message.chat.id, "Format: raqam | narx | tur (uzbek/foreign)", parse_mode="Markdown") bot.register_next_step_handler(message, save_number)

def save_number(message): try: number, price, category = [x.strip() for x in message.text.split("|")] with open(NUMBERS_FILE, "r") as f: data = json.load(f) data[category].append({"number": number, "price": price}) with open(NUMBERS_FILE, "w") as f: json.dump(data, f, indent=4) bot.send_message(message.chat.id, f"✅ {number} qo'shildi.") except: bot.send_message(message.chat.id, "❌ Format xato.")

@bot.message_handler(func=lambda m: m.text == "➖ Raqam o'chirish" and m.from_user.id == ADMIN_ID) def delete_number(message): bot.send_message(message.chat.id, "O'chirmoqchi bo'lgan raqamni yozing:") bot.register_next_step_handler(message, remove_number)

def remove_number(message): number_to_remove = message.text.strip() with open(NUMBERS_FILE, "r") as f: data = json.load(f) found = False for cat in data: before = len(data[cat]) data[cat] = [item for item in data[cat] if item["number"] != number_to_remove] if len(data[cat]) < before: found = True with open(NUMBERS_FILE, "w") as f: json.dump(data, f, indent=4) if found: bot.send_message(message.chat.id, f"✅ {number_to_remove} o'chirildi.") else: bot.send_message(message.chat.id, "❌ Bunday raqam topilmadi.")

@bot.message_handler(func=lambda m: m.text == "📂 Raqamlar ro'yxati" and m.from_user.id == ADMIN_ID) def show_all_numbers(message): with open(NUMBERS_FILE, "r") as f: data = json.load(f) text = "📋 Raqamlar:\n" for cat in data: text += f"\n📂 {cat.upper()}:\n" for item in data[cat]: text += f"📞 {item['number']} — {item['price']} so'm\n" bot.send_message(message.chat.id, text or "Raqamlar yo'q.")

@bot.message_handler(func=lambda m: m.text == "💳 Karta ma'lumotlarini o'zgartirish" and m.from_user.id == ADMIN_ID) def update_card(message): bot.send_message(message.chat.id, "Format: raqam | ism familiya", parse_mode="Markdown") bot.register_next_step_handler(message, save_card_info)

def save_card_info(message): try: card, name = [x.strip() for x in message.text.split("|")] with open(SETTINGS_FILE, "w") as f: json.dump({"card_number": card, "card_name": name}, f) bot.send_message(message.chat.id, "✅ Yangilandi.") except: bot.send_message(message.chat.id, "❌ Xato format.")

@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga" and m.from_user.id == ADMIN_ID) def back_to_start(message): start_handler(message)

#=== Webhook sozlash ===

@app.route("/", methods=['POST']) def webhook(): bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))]) return "", 200

@app.route("/") def index(): return "Bot ishlayapti."

if name == 'main': import threading import time bot.remove_webhook() time.sleep(1) bot.set_webhook(url=WEBHOOK_URL) app.run(host="0.0.0.0", port=10000)

