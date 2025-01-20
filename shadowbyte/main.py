import random
import sqlite3
import string

from config import *
from telethon import Button, TelegramClient, events
from telethon.errors import UserNotParticipantError
from telethon.tl.custom.message import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChannelParticipantsSearch

# راه‌اندازی ربات تلگرام
bot = TelegramClient('shadowbyte', api_id=api_id, api_hash=api_hash).start(bot_token=token)

# شناسه‌های مدیران
ADMIN_IDS = admin_ids

# اتصال به دیتابیس SQLite
conn = sqlite3.connect('orders.db')
cursor = conn.cursor()

# جدول ذخیره سفارشات
cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
                    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    order_status TEXT,
                    order_details TEXT
                 )''')
conn.commit()

# نمایش منوی اصلی
@bot.on(events.NewMessage(pattern=r'/start'))
async def start(event: Message):
    msg = '''درود کاربر گرامی به ربات ثبت سفارش شدو بایت خوش اومدید
این ربات برای ثبت سفارش ساخت ربات تلگرام از مجموعه @MiRALi_SHOP_OG ساخته شده . 
برای دریافت راهنمایی بیشتر درمورد ربات ، میتونید از بخش راهنما استفاده کنید !
'''
    btn = [
        [Button.text('ثبت سفارش 📝', resize=True, single_use=True)],
        [Button.text('سفارشات 📄'), Button.text('مشخصات من 🔍')],
        [Button.text('💡 راهنما'), Button.text('سوالات متداول ⚖️')],
        [Button.text('☎️ پشتیبانی')],
        [Button.force_reply(placeholder='MiRALi_OFFiCiAL |:')]
    ]
    await bot.send_message(entity=event.chat_id, message=msg, buttons=btn)

# ثبت سفارش جدید
@bot.on(events.NewMessage)
async def order_handler(event: Message):
    text = event.message.text
    
    full_user = await event.client(GetFullUserRequest(event.sender_id))
    user = full_user.users[0]
    username = user.username or "ندارد"
    fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
    
    # بررسی دستور ثبت سفارش
    if text == 'ثبت سفارش 📝':
        order_btn = [
            [Button.inline("ادامه ✅", data='continue')],
            [Button.inline("بازگشت", data='back')]
        ]
        await bot.send_message(entity=event.chat_id, message='اینجا بخش ثبت سفارش رباته \nبرای ادامه فرایند روی دکمه ادامه کلیک کنید \nدر غیر این صورت روی بازگشت کلیک کنید', buttons=order_btn)

    # نمایش مشخصات کاربر
    elif text == 'مشخصات من 🔍':
        profile_msg = (f"👤 اطلاعات شما:\n"
                       f"🔑 آیدی عددی: {event.sender_id}\n"
                       f"💛 یوزرنیم: {username}\n"
                       f"👥 نام کامل: {fullname}\n"
                       "تعداد سفارشات ثبت شده : {order_count}")
        
        back_btn = [
            [Button.inline("بازگشت", data='back')]
        ]
        
        await bot.send_message(entity=event.chat_id, message=profile_msg, buttons=back_btn)

    # نمایش سوالات متداول
    elif text == 'سوالات متداول ⚖️':
        faq_msg = '''سوالات متداول:
1. چطور می توانم سفارش ثبت کنم؟
2. قیمت‌گذاری به چه صورت است؟
3. نحوه پرداخت چگونه است؟
برای راهنمایی بیشتر به پشتیبانی مراجعه کنید.'''
        
        await bot.send_message(entity=event.chat_id, message=faq_msg)

    # مدیریت سفارشات
    elif text == 'سفارشات 📄':
        user_orders = get_user_orders(event.sender_id)
        if user_orders:
            orders_msg = "\n".join([f"📝 سفارش {order[0]} - وضعیت: {order[2]}" for order in user_orders])
            await bot.send_message(entity=event.chat_id, message=f"سفارشات شما:\n{orders_msg}")
        else:
            await bot.send_message(entity=event.chat_id, message="شما هنوز سفارشی ثبت نکرده‌اید.")
            
# دریافت سفارشات کاربر از دیتابیس
def get_user_orders(user_id):
    cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
    return cursor.fetchall()

# مدیریت دکمه‌های Inline
@bot.on(events.CallbackQuery)
async def callback_handler(event):
    if event.data == b'continue':
        await event.answer('ادامه ثبت سفارش...')
        # ادامه مراحل ثبت سفارش
        await bot.send_message(event.chat_id, "لطفا جزئیات سفارش خود را وارد کنید:")
        # فرض می‌کنیم جزئیات به صورت متنی از کاربر دریافت می‌شود.
        await event.client.send_message(event.chat_id, "جزئیات سفارش:")
    elif event.data == b'back':
        await event.answer('بازگشت به منوی اصلی...')
        # بازگشت به منوی اصلی
        await start(event)

# مدیریت درخواست پشتیبانی
@bot.on(events.NewMessage(pattern=r'/support'))
async def support_handler(event: Message):
    support_msg = '''برای پشتیبانی بیشتر با ما تماس بگیرید:
📧 ایمیل: support@mishop.com
💬 تلگرام: @MiRALiSupport'''
    
    await bot.send_message(event.chat_id, support_msg)

print('RUN')
bot.run_until_disconnected()