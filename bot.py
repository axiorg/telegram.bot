import telebot
from telebot import types
import json
import os
from flask import Flask, request

# === Sozlamalar ===
TOKEN = "8227719581:AAG0urV7wYg9DRB2am-xknjqTsY2z3Tr2js"
WEBHOOK_URL = "https://telegram-bot-2-lbu8.onrender.com"
ADMIN_ID = 7530173398

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === Fayl nomlari ===
NUMBERS_FILE = "numbers.json"
SETTINGS_FILE = "settings.json"

# === Fayllarni yaratish ===
if not os.path.exists(NUMBERS_FILE):
    with open(NUMBERS_FILE, "w") as f:
        json.dump({"uzbek": [], "foreign": []}, f)

if not os.path.exists(SETTINGS_FILE):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({"card_number": "5614681914238039", "card_name": "Nasriddinova.M"}, f)

# === /start komandasi ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📱 O'zbek raqam olish", "🌍 Chet el raqam olish")
    if message.from_user.id == ADMIN_ID:
        markup.add("⚙️ Admin panel")
    bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

# === Raqamlar ko‘rsatish ===
@bot.message_handler(func=lambda m: m.text in ["📱 O'zbek raqam olish", "🌍 Chet el raqam olish"])
def show_numbers(message):
    category = "uzbek" if "O'zbek" in message.text else "foreign"
    with open(NUMBERS_FILE, "r") as f:
        data = json.load(f)
    numbers = data.get(category, [])
    if not numbers:
        bot.send_message(message.chat.id, "Hozircha bu bo‘limda raqam yo‘q.")
        return
    for item in numbers:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(f"💳 Sotib olish - {item['price']} so'm", callback_data=f"buy_{item['number']}"))
        bot.send_message(message.chat.id, f"📞 {item['number']} — {item['price']} so'm", reply_markup=markup)

# === Sotib olish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_payment(call):
    number = call.data.split("_", 1)[1]
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 To‘lov qildim", callback_data=f"paid_{number}"))
    bot.send_message(call.message.chat.id,
        f"💳 To‘lov uchun karta:\n{settings['card_number']}\nIsm: {settings['card_name']}",
        reply_markup=markup)

# === Chek qabul qilish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def ask_for_receipt(call):
    number = call.data.split("_", 1)[1]
    bot.send_message(call.message.chat.id, "🧾 Chek rasmini yuboring.")
    bot.register_next_step_handler(call.message, handle_receipt, number)

def handle_receipt(message, number):
    if not message.photo:
        bot.send_message(message.chat.id, "Iltimos, chekni rasm sifatida yuboring.")
        return
    caption = f"🧾 Chek!\n📞 Raqam: {number}\n👤 Foydalanuvchi: @{message.from_user.username or message.from_user.first_name}\nID: {message.from_user.id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{message.from_user.id}_{number}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{message.from_user.id}_{number}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Chek yuborildi. Kuting.")

# === Admin tasdiqlash yoki rad etish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data.startswith("reject_"))
def handle_admin_action(call):
    parts = call.data.split("_")
    action, user_id, number = parts[0], int(parts[1]), parts[2]
    if action == "confirm":
        bot.send_message(user_id, f"✅ To‘lov tasdiqlandi! Raqamingiz: {number}")
    else:
        bot.send_message(user_id, "❌ To‘lov rad etildi. Qayta urinib ko‘ring.")
    bot.answer_callback_query(call.id, "Xabar yuborildi.")

# === Admin panel ===
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Raqam qo‘shish", "➖ Raqam o‘chirish", "📂 Raqamlar ro‘yxati", "💳 Karta o‘zgartirish", "⬅️ Orqaga")
    bot.send_message(message.chat.id, "Admin panelga xush kelibsiz!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Raqam qo‘shish" and m.from_user.id == ADMIN_ID)
def add_number(message):
    bot.send_message(message.chat.id, "Format: `raqam | narx | uzbek/foreign`", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_number)

def save_number(message):
    try:
        number, price, category = [x.strip() for x in message.text.split("|")]
        with open(NUMBERS_FILE, "r") as f:
            data = json.load(f)
        data[category].append({"number": number, "price": price})
        with open(NUMBERS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        bot.send_message(message.chat.id, f"✅ {number} qo‘shildi.")
    except:
        bot.send_message(message.chat.id, "❌ Xato format.")

@bot.message_handler(func=lambda m: m.text == "➖ Raqam o‘chirish" and m.from_user.id == ADMIN_ID)
def delete_number(message):
    bot.send_message(message.chat.id, "O‘chirish uchun raqamni yozing:")
    bot.register_next_step_handler(message, remove_number)

def remove_number(message):
    number = message.text.strip()
    with open(NUMBERS_FILE, "r") as f:
        data = json.load(f)
    found = False
    for cat in data:
        before = len(data[cat])
        data[cat] = [n for n in data[cat] if n["number"] != number]
        if len(data[cat]) < before:
            found = True
    with open(NUMBERS_FILE, "w") as f:
        json.dump(data, f, indent=4)
    if found:
        bot.send_message(message.chat.id, f"✅ {number} o‘chirildi.")
    else:
        bot.send_message(message.chat.id, "❌ Topilmadi.")

@bot.message_handler(func=lambda m: m.text == "📂 Raqamlar ro‘yxati" and m.from_user.id == ADMIN_ID)
def list_numbers(message):
    with open(NUMBERS_FILE, "r") as f:
        data = json.load(f)
    text = ""
    for cat in data:
        text += f"📁 {cat.upper()}:\n"
        for item in data[cat]:
            text += f"{item['number']} — {item['price']} so'm\n"
    bot.send_message(message.chat.id, text or "Raqam yo‘q.")

@bot.message_handler(func=lambda m: m.text == "💳 Karta o‘zgartirish" and m.from_user.id == ADMIN_ID)
def change_card(message):
    bot.send_message(message.chat.id, "Format: `karta raqam | ism`", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_card)

def save_card(message):
    try:
        card, name = [x.strip() for x in message.text.split("|")]
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"card_number": card, "card_name": name}, f)
        bot.send_message(message.chat.id, "✅ O‘zgartirildi.")
    except:
        bot.send_message(message.chat.id, "❌ Xato format.")

@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga")
def back(message):
    start_handler(message)

# === Webhook ===
@app.route('/', methods=['POST'])
def webhook():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "ok", 200

@app.route('/')
def index():
    return "Bot ishlayapti."

if __name__ == '__main__':
    import requests
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
