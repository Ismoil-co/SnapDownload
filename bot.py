import os
import telebot
from telebot import types
from yt_dlp import YoutubeDL
from threading import Thread
from flask import Flask

# === ВЕБ-СЕРВЕР ДЛЯ ОБХОДА БЛОКИРОВКИ RENDER ===
app = Flask('')

@app.route('/')
def home():
    return "Бот работает и охраняет канал Ismoil Lab!"

def run():
    # Берем порт, который требует Render, или ставим 10000 по умолчанию
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)


def keep_alive():
    t = Thread(target=run)
    t.start()
# ===============================================

# Твой токен от BotFather
TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Ссылка на твой канал Ismoil Lab
CHANNEL_ID = '@ismoil_lab'

user_links = {}

def check_sub(chat_id):
    try:
        user_status = bot.get_chat_member(CHANNEL_ID, chat_id).status
        if user_status in ['creator', 'administrator', 'member']:
            return True
        return False
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для скачивания видео.\n\n"
        "🎥 Отправь мне ссылку на YouTube, TikTok или Pinterest, и выбери нужное качество!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text'])
def handle_link(message):
    url = message.text.strip()

    if not check_sub(message.chat.id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        channel_url = f"https://t.me/{CHANNEL_ID.replace('@', '')}"

        btn_sub = types.InlineKeyboardButton("📢 Подписаться на Ismoil Lab", url=channel_url)
        btn_check = types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_status")

        markup.add(btn_sub, btn_check)

        bot.reply_to(
            message,
            "❌ Доступ ограничен!\nЧтобы пользоваться ботом, пожалуйста, подпишитесь на наш официальный канал:",
            reply_markup=markup
        )
        return

    if not (url.startswith('http://') or url.startswith('https://')):
        bot.reply_to(message, "⚠️ Пожалуйста, отправь корректную ссылку.")
        return

    user_links[message.chat.id] = url

    markup = types.InlineKeyboardMarkup(row_width=2)

    btn_360 = types.InlineKeyboardButton("🎬 360p", callback_data="quality_360")
    btn_480 = types.InlineKeyboardButton("🎬 480p", callback_data="quality_480")
    btn_720 = types.InlineKeyboardButton("🎬 720p", callback_data="quality_720")
    btn_1080 = types.InlineKeyboardButton("🎬 1080p", callback_data="quality_1080")
    btn_audio = types.InlineKeyboardButton("🎵 Audio", callback_data="quality_audio")

    markup.add(btn_360, btn_480, btn_720, btn_1080)
    markup.add(btn_audio)

    bot.reply_to(message, "Выбери формат для скачивания:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id

    if call.data == "check_subscription_status":
        if check_sub(chat_id):
            bot.answer_callback_query(call.id, "🎉 Спасибо за подписку! Теперь отправь мне ссылку снова.", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Вы всё ещё не подписались на Ismoil Lab!", show_alert=True)
        return

    if call.data.startswith('quality_'):
        if not check_sub(chat_id):
            bot.answer_callback_query(call.id, "❌ Вы не подписаны на канал!", show_alert=True)
            return

        if chat_id not in user_links:
            bot.send_message(chat_id, "⚠️ Ссылка потерялась. Пожалуйста, отправьте её заново.")
            return

        url = user_links[chat_id]
        quality = call.data.split('_')[1]

        bot.answer_callback_query(call.id, "Запрос принят. Начинаю скачивание...")
        status_msg = bot.send_message(chat_id, "⏳ Пожалуйста, подождите. Скачиваю медиа...")

        outtmpl = os.path.join(os.getcwd(), '%(id)s.%(ext)s')

        if quality == 'audio':
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': outtmpl,
                'quiet': True
            }
        else:
            # Улучшенный выбор формата: ищет видео+аудио, а если не может собрать — берет лучшее готовое mp4 до указанного качества
            ydl_opts = {
                'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best[ext=mp4][height<={quality}]/best',
                'outtmpl': outtmpl,
                'merge_output_format': 'mp4',
                'quiet': True
            }

        try:
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)

                if not os.path.exists(filename):
                    filename = os.path.splitext(filename)[0] + '.mp4'

            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except:
                pass

            with open(filename, 'rb') as file:
                if quality == 'audio':
                    bot.send_audio(chat_id, file, caption="🎵 Аудио успешно скачано через Ismoil Lab!")
                else:
                    bot.send_video(chat_id, file, caption=f"🎬 Видео ({quality}) успешно скачано!")

            if os.path.exists(filename):
                os.remove(filename)

        except Exception as e:
            print(f"Ошибка при скачивании: {e}")
            try:
                bot.delete_message(chat_id, status_msg.message_id)
            except:
                pass
            bot.send_message(chat_id, "❌ Не удалось скачать медиа. Возможно, формат недоступен.")

if __name__ == '__main__':
    keep_alive()  # Включаем Flask-сервер для удержания портов Render
    print("Бот успешно запущен и охраняет канал Ismoil Lab!")
    bot.infinity_polling()
