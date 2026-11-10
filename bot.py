import asyncio
import logging
import os
import uuid
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from datetime import datetime, timezone, timedelta

# ================= НАСТРОЙКИ ПАНЕЛИ И БОТА =================
TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_БОТА_ИЗ_BOTFATHER")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Твой Telegram ID

PANEL_URL = "http://82.27.117.53:16843"      # Адрес и порт панели 3X-UI (без слэша на конце)
PANEL_USER = "твой_логин_от_панели"          # Логин от панели 3X-UI
PANEL_PASSWORD = "твой_пароль_от_панели"      # Пароль от панели 3X-UI
INBOUND_ID = 1                              # ID твоего инбаунда (Spaysetta Main)
# ==========================================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

def get_current_time():
    msk_timezone = timezone(timedelta(hours=3))
    return datetime.now(msk_timezone).strftime("%d.%m.%Y в %H:%M")

def get_main_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Купить подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
         InlineKeyboardButton(text="🎁 Тест на 5 часов", callback_data="free_test")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction"),
         InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])
    return keyboard

def get_tariffs_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ 1 неделя — 80 ₽", callback_data="sub_1_week")],
        [InlineKeyboardButton(text="⚡️ 1 месяц — 120 ₽ (вместо 150 ₽)", callback_data="sub_1_month")],
        [InlineKeyboardButton(text="💎 2 месяца — 200 ₽", callback_data="sub_2_months")],
        [InlineKeyboardButton(text="🔥 3 месяца — 400 ₽", callback_data="sub_3_months")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

def get_back_menu():
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])
    return keyboard

# Функция создания клиента в панели 3X-UI через API
async def create_xray_client(telegram_id: int, user_name: str, hours: int = 0):
    client_uuid = str(uuid.uuid4())
    email = f"tg_{telegram_id}"
    
    expiry_time = 0
    if hours > 0:
        expiry_time = int((datetime.now(timezone.utc) + timedelta(hours=hours)).timestamp() * 1000)

    client_data = {
        "id": INBOUND_ID,
        "settings": f"""{{
            "clients": [{{
                "id": "{client_uuid}",
                "alterId": 0,
                "email": "{email}",
                "limitIp": 2,
                "totalGB": 0,
                "expiryTime": {expiry_time},
                "enable": true,
                "tgId": "{telegram_id}",
                "subId": ""
            }}]
        }}"""
    }

    try:
        async with aiohttp.ClientSession() as session:
            # 1. Авторизация в панели
            login_url = f"{PANEL_URL}/login"
            login_payload = {"username": PANEL_USER, "password": PANEL_PASSWORD}
            
            async with session.post(login_url, json=login_payload) as resp:
                if resp.status != 200:
                    return None
                
            # 2. Добавление клиента
            add_url = f"{PANEL_URL}/panel/api/inbound/addClient"
            async with session.post(add_url, json=client_data) as resp:
                res_json = await resp.json()
                if res_json.get("success"):
                    # Формируем готовую VLESS-ссылку с Reality
                    vless_link = (
                        f"vless://{client_uuid}@82.27.117.53:14613"
                        f"?encryption=none&security=reality&fp=chrome&sni=yahoo.com"
                        f"&pbk=pSZY7tLeRZCp8RGQZ8tszKJ_MNRBGdsYH0vzdb_KvgQ"
                        f"&type=tcp&flow=xtls-rprx-vision#Spaysetta-{user_name}"
                    )
                    return vless_link
    except Exception as e:
        print(f"Ошибка API панели: {e}")
        
    return None

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

@dp.callback_query(F.data == "buy_sub")
async def process_buy(callback: CallbackQuery):
    tariffs_text = (
        "💎 <b>Выбери подходящий тариф подписки:</b>\n\n"
        "• Полный доступ ко всем серверам (Нидерланды)\n"
        "• Высокая скорость до 1 Гбит/с\n"
        "• Подключение любых устройств\n\n"
        "<i>Выбирай срок ниже со скидкой: 👇</i>"
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
        f"🔴 <b>Подписка:</b> Активной подписки нет\n\n"
        "<i>Хочешь получить доступ? Жми кнопку ниже! 👇</i>"
    )
    await callback.message.edit_text(profile_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def process_instruction(callback: CallbackQuery):
    instruction_text = (
        "📖 <b>Инструкция по подключению:</b>\n\n"
        "Для работы мы используем самые лучшие и стабильные приложения:\n\n"
        "🍏 <b>Для iPhone / iPad / Mac:</b>\n"
        "• Скачай приложение <b>Happ</b> в App Store.\n\n"
        "🤖 <b>Для Android:</b>\n"
        "• Скачай приложение <b>v2rayNG</b> в Google Play.\n\n"
        "<b>Как подключиться:</b>\n"
        "1. Скопируй свой VLESS-ключ после покупки или теста.\n"
        "2. Открой приложение, добавь ключ (через буфер обмена или плюсик).\n"
        "3. Нажми кнопку запуска и пользуйся интернетом без ограничений!"
    )
    await callback.message.edit_text(instruction_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "free_test")
async def process_free_test(callback: CallbackQuery):
    user = callback.from_user
    await callback.message.edit_text("⏳ <b>Генерируем твой персональный тест на 5 часов...</b>", parse_mode=ParseMode.HTML)
    
    # Автоматически создаем тестовый ключ через API панели
    vless_key = await create_xray_client(user.id, user.first_name, hours=5)
    
    if vless_key:
        test_text = (
            "🎁 <b>Твой пробный период (5 часов) активирован!</b>\n\n"
            "Скопируй ключ ниже и вставь в приложение (Happ / v2rayNG):\n\n"
            f"<code>{vless_key}</code>\n\n"
            "⚠️ <i>Ключ автоматически отключится через 5 часов.</i>"
        )
    else:
        test_text = "❌ Ошибка при создании ключа. Попробуй позже или обратись в поддержку."

    await callback.message.edit_text(test_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

# Обработчики тарифов (отправляют заявку админу)
async def handle_tariff_selection(callback: CallbackQuery, tariff_name: str, price: str):
    user = callback.from_user
    buy_time = get_current_time()
    try:
        admin_notification = (
            f"💰 <b>НОВЫЙ ЗАКАЗ: {tariff_name} ({price})</b>\n\n"
            f"👤 <b>Пользователь:</b> {user.first_name} (@{user.username if user.username else 'нет'})\n"
            f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
            f"⏰ <b>Время:</b> {buy_time}"
        )
        await bot.send_message(ADMIN_ID, admin_notification, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Не удалось отправить уведомление админу: {e}")

    text = (
        f"💳 <b>Тариф: {tariff_name} — {price}</b>\n\n"
        "Счет на оплату сформирован.\n"
        "После перевода средств администратор выдаст тебе ключ, либо здесь появится автооплата!"
    )
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "sub_1_week")
async def process_sub_week(callback: CallbackQuery):
    await handle_tariff_selection(callback, "1 неделя", "80 ₽")

@dp.callback_query(F.data == "sub_1_month")
async def process_sub_1(callback: CallbackQuery):
    await handle_tariff_selection(callback, "1 месяц", "120 ₽")

@dp.callback_query(F.data == "sub_2_months")
async def process_sub_2(callback: CallbackQuery):
    await handle_tariff_selection(callback, "2 месяца", "200 ₽")

@dp.callback_query(F.data == "sub_3_months")
async def process_sub_3(callback: CallbackQuery):
    await handle_tariff_selection(callback, "3 месяца", "400 ₽")

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
    print("Бот Spaysetta VPN успешно запущен и подключен к панели!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
