import asyncio
import logging
import os
import uuid
import json
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from datetime import datetime, timezone, timedelta

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

PANEL_URL = os.getenv("PANEL_URL", "http://82.27.117.53:16843")      
PANEL_USER = os.getenv("PANEL_USER", "Spaysetta")          
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "Gggmoon9")      
INBOUND_ID = 1                              
# =============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция создания клиента в 3X-UI через API[cite: 1]
async def create_xray_client(telegram_id: int, user_name: str, hours: int = 0):
    client_uuid = str(uuid.uuid4())
    email = f"tg_{telegram_id}_{int(datetime.now().timestamp())}"
    
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
            login_url = f"{PANEL_URL}/login"
            async with session.post(login_url, json={"username": PANEL_USER, "password": PANEL_PASSWORD}) as resp:
                if resp.status != 200: 
                    return None
                
            add_url = f"{PANEL_URL}/panel/api/inbound/addClient"
            async with session.post(add_url, json=client_data) as resp:
                res_json = await resp.json()
                if res_json.get("success"):
                    return (
                        f"vless://{client_uuid}@82.27.117.53:14613"
                        f"?encryption=none&security=reality&fp=chrome&sni=yahoo.com"
                        f"&pbk=pSZY7tLeRZCp8RGQZ8tszKJ_MNRBGdsYH0vzdb_KvgQ"
                        f"&type=tcp&flow=xtls-rprx-vision#Spaysetta-{user_name}"
                    )
    except Exception as e:
        print(f"Ошибка API панели: {e}")
    return None

# Инлайн-меню в сообщении (чистый интерфейс)
def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Купить подписку", callback_data="buy_sub")],
        [InlineKeyboardButton(text="👤 Мой профиль", callback_data="profile"),
         InlineKeyboardButton(text="🎁 Тест на 5 часов", callback_data="free_test")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction"),
         InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])

def get_tariffs_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ 1 неделя — 80 ₽", callback_data="sub_week")],
        [InlineKeyboardButton(text="⚡️ 1 месяц — 120 ₽", callback_data="sub_month")],
        [InlineKeyboardButton(text="💎 2 месяца — 200 ₽", callback_data="sub_2months")],
        [InlineKeyboardButton(text="🔥 3 месяца — 400 ₽", callback_data="sub_3months")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

def get_back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        await message.delete()
    except:
        pass
        
    welcome_text = (
        f"<b>Привет, {message.from_user.first_name}! 👋</b>\n\n"
        "Добро пожаловать в <b>SPAYSETTA VPN</b> — твой проводник в свободный и быстрый интернет без границ."
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "buy_sub")
async def process_buy(callback: CallbackQuery):
    text = "💎 <b>Выбери подходящий тариф подписки:</b>"
    await callback.message.edit_text(text, reply_markup=get_tariffs_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("sub_"))
async def process_tariff_select(callback: CallbackQuery):
    tariffs = {
        "sub_week": ("1 неделя", 80),
        "sub_month": ("1 месяц", 120),
        "sub_2months": ("2 месяца", 200),
        "sub_3months": ("3 месяца", 400)
    }
    tariff_key = callback.data
    if tariff_key not in tariffs:
        return
        
    title, price = tariffs[tariff_key]
    
    text = (
        f"🇷🇺 <b>Оплата подписки: {title}</b>\n\n"
        f"Сумма к оплате: <b>{price} ₽</b>\n\n"
        "💳 Переведи указанную сумму или воспользуйся кнопкой меню внизу, "
        "после чего нажми кнопку ниже для получения ключа."
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил (получить ключ)", callback_data=f"paid_key_{price}")],
        [InlineKeyboardButton(text="⬅️ Назад к тарифам", callback_data="buy_sub")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data.startswith("paid_key_"))
async def paid_key_action(callback: CallbackQuery):
    price = callback.data.split("_")[2]
    user = callback.from_user
    
    await callback.message.edit_text("⏳ <b>Проверяем и генерируем ключ...</b>", parse_mode=ParseMode.HTML)
    vless_key = await create_xray_client(user.id, user.first_name, hours=0)
    
    if vless_key:
        success_text = f"🎉 <b>Спасибо за покупку! Твоя подписка активирована:</b>\n\n<code>{vless_key}</code>"
        await callback.message.edit_text(success_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
        try:
            await bot.send_message(ADMIN_ID, f"🔔 Успешная покупка!\n👤 @{user.username} (ID: {user.id})\n💰 Сумма: {price}₽")
        except:
            pass
    else:
        await callback.message.edit_text("❌ Ошибка создания ключа. Администратор уже уведомлен.", reply_markup=get_back_menu())
        await bot.send_message(ADMIN_ID, f"⚠️ Пользователь @{user.username} нажал оплату ({price}₽), но ключ не сгенерировался!")
    await callback.answer()

# Обработка данных из Mini App
@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        if action == "buy":
            title = data.get("title")
            price = data.get("price")
            
            text = (
                f"🇷🇺 <b>Оплата через Mini App: {title}</b>\n\n"
                f"Сумма к оплате: <b>{price} ₽</b>\n\n"
                "После перевода нажмите кнопку ниже для мгновенного получения ключа."
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил (получить ключ)", callback_data=f"paid_key_{price}")],
                [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_menu")]
            ])
            await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            
        elif action == "profile":
            await message.answer(f"👤 <b>Твой профиль:</b>\n\n🆔 ID: <code>{message.from_user.id}</code>\n🔴 Подписка: Активной нет", reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
            
    except Exception as e:
        print(f"Ошибка обработки WebApp data: {e}")

@dp.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    user = callback.from_user
    await callback.message.edit_text(f"👤 <b>Твой профиль:</b>\n\n🆔 ID: <code>{user.id}</code>\n🔴 Подписка: Активной подписки нет", reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def process_instruction(callback: CallbackQuery):
    text = (
        "📖 <b>Инструкция по подключению:</b>\n\n"
        "1. Скачай приложение <b>Happ</b> (iOS) или <b>v2rayNG</b> (Android).\n"
        "2. Скопируй свой VLESS-ключ после покупки или теста.\n"
        "3. Добавь его в приложение и запусти подключение!"
    )
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "free_test")
async def process_free_test(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Генерируем тест на 5 часов...</b>", parse_mode=ParseMode.HTML)
    vless_key = await create_xray_client(callback.from_user.id, callback.from_user.first_name, hours=5)
    
    if vless_key:
        text = f"🎁 <b>Тест успешно активирован!</b>\n\nСкопируй ключ ниже:\n\n<code>{vless_key}</code>\n\n⚠️ <i>Срок действия: 5 часов.</i>"
    else:
        text = "❌ Ошибка создания ключа. Попробуй позже."
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "back_to_menu")
async def process_back(callback: CallbackQuery):
    welcome_text = (
        f"<b>Привет, {callback.from_user.first_name}! 👋</b>\n\n"
        "Добро пожаловать в <b>SPAYSETTA VPN</b> — твой проводник в свободный и быстрый интернет без границ."
    )
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

# Веб-сервер для раздачи Mini App
async def handle_index(request):
    return aiohttp.web.FileResponse('index.html')

async def web_server():
    app = web.Application()
    app.router.add_get("/", handle_index)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()

async def main():
    logging.basicConfig(level=logging.INFO)
    await web_server()
    print("Бот и Mini App сервер успешно запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
