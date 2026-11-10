import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Премиальное главное меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Купить подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
         InlineKeyboardButton(text="🎁 Пробный период", callback_data="free_test")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction"),
         InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])
    return keyboard

# Команда /start с сочным оформлением
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    
    welcome_text = (
        f"<b>Привет, {user_name}! 👋</b>\n\n"
        "Добро пожаловать в <b>SPAYSETTA VPN</b> — твой проводник в свободный, быстрый и безопасный интернет без границ.\n\n"
        "🚀 <b>Наши преимущества:</b>\n"
        "• Высокая скорость и низкий пинг\n"
        "• Обход любых блокировок (YouTube, TikTok, Instagram)\n"
        "• Протокол нового поколения\n"
        "• Дешевые тарифы\n\n"
        "👇👇👇"
    )
    
    await message.answer(
        welcome_text, 
        reply_markup=get_main_menu(), 
        parse_mode=ParseMode.HTML
    )

# HTTP-заглушка для Render
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
    await web_server()
    print("Премиум-бот успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
