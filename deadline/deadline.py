import asyncio
from datetime import datetime
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.handlers import router
from app.utils import load_reminders

# Объект бота
TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=TOKEN)

storage = MemoryStorage()
dp = Dispatcher(bot=bot, storage=storage)

# Основной запуск бота
async def main():
    await bot_health_check()
    dp.include_router(router)
    # Настраиваем планировщик
    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_and_send_reminders,  "cron", hour=9, minute=0)  # Проверяем каждый день в 9 утра
    scheduler.start()
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"error: {e}")
    finally:
        scheduler.shutdown()
        await bot.session.close()

reminders = load_reminders()
# send messages
async def check_and_send_reminders():
    now = datetime.now()
    for user_id, user_data in reminders.items():
        for reminder in user_data["reminders"]:
            # Проверяем, если дата рождения совпадает с текущей или находится в пределах интервала
            deadline = datetime.strptime(reminder["deadline"], "%d.%m")
            current_year_deadline = deadline.replace(year=now.year)

            days_left = (current_year_deadline - now).days
            if days_left in reminder["intervals"]:
                try:
                    await bot.send_message(
                        user_id,
                        f"Напоминание: {reminder['name']} через {days_left} дней!"
                    )
                except Exception as e:
                    print(f"Ошибка при отправке сообщения {user_id}: {e}")

# для проверки работы бота
async def bot_health_check():
    chat_ids = [1185330189]#, 6011302552
    try:
        for chat_id in chat_ids:
            await bot.send_message(
                chat_id,
                text="admin check health\n"
                     "/start\n"
            )
    except Exception as e:
        print(f"Ошибка отправки тестового сообщения: {e}")


if __name__ == "__main__":
    asyncio.run(main())
