from telethon import TelegramClient, events, Button
import asyncio

# تنظیمات اولیه
api_id = "YOUR_API_ID"
api_hash = "YOUR_API_HASH"
bot_token = "YOUR_BOT_TOKEN"

client = TelegramClient('group_assistant_bot', api_id, api_hash).start(bot_token=bot_token)

# ذخیره اطلاعات کانال و ادمین
admin_id = None
channel_link = None
user_messages = {}  # ذخیره پیام‌های اخیر کاربران

# دستور /setlink برای ادمین
@client.on(events.NewMessage(pattern='/setlink'))
async def set_channel_link(event):
    global admin_id, channel_link
    if admin_id is None:
        admin_id = event.sender_id
        await event.reply("شما به عنوان ادمین ثبت شدید.")
    
    if event.sender_id == admin_id:
        link = event.message.text.split(maxsplit=1)[-1]
        channel_link = link
        await event.reply(f"لینک کانال با موفقیت ثبت شد: {link}")
    else:
        await event.reply("شما دسترسی تنظیم لینک ندارید.")

# بررسی پیام‌ها در گروه‌ها
@client.on(events.NewMessage)
async def check_membership(event):
    global admin_id, channel_link, user_messages

    if not channel_link or not admin_id:
        return  # اگر لینک کانال تنظیم نشده باشد، هیچ کاری انجام ندهد

    if event.is_group:
        if event.sender_id == admin_id and "بات روشن" in event.raw_text:
            await event.reply("ربات در این گروه فعال شد.")
            return

        # بررسی عضویت کاربر در کانال
        try:
            member = await client.get_participants(channel_link, filter=event.sender_id)
            is_member = bool(member)
        except:
            is_member = False

        if not is_member:
            # ارسال پیام در صورت عدم عضویت
            if event.sender_id not in user_messages:
                message = await event.reply(
                    f"کاربر {event.sender.first_name} عزیز، برای دریافت خدمات کامل عضو کانال شوید.",
                    buttons=[
                        [Button.url("عضویت در کانال", url=channel_link)]
                    ]
                )
                user_messages[event.sender_id] = message.id
            else:
                await client.edit_message(
                    event.chat_id,
                    user_messages[event.sender_id],
                    f"کاربر {event.sender.first_name} عزیز، همچنان عضو کانال نیستید. لطفاً عضو شوید.",
                    buttons=[
                        [Button.url("عضویت در کانال", url=channel_link)]
                    ]
                )

        else:
            # پیام ادیت شده در صورت عضویت
            if event.sender_id in user_messages:
                await client.edit_message(
                    event.chat_id,
                    user_messages[event.sender_id],
                    f"کاربر {event.sender.first_name} عزیز، عضویت شما تایید شد. ممنون از همکاری شما!"
                )
                del user_messages[event.sender_id]

# شروع بات
print("ربات فعال شد.")
client.run_until_disconnected()
