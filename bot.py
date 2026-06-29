import telebot
import requests
from telebot import types

# Твой новый токен от BotFather
TOKEN = '8869339637:AAETLPiSJbemj-BjKDlpwWgYmBInD-Pgfhw'
bot = telebot.TeleBot(TOKEN)

# Ссылка на твой канал Ismoil Lab
CHANNEL_ID = '@ismoil_lab' 

def check_sub(chat_id):
    try:
        user_status = bot.get_chat_member(CHANNEL_ID, chat_id).status
        return user_status in ['creator', 'administrator', 'member']
    except Exception:
        return False

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = (
        "👋 Привет! Я бот для скачивания медиа.\n\n"
        "🎥 Отправь мне ссылку на Instagram, TikTok или Pinterest, и я пришлю тебе видео!"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(content_types=['text'])
def handle_link(message):
    url = message.text.strip()
    chat_id = message.chat.id
    
    if not check_sub(chat_id):
        markup = types.InlineKeyboardMarkup(row_width=1)
        channel_url = f"https://t.me/{CHANNEL_ID.replace('@', '')}"
        btn_sub = types.InlineKeyboardButton("📢 Подписаться на Ismoil Lab", url=channel_url)
        btn_check = types.InlineKeyboardButton("✅ Я подписался", callback_data="check_subscription_status")
        markup.add(btn_sub, btn_check)
        
        bot.reply_to(message, "❌ Доступ ограничен!\nЧтобы пользоваться ботом, пожалуйста, подпишитесь на наш официальный канал:", reply_markup=markup)
        return

    if not (url.startswith('http://') or url.startswith('https://')):
        bot.reply_to(message, "⚠️ Пожалуйста, отправь корректную ссылку.")
        return

    if "youtube.com" in url or "youtu.be" in url:
        bot.reply_to(message, "⚠️ Скачивание с YouTube отключено. Я поддерживаю только Instagram, TikTok и Pinterest!")
        return

    status_msg = bot.send_message(chat_id, "⏳ Пожалуйста, подождите. Генерирую видео...")

    try:
        # Используем ультра-быстрое API
        if "tiktok.com" in url:
            api_url = "https://api.tikconvert.com/api/download"
            payload = {"url": url}
        else:
            api_url = "https://cobalt.api.v0.ratelimited.me/api/json"
            payload = {"url": url, "videoQuality": "720"}

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        response = requests.post(api_url, json=payload, headers=headers, timeout=20)
        
        if response.status_code != 200:
            api_url = "https://co.wuk.sh/api/json"
            response = requests.post(api_url, json={"url": url}, headers=headers, timeout=20)

        result = response.json()
        download_url = result.get("url")
        
        if download_url:
            # Отправляем видео напрямую ССЫЛКОЙ (Render это не заблокирует!)
            bot.send_video(chat_id, download_url, caption="🎬 Успешно скачано через Ismoil Lab!")
            bot.delete_message(chat_id, status_msg.message_id)
        else:
            raise Exception("API не вернуло ссылку")

    except Exception as e:
        print(f"Ошибка: {e}")
        bot.delete_message(chat_id, status_msg.message_id)
        bot.send_message(chat_id, "❌ Не удалось обработать ссылку. Убедись, что профиль открыт.")

@bot.callback_query_handler(func=lambda call: True)
def handle_all_callbacks(call):
    chat_id = call.message.chat.id
    if call.data == "check_subscription_status":
        if check_sub(chat_id):
            bot.answer_callback_query(call.id, "🎉 Спасибо за подписку! Теперь отправь мне ссылку снова.", show_alert=True)
            bot.delete_message(chat_id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, "❌ Вы всё ещё не подписались на Ismoil Lab!", show_alert=True)

if __name__ == '__main__':
    bot.infinity_polling()
