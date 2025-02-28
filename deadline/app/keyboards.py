from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Установить напоминание 📆')],
    [KeyboardButton(text='настройки ⚙️'), KeyboardButton(text='следующий дедлайн ➡️')]
],
    resize_keyboard=True,
    input_field_placeholder="Выберите пункт меню"
)
clear = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='отмена❌')],
], resize_keyboard=True,
)
settings = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='изменить интервал 🗓')],
    [KeyboardButton(text='Вывести всю базу данных 📂')],
    [KeyboardButton(text='удалить запись 🔒')],
    [KeyboardButton(text='help')],
    [KeyboardButton(text='отмена❌')]
],
    resize_keyboard=True,
    input_field_placeholder="Настройки..."
)