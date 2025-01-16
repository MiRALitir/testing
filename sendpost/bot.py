from telebot import TeleBot
import sqlite3

BOT_TOKEN = '7656738137:AAFJVHFXgdLn5d20lDQFzRylsnDapur6xuE'
bot = TeleBot(BOT_TOKEN)

# اتصال به دیتابیس
conn = sqlite3.connect('requests.db', check_same_thread=False)
cursor = conn.cursor()

# ساخت جدول اگر وجود ندارد
cursor.execute("""
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    link TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
conn.commit()

@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "سلام! لینک پست را با دستور /getpost ارسال کنید.")

@bot.message_handler(commands=['getpost'])
def get_post(message):
    bot.send_message(message.chat.id, "لینک پست را ارسال کنید:")
    bot.register_next_step_handler(message, save_request)

def save_request(message):
    link = message.text
    cursor.execute("INSERT INTO requests (user_id, link, status) VALUES (?, ?, ?)", 
                   (message.chat.id, link, 'pending'))
    conn.commit()
    bot.send_message(message.chat.id, "درخواست شما ثبت شد و در حال پردازش است.")

bot.polling()
