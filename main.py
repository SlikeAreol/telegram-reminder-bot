import os
import json
from datetime import datetime

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATA_FILE = "reminders.json"


def load_reminders():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_reminders(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет!\n\n"
        "Напиши напоминание в формате:\n"
        "DD.MM.YYYY HH:MM — текст\n\n"
        "Пример:\n"
        "05.12.2025 18:00 — Позвонить маме"
    )


async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    reminders = load_reminders()
    if not reminders:
        await update.message.reply_text("📭 Напоминаний пока нет")
        return

    text = "📋 Твои напоминания:\n\n"
    for i, r in enumerate(reminders, 1):
        text += f"{i}. {r['time']} — {r['text']}\n"

    await update.message.reply_text(text)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        date_part, reminder_text = text.split("—", 1)
        reminder_time = datetime.strptime(date_part.strip(), "%d.%m.%Y %H:%M")
    except Exception:
        await update.message.reply_text("❌ Не понял дату и время")
        return

    reminders = load_reminders()
    reminders.append({
        "time": reminder_time.strftime("%d.%m.%Y %H:%M"),
        "timestamp": reminder_time.timestamp(),
        "text": reminder_text.strip(),
        "chat_id": update.message.chat_id
    })
    save_reminders(reminders)

    await update.message.reply_text("✅ Напоминание сохранено")


async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().timestamp()
    reminders = load_reminders()
    remaining = []

    for r in reminders:
        if now >= r["timestamp"]:
            await context.bot.send_message(
                chat_id=r["chat_id"],
                text=f"⏰ Напоминание:\n{r['text']}"
            )
        else:
            remaining.append(r)

    save_reminders(remaining)


def main():
    print("🤖 БОТ ЗАПУЩЕН И ЖДЁТ СООБЩЕНИЙ")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.job_queue.run_repeating(check_reminders, interval=60, first=10)

    app.run_polling()


if __name__ == "__main__":
    main()




