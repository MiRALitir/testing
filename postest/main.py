import random
import sqlite3
import string

import telethon
from config import api_hash, api_id, token
from telethon import Button, TelegramClient, events
from telethon.errors import UserNotParticipantError
from telethon.tl.custom.message import Message
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.types import ChannelParticipantsSearch

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

cursor.execute("""
CREATE TABLE IF NOT EXISTS locked_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_username TEXT UNIQUE
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
        # اضافه کردن امتیاز به صاحب لینک
        cursor.execute("UPDATE users SET points = points + 5 WHERE id = ?", (referrer_id,))
        conn.commit()

        # ارسال پیام به صاحب لینک
        cursor.execute("SELECT username FROM users WHERE id = ?", (referrer_id,))
        referrer_username = cursor.fetchone()[0]
        await bot.send_message(
            referrer_id,
            f"🎉 کاربر جدید با یوزرنیم @{username} با لینک شما وارد شد!\n💰 به شما ۵ امتیاز تعلق گرفت."
        )

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

    if is_admin(user_id):
        await event.reply("شما ادمین هستید ، امتیاز شما نامحدود است 💎")
        return

    cursor.execute("SELECT points FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    if result:
        points = result[0]
        await event.reply(f"امتیازات فعلی شما: {points} امتیاز")
    else:
        await event.reply("شما هنوز ثبت‌نام نکرده‌اید. لطفاً ابتدا دستور /start را وارد کنید.")

ADMINS = [123456789, 6087657605]

def is_admin(user_id):
    return user_id in ADMINS

@bot.on(events.NewMessage(pattern='/admin_panel'))
async def admin_panel(event):
    user_id = event.sender_id

    if not is_admin(user_id):
        await event.reply("⛔ شما دسترسی به این دستور ندارید.")
        return

    # ایجاد پنل دکمه شیشه‌ای
    buttons = [
    [Button.inline("📋 لیست کاربران", b"list_users")],
    [Button.inline("👤 مشاهده امتیاز کاربر", b"view_points")],
    [Button.inline("📝 تغییر امتیاز کاربر", b"update_points")],
    [Button.inline("➕ افزودن کانال", b"add_channel")],
    [Button.inline("❌ حذف کانال", b"remove_channel")],
    [Button.inline("📋 مشاهده کانال‌ها", b"view_channels")]
    ]


    await event.reply("📊 پنل مدیریت:", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    data = event.data.decode("utf-8")

    # مدیریت هر دکمه
    if data == "list_users":
        cursor.execute("SELECT id, username, points FROM users;")
        users = cursor.fetchall()

        if users:
            user_list = "\n".join([f"""ID: `{user[0]}`\nUsername: `{user[1]}`\nPoints: {user[2]}\n-----------------""" for user in users])
            await event.edit(f"📋 لیست کاربران:\n{user_list}")
        else:
            await event.edit("📋 لیست کاربران خالی است.")

    elif data == "view_points":
        await event.edit("👤 لطفاً شناسه کاربر را ارسال کنید:")
        
        @bot.on(events.NewMessage(func=lambda e: e.sender_id == event.sender_id))
        async def get_user_id(msg_event):
            target_id = int(msg_event.text)
            cursor.execute("SELECT username, points FROM users WHERE id = ?", (target_id,))
            user = cursor.fetchone()

            if user:
                await msg_event.reply(f"👤 کاربر: @{user[0]}\n💰 امتیازات: {user[1]}")
            else:
                await msg_event.reply("❌ کاربر موردنظر یافت نشد.")
            bot.remove_event_handler(get_user_id)

    elif data == "update_points":
        await event.edit("📝 لطفاً شناسه کاربر و مقدار امتیاز را به این فرمت ارسال کنید:\n`user_id points_change`")

        @bot.on(events.NewMessage(func=lambda e: e.sender_id == event.sender_id))
        async def update_user_points(msg_event):
            args = msg_event.text.split()
            if len(args) < 2:
                await msg_event.reply("⚠️ فرمت نادرست است. لطفاً دوباره ارسال کنید.")
                return

            target_id = int(args[0])
            points_change = int(args[1])

            if is_admin(target_id):
                await msg_event.reply("❌ نمی‌توانید امتیازات ادمین را تغییر دهید.")
                return

            cursor.execute("SELECT points FROM users WHERE id = ?", (target_id,))
            user = cursor.fetchone()

            if user:
                new_points = user[0] + points_change
                cursor.execute("UPDATE users SET points = ? WHERE id = ?", (new_points, target_id))
                conn.commit()
                await msg_event.reply(f"""✅ امتیازات کاربر {target_id} 
امتیاز قبلی کاربر : {user[0]}                                      
💰 امتیاز جدید: {new_points}
میزان تغییر امتیاز : {points_change}
به‌روزرسانی شد.""")
            else:
                await msg_event.reply("❌ کاربر موردنظر یافت نشد.")
            bot.remove_event_handler(update_user_points)
    elif data == "add_channel":
        await event.edit("➕ لطفاً نام کاربری کانال را به این فرمت ارسال کنید:\n`@channel_username`")

        @bot.on(events.NewMessage(func=lambda e: e.sender_id == event.sender_id))
        async def add_channel_handler(msg_event):
            channel_username = msg_event.text.strip()

            if not channel_username.startswith("@"):
                await msg_event.reply("❌ فرمت نادرست است. لطفاً دوباره تلاش کنید.")
                return

            try:
                cursor.execute("INSERT INTO locked_channels (channel_username) VALUES (?)", (channel_username,))
                conn.commit()
                await msg_event.reply(f"✅ کانال {channel_username} با موفقیت اضافه شد.")
            except sqlite3.IntegrityError:
                await msg_event.reply("❌ این کانال قبلاً اضافه شده است.")
            bot.remove_event_handler(add_channel_handler)
        
    elif data == "remove_channel":
        await event.edit("❌ لطفاً نام کاربری کانال را برای حذف ارسال کنید:\n`@channel_username`")

        @bot.on(events.NewMessage(func=lambda e: e.sender_id == event.sender_id))
        async def remove_channel_handler(msg_event):
            channel_username = msg_event.text.strip()

            cursor.execute("DELETE FROM locked_channels WHERE channel_username = ?", (channel_username,))
            conn.commit()

            if cursor.rowcount > 0:
                await msg_event.reply(f"✅ کانال {channel_username} با موفقیت حذف شد.")
            else:
                await msg_event.reply("❌ کانال موردنظر یافت نشد.")
            bot.remove_event_handler(remove_channel_handler)
        
    elif data == "view_channels":
        cursor.execute("SELECT channel_username FROM locked_channels")
        channels = cursor.fetchall()

        if channels:
            channel_list = "\n".join([f"- {channel[0]}" for channel in channels])
            await event.edit(f"📋 لیست کانال‌های قفل‌شده:\n{channel_list}")
        else:
            await event.edit("📋 لیست کانال‌های قفل‌شده خالی است.")

@bot.on(events.NewMessage(pattern='/check_membership'))
async def check_user_membership(event):
    user_id = event.sender_id

    # بررسی عضویت کاربر
    is_member, missing_channels = await check_membership(user_id)

    if is_member:
        await event.reply("✅ شما در همه چنل‌های موردنظر عضو هستید.")
    else:
        channels_list = "\n".join([f"@{ch}" for ch in missing_channels])
        await event.reply(f"❌ شما در چنل‌های زیر عضو نیستید:\n{channels_list}\nلطفاً ابتدا عضو شوید.")

async def get_missing_channels_from_db(user_id):
    """
    بررسی عضویت کاربر در چنل‌های قفل‌شده که در دیتابیس تعریف شده‌اند.
    """
    missing_channels = []

    # گرفتن لیست چنل‌ها از دیتابیس
    cursor.execute("SELECT channel_username FROM locked_channels")
    channels = cursor.fetchall()

    for channel in channels:
        try:
            # بررسی عضویت کاربر در هر چنل
            await bot(GetParticipantRequest(channel[0], user_id))
        except UserNotParticipantError:
            # اگر کاربر عضو نبود، به لیست اضافه می‌شود
            missing_channels.append(channel[0])
        except Exception as e:
            print(f"Error checking channel {channel[0]}: {e}")

    return missing_channels


async def check_membership(user_id):
    """
    بررسی عضویت کاربر در تمام چنل‌ها و بازگرداندن اولین چنلی که عضو نیست.
    """
    missing_channels = await get_missing_channels_from_db(user_id)

    if missing_channels:
        # اگر چنل‌هایی وجود داشت که کاربر عضو نیست
        return False, missing_channels
    else:
        # اگر کاربر در همه چنل‌ها عضو بود
        return True, None

@bot.on(events.NewMessage(pattern='/post'))
async def post(event: Message):
    user_id = event.sender_id

    is_member, missing_channel = await check_membership(user_id)
    if not is_member:
        await event.reply(f"⛔ شما عضو کانال {missing_channel} نیستید. لطفاً ابتدا عضو شوید.")
        return

    # ادامه دستور /post
    await event.reply("✅ شما می‌توانید ادامه دهید.")

print("✅ Bot is running...")
bot.run_until_disconnected()