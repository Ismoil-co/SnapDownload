import os
import requests
import telebot
from telebot import types

# ⚠️ ВСТАВЬ СЮДА НОВЫЙ ТОКЕН, КОТОРЫЙ ДАСТ BOTFATHER:
TOKEN = '8869339637:AAETLPiSJbemj-BjKDlpwWgYmBInD-Pgfhw'

bot = telebot.TeleBot(TOKEN)

# Ссылка на твой канал Ismoil Lab
CHANNEL_ID = '@ismoil_lab' 

# Функция для проверки подписки
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
        "👋 Привет! Я бот для скачивания медиа.\n\n"
        "🎥 Отправь мне ссылку на Instagram, TikTok или Pinterest, и я пришлю тебе видео!"
    )
    bot.reply_to(message, welcome_text)

# Ловим текстовые сообщения со ссылками
@bot.message_handler(content_types=['text'])
def handle_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    
    # 1. Проверяем подписку на канал
    if not check_sub(chat_id):
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

    # 2. Проверяем, что это ссылка
    if not (url.startswith('http://') or url.startswith('https://')):
        bot.reply_to(message, "⚠️ Пожалуйста, отправь корректную ссылку.")
        return

    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "⚠️ Скачивание с YouTube отключено. Я поддерживаю только Instagram, TikTok и Pinterest!")
        return

    # Запускаем универсальное скачивание
    download_media(message, url)


# Обработчик кнопки подписки
@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id
    if call.data == "check_subscription_status":
        if check_sub(chat_id):
            bot.answer_callback_query(call.id, "🎉 Спасибо за подписку! Теперь отправь мне ссылку снова.", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Вы всё ещё не подписались на Ismoil Lab!", show_alert=True)


# Универсальная функция скачивания медиа
def download_media(message, video_url):
    chat_id = message.chat.id
    status_msg = bot.send_message(chat_id, "⏳ Пожалуйста, подождите. Скачиваю видео...")

    try:
        # Для TikTok и Instagram используем разные стабильные эндпоинты
        if "tiktok.com" in video_url:
            api_url = "https://api.tikconvert.com/api/download"
            payload = {"url": video_url}
        else:
            api_url = "https://cobalt.api.v0.ratelimited.me/api/json"
            payload = {"url": video_url, "videoQuality": "720"}

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        
        # Резервный шлюз, если основной не ответил
        if response.status_code != 200:
            api_url = "https://co.wuk.sh/api/json"
            response = requests.post(api_url, json={"url": video_url}, headers=headers, timeout=20)

        result = response.json()
        download_url = result.get("url")
        
        if download_url:
            file_response = requests.get(download_url, stream=True, timeout=60)
            filename = "downloaded_media.mp4"
            
            with open(filename, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            bot.delete_message(chat_id, status_msg.message_id)

            with open(filename, 'rb') as video_file:
                bot.send_video(chat_id, video_file, caption="🎬 Успешно скачано через Ismoil Lab!")
            
            os.remove(filename)
        else:
            raise Exception("API не вернуло прямую ссылку")

    except Exception as e:
        print(f"Ошибка скачивания: {e}")
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except:
            pass
        bot.send_message(
            chat_id, 
            "❌ Не удалось скачать медиа.\nУбедись, что видео не приватное и ссылка правильная."
        )

# Запуск бота
if __name__ == '__main__':
    bot.infinity_polling()
