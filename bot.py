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
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def process_payment(call):
    number = call.data.split("_", 1)[1]
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    card = settings["card_number"]
    card_name = settings["card_name"]
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("📤 To‘lov qildim", callback_data=f"paid_{number}"))
    bot.send_message(call.message.chat.id,
        f"💳 To‘lov uchun karta:\n\n{card}\nIsm: {card_name}\n\nTo‘lovni amalga oshirgach 'To‘lov qildim' tugmasini bosing.",
        reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def ask_for_receipt(call):
    bot.send_message(call.message.chat.id, "🧾 Chek rasmini yuboring.")
    bot.register_next_step_handler(call.message, handle_receipt, call.data.split("_", 1)[1])

def handle_receipt(message, number):
    if not message.photo:
        bot.send_message(message.chat.id, "Iltimos, chek rasmini rasm sifatida yuboring.")
        return
    caption = f"🧾 Chek keldi!\n\n📞 Raqam: {number}\n👤 Foydalanuvchi: @{message.from_user.username or message.from_user.first_name}\nID: {message.from_user.id}"
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{message.from_user.id}_{number}"),
        types.InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{message.from_user.id}_{number}")
    )
    bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=caption, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_") or call.data.startswith("reject_"))
def handle_admin_action(call):
    parts = call.data.split("_")
    action, user_id, number = parts[0], int(parts[1]), parts[2]
    if action == "confirm":
        bot.send_message(user_id, f"✅ To‘lovingiz tasdiqlandi!\n📞 {number}")
    else:
        bot.send_message(user_id, f"❌ To‘lovingiz rad etildi. Iltimos, qayta urinib ko‘ring.")
    bot.answer_callback_query(call.id, "Xabar yuborildi.")
