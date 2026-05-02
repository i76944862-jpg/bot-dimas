import telebot
import random
import json
import os
from datetime import datetime, timedelta

# ================= CONFIG =================
TOKEN = "8254564948:AAE3Amva6Gw6GCRbVUBu4L0F6X60K6ZR7Wo"  # ⚠️ GANTI DENGAN TOKEN BARU
ADMIN_ID = 6938192333

bot = telebot.TeleBot(TOKEN)

# ================= DATABASE =================
DATA_FILE = "users.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({"approved": []}, f)

def load_users():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"approved": []}

def save_users(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

users = load_users()

# ================= MARKETS =================
markets = {
    "crypto": "🪙 Crypto IDX",
    "eurusd": "🇪🇺🇺🇸 EUR/USD",
    "audusd": "🇦🇺🇺🇸 AUD/USD",
    "sgdjpy": "🇸🇬🇯🇵 SGD/JPY",
    "eurhuf": "🇪🇺🇭🇺 EUR/HUF",
    "usdmxn": "🇺🇸🇲🇽 USD/MXN"
}

active_signals = {}

# ================= SIGNAL =================
def generate_signal():
    return random.choice(["BUY 🟢", "SELL 🔴"])

def get_signal(market_key):
    now = datetime.utcnow() + timedelta(hours=7)

    if market_key in active_signals:
        saved = active_signals[market_key]
        if now < saved["entry_time"]:
            return saved

    entry_time = now + timedelta(minutes=5)

    new_signal = {
        "direction": generate_signal(),
        "entry_time": entry_time
    }

    active_signals[market_key] = new_signal
    return new_signal

# ================= START =================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id

    if user_id not in users["approved"]:
        markup = telebot.types.InlineKeyboardMarkup()
        btn = telebot.types.InlineKeyboardButton(
            "🔐 REQUEST ACCESS",
            callback_data="request_access"
        )
        markup.add(btn)

        bot.send_message(
            message.chat.id,
            "🔒 PRIVATE BOT\n\nKlik tombol untuk request akses.",
            reply_markup=markup
        )
        return

    show_markets(message.chat.id)

# ================= SHOW MARKETS =================
def show_markets(chat_id):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2)

    buttons = []
    for key, name in markets.items():
        buttons.append(
            telebot.types.InlineKeyboardButton(name, callback_data=key)
        )

    markup.add(*buttons)

    bot.send_message(
        chat_id,
        "🔥 YOYO SIGNAL BOT 🔥\n\nPilih Market:",
        reply_markup=markup
    )

# ================= CALLBACK =================
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    user_id = call.from_user.id

    # REQUEST ACCESS
    if call.data == "request_access":
        username = call.from_user.username or "NoUsername"

        markup = telebot.types.InlineKeyboardMarkup()
        acc = telebot.types.InlineKeyboardButton("✅ ACC", callback_data=f"acc_{user_id}")
        reject = telebot.types.InlineKeyboardButton("❌ REJECT", callback_data=f"reject_{user_id}")
        markup.add(acc, reject)

        bot.send_message(
            ADMIN_ID,
            f"📢 REQUEST AKSES\n\nID: {user_id}\nUsername: @{username}",
            reply_markup=markup
        )

        bot.answer_callback_query(call.id, "Request dikirim ke admin ✅")
        return

    # ADMIN ACC
    if call.data.startswith("acc_") and user_id == ADMIN_ID:
        target_id = int(call.data.split("_")[1])

        if target_id not in users["approved"]:
            users["approved"].append(target_id)
            save_users(users)

        bot.send_message(target_id, "✅ AKSES ANDA DISETUJUI")
        bot.edit_message_text("✅ User sudah di-ACC", call.message.chat.id, call.message.message_id)
        return

    # ADMIN REJECT
    if call.data.startswith("reject_") and user_id == ADMIN_ID:
        target_id = int(call.data.split("_")[1])

        bot.send_message(target_id, "❌ AKSES ANDA DITOLAK")
        bot.edit_message_text("❌ User ditolak", call.message.chat.id, call.message.message_id)
        return

    # SIGNAL
    if user_id not in users["approved"]:
        bot.answer_callback_query(call.id, "❌ Anda belum memiliki akses")
        return

    try:
        bot.answer_callback_query(call.id, "⏳ Generating signal...")

        signal = get_signal(call.data)
        market_name = markets.get(call.data, "Unknown Market")
        entry_str = signal["entry_time"].strftime("%H:%M")

        text = (
            f"{signal['direction']} {entry_str}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"{market_name}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "⚠️ MAXIMAL K2 | KOMPENSASI SEARAH\n"
            "⚠️ LIHAT JAM DI GMT+7\n"
            "⚠️ ENTRY -1 MENIT SEBELUM SIGNAL\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "©️ YOYO SIGNAL BOT"
        )

        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=text
        )

    except Exception as e:
        print("ERROR:", e)

# ================= RUN =================
print("🤖 Bot running...")
bot.infinity_polling(skip_pending=True)
