from flask import Flask, request
import telebot
from telebot import types
from tinydb import TinyDB, Query

# === Sozlamalar ===
TOKEN = "8227719581:AAEWcJBttuFCTUqtXJPZVR39_pnj_WZWDDY"
WEBHOOK_URL = "https://telegram-bot-2-lbu8.onrender.com"
ADMIN_ID = 7530173398

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# === TinyDB ===
db = TinyDB("db.json")
numbers_table = db.table("numbers")
settings_table = db.table("settings")

# === Dastlabki karta yozuvi (agar bo‘sh bo‘lsa) ===
if len(settings_table) == 0:
    settings_table.insert({
        "card_number": "5614681914238039",
        "card_name": "Nasriddinova.M"
    })

# === /start komandasi ===
@bot.message_handler(commands=['start'])
def start_handler(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📱 O'zbek raqam olish", "🌍 Chet el raqam olish")
    if message.from_user.id == ADMIN_ID:
        markup.add("⚙️ Admin panel")
    bot.send_message(message.chat.id, "Xush kelibsiz! Qaysi turdagi raqam kerak?", reply_markup=markup)

# === Raqam ko‘rsatish ===
@bot.message_handler(func=lambda m: m.text in ["📱 O'zbek raqam olish", "🌍 Chet el raqam olish"])
def show_numbers(message):
    category = "uzbek" if "O'zbek" in message.text else "foreign"
    found = numbers_table.search(Query().category == category)
    if not found:
        bot.send_message(message.chat.id, "Hozircha bu bo‘limda raqam yo‘q.")
        return
    for item in found:
        btn = types.InlineKeyboardMarkup()
        btn.add(types.InlineKeyboardButton(f"💳 Sotib olish - {item['price']} so'm", callback_data=f"buy_{item['number']}"))
        bot.send_message(message.chat.id, f"📞 {item['number']} — {item['price']} so'm", reply_markup=btn)

# === To‘lov qilish ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_payment(call):
    number = call.data.split("_", 1)[1]
    settings = settings_table.all()[0]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 To‘lov qildim", callback_data=f"paid_{number}"))
    bot.send_message(call.message.chat.id,
        f"💳 To‘lov uchun karta:\n\n`{settings['card_number']}`\nIsm: {settings['card_name']}\n\nTo‘lovni amalga oshirgach 'To‘lov qildim' tugmasini bosing.",
        parse_mode="Markdown", reply_markup=markup)

# === Chek so‘rash ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def ask_receipt(call):
    bot.send_message(call.message.chat.id, "🧾 Chek rasmini yuboring.")
    bot.register_next_step_handler(call.message, lambda msg: handle_receipt(msg, call.data.split("_")[1]))

def handle_receipt(message, number):
    if not message.photo:
        bot.send_message(message.chat.id, "Iltimos, chekni rasm sifatida yuboring.")
        return
    caption = f"🧾 Chek keldi!\n📞 {number}\n👤 @{message.from_user.username or message.from_user.first_name}\nID: {message.from_user.id}"
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{message.from_user.id}_{number}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{message.from_user.id}_{number}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=btn)
    bot.send_message(message.chat.id, "✅ Chekingiz yuborildi. Iltimos kuting.")

# === Admin tasdiqlashi yoki rad etishi ===
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data.startswith("reject_"))
def admin_decision(call):
    parts = call.data.split("_")
    action, user_id, number = parts[0], int(parts[1]), parts[2]
    if action == "confirm":
        bot.send_message(user_id, f"✅ To‘lov tasdiqlandi!\n📞 {number}")
    else:
        bot.send_message(user_id, f"❌ To‘lov rad etildi.")
    bot.answer_callback_query(call.id, "Xabar yuborildi.")

# === Admin panel ===
@bot.message_handler(func=lambda m: m.text == "⚙️ Admin panel" and m.from_user.id == ADMIN_ID)
def admin_panel(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("➕ Raqam qo‘shish", "➖ Raqam o‘chirish", "📂 Raqamlar ro‘yxati", "💳 Karta o‘zgarishi", "⬅️ Orqaga")
    bot.send_message(message.chat.id, "Admin panelga xush kelibsiz!", reply_markup=markup)

# === Admin: Raqam qo‘shish ===
@bot.message_handler(func=lambda m: m.text == "➕ Raqam qo‘shish" and m.from_user.id == ADMIN_ID)
def add_number(message):
    bot.send_message(message.chat.id, "Format: `raqam | narx | tur (uzbek/foreign)`", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_number)

def save_number(message):
    try:
        number, price, category = [x.strip() for x in message.text.split("|")]
        numbers_table.insert({"number": number, "price": price, "category": category})
        bot.send_message(message.chat.id, f"✅ {number} qo‘shildi.")
    except:
        bot.send_message(message.chat.id, "❌ Format xato.")

# === Admin: Raqam o‘chirish ===
@bot.message_handler(func=lambda m: m.text == "➖ Raqam o‘chirish" and m.from_user.id == ADMIN_ID)
def delete_number(message):
    bot.send_message(message.chat.id, "O‘chirmoqchi bo‘lgan raqamni yozing:")
    bot.register_next_step_handler(message, remove_number)

def remove_number(message):
    removed = numbers_table.remove(Query().number == message.text.strip())
    if removed:
        bot.send_message(message.chat.id, "✅ O‘chirildi.")
    else:
        bot.send_message(message.chat.id, "❌ Topilmadi.")

# === Admin: Raqam ro‘yxati ===
@bot.message_handler(func=lambda m: m.text == "📂 Raqamlar ro‘yxati" and m.from_user.id == ADMIN_ID)
def list_numbers(message):
    all_numbers = numbers_table.all()
    if not all_numbers:
        bot.send_message(message.chat.id, "Raqamlar yo‘q.")
        return
    text = "📋 Barcha raqamlar:\n\n"
    for item in all_numbers:
        text += f"📞 {item['number']} — {item['price']} so‘m ({item['category']})\n"
    bot.send_message(message.chat.id, text)

# === Admin: Karta ma’lumotini yangilash ===
@bot.message_handler(func=lambda m: m.text == "💳 Karta o‘zgarishi" and m.from_user.id == ADMIN_ID)
def update_card(message):
    bot.send_message(message.chat.id, "Format: `raqam | ism familiya`", parse_mode="Markdown")
    bot.register_next_step_handler(message, save_card)

def save_card(message):
    try:
        card, name = [x.strip() for x in message.text.split("|")]
        settings_table.truncate()
        settings_table.insert({"card_number": card, "card_name": name})
        bot.send_message(message.chat.id, "✅ Karta ma’lumotlari yangilandi.")
    except:
        bot.send_message(message.chat.id, "❌ Format xato.")

# === Webhook ===
@app.route('/', methods=['POST'])
def webhook():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])
    return 'ok', 200

if __name__ == "__main__":
    bot.remove_webhook()
    bot.set_webhook(url=WEBHOOK_URL)
    app.run(host="0.0.0.0", port=10000)
