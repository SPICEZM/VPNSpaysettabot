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
TOKEN = os.getenv("BOT_TOKEN")
PORT = int(os.getenv("PORT", 10000))
ADMIN_ID = int(os.getenv("ADMIN_ID", "123456789"))  # Укажи свой Telegram ID

# Реквизиты для оплаты через СБП / перевод
SBP_PHONE = os.getenv("SBP_PHONE", "+79000000000")  # Твой номер телефона
SBP_BANK = os.getenv("SBP_BANK", "Озон Банк / Сбер")   # Название банка

PANEL_URL = os.getenv("PANEL_URL", "http://82.27.117.53:16843")      
PANEL_USER = os.getenv("PANEL_USER", "Spaysetta")          
PANEL_PASSWORD = os.getenv("PANEL_PASSWORD", "Gggmoon9")      
INBOUND_ID = 1                              

CRYPTO_TOKEN = os.getenv("CRYPTO_TOKEN", "673279:AA0ivNrdzr8wyr6gxIVN9tkKVnJ7zFfiADi")
# =============================================

bot = Bot(token=TOKEN)
dp = Dispatcher()
crypto = None

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
        [InlineKeyboardButton(text="💳 Рубли (СБП / Карта)", callback_data="pay_rub_menu")],
        [InlineKeyboardButton(text="💎 Криптовалюта (USDT/TON)", callback_data="pay_crypto_menu")],
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

def get_rub_tariffs_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ 1 неделя — 80 ₽", callback_data="sbp_week")],
        [InlineKeyboardButton(text="⚡️ 1 месяц — 120 ₽", callback_data="sbp_month")],
        [InlineKeyboardButton(text="💎 2 месяца — 200 ₽", callback_data="sbp_2months")],
        [InlineKeyboardButton(text="🔥 3 месяца — 400 ₽", callback_data="sbp_3months")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору оплаты", callback_data="buy_sub")]
    ])

def get_crypto_tariffs_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ 1 неделя — $0.90", callback_data="sub_week")],
        [InlineKeyboardButton(text="⚡️ 1 месяц — $1.40", callback_data="sub_month")],
        [InlineKeyboardButton(text="💎 2 месяца — $2.30", callback_data="sub_2months")],
        [InlineKeyboardButton(text="🔥 3 месяца — $4.50", callback_data="sub_3months")],
        [InlineKeyboardButton(text="⬅️ Назад к выбору оплаты", callback_data="buy_sub")]
    ])

def get_back_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="back_to_menu")]
    ])

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
    text = "💎 <b>Выберите способ оплаты подписки:</b>"
    await callback.message.edit_text(text, reply_markup=get_tariffs_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "pay_rub_menu")
async def pay_rub_menu(callback: CallbackQuery):
    text = "🇷🇺 <b>Выберите тариф для оплаты в рублях (СБП):</b>"
    await callback.message.edit_text(text, reply_markup=get_rub_tariffs_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "pay_crypto_menu")
async def pay_crypto_menu(callback: CallbackQuery):
    text = "🪙 <b>Выберите тариф для оплаты криптовалютой (USDT/TON):</b>"
    await callback.message.edit_text(text, reply_markup=get_crypto_tariffs_menu(), parse_mode=ParseMode.HTML)
    await callback.answer()

# Обработка выбора рублевого тарифа через СБП
async def process_sbp_order(callback: CallbackQuery, amount: int, title: str):
    user = callback.from_user
    text = (
        f"🇷🇺 <b>Оплата по СБП: {title}</b>\n\n"
        f"Сумма к оплате: <b>{amount} ₽</b>\n\n"
        f"📲 <b>Реквизиты для перевода:</b>\n"
        f"Банк: <code>{SBP_BANK}</code>\n"
        f"Номер телефона: <code>{SBP_PHONE}</code>\n\n"
        f"⚠️ <i>Обязательно переведите точную сумму. После перевода нажмите кнопку ниже, чтобы уведомить администратора.</i>"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"sbp_paid_{user.id}_{amount}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="pay_rub_menu")]
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
    await callback.answer()

@dp.callback_query(F.data == "sbp_week")
async def sbp_week(callback: CallbackQuery): await process_sbp_order(callback, 80, "1 неделя")

@dp.callback_query(F.data == "sbp_month")
async def sbp_month(callback: CallbackQuery): await process_sbp_order(callback, 120, "1 месяц")

@dp.callback_query(F.data == "sbp_2months")
async def sbp_2months(callback: CallbackQuery): await process_sbp_order(callback, 200, "2 месяца")

@dp.callback_query(F.data == "sbp_3months")
async def sbp_3months(callback: CallbackQuery): await process_sbp_order(callback, 400, "3 месяца")

# Пользователь нажал "Я оплатил" через СБП
@dp.callback_query(F.data.startswith("sbp_paid_"))
async def sbp_paid_notify(callback: CallbackQuery):
    parts = callback.data.split("_")
    user_id = int(parts[2])
    amount = parts[3]
    user = callback.from_user
    
    # Сообщение пользователю
    await callback.message.edit_text(
        "⏳ <b>Заявка принята!</b>\х"
        "Мы проверяем поступление средств. Как только платеж подтвердится, бот пришлет ваш ключ.",
        reply_markup=get_back_menu(), parse_mode=ParseMode.HTML
    )
    
    # Уведомление админу с кнопкой быстрого подтверждения
    admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить и выдать ключ", callback_data=f"adm_approve_{user_id}")],
        [InlineKeyboardButton(text="❌ Отклонить", callback_data=f"adm_reject_{user_id}")]
    ])
    
    await bot.send_message(
        ADMIN_ID,
        f"🔔 <b>Новый запрос на оплату (СБП)!</b>\n\n"
        f"👤 Пользователь: @{user.username or 'нет'} (ID: <code>{user.id}</code>)\n"
        f"💰 Сумма: <b>{amount} ₽</b>",
        reply_markup=admin_keyboard,
        parse_mode=ParseMode.HTML
    )
    await callback.answer("Заявка отправлена администратору!")

