import telebot
from telebot import types
import json
import os
from flask import Flask, request

# === Sozlamalar ===
TOKEN = "7511389832:AAE7UGj9hFKHpNkYsi1hvqcgk03Q4aWRCs0"
WEBHOOK_URL = "https://telegram-bot-2-lbu8.onrender.com"
ADMIN_ID = 6990930957

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
        json.dump({
            "card_number": "5614681914238039",
            "card_name": "Nasriddinova.M"
        }, f)

# === START komandasi ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("📱 O'zbek raqam olish"), types.KeyboardButton("🌍 Chet el raqam olish"))
    if message.from_user.id == ADMIN_ID:
        markup.add(types.KeyboardButton("⚙️ Admin panel"))
    bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

# === Raqamlarni ko‘rsatish ===
@bot.message_handler(func=lambda message: message.text in ["📱 O'zbek raqam olish", "🌍 Chet el raqam olish"])
def show_numbers(message):
    category = "uzbek" if "O'zbek" in message.text else "foreign"
    with open(NUMBERS_FILE, "r") as f:
        data = json.load(f)
    numbers = data.get(category, [])
    if not numbers:
        bot.send_message(message.chat.id, "Hozircha bu bo‘limda raqam yo‘q.")
        return
    for item in numbers:
        number = item["number"]
        price = item["price"]
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton(f"💳 Sotib olish - {price} so'm", callback_data=f"buy_{number}"))
        bot.send_message(message.chat.id, f"📞 {number} — {price} so'm", reply_markup=btn)

# === Sotib olish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_payment(call):
    number = call.data.split("_", 1)[1]
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    card = settings["card_number"]
    name = settings["card_name"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 To‘lov qildim", callback_data=f"paid_{number}"))
    bot.send_message(call.message.chat.id,
                     f"💳 To‘lov uchun karta:\n{card}\nIsm: {name}\n\nTo‘lovdan so‘ng 'To‘lov qildim' tugmasini bosing.",
                     reply_markup=markup)

# === Chek rasmini so‘rash ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def ask_receipt(call):
    bot.send_message(call.message.chat.id, "🧾 Chek rasmini yuboring.")
    bot.register_next_step_handler(call.message, handle_receipt, call.data.split("_", 1)[1])

# === Chekni qabul qilish ===
def handle_receipt(message, number):
    if not message.photo:
        bot.send_message(message.chat.id, "❌ Iltimos, rasm yuboring.")
        return
    caption = f"🧾 Chek:\n📞 {number}\n👤 @{message.from_user.username or message.from_user.first_name}\nID: {message.from_user.id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{message.from_user.id}_{number}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{message.from_user.id}_{number}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)
    bot.send_message(message.chat.id, "✅ Chekingiz yuborildi. Iltimos, kuting.")

# === Admin tasdiqlash yoki rad etish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data.startswith("reject_"))
def handle_admin(call):
    action, user_id, number = call.data.split("_")
    user_id = int(user_id)
    if action == "confirm":
        bot.send_message(user_id, f"✅ To‘lovingiz tasdiqlandi!\n📞 {number}")
    else:
        bot.send_message(user_id, "❌ To‘lov rad etildi. Qayta urinib ko‘ring.")
    bot.answer_callback_query(call.id)

# === ADMIN PANEL ===
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        types.KeyboardButton("➕ Raqam qo‘shish"),
        types.KeyboardButton("➖ Raqam o‘chirish"),
        types.KeyboardButton("📂 Raqamlar ro‘yxati"),
        types.KeyboardButton("💳 Karta o‘zgarishi"),
        types.KeyboardButton("⬅️ Orqaga")
    )
    bot.send_message(message.chat.id, "Admin paneliga xush kelibsiz!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "➕ Raqam qo‘shish" and m.from_user.id == ADMIN_ID)
def add_number(message):
    bot.send_message(message.chat.id, "Format: `raqam | narx | tur (uzbek/foreign)`", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_number)

def save_number(message):
    try:
        number, price, category = [x.strip() for x in message.text.split("|")]
        with open(NUMBERS_FILE, "r") as f:
            data = json.load(f)
        data[category].append({"number": number, "price": price})
        with open(NUMBERS_FILE, "w") as f:
            json.dump(data, f, indent=4)
        bot.send_message(message.chat.id, "✅ Raqam qo‘shildi.")
    except:
        bot.send_message(message.chat.id, "❌ Format xato.")

@bot.message_handler(func=lambda m: m.text == "➖ Raqam o‘chirish" and m.from_user.id == ADMIN_ID)
def delete_number(message):
    bot.send_message(message.chat.id, "O‘chirmoqchi bo‘lgan raqamni yozing:")
    bot.register_next_step_handler(message, remove_number)

def remove_number(message):
    number = message.text.strip()
    with open(NUMBERS_FILE, "r") as f:
        data = json.load(f)
    found = False
    for cat in data:
        old = len(data[cat])
        data[cat] = [x for x in data[cat] if x["number"] != number]
        if len(data[cat]) < old:
            found = True
    with open(NUMBERS_FILE, "w") as f:
        json.dump(data, f, indent=4)
    if found:
        bot.send_message(message.chat.id, "✅ O‘chirildi.")
    else:
        bot.send_message(message.chat.id, "❌ Topilmadi.")

@bot.message_handler(func=lambda m: m.text == "📂 Raqamlar ro‘yxati" and m.from_user.id == ADMIN_ID)
def list_numbers(message):
    with open(NUMBERS_FILE, "r") as f:
        data = json.load(f)
    text = ""
    for cat in data:
        text += f"\n📂 {cat.upper()}:\n"
        for item in data[cat]:
            text += f"📞 {item['number']} — {item['price']} so‘m\n"
    bot.send_message(message.chat.id, text or "Raqamlar yo‘q.")

@bot.message_handler(func=lambda m: m.text == "💳 Karta o‘zgarishi" and m.from_user.id == ADMIN_ID)
def update_card(message):
    bot.send_message(message.chat.id, "Format: `karta raqami | ism familiya`", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_card)

def save_card(message):
    try:
        card, name = [x.strip() for x in message.text.split("|")]
        with open(SETTINGS_FILE, "w") as f:
            json.dump({"card_number": card, "card_name": name}, f)
        bot.send_message(message.chat.id, "✅ Yangilandi.")
    except:
        bot.send_message(message.chat.id, "❌ Format xato.")

@bot.message_handler(func=lambda m: m.text == "⬅️ Orqaga" and m.from_user.id == ADMIN_ID)
def back(message):
    start_handler(message)

# === Webhook sozlamalari ===
@app.route('/', methods=["POST"])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return '', 200
    else:
        return '', 403

# === Webhookni o‘rnatish ===
if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
