from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from datetime import datetime, timedelta
import re
import uuid

BOT_TOKEN = "8029046646:AAF6hjKnQGfE303qVAzZAT3O0mqqKQoJvnE"

# Хранилище напоминаний
reminders = {}  # reminder_id -> dict


# ====== ПАРСИНГ СООБЩЕНИЯ ======
def parse_message(text: str):
    pattern = r"через\s+(\d+)\s+(минут|минуты|минуту|час|часа|часов)\s*—\s*(.+)"
    match = re.match(pattern, text.lower())

    if not match:
        return None

    value = int(match.group(1))
    unit = match.group(2)
    message = match.group(3)

    if "минут" in unit:
        delta = timedelta(minutes=value)
    else:
        delta = timedelta(hours=value)

    remind_time = datetime.now() + delta
    return remind_time, message


# ====== ОБРАБОТКА СООБЩЕНИЙ ======
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.message.chat_id

    parsed = parse_message(text)
    if not parsed:
        await update.message.reply_text(
            "❌ Я не понял формат\n\n"
            "Пример:\n"
            "через 10 минут — сделать чай\n"
            "через 1 час — позвонить маме"
        )
        return

    remind_time, message = parsed
    delay = (remind_time - datetime.now()).total_seconds()

    reminder_id = str(uuid.uuid4())[:8]

    job = context.job_queue.run_once(
        send_reminder,
        when=delay,
        chat_id=chat_id,
        data={"id": reminder_id, "text": message},
    )

    reminders[reminder_id] = {
        "time": remind_time,
        "text": message,
        "job": job,
    }

    await update.message.reply_text(
        f"✅ Напоминание добавлено\n"
        f"🆔 ID: {reminder_id}\n"
        f"⏰ {remind_time.strftime('%d.%m %H:%M')}"
    )


# ====== ОТПРАВКА НАПОМИНАНИЯ ======
async def send_reminder(context: ContextTypes.DEFAULT_TYPE):
    data = context.job.data
    reminder_id = data["id"]
    text = data["text"]

    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text=f"⏰ НАПОМИНАНИЕ:\n{text}",
    )

    reminders.pop(reminder_id, None)


# ====== СПИСОК НАПОМИНАНИЙ ======
async def list_reminders(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not reminders:
        await update.message.reply_text("📭 Напоминаний нет")
        return

    lines = ["📋 Текущие напоминания:\n"]
    for rid, r in reminders.items():
        lines.append(
            f"🆔 {rid}\n"
            f"⏰ {r['time'].strftime('%d.%m %H:%M')}\n"
            f"📝 {r['text']}\n"
        )

    await update.message.reply_text("\n".join(lines))


# ====== СТАРТ ======
def main():
    print("🤖 БОТ ЗАПУЩЕН И ЖДЁТ СООБЩЕНИЙ")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("list", list_reminders))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()