# Админ подтверждает платеж
@dp.callback_query(F.data.startswith("adm_approve_"))
async def adm_approve(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("Недостаточно прав!", show_alert=True)
        return
        
    target_user_id = int(callback.data.split("_")[2])
    
    # Генерируем ключ
    vless_key = await create_xray_client(target_user_id, "User", hours=0)
    
    if vless_key:
        try:
            await bot.send_message(
                target_user_id,
                f"🎉 <b>Оплата подтверждена администратором! Твоя подписка активирована:</b>\n\n<code>{vless_key}</code>",
                reply_markup=get_back_menu(),
                parse_Mode=ParseMode.HTML
            )
            await callback.message.edit_text("✅ <b>Платеж подтвержден, ключ успешно отправлен пользователю!</b>")
        except Exception as e:
            await callback.message.edit_text(f"⚠️ Ключ создан, но не удалось отправить пользователю: {e}")
    else:
        await callback.message.edit_text("❌ Ошибка при создании ключа в панели 3X-UI!")
    await callback.answer()

@dp.callback_query(F.data.startswith("adm_reject_"))
async def adm_reject(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    target_user_id = int(callback.data.split("_")[2])
    try:
        await bot.send_message(target_user_id, "❌ Ваша оплата не была подтверждена администратором. Если это ошибка, обратитесь в поддержку.", reply_markup=get_back_menu())
    except:
        pass
    await callback.message.edit_text("❌ Заявка отклонена.")
    await callback.answer()

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

# Создание счета через Crypto Pay[cite: 1]
async def create_invoice_for_user(callback: CallbackQuery, amount_usd: float, title: str):
    try:
        invoice = await crypto.create_invoice(amount=amount_usd, fiat='USD', currency_type='fiat', description=f"Spaysetta VPN: {title}")
        
        pay_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить в Wallet", url=invoice.bot_invoice_url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"check_{invoice.invoice_id}")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="pay_crypto_menu")]
        ])
        
        await callback.message.edit_text(
            f"💳 <b>Счет на оплату: {title}</b>\n\n"
            f"Сумма: <b>${amount_usd} USDT</b>\n\n"
            "Нажми кнопку ниже для оплаты через Telegram Wallet. После оплаты обязательно нажми «Проверить оплату».",
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

# Проверка оплаты криптой[cite: 1]
@dp.callback_query(F.data.startswith("check_"))
async def check_payment(callback: CallbackQuery):
    invoice_id = int(callback.data.split("_")[1])
    try:
        invoices = await crypto.get_invoices(invoice_ids=[invoice_id])
        
        if invoices and invoices[0].status == "paid":
            await callback.message.edit_text("✅ <b>Оплата получена! Генерируем твой ключ...</b>", parse_mode=ParseMode.HTML)
            vless_key = await create_xray_client(callback.from_user.id, callback.from_user.first_name, hours=0)
            
            if vless_key:
                success_text = f"🎉 <b>Спасибо за покупку! Твоя подписка активирована:</b>\n\n<code>{vless_key}</code>"
            else:
                success_text = "❌ Оплата прошла, но произошла ошибка при создании ключа. Администратор уже уведомлен."
                await bot.send_message(ADMIN_ID, f"⚠️ Пользователь @{callback.from_user.username} оплатил счет, но ключ в панели не создался!")
                
            await callback.message.answer(success_text, reply_markup=get_back_menu(), parse_mode=ParseMode.HTML)
        else:
            await callback.answer("⏳ Платеж еще не поступил. Оплати счет в Wallet и попробуй снова.", show_alert=True)
    except Exception as e:
        await callback.answer(f"⚠️ Ошибка проверки: {e}", show_alert=True)

@dp.callback_query(F.data == "back_to_menu")
async def process_back(callback: CallbackQuery):
    welcome_text = (
        f"<b>Привет, {callback.from_user.first_name}! 👋</b>\n\n"
        "Добро пожаловать в <b>SPAYSETTA VPN</b> — твой проводник в свободный и быстрый интернет без границ."
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
    global crypto
    crypto = AioCryptoPay(token=CRYPTO_TOKEN, network=Networks.MAIN_NET)
    
    logging.basicConfig(level=logging.INFO)
    await web_server()
    print("Бот Spaysetta успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
