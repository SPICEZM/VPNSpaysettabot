import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
import os

# Получаем токен из переменных окружения Render
TOKEN = os.getenv("BOT_TOKEN")

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню с кнопками
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку (VPN / Proxy)", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])
    return keyboard

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"Здравствуй, {user_name}! 🚀\n\n"
        "Добро пожаловать в наш сервис быстрого и безопасного интернета.\n"
        "Выбери нужный пункт в меню ниже:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

# Запуск бота
async def main():
    logging.basicConfig(level=logging.INFO)
    print("Бот успешно запущен и готов к работе...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
