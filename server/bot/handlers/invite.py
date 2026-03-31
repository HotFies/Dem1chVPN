"""
Dem1chVPN Bot — Invite Handler
Create and manage invitation links.
"""
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..config import config
from ..keyboards.menus import back_button
from ..services.user_manager import UserManager
from ..services.xray_config import XrayConfigManager
from ..services.invite_manager import InviteManager
from ..utils.qr_generator import generate_qr_code
from ..utils.formatters import format_user_info

router = Router()


class InviteStates(StatesGroup):
    waiting_name = State()
    waiting_limit = State()
    waiting_days = State()


@router.callback_query(F.data == "users:invite")
async def invite_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "🎟️ <b>Создание приглашения</b>\n\n"
        "Введите имя для нового пользователя:"
    )
    await state.set_state(InviteStates.waiting_name)
    await callback.answer()


@router.message(InviteStates.waiting_name)
async def invite_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name or len(name) > 50:
        await message.answer("❌ Имя от 1 до 50 символов:")
        return
    await state.update_data(name=name)
    await message.answer(
        f"👤 Имя: <b>{name}</b>\n\n"
        "📊 Лимит трафика в ГБ (0 = безлимит):"
    )
    await state.set_state(InviteStates.waiting_limit)


@router.message(InviteStates.waiting_limit)
async def invite_limit(message: Message, state: FSMContext):
    try:
        gb = float(message.text.strip())
        if gb < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число:")
        return

    traffic_limit = int(gb * 1024 ** 3) if gb > 0 else None
    await state.update_data(traffic_limit=traffic_limit, traffic_gb=gb)
    await message.answer(
        f"📊 Лимит: <b>{'♾️' if not traffic_limit else f'{gb} GB'}</b>\n\n"
        "⏰ Срок действия аккаунта в днях (0 = бессрочно):"
    )
    await state.set_state(InviteStates.waiting_days)


@router.message(InviteStates.waiting_days)
async def invite_days(message: Message, state: FSMContext):
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число:")
        return

    data = await state.get_data()
    await state.clear()

    # Create invitation
    mgr = InviteManager()
    invite = await mgr.create_invite(
        name=data["name"],
        traffic_limit=data.get("traffic_limit"),
        days_valid=days if days > 0 else None,
        created_by=message.from_user.id,
    )

    # Bot username for the link
    bot_info = await message.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=inv_{invite.code}"

    limit_str = f"{data.get('traffic_gb', 0)} GB" if data.get("traffic_limit") else "♾️"
    days_str = f"{days} дней" if days > 0 else "♾️ Бессрочно"

    await message.answer(
        f"🎟️ <b>Приглашение создано!</b>\n\n"
        f"🔗 Ссылка:\n<code>{link}</code>\n\n"
        f"👤 Имя: <b>{data['name']}</b>\n"
        f"📊 Лимит: <b>{limit_str}</b>\n"
        f"⏰ Срок: <b>{days_str}</b>\n\n"
        "Отправьте эту ссылку получателю.\n"
        "При переходе бот автоматически:\n"
        "• Создаст аккаунт\n"
        "• Выдаст VLESS ссылку и QR-код\n"
        "• Отправит инструкцию по подключению",
        reply_markup=back_button("menu:users"),
    )


# ── Handle invite deep link ──

@router.message(F.text.startswith("/start inv_"))
async def invite_activate(message: Message):
    """Activate an invitation link."""
    code = message.text.replace("/start inv_", "").strip()

    inv_mgr = InviteManager()
    invite = await inv_mgr.get_invite(code)

    if not invite or not invite.is_active or invite.is_exhausted:
        await message.answer(
            "❌ <b>Приглашение недействительно</b>\n\n"
            "Ссылка истекла или уже использована. Обратитесь к администратору."
        )
        return

    # Check if user already exists
    user_mgr = UserManager()
    existing = await user_mgr.get_user_by_telegram_id(message.from_user.id)
    if existing:
        await message.answer(
            f"✅ У вас уже есть аккаунт: <b>{existing.name}</b>\n"
            "Используйте /start для доступа к меню."
        )
        return

    # Create user
    user = await user_mgr.create_user(
        name=invite.name,
        traffic_limit=invite.traffic_limit,
        expiry_days=invite.days_valid,
        telegram_id=message.from_user.id,
    )

    # Add to Xray
    xray_mgr = XrayConfigManager()
    await xray_mgr.add_client(user.uuid, user.email)

    # Mark invite as used
    await inv_mgr.use_invite(code)

    # Generate VLESS link
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"

    # Send welcome
    await message.answer(
        f"🎉 <b>Добро пожаловать в Dem1chVPN!</b>\n\n"
        f"Аккаунт <b>{user.name}</b> создан.\n\n"
        f"{format_user_info(user)}\n\n"
        f"🔗 <b>Ссылка подключения:</b>\n"
        f"<code>{vless_url}</code>\n\n"
        f"📡 <b>Подписка (автообновление):</b>\n"
        f"<code>{sub_url}</code>\n\n"
        "Нажмите /start для доступа к меню."
    )

    # Send QR
    from aiogram.types import BufferedInputFile
    qr_bytes = generate_qr_code(vless_url)
    qr_file = BufferedInputFile(qr_bytes, filename=f"dem1chvpn_{user.name}.png")
    await message.answer_photo(
        qr_file,
        caption=f"📱 QR-код для <b>{user.name}</b>\nСканируйте в v2rayNG/Streisand",
    )

    # Notify admin
    for admin_id in config.ADMIN_IDS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🆕 Новый пользователь по приглашению!\n"
                f"👤 {user.name} (@{message.from_user.username or '—'})\n"
                f"🎟️ Код: {code}",
            )
        except Exception:
            pass
