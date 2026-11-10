import asyncio
import logging
import os
import uuid
import json
import aiohttp
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.enums import ParseMode
from datetime import datetime, timezone, timedelta
from aiocryptopay import AioCryptoPay, Networks

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))

# URL твоего приложения на Render (например: https://spaysetta-vpn.onrender.com)
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://tvoj-sait.onrender.com")

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

def get_main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⚡️ Открыть магазин (Mini App)", web_app=WebAppInfo(url=WEBAPP_URL))],
        [InlineKeyboardButton(text="🎁 Тест на 5 часов", callback_data="free_test")],
        [InlineKeyboardButton(text="📖 Инструкция", callback_data="instruction"),
         InlineKeyboardButton(text="💬 Поддержка", url="https://t.me/твой_логин")]
    ])

def get_back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Главное меню", callback_data="back_to_menu")]
    ])

@dp.message(Command("start"))
async def cmd_start(message: Message):
    try:
        await message.delete()
    except:
        pass
        
    welcome_text = (
        f"<b>Привет, {message.from_user.first_name}! 👋</b>\n\n"
        "Добро пожаловать в <b>SPAYSETTA VPN</b> — нажми кнопку ниже, чтобы открыть каталог подписок в удобном окне!"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

# Обработка данных, прилетевших из Mini App
@dp.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        if action == "buy":
            title = data.get("title")
            price = data.get("price")
            user = message.from_user
            
            text = (
                f"🇷🇺 <b>Оплата подписки: {title}</b>\n\n"
                f"Сумма к оплате: <b>{price} ₽</b>\n\n"
                "💳 Чтобы оплатить без засвета номера, переведите сумму по реквизитам или воспользуйтесь поддержкой, "
                "после чего нажмите кнопку ниже для мгновенного получения ключа."
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Я оплатил (получить ключ)", callback_data=f"app_paid_{price}")],
                [InlineKeyboardButton(text="⬅️ В меню", callback_data="back_to_menu")]
            ])
            await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            
        elif action == "profile":
            await message.answer(f"👤 <b>Твой профиль:</b>\n\n🆔 ID: <code>{message.from_user.id}</code>\n🔴 Подписка: Активной нет", reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
            
    except Exception as e:
        print(f"Ошибка обработки WebApp data: {e}")

@dp.callback_query(F.data.startswith("app_paid_"))
async def app_paid_action(callback: CallbackQuery):
    amount = callback.data.split("_")[2]
    user = callback.from_user
    
    await callback.message.edit_text("⏳ <b>Генерируем твой ключ подписки...</b>", parse_mode=ParseMode.HTML)
    vless_key = await create_xray_client(user.id, user.first_name, hours=0)
    
    if vless_key:
        success_text = f"🎉 <b>Оплата подтверждена! Твой ключ:</b>\n\n<code>{vless_key}</code>"
        await callback.message.edit_text(success_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
        try:
            await bot.send_message(ADMIN_ID, f"🔔 Успешная покупка через Mini App!\n👤 @{user.username} (ID: {user.id})\n💰 Сумма: {amount}₽")
        except:
            pass
    else:
        await callback.message.edit_text("❌ Ошибка генерации ключа. Обратитесь в поддержку.", reply_markup=get_back_menu())
    await callback.answer()

@dp.callback_query(F.data == "free_test")
async def process_free_test(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Генерируем тест на 5 часов...</b>", parse_mode=ParseMode.HTML)
    vless_key = await create_xray_client(callback.from_user.id, callback.from_user.first_name, hours=5)
    
    if vless_key:
        text = f"🎁 <b>Тест успешно активирован!</b>\n\nСкопируй ключ ниже:\n\n<code>{vless_key}</code>"
    else:
        text = "❌ Ошибка создания ключа."
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_Mode=ParseMode.HTML)

@dp.callback_query(F.data == "instruction")
async def process_instruction(callback: CallbackQuery):
    text = "📖 <b>Инструкция:</b> Скачай Happ (iOS) или v2rayNG (Android), вставь ключ и подключись!"
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "back_to_menu")
async def process_back(callback: CallbackQuery):
    welcome_text = "<b>Привет! 👋</b>\nДобро пожаловать в <b>SPAYSETTA VPN</b>."
    await callback.message.edit_text(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

# Веб-сервер для бота и выдачи index.html
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
    print("Mini App сервер и бот запущены!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
