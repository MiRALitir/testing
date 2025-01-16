import asyncio
import os

from aiogram import Bot, Dispatcher, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError

BOT_TOKEN = "7318011977:AAF52qGRaXv4FipsL7YCWoAumT8tOMAjeds"
ADMIN_ID = [6087657605, 6365892466]

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

SESSIONS_DIR = "sessions"
os.makedirs(SESSIONS_DIR, exist_ok=True)


# تعریف وضعیت‌ها
class SessionStates(StatesGroup):
    waiting_for_api_id = State()
    waiting_for_api_hash = State()
    waiting_for_phone_number = State()
    waiting_for_code = State()
    waiting_for_password = State()


# هندل پیام ادمین برای شروع ایجاد سشن
@router.message(F.text.startswith("/setnumber") & F.from_user.id.in_(ADMIN_ID))
async def add_session(message: Message, state: FSMContext):
    await message.answer("لطفاً API ID را ارسال کنید:")
    await state.set_state(SessionStates.waiting_for_api_id)


@router.message(SessionStates.waiting_for_api_id, F.text.regexp(r"^\d+$") & F.from_user.id.in_(ADMIN_ID))
async def get_api_id(message: Message, state: FSMContext):
    await state.update_data(api_id=message.text)
    await message.answer("لطفاً API Hash را ارسال کنید:")
    await state.set_state(SessionStates.waiting_for_api_hash)


@router.message(SessionStates.waiting_for_api_hash, F.text & F.from_user.id.in_(ADMIN_ID))
async def get_api_hash(message: Message, state: FSMContext):
    if len(message.text) != 32:
        await message.answer("API Hash باید دقیقاً 32 کاراکتر باشد. لطفاً دوباره ارسال کنید.")
        return
    await state.update_data(api_hash=message.text)
    await message.answer("لطفاً شماره تلفن را ارسال کنید:")
    await state.set_state(SessionStates.waiting_for_phone_number)


@router.message(SessionStates.waiting_for_phone_number, F.text.startswith("+") & F.from_user.id.in_(ADMIN_ID))
async def get_phone_number(message: Message, state: FSMContext):
    data = await state.get_data()
    api_id = data["api_id"]
    api_hash = data["api_hash"]
    phone_number = message.text
    session_name = phone_number.replace("+", "")
    session_path = os.path.join(SESSIONS_DIR, f"{session_name}.session")

    if os.path.exists(session_path):
        await message.answer("این شماره قبلاً ثبت شده است.")
        await state.clear()
        return

    client = TelegramClient(session_path, api_id, api_hash)
    await state.update_data(client=client, phone_number=phone_number)
    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone_number)
            await message.answer("کد ارسال شده به شماره را وارد کنید:")
            await state.set_state(SessionStates.waiting_for_code)
    except Exception as e:
        await message.answer(f"خطایی رخ داد: {str(e)}")
        await state.clear()


@router.message(SessionStates.waiting_for_code, F.text.regexp(r"^\d+$") & F.from_user.id.in_(ADMIN_ID))
async def get_code(message: Message, state: FSMContext):
    data = await state.get_data()
    client = data["client"]
    phone_number = data["phone_number"]
    code = message.text
    try:
        await client.sign_in(phone_number, code)
        await message.answer("سشن با موفقیت ساخته شد!")
    except SessionPasswordNeededError:
        await message.answer("این شماره نیاز به تایید دو مرحله‌ای دارد. لطفاً رمز عبور را ارسال کنید:")
        await state.set_state(SessionStates.waiting_for_password)
    except Exception as e:
        await message.answer(f"خطا در ورود: {str(e)}")
        await state.clear()
    finally:
        await client.disconnect()


@router.message(SessionStates.waiting_for_password, F.from_user.id.in_(ADMIN_ID))
async def get_password(message: Message, state: FSMContext):
    data = await state.get_data()
    client = data["client"]
    password = message.text
    try:
        await client.sign_in(password=password)
        await message.answer("سشن با موفقیت ساخته شد!")
    except Exception as e:
        await message.answer(f"خطا در ورود: {str(e)}")
    finally:
        await client.disconnect()
        await state.clear()


async def main():
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
