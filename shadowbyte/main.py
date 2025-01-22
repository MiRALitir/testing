import asyncio
import json
import os
import random
import sqlite3
import string
import time
from asyncio import sleep

from config import *
from telethon import Button, TelegramClient, events
from telethon.errors import UserNotParticipantError
from telethon.tl.custom.message import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import ChannelParticipantsSearch

bot = TelegramClient('shadowbyte', api_id=api_id, api_hash=api_hash).start(bot_token=token)

async def get_bot_username():
    bot_user = await bot.get_me()
    return bot_user.username

ADMIN_IDS = admin_ids

START_MSG = '''درود کاربر گرامی به ربات ثبت سفارش شدو بایت خوش اومدید
این ربات برای ثبت سفارش ساخت ربات تلگرام از مجموعه @MiRALi_SHOP_OG ساخته شده.
برای دریافت راهنمایی بیشتر درمورد ربات، میتونید از بخش راهنما استفاده کنید!'''

START_BTN = [
    [Button.text('ثبت سفارش 📝', resize=True, single_use=True)],
    [Button.text('سفارشات 📄'), Button.text('مشخصات من 🔍')],
    [Button.text('💡راهنما'), Button.text('سوالات متداول ⚖️')],
    [Button.text('☎️ پشتیبانی')]
]

