import json
import logging
import os

from config import *
from telethon import Button, TelegramClient, events
from telethon.errors import UserNotParticipantError
from telethon.tl.types import MessageEntityTextUrl

api_id = api_id
api_hash = api_hash
bot_token = token

client = TelegramClient('group_assistant_bot', api_id, api_hash).start(bot_token=bot_token)

config_file = 'channel_config.json'
def load_channel_config():
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return {"channel_id": None, "channel_username": None}

def save_channel_config(channel_id, channel_username):
    with open(config_file, 'w') as f:
        json.dump({"channel_id": channel_id, "channel_username": channel_username}, f)

config = load_channel_config()
channel_id = config.get("channel_id")
channel_username = config.get("channel_username")
user_messages = {}

active_groups_file = 'active_groups.json'

def load_active_groups():
    if os.path.exists(active_groups_file):
        with open(active_groups_file, 'r') as f:
            return json.load(f)
    return []

def save_active_groups(groups):
    with open(active_groups_file, 'w') as f:
        json.dump(groups, f)

active_groups = load_active_groups()

@client.on(events.NewMessage)
async def activate_bot(event):
    global active_groups

    if event.is_group and event.sender_id == admin:
        if "دستیار گروه فعال" in event.raw_text:
            group_id = event.chat_id
            if group_id not in active_groups:
                active_groups.append(group_id)
                save_active_groups(active_groups)
                await event.reply("✅ دستیار گروه در این گروه فعال شد!")
            else:
                await event.reply("⚠️ دستیار گروه قبلاً در این گروه فعال شده است.")

# متغیر وضعیت
link_setting_state = {}

@client.on(events.NewMessage(pattern='/setlink'))
async def set_channel_link(event):
    global link_setting_state

    # بررسی دسترسی
    if not event.is_private or event.sender_id != admin:
        await event.reply("❌ شما دسترسی تنظیم لینک را ندارید.")
        return

    # ذخیره وضعیت برای کاربر
    link_setting_state[event.sender_id] = 'awaiting_link'
    await event.reply("لطفاً لینک کانال را ارسال کنید (مثال: @example یا لینک خصوصی کانال).")


@client.on(events.NewMessage)
async def handle_channel_link(event):
    global link_setting_state, channel_username, channel_id

    if not event.is_private or event.sender_id != admin:
        return

    # جلوگیری از پردازش کامندها
    if event.raw_text.startswith('/'):
        return

    # بررسی وضعیت تنظیم لینک
    if link_setting_state.get(event.sender_id) == 'awaiting_link':
        link = event.raw_text.strip()
        if link.startswith('@') or link.startswith('https://t.me/+'):
            channel_username = link
            channel_id = None
            link_setting_state[event.sender_id] = 'awaiting_id'
            await event.reply(
                "✅ لینک کانال با موفقیت ثبت شد!\n"
                "🔹 اکنون لطفاً آیدی عددی کانال را ارسال کنید (این آیدی باید از طریق ربات‌های مخصوص استخراج شود)."
            )
        else:
            await event.reply("❌ لینک نامعتبر است! لطفاً یک لینک معتبر ارسال کنید.")

    elif link_setting_state.get(event.sender_id) == 'awaiting_id':
        try:
            channel_id = int(event.raw_text.strip())
            if channel_username:
                save_channel_config(channel_id, channel_username)
                link_setting_state.pop(event.sender_id, None)  # حذف وضعیت کاربر
                await event.reply(
                    "✅ لینک و آیدی عددی کانال با موفقیت ثبت شدند!\n\n"
                    f"🔹 لینک کانال: `{channel_username}`\n"
                    f"🔹 آیدی عددی: `{channel_id}`\n\n"
                    "🛠️ لطفاً ربات را به‌عنوان ادمین کانال اضافه کنید تا بتواند وظایف خود را انجام دهد."
                )
            else:
                await event.reply(
                    "❌ ابتدا باید لینک کانال را ارسال کنید (لینک عمومی یا خصوصی)."
                )
        except ValueError:
            await event.reply(
                "❌ **آیدی عددی نامعتبر است!**\n"
                "لطفاً یک آیدی عددی معتبر ارسال کنید."
            )

@client.on(events.NewMessage)
async def check_membership(event):
    global channel_id, channel_username

    if event.chat_id not in active_groups:
        return

    if not channel_id or not channel_username or event.is_private:
        return

    if event.is_group:
        sender_id = event.sender_id
        sender_name = event.sender.first_name or "کاربر"

        try:
            await client.get_permissions(channel_id, sender_id)
            is_member = True
        except UserNotParticipantError:
            is_member = False
        except Exception as e:
            print(f"خطا در بررسی عضویت: {e}")
            return

        if not is_member:
            message_text = (
                f"کاربر <b><a href='tg://user?id={sender_id}'>{sender_name}</a></b> عزیز،\n\n"
                "📢 برای استفاده از تمامی امکانات گروه، ابتدا باید به کانال ما بپیوندید.\n\n"
                "🔹 برای عضویت در کانال، لطفاً روی دکمه زیر کلیک کنید 👇"
            )

            button = Button.url(
                "عضویت در کانال",
                url=f"{channel_username}" if channel_username.startswith('https://t.me/+') else f"https://t.me/{channel_username.lstrip('@')}"
            )

            if sender_id in user_messages:
                old_message_id = user_messages[sender_id]
                try:
                    await client.edit_message(
                        event.chat_id,
                        old_message_id,
                        message_text,
                        buttons=[button],
                        parse_mode='html'
                    )
                except Exception:
                    message = await event.reply(message_text, buttons=[button], parse_mode='html')
                    user_messages[sender_id] = message.id
            else:
                message = await event.reply(message_text, buttons=[button], parse_mode='html')
                user_messages[sender_id] = message.id
        else:
            if sender_id in user_messages:
                confirmation_text = (
                    f"کاربر <b><a href='tg://user?id={sender_id}'>{sender_name}</a></b> عزیز،\n\n"
                    "✅ <b>عضویت شما با موفقیت تایید شد!</b>\n\n"
                    "🙏 از همکاری شما سپاسگزاریم.\n\n"
                    "🔹 اکنون می‌توانید از تمامی امکانات گروه استفاده کنید."
                )
                old_message_id = user_messages[sender_id]
                try:
                    await client.edit_message(
                        event.chat_id,
                        old_message_id,
                        confirmation_text,
                        parse_mode='html'
                    )
                except Exception as e:
                    print(f"خطا در ویرایش پیام تایید عضویت: {e}")
                del user_messages[sender_id]

async def main():
    try:
        bot_info = await client.get_me()
        print(f'Bot Username: @{bot_info.username}')
    except Exception as e:
        logging.error(f'Error fetching bot info: {str(e)}')

print("Bot Is Run")
client.run_until_disconnected()
