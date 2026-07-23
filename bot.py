import os
from telegram import Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, filters
from groq import Groq
import json

# Токен бота от BotFather (берётся из переменных окружения)
TOKEN = os.environ.get("TELEGRAM_TOKEN")

# Ключ Groq API (берётся из переменных окружения)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Инициализация Groq
client = Groq(api_key=GROQ_API_KEY)

# ====== Работа с файлом памяти ======
MEMORY_FILE = "memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_memory(memory):
    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory, f, ensure_ascii=False, indent=2)

# Загружаем память при старте
memory = load_memory()

def get_ai_response(user_id, user_message):
    if user_id not in memory:
        memory[user_id] = []
    
    memory[user_id].append({"role": "user", "content": user_message})
    
    # Ограничиваем историю последними 10 сообщениями
    if len(memory[user_id]) > 10:
        memory[user_id] = memory[user_id][-10:]
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
    {"role": "system", "content": "Ты — экспертный копирайтер и маркетолог с 10-летним опытом создания продающих карточек для Ozon, Wildberries и Яндекс.Маркета. Твой тон общения: дружелюбный, энергичный и профессиональный. Твой алгоритм работы: когда пользователь называет товар, НЕ пиши текст сразу. Сначала задай 2-3 коротких уточняющих вопроса (например: какой цвет/версия, для какой аудитории, есть ли свой список SEO-ключей). После получения ответов сгенерируй карточку по структуре: 🔥 Заголовок (до 60 символов с эмодзи), ✅ Главные выгоды (3-5 пунктов с решением боли покупателя), 📝 SEO-описание (до 1000 символов с ключами в начале и конце), ⚙️ Краткие характеристики, 🚀 Призыв к действию. Строго запрещено использовать слова: дешево, просто, плохо, качественный."},
    *memory[user_id]
]
        )
        ai_message = response.choices[0].message.content
        memory[user_id].append({"role": "assistant", "content": ai_message})
        save_memory(memory)
        return ai_message
    except Exception as e:
        return f"Ошибка: {str(e)}"

# ====== Обработчики команд ======
def start(update, context):
    update.message.reply_text("Привет! Я AI-бот. Напиши мне что-нибудь!")

def clear(update, context):
    user_id = update.message.from_user.id
    if user_id in memory:
        del memory[user_id]
        save_memory(memory)
    update.message.reply_text("Память очищена!")

def newchat(update, context):
    user_id = update.message.from_user.id
    memory[user_id] = []
    save_memory(memory)
    update.message.reply_text("Новый чат начат!")

def stats(update, context):
    user_id = update.message.from_user.id
    count = len(memory.get(user_id, []))
    update.message.reply_text(f"Сообщений в памяти: {count}")

def handle_message(update, context):
    user_id = update.message.from_user.id
    user_message = update.message.text
    response = get_ai_response(user_id, user_message)
    update.message.reply_text(response)

# ====== Запуск бота ======
def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher
    
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("clear", clear))
    dp.add_handler(CommandHandler("newchat", newchat))
    dp.add_handler(CommandHandler("stats", stats))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Бот запущен!")
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
