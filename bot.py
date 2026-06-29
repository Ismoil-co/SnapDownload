import os
import requests
import telebot
from telebot import types

# Твой токен от BotFather
TOKEN = '8869339637:AAGwxnRcgCWwKuk3w1DKrXtRvnl7uSzX3hQ'
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
        "🎥 Отправь мне ссылку на Instagram (Reels), TikTok или Pinterest, и я пришлю тебе видео!"
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

    # Запрещаем ссылки на YouTube, так как он нам больше не нужен
    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "⚠️ Извини, скачивание с YouTube отключено. Я поддерживаю только Instagram, TikTok и Pinterest!")
        return

    # Если ссылка верная, сразу запускаем скачивание без лишних кнопок выбора качества
    download_instagram_or_other(message, url)


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


# Функция скачивания медиа (Instagram / TikTok / Pinterest)
def download_instagram_or_other(message, video_url):
    chat_id = message.chat.id
    status_msg = bot.send_message(chat_id, "⏳ Пожалуйста, подождите. Обрабатываю ссылку и скачиваю...")

    try:
        # Используем стабильное API Cobalt для Instagram и других соцсетей
        api_url = "https://cobalt.api.v0.ratelimited.me/api/json"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        data = {
            "url": video_url,
            "videoQuality": "720", # Хорошее качество для Instagram Reels
            "filenameStyle": "basic"
        }

        response = requests.post(api_url, json=data, headers=headers, timeout=20)
        
        # Если первое зеркало занято, пробуем запасное
        if response.status_code != 200:
            api_url = "https://co.wuk.sh/api/json"
            response = requests.post(api_url, json=data, headers=headers, timeout=20)

        result = response.json()
        download_url = result.get("url")
        
        if download_url:
            # Скачиваем файл во временную память сервера NomadHost
            file_response = requests.get(download_url, stream=True, timeout=60)
            filename = "instagram_video.mp4"
            
            with open(filename, 'wb') as f:
                for chunk in file_response.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)

            # Удаляем текст "Скачиваю..."
            bot.delete_message(chat_id, status_msg.message_id)

            # Отправляем готовое видео пользователю в Telegram
            with open(filename, 'rb') as video_file:
                bot.send_video(chat_id, video_file, caption="🎬 Видео успешно скачано через Ismoil Lab!")
            
            # Удаляем временный файл с хостинга
            os.remove(filename)
        else:
            raise Exception("Не удалось извлечь прямую ссылку на видео.")

    except Exception as e:
        print(f"Ошибка API: {e}")
        try:
            bot.delete_message(chat_id, status_msg.message_id)
        except:
            pass
        bot.send_message(
            chat_id, 
            "❌ Не удалось скачать медиа по этой ссылке.\nУбедись, что аккаунт открытый (не приватный) и ссылка правильная."
        )

# Запуск бота (в самом конце файла)
if __name__ == '__main__':
    print("Бот успешно запущен и охраняет канал Ismoil Lab!")
    bot.infinity_polling()
