from telethon import TelegramClient
from telebot import TeleBot
import sqlite3
import asyncio
import logging
import os
import aiohttp

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# تنظیمات ربات و API
API_ID = 21266027
API_HASH = '8563c2456fa80793ccf835eec5be4a72'
SESSION_NAME = '989169713311.session'
BOT_TOKEN = '7656738137:AAFJVHFXgdLn5d20lDQFzRylsnDapur6xuE'

# اتصال به دیتابیس
conn = sqlite3.connect('requests.db', check_same_thread=False)
cursor = conn.cursor()

# ساخت جدول در صورت عدم وجود
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

# مسیر ذخیره‌سازی موقت فایل‌ها
TEMP_DIR = 'temp_downloads'
os.makedirs(TEMP_DIR, exist_ok=True)

# ایجاد کلاینت‌های Telethon و TeleBot
client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
bot = TeleBot(BOT_TOKEN)

# ارسال پیام یا فایل به کاربر
async def send_to_bot(user_id, text=None, file_path=None):
    if text:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
        data = {'chat_id': user_id, 'text': text}
    else:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument"
        data = aiohttp.FormData()
        data.add_field('chat_id', str(user_id))
        data.add_field('document', open(file_path, 'rb'))

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, data=data) as resp:
                if resp.status == 200:
                    logger.info(f"محتوا با موفقیت به ربات ارسال شد برای کاربر {user_id}.")
                else:
                    logger.error(f"خطا در ارسال به ربات برای کاربر {user_id}: {resp.status}")
        except Exception as e:
            logger.error(f"خطا در ارتباط با ربات: {e}")

# دانلود و ارسال مدیا
async def download_and_send_media(message, user_id):
    try:
        file_path = await message.download_media(file=TEMP_DIR)
        if file_path:
            await send_to_bot(user_id, file_path=file_path)
            os.remove(file_path)
    except Exception as e:
        logger.error(f"خطا در دانلود و ارسال مدیا: {e}")

# پردازش درخواست‌ها
async def process_requests():
    while True:
        cursor.execute("SELECT id, user_id, link FROM requests WHERE status = 'pending'")
        requests = cursor.fetchall()

        for req_id, user_id, link in requests:
            logger.info(f"پردازش درخواست {req_id}: کاربر {user_id}, لینک {link}")
            try:
                if "t.me/c/" in link:
                    parts = link.split('/')
                    channel_id = int("-100" + parts[4])
                    post_id = int(parts[5])
                    logger.info(f"شناسه پیام: {post_id}, آیدی عددی کانال: {channel_id}")
                    message = await client.get_messages(channel_id, ids=post_id)
                else:
                    parts = link.split('/')
                    channel_username = parts[3]
                    post_id = int(parts[4])
                    logger.info(f"شناسه پیام: {post_id}, نام کانال: {channel_username}")
                    message = await client.get_messages(channel_username, ids=post_id)

                if message:
                    if message.text:
                        await send_to_bot(user_id, text=message.text)
                    if message.media:
                        await download_and_send_media(message, user_id)

                    logger.info(f"محتوای پیام با موفقیت برای کاربر {user_id} ارسال شد.")
                    cursor.execute("UPDATE requests SET status = 'processed' WHERE id = ?", (req_id,))
                else:
                    logger.warning(f"لینک {link} پیام معتبری ندارد.")
                    cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))

            except Exception as e:
                logger.error(f"خطا در پردازش لینک {link}: {e}")
                cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))
                await send_to_bot(user_id, text="\u274C خطا در دریافت پیام.")

        conn.commit()
        await asyncio.sleep(5)

# مدیریت پیام‌های TeleBot
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

# اجرای هم‌زمان کلاینت‌ها
async def main():
    async with client:
        # شروع ربات تلگرام
        await asyncio.gather(process_requests(), bot.polling())

if __name__ == "__main__":
    asyncio.run(main())