@bot.on(events.NewMessage(pattern=r'/start'))
async def start(event):
    await bot.send_message(entity=event.chat_id, message=START_MSG, buttons=START_BTN)


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
        start_time = time.time()
    
        # ارسال پیام موقت
        processing_message = await event.reply("⏳ در حال پردازش اطلاعات شما... لطفاً صبر کنید.")

        try:
            await asyncio.sleep(2.5)

            profile_msg = (
                f"👤 اطلاعات شما:\n"
                f"🔑 آیدی عددی: <code>{user_id}</code>\n"
                f"💛 یوزرنیم: @{username}\n"
                f"👥 نام کامل: {fullname}\n"
                f"📝 بیو: {bio}\n"
                f"🖼️ تصویر پروفایل: {'دارد' if photos else 'ندارد'}\n"
                "تعداد سفارشات ثبت شده : {count}"  # متغیر count باید از دیتابیس یا فایل به دست بیاد
            )

            await processing_message.delete()
            
            await asyncio.sleep(0.5)

            await bot.send_file(entity=event.chat_id, file=profile_photo, caption=profile_msg, parse_mode='html')

        except Exception as e:
            await processing_message.edit(f"⚠️ خطایی رخ داد: {str(e)}")

        print(f"Time taken: {time.time() - start_time} seconds")

        
    elif text == 'سفارشات 📄':
        # start_time = time.time()
        # user_id = event.sender_id
        # full_user = await event.client(GetFullUserRequest(user_id))
        # user_id = event.sender_id
        # fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()

        # processing_message = await event.reply("⏳ در حال پردازش سفارشات شما... لطفاً صبر کنید.")

        # try:
        #     await asyncio.sleep(0.5)

        #     orders = [
        #         {"status": "پذیرفته شده", "details": "سفارش 1"},
        #         {"status": "رد شده", "details": "سفارش 2"},
        #         {"status": "در انتظار تایید", "details": "سفارش 3"}
        #     ]

        #     if orders:
        #         orders_text = "\n\n".join(
        #             [f"📄 {o['details']}\nوضعیت: {o['status']}" for o in orders]
        #         )
        #         final_message = (f"کاربر گرامی <a href='tg://user?id={user_id}'>{fullname}</a>\n📦 سفارشات شما:\n\n{orders_text}")
        #     else:
        #         final_message = "❌ شما هنوز هیچ سفارشی ثبت نکرده‌اید."

        #     await processing_message.edit(final_message, parse_mode='html')

        # except Exception as e:
        #     await processing_message.edit(f"⚠️ خطایی رخ داد: {str(e)}")

        # print(f"Time taken: {time.time() - start_time} seconds")
        await event.respond('این بخش موقتا از دسترس خارج شده')

    elif text == '💡راهنما':
        help_msg = (
            "💡 <b>راهنمای استفاده از ربات:</b>\n\n"
            "📌 <b>ثبت سفارش 📝:</b>\n"
            "از این بخش می‌توانید برای ثبت سفارش ساخت ربات تلگرام اقدام کنید. مراحل سفارش شامل پاسخ به چند سوال ساده است و در نهایت سفارش شما برای بررسی به ادمین ارسال می‌شود.\n\n"
            "📌 <b>سفارشات 📄:</b>\n"
            "در این بخش می‌توانید وضعیت سفارش‌های خود را مشاهده کنید. اطلاعاتی مانند جزئیات سفارش و وضعیت آن (پذیرفته شده، رد شده، یا در انتظار) نمایش داده خواهد شد.\n\n"
            "📌 <b>مشخصات من 🔍:</b>\n"
            "این بخش اطلاعات حساب کاربری شما مانند آیدی عددی، نام کاربری، نام کامل، بیو و وضعیت تصویر پروفایل را نمایش می‌دهد.\n\n"
            "📌 <b>💡 راهنما:</b>\n"
            "با انتخاب این گزینه می‌توانید اطلاعات کامل درباره ویژگی‌های ربات و نحوه استفاده از هر بخش را مطالعه کنید.\n\n"
            "📌 <b>سوالات متداول ⚖️:</b>\n"
            "سوالات پرتکرار و توضیحات مربوط به قوانین و شرایط استفاده از خدمات ما در این بخش قرار دارد.\n\n"
            "📌 <b>☎️ پشتیبانی:</b>\n"
            "اگر نیاز به راهنمایی بیشتر دارید یا سوال و پیشنهادی دارید، می‌توانید از این بخش با تیم پشتیبانی ارتباط برقرار کنید.\n\n"
            "🚀 <b>ویژگی‌های اصلی ربات:</b>\n"
            "✔️ ثبت سفارش سریع و ساده\n"
            "✔️ نمایش وضعیت سفارش‌ها\n"
            "✔️ مشاهده اطلاعات حساب کاربری\n"
            "✔️ پشتیبانی 24/7\n\n"
            "📩 برای شروع کافیست یکی از گزینه‌های موجود در منو را انتخاب کنید!"
        )
        
        await event.reply(help_msg, parse_mode='html')

    
    elif text == 'سوالات متداول ⚖️':
        question_btn = [
            [Button.url(text='ورود به بخش سوالات متداول', url='https://t.me/Miralishop')],
            [Button.inline(text='بازگشت 🔙', data='back')]
        ]
        await bot.send_message(
            entity=event.chat_id,
            message=('📔 به بخش سوالات متداول خوش اومدید \n'
                     '🌀برای دونستن قوانین و شرایط خرید از مجموعه ما روی دکمه زیر کلیک کنید و در غیر این صورت روی بازگشت کلیک کنید !'
            ),
            buttons=question_btn
        )
    
    elif text == '☎️ پشتیبانی':
        support_btn = [
            [Button.inline(text='گزارش ایراد ربات', )],
            [Button.inline(text='ارتباط با پشتیبانی')]
        ]
        
        supp = await bot.send_message(entity=event.chat_id,
                                    message='''🔰 کاربر گرامی به بخش پشتیبانی ربات خوش اومدی 

⚙️ اگر ربات ایرادی داره روی دکمه "گزارش ایراد ربات" کلیک کن 💎
📍 اگر حرف ، پیشنهاد یا انتقادی داری روی دکمه "ارتباط با پشتیبانی" کلیک کنی 💎''',
                                    buttons=support_btn
        )
        

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

@bot.on(events.CallbackQuery(data='back'))
async def back(event):
    await event.delete()
    
    await bot.send_message(event.chat_id, message=START_MSG, buttons=START_BTN)

print('RUN')
bot.run_until_disconnected()