import logging
import json
import os
from datetime import datetime, time, timedelta
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, JobQueue

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = "user_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

data = load_data()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in data:
        data[user_id] = {
            "streak": 0,
            "max_streak": 0,
            "last_drawn_date": "",
            "drawn_today": False
        }
        save_data(data)
    keyboard = [["✅ Я рисовал сегодня"]]
    await update.message.reply_text(
        "Привет! Я помогу тебе следить за прогрессом в рисовании.\nКаждый день я буду напоминать тебе рисовать.",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=False, resize_keyboard=True)
    )

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_data = data.get(user_id, {})
    await update.message.reply_text(
        f"Текущий стрик: {user_data.get('streak', 0)}\n"
        f"Максимальный стрик: {user_data.get('max_streak', 0)}"
    )

async def drawn_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    today_str = datetime.now().strftime("%Y-%m-%d")

    user = data.get(user_id)
    if not user:
        await start(update, context)
        return

    if user["last_drawn_date"] != today_str:
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        if user["last_drawn_date"] == yesterday:
            user["streak"] += 1
        else:
            user["streak"] = 1
        user["last_drawn_date"] = today_str
        user["drawn_today"] = True
        user["max_streak"] = max(user["max_streak"], user["streak"])
        save_data(data)
        await update.message.reply_text("Молодец! Я отметил, что ты сегодня рисовал ✍️")
    else:
        await update.message.reply_text("Ты уже отметил, что рисовал сегодня 🎉")

# Напоминания
async def morning_reminder(context: ContextTypes.DEFAULT_TYPE):
    for user_id in data:
        await context.bot.send_message(chat_id=int(user_id), text="Доброе утро! Не забудь сегодня порисовать ✨")

async def evening_reminder(context: ContextTypes.DEFAULT_TYPE):
    today_str = datetime.now().strftime("%Y-%m-%d")
    for user_id, user in data.items():
        if user.get("last_drawn_date") != today_str:
            await context.bot.send_message(chat_id=int(user_id), text="ПОРА РИСОВАТЬ, А ТО СТРИК СЛЕТИТ 😱")

# Обработка кнопки
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "✅ Я рисовал сегодня":
        await drawn_today(update, context)

# Главный запуск
async def main():
    token = os.environ.get("8140971779:AAEmPDX6kOu2w22Fg8lGkQPW00YTj5Fqngg")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Планировщик заданий
    job_queue: JobQueue = app.job_queue
    job_queue.run_daily(morning_reminder, time(hour=9, minute=0))
    job_queue.run_daily(evening_reminder, time(hour=20, minute=0))

    logger.info("Бот запущен")
    await app.run_polling()

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
