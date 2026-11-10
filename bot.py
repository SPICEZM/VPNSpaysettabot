import asyncio
import logging
import os
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode

TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Главное меню
def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Купить подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
         InlineKeyboardButton(text="🎁 Пробный период", callback_data="free_test")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction"),
         InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])
    return keyboard

# Меню выбора тарифов (появляется при нажатии «Купить подписку»)
def get_tariffs_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ 1 месяц — 150 ₽", callback_data="sub_1_month")],
        [InlineKeyboardButton(text="🔥 3 месяца — 400 ₽ (Выгода!)", callback_data="sub_3_months")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

# Кнопка возврата
def get_back_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

# Команда /start
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
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

# Обработка нажатий на кнопки (Callback Query)
@dp.callback_query(F.data == "buy_sub")
async def process_buy(callback: CallbackQuery):
    tariffs_text = (
        "💎 <b>Выбери подходящий тариф подписки:</b>\n\n"
        "• Полный доступ ко всем серверам (Нидерланды)\n"
        "• Высокая скорость до 1 Гбит/с\n"
        "• Подключение любых устройств (ПК, телефон, планшет)\n\n"
        "<i>Нажми на кнопку ниже для выбора срока:</i>"
    )
    await callback.message.edit_text(tariffs_text, reply_markup=get_tariffs_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    user = callback.from_user
    profile_text = (
        f"👤 <b>Твой профиль:</b>\n\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"👤 <b>Имя:</b> {user.first_name}\n"
        f"status 🔴 <b>Подписка:</b> Активной подписки нет\n\n"
        "<i>Хочешь получить доступ? Жми кнопку ниже! 👇</i>"
    )
    await callback.message.edit_text(profile_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def process_instruction(callback: CallbackQuery):
    instruction_text = (
        "📖 <b>Инструкция по подключению:</b>\n\n"
        "1. Скачай приложение для своего устройства (v2rayNG для Android, FoXray или Streisand для iOS, v2rayN для ПК).\n"
        "2. Купи подписку и получи свой индивидуальный VLESS-ключ.\n"
        "3. Скопируй ключ, добавь его в приложение и нажми кнопку подключения (старт).\n\n"
        "⚡️ Готово! Интернет без ограничений у тебя в кармане."
    )
    await callback.message.edit_text(instruction_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "free_test")
async def process_free_test(callback: CallbackQuery):
    test_text = (
        "🎁 <b>Пробный период:</b>\n\n"
        "Ты можешь протестировать скорость и стабильность нашего VPN абсолютно бесплатно!\n\n"
        "⚠️ <i>Функция бесплатного теста временно настраивается, скоро здесь будет выдаваться тестовый ключ на 24 часа.</i>"
    )
    await callback.message.edit_text(test_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "sub_1_month")
async def process_sub_1(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 <b>Оплата тарифа на 1 месяц (150 ₽):</b>\n\n"
        "Здесь скоро появится интеграция с оплатой (ЮKassa / СБП / CryptoBot).\n"
        "После оплаты бот автоматически выдаст тебе VLESS-ключ!",
        reply_markup=get_back_menu(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "sub_3_months")
async def process_sub_3(callback: CallbackQuery):
    await callback.message.edit_text(
        "💳 <b>Оплата тарифа на 3 месяца (400 ₽):</b>\n\n"
        "Здесь скоро появится интеграция с оплатой.\n"
        "После оплаты бот автоматически сгенерирует ключ!",
        reply_markup=get_back_menu(),
        parse_mode=ParseMode.HTML
    )
    await callback.answer()

@dp.callback_query(F.data == "back_to_menu")
async def process_back(callback: CallbackQuery):
    user_name = callback.from_user.first_name
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
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

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
    print("Интерактивный бот успешно запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
