from telethon import TelegramClient
import sqlite3
import asyncio
import logging
import os
import aiohttp

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = 21266027
API_HASH = '8563c2456fa80793ccf835eec5be4a72'
SESSION_NAME = '989169713311.session'
BOT_TOKEN = '7656738137:AAFJVHFXgdLn5d20lDQFzRylsnDapur6xuE'

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# اتصال به دیتابیس
try:
    conn = sqlite3.connect('requests.db')
    cursor = conn.cursor()
    logger.info("اتصال به دیتابیس برقرار شد.")
except sqlite3.Error as e:
    logger.error(f"خطا در اتصال به دیتابیس: {e}")
    exit()

# مسیر ذخیره‌سازی موقت فایل‌ها
TEMP_DIR = 'temp_downloads'
os.makedirs(TEMP_DIR, exist_ok=True)

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

async def download_and_send_media(message, user_id):
    try:
        file_path = await message.download_media(file=TEMP_DIR)
        if file_path:
            await send_to_bot(user_id, file_path=file_path)
            os.remove(file_path)
    except Exception as e:
        logger.error(f"خطا در دانلود و ارسال مدیا: {e}")

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
                await send_to_bot(user_id, text="❌ خطا در دریافت پیام.")

        conn.commit()
        await asyncio.sleep(5)

with client:
    try:
        logger.info("شروع کلاینت تلگرام...")
        client.loop.run_until_complete(process_requests())
    except Exception as e:
        logger.critical(f"خطا در اجرای کلاینت: {e}")
