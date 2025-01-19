import random
import sqlite3
import string

from config import api_hash, api_id, token
from telethon import Button, TelegramClient, events
from telethon.tl.custom.message import Message

conn = sqlite3.connect('poster.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    number TEXT,
    points INTEGER DEFAULT 50,
    referral_code TEXT,
    referrer_id INTEGER,
    posts INTEGER DEFAULT 0
);
""")
conn.commit()

bot = TelegramClient('shadow_poster', api_id, api_hash).start(bot_token=token)

def generate_referral_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

async def get_bot_username():
    bot_user = await bot.get_me()
    return bot_user.username

@bot.on(events.NewMessage(pattern='/start'))
async def start(event: Message):
    user_id = event.sender_id
    username = event.sender.username or "بدون نام"

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()

    if user:
        await event.reply("👋 شما قبلاً ثبت‌نام کرده‌اید! از امکانات ربات استفاده کنید.")
        return

    referral_code = None
    if len(event.message.text.split()) > 1:
        referral_code = event.message.text.split()[1]

    referrer_id = None
    if referral_code:
        cursor.execute("SELECT id FROM users WHERE referral_code = ?", (referral_code,))
        referrer = cursor.fetchone()
        if referrer:
            referrer_id = referrer[0]

    buttons = [[Button.request_phone('اشتراک‌گذاری شماره موبایل 📞', resize=True, selective=True, single_use=True)]]
    await event.respond(
        "👋 خوش آمدید!\nلطفاً شماره موبایل خود را برای شروع به اشتراک بگذارید.",
        buttons=buttons
    )

    new_referral_code = generate_referral_code()
    cursor.execute("""
        INSERT INTO users (id, username, referral_code, referrer_id)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(id) DO NOTHING;
    """, (user_id, username, new_referral_code, referrer_id))
    conn.commit()

    if referrer_id:
        cursor.execute("UPDATE users SET points = points + 5 WHERE id = ?", (referrer_id,))
        conn.commit()

@bot.on(events.NewMessage(func=lambda e: e.contact))
async def handle_contact(event: Message):
    user_id = event.sender_id
    username = event.sender.username or "بدون نام"
    number = event.contact.phone_number

    cursor.execute("UPDATE users SET number = ? WHERE id = ?", (number, user_id))
    conn.commit()

    await event.reply("✅ شماره موبایل شما با موفقیت ثبت شد! اکنون ۵۰ امتیاز به حساب شما افزوده شد.\nبرای شروع، دستور /post را وارد کنید.")

@bot.on(events.NewMessage(pattern='/referral'))
async def referral_link(event: Message):
    user_id = event.sender_id

    cursor.execute("SELECT referral_code FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        referral_code = result[0]
        bot_username = await get_bot_username()
        referral_link = f"https://t.me/{bot_username}?start={referral_code}"
        await event.reply(f"کد رفرال اختصاصی شما: {referral_code}\nبرای دعوت از دوستان خود، از لینک زیر استفاده کنید:\n{referral_link}")
    else:
        await event.reply("شما هنوز ثبت‌نام نکرده‌اید. لطفاً ابتدا دستور /start را وارد کنید.")

@bot.on(events.NewMessage(pattern='/referrals'))
async def show_referrals(event: Message):
    user_id = event.sender_id

    cursor.execute("""
        SELECT username FROM users
        WHERE referrer_id = ?;
    """, (user_id,))
    referrals = cursor.fetchall()

    if referrals:
        referral_list = "\n".join([f"- {referral[0]}" for referral in referrals])
        await event.reply(f"کاربران معرفی‌شده توسط شما:\n{referral_list}")
    else:
        await event.reply("شما هنوز هیچ کاربری را معرفی نکرده‌اید.")

@bot.on(events.NewMessage(pattern='/points'))
async def show_points(event: Message):
    user_id = event.sender_id

    cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        points = result[0]
        await event.reply(f"امتیازات فعلی شما: {points} امتیاز")
    else:
        await event.reply("شما هنوز ثبت‌نام نکرده‌اید. لطفاً ابتدا دستور /start را وارد کنید.")

print("✅ Bot is running...")
bot.run_until_disconnected()