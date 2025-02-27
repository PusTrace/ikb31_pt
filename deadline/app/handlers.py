from datetime import datetime
import json

from aiogram import types, Router, F
from aiogram.filters.command import CommandStart
from aiogram.fsm.context import FSMContext

import app.keyboards as kb
from app.keyboards import clear
from app.states import ReminderStates
from app.utils import load_reminders, save_reminders


reminders = load_reminders()
birthday = []

router = Router()

@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.reply(
        "Привет! Я бот-напоминалка.\n",
        reply_markup=kb.main,
    )

@router.message(F.text == 'Установить напоминание 📆')
async def start_set_reminder(message: types.Message, state: FSMContext):
    user_id = str(message.chat.id)  # ID чата или пользователя
    await state.set_state(ReminderStates.waiting_for_name)
    await state.update_data(user_id=user_id)  # Сохраняем ID в состоянии
    await message.answer("Введите имя кого хотите добавить", reply_markup=clear)

@router.message(ReminderStates.waiting_for_name)
async def enter_name(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Установка напоминания отменена.", reply_markup=kb.main)
        return

    await state.update_data(name=message.text)
    await state.set_state(ReminderStates.waiting_for_birthday)
    await message.answer("Введите дату рождения в формате ДД.ММ.ГГГГ")

@router.message(ReminderStates.waiting_for_birthday)
async def enter_birthday(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Установка напоминания отменена.", reply_markup=kb.main)
        return

    try:
        birthday = datetime.strptime(message.text, "%d.%m.%Y")
        user_data = await state.get_data()

        # Сохраняем напоминание
        user_id = str(message.from_user.id)
        if user_id not in reminders:
            reminders[user_id] = {"reminders": []}

        reminders[user_id]["reminders"].append({
            "name": user_data["name"],
            "birthday": birthday.strftime("%d.%m.%Y"),
            "intervals": [1, 7, 30]
        })

        # Завершаем процесс и возвращаем главную клавиатуру
        save_reminders(reminders)
        await state.clear()
        await message.answer(
            f"Напоминание для {user_data['name']} на {birthday.strftime('%d.%m.%Y')} успешно установлено!",
            reply_markup=kb.main
        )
    except ValueError:
        await message.answer("Ошибка: введите дату в формате ДД.ММ.ГГГГ")



@router.message(F.text.casefold() == 'отмена❌'.casefold())
async def cancel_anywhere(message: types.Message, state: FSMContext):
    if await state.get_state():
        await state.clear()
        await message.answer("Действие отменено.", reply_markup=kb.main)
    else:
        await message.answer("Вы не находитесь в процессе настройки ⚙️.", reply_markup=kb.main)



@router.message(F.text == 'следующий др ➡️')
async def info(message: types.Message):
    now = datetime.now()
    user_id = str(message.from_user.id)

    if user_id not in reminders or not reminders[user_id]["reminders"]:
        await message.answer("У вас нету напоминаний.")
        return

    # Ищем ближайший день рождения
    user_reminders = reminders[user_id]["reminders"]
    next_birthday = None

    for reminder in user_reminders:
        birthday = datetime.strptime(reminder["birthday"], "%d.%m.%Y")
        current_year_birthday = birthday.replace(year=now.year)

        # Если день рождения в текущем году уже прошёл, переносим его на следующий год
        if current_year_birthday < now:
            current_year_birthday = current_year_birthday.replace(year=now.year + 1)

        # Обновляем ближайший день рождения
        if not next_birthday or current_year_birthday < next_birthday["date"]:
            next_birthday = {"name": reminder["name"], "date": current_year_birthday}

    # Если нашли ближайший день рождения
    if next_birthday:
        time_left = next_birthday["date"] - now
        days_left = time_left.days
        hours_left = time_left.seconds // 3600
        minutes_left = (time_left.seconds // 60) % 60

        await message.answer(
            f"Следующий день рождения у : {next_birthday['name']} через {days_left} дня, {hours_left} часов и {minutes_left} минут.")
    else:
        await message.answer("У вас нет предстоящих дней рождения.")



@router.message(F.text.casefold() == 'настройки ⚙️'.casefold())
async def settings(message: types.Message):
    await message.answer("настройки ⚙️", reply_markup=kb.settings)

@router.message(F.text.casefold() == 'изменить интервал 🗓'.casefold())
async def settings_interval(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Установка интервала отменено.", reply_markup=kb.main)
        return
    await state.set_state(ReminderStates.waiting_for_name_settings)
    await message.answer("Введите имя для кого хотите изменить интервал 🗓", reply_markup=clear)

@router.message(ReminderStates.waiting_for_name_settings)
async def enter_name(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Изменение интервала отменено.", reply_markup=kb.main)
        return

    name_to_check = message.text.strip()  # Имя, которое ввел пользователь

    # Проверяем, существует ли человек с таким именем в базе данных
    user_exists = False
    for user_id, user_info in reminders.items():
        for reminder in user_info["reminders"]:
            if reminder["name"].lower() == name_to_check.lower():  # Сравниваем имена без учета регистра
                user_exists = True
                break
        if user_exists:
            break

    if not user_exists:
        # Если такого имени нет в базе
        await message.answer("Пользователь с таким именем не существует в базе данных.", reply_markup=kb.main)
        return

    # Сохраняем имя пользователя в состоянии для дальнейшего использования
    await state.update_data(name=name_to_check)

    # Переходим к следующему шагу (ввод интервалов)
    await state.set_state(ReminderStates.waiting_for_interval_settings)
    await message.answer("Введите интервалы через запятую.\n"
                         "Пример: 1, 7, 30\n"
                         "Это изменит интервал так, что оповещения придут за 1, 7, 30 дней")

@router.message(ReminderStates.waiting_for_interval_settings)
async def enter_interval(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Изменение интервала отменено.", reply_markup=kb.main)
        return

    try:
        user_interval_str = str(message.text)
        user_interval = [int(item.strip()) for item in user_interval_str.split(",")] #нужно превращать строки в числа перед добавлением в список
        user_data = await state.get_data()

        # Сохраняем напоминание
        user_id = str(message.from_user.id)
        if user_id not in reminders:
            reminders[user_id] = {"reminders": []}

        # Ищем существующее напоминание для данного пользователя
        for reminder in reminders[user_id]["reminders"]:
            if reminder["name"] == user_data["name"]:
                # Обновляем интервалы
                reminder["intervals"] = user_interval  # Просто присваиваем новый список интервалов
                break

        # Сохраняем изменения в базе данных
        save_reminders(reminders)

        # Завершаем процесс и возвращаем главную клавиатуру
        await state.clear()
        await message.answer(
            f"Интервал для {user_data['name']} на {user_interval_str} успешно изменён!",
            reply_markup=kb.main
        )
    except ValueError:
        await message.answer("Ошибка: введите интервал в формате: 1, 7, 30")


# Вывести всю базу данных 📂
@router.message(F.text.casefold() == 'Вывести всю базу данных 📂'.casefold())
async def settings_interval(message: types.Message):

    user_id = str(message.from_user.id)
    if user_id not in reminders:
        reminders[user_id] = {"reminders": []}
        output_database = "у вас ещё нет базы данных"
    else:
        user_data = reminders.get(user_id, {})
        output_database = json.dumps(user_data, ensure_ascii=False, indent=4)

    await message.answer(output_database, reply_markup=kb.main)

@router.message(F.text.casefold() == 'удалить запись 🔒'.casefold())
async def delete_entry(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Удаление записи отменено.", reply_markup=kb.main)
        return

    await state.set_state(ReminderStates.waiting_for_name_delete)
    await message.answer("Введите имя для кого хотите удалить запись 🔒", reply_markup=clear)

@router.message(ReminderStates.waiting_for_name_delete)
async def confirm_deletion(message: types.Message, state: FSMContext):
    if message.text.lower() == "отмена❌":
        await state.clear()
        await message.answer("Удаление записи отменено.", reply_markup=kb.main)
        return

    name_to_delete = message.text.strip()

    # Проверяем существование записи с таким именем
    user_id = str(message.chat.id)
    record_found = False

    if user_id in reminders:
        for reminder in reminders[user_id]["reminders"]:
            if reminder["name"].lower() == name_to_delete.lower():
                reminders[user_id]["reminders"].remove(reminder)
                record_found = True
                break

        # Удаляем пользователя из базы, если у него больше нет записей
        if not reminders[user_id]["reminders"]:
            del reminders[user_id]

    if record_found:
        save_reminders(reminders)  # Сохраняем изменения в базе данных
        await message.answer(f"Запись для {name_to_delete} успешно удалена!", reply_markup=kb.main)
    else:
        await message.answer("Пользователь с таким именем не найден в базе данных.", reply_markup=kb.main)

    await state.clear()


@router.message(F.text.casefold() == 'о нас 👤'.casefold())
async def about_us(message: types.Message):
    await message.answer(
        "Разработчик: Вавилин Сергей\n"
        "Контакты:\n"
        "https://t.me/PusTrace\n"
        "sergeivavilin2005@mail.ru\n"
        "\n"
        "Системный администратор, а так же владелец сервера и бота: Вавилин Дмитрий\n"
        "Контакты:\n"
        "https://t.me/VDmitriiyM\n", reply_markup=kb.main)