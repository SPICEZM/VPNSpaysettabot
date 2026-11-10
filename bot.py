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
from aiocryptopay import AioCryptoPay, Networks

# ================= НАСТРОЙКИ =================
TOKEN = os.getenv("BOT_TOKEN", "ТВОЙ_ТОКЕН_БОТА_ИЗ_BOTFATHER")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Твой Telegram ID

# Доступы к панели 3X-UI
PANEL_URL = "http://82.27.117.53:16843"      
PANEL_USER = "твой_логин_от_панели"          
PANEL_PASSWORD = "твой_пароль_от_панели"      
INBOUND_ID = 1                              

# Токен Crypto Pay (от @CryptoBot)
CRYPTO_TOKEN = "673279:AA0ivNrdzr8wyr6gxIVN9tkKVnJ7zFfiADi"
# =============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()
crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)

def get_current_time():
    msk_timezone = timezone(timedelta(hours=3))
    return datetime.now(msk_timezone).strftime("%d.%m.%Y в %H:%M")

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
        [InlineKeyboardButton(text="⏳ 1 неделя — 80 ₽ (~0.85 USDT)", callback_data="sub_week")],
        [InlineKeyboardButton(text="⚡️ 1 месяц — 120 ₽ (~1.30 USDT)", callback_data="sub_month")],
        [InlineKeyboardButton(text="💎 2 месяца — 200 ₽ (~2.15 USDT)", callback_data="sub_2months")],
        [InlineKeyboardButton(text="🔥 3 месяца — 400 ₽ (~4.30 USDT)", callback_data="sub_3months")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

def get_back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

# Функция создания клиента в 3X-UI
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
                if resp.status != 200: return None
                
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

@dp.message(Command("start"))
async def cmd_start(message: Message):
    welcome_text = (
        f"<b>Привет, {message.from_user.first_name}! 👋</b>\n\n"
        "Добро пожаловать в <b>SPAYSETTA VPN</b> — твой проводник в свободный и быстрый интернет."
    )
    await message.answer(welcome_text, reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)

@dp.callback_query(F.data == "buy_sub")
async def process_buy(callback: CallbackQuery):
    tariffs_text = "💎 <b>Выбери подходящий тариф подписки:</b>\n\nОплата происходит через официальный Telegram Wallet в криптовалюте (USDT/TON)."
    await callback.message.edit_text(tariffs_text, reply_markup=get_tariffs_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "profile")
async def process_profile(callback: CallbackQuery):
    user = callback.from_user
    await callback.message.edit_text(f"👤 <b>Твой профиль:</b>\n\n🆔 ID: <code>{user.id}</code>", reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "instruction")
async def process_instruction(callback: CallbackQuery):
    text = "📖 <b>Инструкция:</b>\n\n1. Скачай Happ (iOS) или v2rayNG (Android).\n2. Скопируй ключ и добавь в приложение."
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "free_test")
async def process_free_test(callback: CallbackQuery):
    await callback.message.edit_text("⏳ <b>Генерируем тест на 5 часов...</b>", parse_mode=ParseMode.HTML)
    vless_key = await create_xray_client(callback.from_user.id, callback.from_user.first_name, hours=5)
    
    if vless_key:
        text = f"🎁 <b>Тест активирован!</b>\n\n<code>{vless_key}</code>\n\n⚠️ <i>Срок действия: 5 часов.</i>"
    else:
        text = "❌ Ошибка создания ключа."
    await callback.message.edit_text(text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)

# Создание счета через Crypto Pay для каждого тарифа
async def create_invoice_for_user(callback: CallbackQuery, amount_usd: float, title: str):
    try:
        # Создаем инвойс в USDT
        invoice = await crypto.create_invoice(amount=amount_usd, fiat='USD', currency_type='fiat', description=f"Подписка Spaysetta VPN: {title}")
        
        pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить в Wallet", url=invoice.bot_invoice_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_{invoice.invoice_id}")],
            [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
        ])
        
        await callback.message.edit_text(
            f"💳 <b>Счет на оплату: {title}</b>\n\n"
            f"Сумма: <b>${amount_usd} USDT</b>\n\n"
            "Нажми кнопку ниже для оплаты через Telegram Wallet. После оплаты нажми «Проверить оплату».",
            reply_markup=pay_keyboard,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        await callback.message.edit_text(f"❌ Ошибка создания платежа: {e}", reply_markup=get_back_menu())
    await callback.answer()

@dp.callback_query(F.data == "sub_week")
async def sub_week(callback: CallbackQuery): await create_invoice_for_user(callback, 0.90, "1 неделя")

@dp.callback_query(F.data == "sub_month")
async def sub_month(callback: CallbackQuery): await create_invoice_for_user(callback, 1.40, "1 месяц")

@dp.callback_query(F.data == "sub_2months")
async def sub_2months(callback: CallbackQuery): await create_invoice_for_user(callback, 2.30, "2 месяца")

@dp.callback_query(F.data == "sub_3months")
async def sub_3months(callback: CallbackQuery): await create_invoice_for_user(callback, 4.50, "3 месяца")

# Проверка оплаты пользователем
@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: CallbackQuery):
    invoice_id = int(callback.data.split("_")[1])
    invoices = await crypto.get_invoices(invoice_ids=invoice_id)
    
    if invoices and invoices[0].status == "paid":
        await callback.message.edit_text("✅ <b>Оплата получена! Создаем твой ключ...</b>", parse_mode=ParseMode.HTML)
        vless_key = await create_xray_client(callback.from_user.id, callback.from_user.first_name, hours=0)
        
        if vless_key:
            success_text = f"🎉 <b>Спасибо за покупку! Твоя подписка активирована:</b>\n\n<code>{vless_key}</code>"
        else:
            success_text = "❌ Оплата прошла, но произошла ошибка при создании ключа. Админ уже уведомлен!"
            await bot.send_message(ADMIN_ID, f"⚠️ Пользователь @{callback.from_user.username} оплатил счет, но ключ не создался!")
            
        await callback.message.answer(success_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
    else:
        await callback.answer("⏳ Платеж еще не поступил. Оплатите счет в Wallet и попробуйте снова.", show_alert=True)

@dp.callback_query(F.data == "back_to_menu")
async def process_back(callback: CallbackQuery):
    await callback.message.edit_text(f"<b>Привет, {callback.from_user.first_name}! 👋</b>", reply_markup=get_main_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

async def handle_ping(request): return web.Response(text="Bot is running!")

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
    print("Бот с Crypto Pay запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
