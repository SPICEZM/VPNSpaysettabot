import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💎 Купить подписку (VPN / Proxy)", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction")],
        [InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])
    return keyboard

@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"Здравствуй, {user_name}! 🚀\n\n"
        "Добро пожаловать в наш сервис быстрого и безопасного интернета.\n"
        "Выбери нужный пункт в меню ниже:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu())

# Заглушка для HTTP-сервера, чтобы Render не ругался на закрытый порт
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO)
    # Запускаем и HTTP-сервер для порта, и поллинг телеграм-бота одновременно
    await web_server()
    print("Бот и веб-сервер успешно запущены...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
