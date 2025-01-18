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

    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    db_user = cursor.fetchone()

    if not db_user or not db_user[2]:
        btn = [[Button.request_phone('📞 ارسال شماره تلفن', single_use=True, resize=True)]]
        await event.reply("❗️ برای استفاده از این ربات ابتدا باید شماره تلفن خود را ارسال کنید.", buttons=btn)
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
    if photos:
        profile_photo = photos[0]  # آخرین تصویر پروفایل
        profile_photo_id = profile_photo.id
        if db_user[5] != profile_photo_id:
            cursor.execute("UPDATE users SET profile_photo_id = ? WHERE id = ?", (profile_photo_id, user_id))
            conn.commit()
    else:
        profile_photo = None

    # ساخت پیام پاسخ
    msg = (f"👤 اطلاعات شما:\n"
           f"🔑 آیدی عددی: {user_id}\n"
           f"💛 یوزرنیم: {username}\n"
           f"📞 شماره: {db_user[2]}\n"
           f"👥 نام کامل: {fullname}\n"
           f"📝 بیو: {bio}\n"
           f"🖼️ تصویر پروفایل: {'دارد' if photos else 'ندارد'}\n"
           f"🔢 تعداد درخواست‌ها: {request_count}")

    # ارسال پیام همراه با تصویر پروفایل (در صورت وجود)
    if profile_photo:
        await bot.send_file(event.chat_id, profile_photo, caption=msg)
    else:
        await event.reply("تصویر پروفایل موجود نیست.\n\n" + msg)

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

        await event.reply("✅ شماره شما با موفقیت ثبت شد. اکنون می‌توانید مجدداً دستور /myid را ارسال کنید.")

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
        await event.answer("اطلاعات کاربر ثبت شد.", alert=False)

    elif data == 'reject_user':
        await bot.send_message(user_id, "اطلاعات شما مورد پذیرش قرار نگرفت.")
        await event.answer("اطلاعات کاربر رد شد.", alert=False)

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

is_waiting_for_broadcast = False  # حالت انتظار برای پیام برودکست
broadcast_message_text = None    # ذخیره پیام برودکست

@bot.on(events.NewMessage(pattern=r'/broadcast'))
async def start_broadcast(event):
    global is_waiting_for_broadcast, broadcast_message_text

    if event.sender_id == admin_id:
        if is_waiting_for_broadcast:
            await event.reply("⚠️ شما در حال حاضر در حالت ارسال پیام برودکست هستید. لطفاً پیام خود را وارد کنید.")
            return

        await event.reply("📝 لطفاً پیام برودکست خود را وارد کنید:")
        is_waiting_for_broadcast = True
        broadcast_message_text = None  # ریست کردن پیام قبلی

@bot.on(events.NewMessage(func=lambda e: e.is_private and e.sender_id == admin_id and not e.raw_text.startswith('/')))
async def handle_broadcast(event):
    global is_waiting_for_broadcast, broadcast_message_text

    if is_waiting_for_broadcast:
        # ذخیره پیام برودکست
        if not broadcast_message_text:
            broadcast_message_text = event.raw_text
            # ارسال پیام تأیید با دکمه‌های شیشه‌ای
            buttons = [
                [Button.inline("✅ ارسال پیام", b'send_broadcast'), Button.inline("❌ لغو", b'cancel_broadcast')]
            ]
            await event.reply(f"📨 پیام برودکست:\n\n{broadcast_message_text}\n\nآیا این پیام ارسال شود؟", buttons=buttons)

@bot.on(events.CallbackQuery)
async def callback_handler(event):
    global is_waiting_for_broadcast, broadcast_message_text

    # چک کردن نوع کلیک
    if event.data == b'send_broadcast' and is_waiting_for_broadcast:
        try:
            # ارسال پیام به همه کاربران
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()
            for user in users:
                try:
                    await bot.send_message(user[0], broadcast_message_text)
                except Exception as e:
                    print(f"❌ ارسال پیام به کاربر {user[0]} با خطا مواجه شد: {e}")

            await event.edit("✅ پیام شما با موفقیت به تمامی کاربران ارسال شد.")
        except Exception as e:
            await event.edit(f"❌ خطایی در ارسال پیام رخ داد: {e}")
        finally:
            # ریست کردن وضعیت برودکست
            is_waiting_for_broadcast = False
            broadcast_message_text = None

    elif event.data == b'cancel_broadcast' and is_waiting_for_broadcast:
        await event.edit("❌ ارسال پیام برودکست لغو شد.")
        is_waiting_for_broadcast = False
        broadcast_message_text = None

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
@bot.on(events.NewMessage(pattern=r'/staff'))
async def staff_info(event):
    if event.sender_id != admin_id:  # فقط ادمین اجازه استفاده دارد
        await event.reply("❌ شما مجاز به استفاده از این دستور نیستید.")
        return

    try:
        # بازیابی تمام کاربران از دیتابیس
        cursor.execute("SELECT * FROM users")
        users = cursor.fetchall()

        if not users:  # اگر دیتابیس خالی باشد
            await event.reply("⚠️ هیچ کاربری در دیتابیس ثبت نشده است.")
            return

        # قالب‌بندی اطلاعات کاربران
        for user in users:
            user_id = user[0]
            username = user[1] or "ندارد"
            phone = user[2] or "ندارد"
            fullname = user[3] or "ندارد"
            profile_photo_id = user[5] or "ندارد"
            request_count = user[6] or 0

            # دریافت بیو از تلگرام
            try:
                full_user = await event.client(GetFullUserRequest(user_id))
                bio = full_user.full_user.about or "ندارد"
            except Exception:
                bio = "نامشخص"

            user_info = (
                f"👤 **کاربر:**\n"
                f"🔑 آیدی عددی: `{user_id}`\n"
                f"💛 یوزرنیم: `{username}`\n"
                f"📞 شماره: `{phone}`\n"
                f"👥 نام کامل: `{fullname}`\n"
                f"📝 بیو: `{bio}`\n"
                f"🖼️ تصویر پروفایل: {'دارد' if profile_photo_id != 'ندارد' else 'ندارد'}\n"
                f"🔢 تعداد درخواست‌ها: `{request_count}`\n"
                f"— — — — —"
            )

            # ارسال اطلاعات کاربر به ادمین
            await bot.send_message(admin_id, user_info)

        await event.reply("✅ اطلاعات کاربران با موفقیت ارسال شد.")
    except Exception as e:
        await event.reply(f"❌ خطایی رخ داد:\n`{e}`")

print('Run')
bot.run_until_disconnected()
# pip install watchdog
# watchmedo auto-restart --patterns="*.py" -- python main.py