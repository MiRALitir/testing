import sqlite3
import time

from config import admin_id, api_hash, api_id, token
from telethon import Button, TelegramClient, events
# from telethon.tl.functions.photos import GetProfilePhotos
from telethon.tl.functions.users import GetFullUserRequest

conn = sqlite3.connect('poster.db', check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT,
    number TEXT,
    fullname TEXT,
    bio TEXT,
    profile_photo_id TEXT,
    request_count INTEGER DEFAULT 0,
    last_active INTEGER DEFAULT NULL
);
""")
conn.commit()

bot = TelegramClient('posting', api_id, api_hash).start(bot_token=token)

@bot.on(events.NewMessage(pattern=r'/start'))
async def start(event):
    await event.reply("سلام! به ربات خوش آمدید. دستور /myid را برای شروع ارسال کنید.")

@bot.on(events.NewMessage(pattern=r'/help'))
async def show_help(event):
    user_id = event.sender_id
    if user_id == admin_id:
        help_message = """
🛠 **راهنمای دستورات ربات:**
🔹 **دستورات کاربران:**
/start - شروع ربات
/help - مشاهده راهنما

🔹 **دستورات ادمین‌ها:**
/usercount - نمایش تعداد کاربران ثبت‌شده
/broadcast - ارسال پیام به همه کاربران
/cleanup - حذف کاربران غیرفعال
/inactive - مشاهده کاربران غیرفعال
/search <username> - جستجوی کاربران بر اساس یوزرنیم
"""
        await event.reply(help_message)
    else:
        help_message = "این ربات برای ثبت اطلاعات شما ساخته شده است. برای شروع، دستور /start را ارسال کنید."
        await event.reply(help_message)

@bot.on(events.NewMessage(pattern=r'/myid'))
async def myid(event):
    user_id = event.sender_id

    # بررسی وجود کاربر در پایگاه داده
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    db_user = cursor.fetchone()

    if not db_user:
        # درخواست شماره تلفن از کاربر
        btn = [[Button.request_phone('ارسال شماره تلفن', single_use=True)]]
        await event.reply("برای استفاده از این ربات ابتدا باید شماره تلفن خود را ارسال کنید.", buttons=btn)
        return

    # دریافت اطلاعات کامل کاربر از طریق Telethon
    full_user = await event.client(GetFullUserRequest(user_id))
    user = full_user.users[0]  # دسترسی به اولین کاربر موجود در UserFull
    username = user.username or "ندارد"
    bio = full_user.full_user.about or "ندارد"  # دسترسی به بیو
    fullname = f"{user.first_name or ''} {user.last_name or ''}".strip()

    # بررسی تغییرات در یوزرنیم
    if db_user[1] != username:
        old_username = db_user[1] or "ندارد"
        cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
        conn.commit()

        report = (f"🚨 تغییر یوزرنیم کاربر:\n"
                  f"🔑 آیدی عددی: {user_id}\n"
                  f"💛 تغییر یافته از: {old_username}\n"
                  f"➡️ به: {username}\n")
        await bot.send_message(admin_id, report)

    # به‌روزرسانی تعداد درخواست‌ها
    request_count = db_user[6] + 1
    cursor.execute("UPDATE users SET request_count = ? WHERE id = ?", (request_count, user_id))
    conn.commit()

    # دریافت تصویر پروفایل
    photos = await bot.get_profile_photos(user_id)
    profile_photo_id = photos[0].id if photos else "ندارد"

    if db_user[5] != profile_photo_id:
        cursor.execute("UPDATE users SET profile_photo_id = ? WHERE id = ?", (profile_photo_id, user_id))
        conn.commit()

    # ساخت پیام پاسخ
    msg = (f"👤 اطلاعات شما:\n"
           f"🔑 آیدی عددی: {user_id}\n"
           f"💛 یوزرنیم: {username}\n"
           f"📞 شماره: {db_user[2]}\n"
           f"👥 نام کامل: {fullname}\n"
           f"📝 بیو: {bio}\n"
           f"🖼️ تصویر پروفایل: {'دارد' if photos else 'ندارد'}\n"
           f"🔢 تعداد درخواست‌ها: {request_count}")
    await event.reply(msg)

@bot.on(events.NewMessage(func=lambda e: e.is_private, incoming=True))
async def handle_contact(event):
    if event.contact and event.contact.phone_number:
        user_id = event.sender_id
        number = event.contact.phone_number
        fullname = f"{event.contact.first_name} {event.contact.last_name or ''}".strip()
        
        cursor.execute("""
            INSERT INTO users (id, username, number, fullname, bio, profile_photo_id, request_count)
            VALUES (?, ?, ?, ?, ?, ?, 1)
            ON CONFLICT(id) DO UPDATE SET number = ?, fullname = ?, bio = ?, profile_photo_id = ?;
        """, (user_id, None, number, fullname, None, None, number, fullname, None, None))

        conn.commit()

        await event.reply("شماره شما با موفقیت ثبت شد. اکنون می‌توانید مجدداً دستور /myid را ارسال کنید.")
@bot.on(events.NewMessage(pattern=r'/admin'))
async def admin_panel(event):
    if event.sender_id == admin_id:
        buttons = [
            [Button.inline('ثبت اطلاعات کاربر', b'accept_user'), Button.inline('رد اطلاعات کاربر', b'reject_user')],
            [Button.inline('پیام به کاربر', b'message_user')]
        ]
        await event.reply("✅ بخش مدیریت", buttons=buttons)
    else:
        await event.reply("شما دسترسی ادمین ندارید.")

@bot.on(events.CallbackQuery())
async def callback_handler(event):
    data = event.data.decode('utf-8')
    user_id = event.sender_id

    if data == 'accept_user':
        cursor.execute("UPDATE users SET request_count = request_count + 1 WHERE id = ?", (user_id,))
        conn.commit()
        await event.respond("اطلاعات کاربر ثبت شد.", alert=True)

    elif data == 'reject_user':
        await bot.send_message(user_id, "اطلاعات شما مورد پذیرش قرار نگرفت.")
        await event.respond("اطلاعات کاربر رد شد.", alert=True)

    elif data == 'message_user':
        await bot.send_message(admin_id, "پیام خود را وارد کنید و ارسال نمایید.")
        @bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id == admin_id))
        async def admin_message(event):
            message = event.raw_text
            await bot.send_message(user_id, f"پیام از ادمین: {message}")
            await bot.send_message(admin_id, "پیام شما ارسال شد.")

@bot.on(events.NewMessage(pattern=r'/usercount'))
async def user_count(event):
    if event.sender_id == admin_id:
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        await event.reply(f"👥 تعداد کاربران ثبت‌شده: {count}")
    else:
        await event.reply("❌ شما دسترسی ادمین ندارید.")

broadcast_listener = None

@bot.on(events.NewMessage(pattern=r'/broadcast'))
async def broadcast_message(event):
    if event.sender_id == admin_id:
        await event.reply("📝 لطفاً پیام خود را وارد کنید:")
        
        global broadcast_listener

        if broadcast_listener is not None:
            return

        @bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id == admin_id))
        async def send_broadcast(event):
            message = event.raw_text
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()
            for user in users:
                try:
                    await bot.send_message(user[0], message)
                except Exception as e:
                    print(f"❌ ارسال پیام به کاربر {user[0]} با خطا مواجه شد: {e}")
            await event.reply("✅ پیام شما با موفقیت به تمامی کاربران ارسال شد.")

        broadcast_listener = send_broadcast


@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def save_user(event):
    user_id = event.sender_id
    username = event.sender.username
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
    conn.commit()

@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def update_last_active(event):
    user_id = event.sender_id
    last_active = int(time.time())
    cursor.execute("UPDATE users SET last_active = ? WHERE id = ?", (last_active, user_id))
    conn.commit()
    # await event.reply("✅ تاریخ آخرین فعالیت شما به‌روزرسانی شد.")

@bot.on(events.NewMessage(pattern=r'/inactive'))
async def show_inactive_users(event):
    if event.sender_id == admin_id:
        thirty_days_ago = int(time.time()) - (30 * 24 * 60 * 60)
        cursor.execute("SELECT id, username FROM users WHERE last_active < ?", (thirty_days_ago,))
        inactive_users = cursor.fetchall()
        if inactive_users:
            msg = "👥 کاربران غیرفعال:\n"
            for user in inactive_users:
                msg += f"🔑 آیدی عددی: {user[0]}, 💛 یوزرنیم: {user[1] or 'ندارد'}\n"
            await event.reply(msg)
        else:
            await event.reply("✅ هیچ کاربر غیرفعالی یافت نشد.")
    else:
        await event.reply("❌ شما دسترسی ادمین ندارید.")

@bot.on(events.NewMessage(func=lambda e: e.is_private))
async def save_user(event):
    user_id = event.sender_id
    username = event.sender.username
    cursor.execute("INSERT OR IGNORE INTO users (id, username) VALUES (?, ?)", (user_id, username))
    cursor.execute("UPDATE users SET username = ? WHERE id = ?", (username, user_id))
    conn.commit()

# @bot.on(events.NewMessage(func=lambda e: e.is_private))
# async def update_last_active(event):
#     user_id = event.sender_id
#     last_active = int(time.time())
#     cursor.execute("UPDATE users SET last_active = ? WHERE id = ?", (last_active, user_id))
#     conn.commit()
#     await event.reply("✅ تاریخ آخرین فعالیت شما به‌روزرسانی شد.")

print('Run')
bot.run_until_disconnected()