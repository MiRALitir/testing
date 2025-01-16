from telethon import TelegramClient
import sqlite3
import asyncio

API_ID = 21266027
API_HASH = '8563c2456fa80793ccf835eec5be4a72'
SESSION_NAME = '989169713311.session'

client = TelegramClient(SESSION_NAME, API_ID, API_HASH)

# اتصال به دیتابیس
conn = sqlite3.connect('requests.db')
cursor = conn.cursor()

async def process_requests():
    while True:
        # دریافت درخواست‌های منتظر پردازش
        cursor.execute("SELECT id, user_id, link FROM requests WHERE status = 'pending'")
        requests = cursor.fetchall()

        for req_id, user_id, link in requests:
            try:
                # دریافت پیام از لینک
                message = await client.get_messages(link)
                # ارسال پیام به کاربر
                await client.send_message(user_id, f"🔗 محتوای پست:\n{message.text}")
                # به‌روزرسانی وضعیت به 'processed'
                cursor.execute("UPDATE requests SET status = 'processed' WHERE id = ?", (req_id,))
            except Exception as e:
                # به‌روزرسانی وضعیت به 'failed'
                cursor.execute("UPDATE requests SET status = 'failed' WHERE id = ?", (req_id,))
                await client.send_message(user_id, "❌ خطا در دریافت پست.")
            
        conn.commit()
        await asyncio.sleep(5)  # بررسی درخواست‌ها هر 5 ثانیه

with client:
    client.loop.run_until_complete(process_requests())
