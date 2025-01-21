import json
import os
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

bot = TelegramClient('shadowbyte', api_id=api_id, api_hash=api_hash).start(bot_token=token)

ADMIN_IDS = admin_ids

@bot.on(events.NewMessage(pattern=r'/start'))
async def start(event: Message):
    msg = '''درود کاربر گرامی به ربات ثبت سفارش شدو بایت خوش اومدید
این ربات برای ثبت سفارش ساخت ربات تلگرام از مجموعه @MiRALi_SHOP_OG ساخته شده .
برای دریافت راهنمایی بیشتر درمورد ربات ، میتونید از بخش راهنما استفاده کنید !
'''
    btn = [
        [Button.text('ثبت سفارش 📝', resize=True, single_use=True)],
        [Button.text('سفارشات 📄'), Button.text('مشخصات من 🔍')],
        [Button.text('💡راهنما'), Button.text('سوالات متداول ⚖️')],
        [Button.text('☎️ پشتیبانی')]
    ]
    await bot.send_message(entity=event.chat_id, message=msg, buttons=btn)


@bot.on(events.NewMessage)
async def start_handler(event: Message):
    text = event.message.text
    user_id = event.sender_id
    
    full_user = await event.client(GetFullUserRequest(user_id))
    user = full_user.users[0]
    username = user.username or "ندارد"
    fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
    bio = full_user.full_user.about or "ندارد"
    photos = await bot.get_profile_photos(user_id)
    if photos:
        profile_photo = photos[0]
    
    if text == 'ثبت سفارش 📝':
        
        order_btn = [
            [Button.inline("ادامه ✅", data='continue_create_order')],
            [Button.inline("بازگشت", data='back'), Button.inline("سوالات متداول", data='questions')]
        ]
        
        create_order = await bot.send_message(entity=event.chat_id, message='اینجا بخش ثبت سفارش رباته \nبرای ادامه فرایند روی دکمه ادامه کلیک کنید \nدر غیر این صورت روی بازگشت کلیک کنید', buttons=order_btn)

    elif text == 'مشخصات من 🔍':
        
        profile_msg = (f"👤 اطلاعات شما:\n"
           f"🔑 آیدی عددی: {user_id}\n"
           f"💛 یوزرنیم: {username}\n"
           f"👥 نام کامل: {fullname}\n"
           f"📝 بیو: {bio}\n"
           f"🖼️ تصویر پروفایل: {'دارد' if photos else 'ندارد'}\n"
           "تعداد سفارشات ثبت شده : {count}")
        
        back_btn = [
            [Button.inline("بازگشت", data='back')]
        ]
        
        await bot.send_file(entity=event.chat_id, file=profile_photo, caption=profile_msg, buttons=back_btn)
    
    # elif text == 'سفارشات 📄':
            
    #     full_user = await event.client(GetFullUserRequest(user_id))
    #     user_id = event.sender_id
    #     fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()
    
    #     orders_msg = (f"کاربر گرامی <a href='tg://user?id={user_id}'>{fullname}<a>\n"
    #         f"تعداد سفارشات ثبت شده توسط شما : {تعداد سفارشات همون کاربر} است\n"
    #         f"تعداد سفارشات پذیرفته شده : {تعداد سفارشات تایید شده توسط ادمین}\n"
    #         f"تعداد سفارشات رد شده : {تعداد سفارشات رد شده}"
    #     )


questions = [
    "تمام ویژگی‌های رباتی که قصد سفارشش رو دارید رو در قالب یک پیام ارسال کنید.\n❗️ لطفاً خودتون توضیح بدید، ادمین مجموعه به صورت خودکار بررسی نمی‌کند.",
    "نیاز به پنل ادمین درون ربات دارین یا خیر؟ (روی قیمت ربات تأثیر مستقیم خواهد داشت) ⁉️",
    "در مورد ساخت ربات از بات فادر (دریافت API Token و ...) اطلاع دارین؟ ⁉️",
    "ربات رو می‌تونید روی هاست یا سرور اجرا کنید؟ ‼️",
    "هاست یا سرور رو از مجموعه ما می‌خرید؟",
    "سورس کد رو دریافت می‌کنید یا که خود ادمین ربات رو برای شما اجرا کنه؟",
    "نوع پرداخت رو هم مشخص کنید (ارزی یا تومانی) ❗"
]

def ensure_orders_directory():
    """ایجاد پوشه orders در صورت عدم وجود."""
    if not os.path.exists("orders"):
        os.makedirs("orders")

def save_order_data(user_id, data):
    """ذخیره اطلاعات سفارش به صورت JSON."""
    ensure_orders_directory()
    with open(f"orders/{user_id}_order.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def delete_order_data(user_id):
    """حذف فایل سفارش کاربر پس از اتمام."""
    file_path = f"orders/{user_id}_order.json"
    if os.path.exists(file_path):
        os.remove(file_path)

@bot.on(events.CallbackQuery)
async def callback(event):
    if event.data == b'continue_create_order':
        user_id = event.sender_id
        user_data = {"step": 0, "answers": []}
        save_order_data(user_id, user_data)

        buttons = [[Button.inline("بازگشت ↩️", data="back")]]
        await event.edit("ثبت سفارش شروع شد.\n" + questions[0], buttons=buttons)

    elif event.data == b'back':
        await event.delete() 
        await start(event) 

@bot.on(events.NewMessage)
async def process_order(event):
    user_id = event.sender_id
    try:
        with open(f"orders/{user_id}_order.json", "r", encoding="utf-8") as f:
            user_data = json.load(f)
    except FileNotFoundError:
        return

    if user_data["step"] < len(questions):
        user_data["answers"].append(event.message.text)
        user_data["step"] += 1

        save_order_data(user_id, user_data)

        if user_data["step"] < len(questions):
            buttons = [[Button.inline("بازگشت ↩️", data="back")]]
            await event.reply(questions[user_data["step"]], buttons=buttons)
        else:
            order_details = "\n".join([f"سوال {i + 1}: {answer}" for i, answer in enumerate(user_data["answers"])])
            for admin_id in ADMIN_IDS:
                await bot.send_message(admin_id, f"یک سفارش جدید از کاربر {user_id} دریافت شد:\n{order_details}")

            await event.reply("سفارش شما با موفقیت ثبت شد! ✅")

            delete_order_data(user_id)


print('RUN')
bot.run_until_disconnected()