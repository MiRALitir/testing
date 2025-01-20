import telebot
from telebot import types
from config import *

# توکن ربات تلگرام خود را وارد کنید
API_TOKEN = token
bot = telebot.TeleBot(API_TOKEN)

# لیست آیدی ادمین‌ها
ADMIN_IDS = admin_ids

@bot.message_handler(commands=['start'])
def start(message):
    msg = '''درود کاربر گرامی به ربات ثبت سفارش خوش اومدید!
این ربات برای ثبت سفارش ساخت ربات تلگرام از مجموعه @MiRALi_SHOP_OG ساخته شده.
برای دریافت راهنمایی بیشتر درمورد ربات، می‌توانید از بخش راهنما استفاده کنید!'''
    
    markup = types.ReplyKeyboardMarkup(row_width=2)
    button1 = types.KeyboardButton('ثبت سفارش 📝')
    button2 = types.KeyboardButton('سفارشات 📄')
    button3 = types.KeyboardButton('مشخصات من 🔍')
    button4 = types.KeyboardButton('💡 راهنما')
    button5 = types.KeyboardButton('سوالات متداول ⚖️')
    button6 = types.KeyboardButton('☎️ پشتیبانی')
    
    markup.add(button1, button2, button3, button4, button5, button6)
    bot.send_message(message.chat.id, msg, reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == 'مشخصات من 🔍')
def profile(message):
    user_id = message.from_user.id
    username = message.from_user.username or "ندارد"
    fullname = f"{message.from_user.first_name or ''} {message.from_user.last_name or ''}".strip() or "ندارد"
    
    # دریافت اطلاعات کامل کاربر (از جمله بیو)
    chat_info = bot.get_chat(user_id)
    bio = getattr(chat_info, 'bio', 'ندارد')  # بیو را از اطلاعات چت دریافت کنید

    profile_info = f'''
    👤 اطلاعات شما:
    🔑 آیدی عددی: {user_id}
    💛 یوزرنیم: {username}
    👥 نام کامل: {fullname}
    📝 بیو: {bio}
    '''
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    back_button = types.KeyboardButton("بازگشت")
    markup.add(back_button)
    
    bot.send_message(message.chat.id, profile_info, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "back")
def back_to_start(call):
    bot.answer_callback_query(call.id)
    start(call.message)

@bot.callback_query_handler(func=lambda call: call.data == "continue")
def continue_order(call):
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "ادامه ثبت سفارش...")
    
print('Bot is running...')
bot.polling()
