from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, ContextTypes, filters
from datetime import datetime
from dateutil import parser
import json
import os

BOT_TOKEN = os.environ.get("BOT_TOKEN")

DATA_FILE = "reminders.json"


def load_reminders():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_reminders(reminders):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(reminders, f, ensure_ascii=False, indent=2)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    try:
        if "—" not in text:
            raise ValueError

        date_part, message = text.split("—", 1)
        remind_time = parser.parse(date_part.strip(), dayfirst=True)

        reminders = load_reminders()
        reminders.append({
            "chat_id": update.effective_chat.id,
            "time": remind_time.isoformat(),
            "text": message.strip()
        })
        save_reminders(reminders)

        await update.message.reply_text(
            f"✅ Напоминание сохранено:\n{remind_time.strftime('%d.%m.%Y %H:%M')}"
        )

    except Exception:
        await update.message.reply_text(
            "❌ Не понял формат.\nПример:\n25.12.2025 18:00 — Позвонить маме"
        )


async def reminder_loop(app):
    while True:
        now = datetime.now()
        reminders = load_reminders()
        remaining = []

        for r in reminders:
            remind_time = datetime.fromisoformat(r["time"])
            if remind_time <= now:
                await app.bot.send_message(
                    chat_id=r["chat_id"],
                    text=f"⏰ Напоминание:\n{r['text']}"
                )
            else:
                remaining.append(r)

        save_reminders(remaining)
        await app.bot.sleep(30)


def main():
    print("🤖 БОТ ЗАПУЩЕН")

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.create_task(reminder_loop(app))
    app.run_polling()


if __name__ == "__main__":
    main()






