from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import json
import os
from datetime import datetime
import time
import threading

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
        "ДД.ММ.ГГГГ ЧЧ:ММ — текст\n\n"
        "Пример:\n"
        "05.01.2026 18:00 — Позвонить маме"
    )


async def add_reminder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        date_part, message = text.split("—", 1)
        date_part = date_part.strip()
        message = message.strip()

        remind_time = datetime.strptime(date_part, "%d.%m.%Y %H:%M")

        reminders = load_reminders()
        reminders.append({
            "time": remind_time.isoformat(),
            "text": message,
            "chat_id": update.message.chat_id
        })
        save_reminders(reminders)

        await update.message.reply_text("✅ Напоминание добавлено")

    except Exception:
        await update.message.reply_text("❌ Не понял формат даты и времени")


def reminder_worker(app):
    while True:
        now = datetime.now()
        reminders = load_reminders()
        updated = []

        for r in reminders:
            remind_time = datetime.fromisoformat(r["time"])
            if remind_time <= now:
                app.bot.send_message(
                    chat_id=r["chat_id"],
                    text=f"⏰ Напоминание:\n{r['text']}"
                )
            else:
                updated.append(r)

        save_reminders(updated)
        time.sleep(30)


def main():
    print("🤖 БОТ ЗАПУЩЕН")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_reminder))

    thread = threading.Thread(target=reminder_worker, args=(app,), daemon=True)
    thread.start()

    app.run_polling()


if __name__ == "__main__":
    main()





