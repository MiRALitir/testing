from telethon.tl.types import InputMediaPhoto, InputMediaDocument
from telethon import TelegramClient
import sqlite3
import asyncio
import logging

# تنظیمات لاگینگ
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

API_ID = 21266027
API_HASH = '8563c2456fa80793ccf835eec5be4a72'
SESSION_NAME = '989169713311.session'

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# اتصال به دیتابیس
try:
    conn = sqlite3.connect('requests.db')
    cursor = conn.cursor()
    logger.info("اتصال به دیتابیس برقرار شد.")
except sqlite3.Error as e:
    logger.error(f"خطا در اتصال به دیتابیس: {e}")
    exit()


async def process_requests():
    while True:
        cursor.execute("SELECT id, user_id, link FROM requests WHERE status = 'pending'")
        requests = cursor.fetchall()

        for req_id, user_id, link in requests:
            logger.info(f"پردازش درخواست {req_id}: کاربر {user_id}, لینک {link}")
            try:
                # استخراج شناسه پیام از لینک
                if "t.me" in link:
                    post_id = link.split('/')[-1]
                    channel_username = link.split('/')[3]  # کانال

                    logger.info(f"شناسه پیام: {post_id}, نام کانال: {channel_username}")
                    try:
                        # دریافت پیام از کانال
                        message = await client.get_messages(channel_username, ids=int(post_id))

                        if message:
                            # ارسال محتوای پیام به کاربر
                            if message.text:
                                await client.send_message(user_id, f"📜 متن پیام:\n{message.text}")
                            if message.photo:
                                await client.send_file(user_id, message.photo)
                            if message.video:
                                await client.send_file(user_id, message.video)
                            if message.audio:
                                await client.send_file(user_id, message.audio)
                            if message.document:
                                await client.send_file(user_id, message.document)
                            logger.info(f"محتوای پیام با موفقیت برای کاربر {user_id} ارسال شد.")
                            cursor.execute("UPDATE requests SET status = 'processed' WHERE id = ?", (req_id,))
                        else:
                            logger.warning(f"لینک {link} پیام معتبری ندارد.")
                            cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))

                    except Exception as e:
                        logger.error(f"خطا در پردازش لینک {link}: {e}")
                        cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))
                        await client.send_message(user_id, "❌ خطا در دریافت پیام.")

                else:
                    logger.error(f"لینک غیرمعتبر: {link}")
                    cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))

            except Exception as e:
                logger.error(f"خطا در پردازش درخواست {req_id}: {e}")
                cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))

        conn.commit()
        await asyncio.sleep(5)

with client:
    try:
        logger.info("شروع کلاینت تلگرام...")
        client.loop.run_until_complete(process_requests())
    except Exception as e:
        logger.critical(f"خطا در اجرای کلاینت: {e}")
