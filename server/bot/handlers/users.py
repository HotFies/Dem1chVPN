"""
XShield Bot — User Management Handler
Add/list/delete/toggle users via Telegram bot.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..config import config
from ..keyboards.menus import users_menu, user_actions, back_button, confirm_action
from ..services.user_manager import UserManager
from ..services.xray_config import XrayConfigManager
from ..utils.qr_generator import generate_qr_code
from ..utils.formatters import format_traffic, format_user_info

router = Router()


class AddUserStates(StatesGroup):
    """FSM states for adding a user."""
    waiting_name = State()
    waiting_traffic_limit = State()
    waiting_expiry = State()


# ── Add User Flow ──

@router.callback_query(F.data == "users:add")
async def users_add_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new user."""
    await callback.message.edit_text(
        "➕ <b>Добавление пользователя</b>\n\n"
        "Введите имя нового пользователя:\n\n"
        "<i>Или нажмите ◀️ Отмена</i>",
        reply_markup=back_button("menu:users"),
    )
    await state.set_state(AddUserStates.waiting_name)
    await callback.answer()


@router.callback_query(F.data == "menu:users", AddUserStates.waiting_name)
@router.callback_query(F.data == "menu:users", AddUserStates.waiting_traffic_limit)
@router.callback_query(F.data == "menu:users", AddUserStates.waiting_expiry)
async def users_add_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel adding a user."""
    await state.clear()
    await callback.message.edit_text(
        "👥 <b>Пользователи</b>\n\n"
        "❌ Добавление отменено.",
        reply_markup=users_menu(),
    )
    await callback.answer()

@router.message(AddUserStates.waiting_name)
async def users_add_name(message: Message, state: FSMContext):
    """Receive user name."""
    name = message.text.strip()
    if not name or len(name) > 50:
        await message.answer("❌ Имя должно быть от 1 до 50 символов. Попробуйте ещё раз:")
        return

    await state.update_data(name=name)
    await message.answer(
        f"👤 Имя: <b>{name}</b>\n\n"
        "📊 Введите лимит трафика в ГБ (или 0 для безлимита):",
    )
    await state.set_state(AddUserStates.waiting_traffic_limit)


@router.message(AddUserStates.waiting_traffic_limit)
async def users_add_traffic(message: Message, state: FSMContext):
    """Receive traffic limit."""
    try:
        gb = float(message.text.strip())
        if gb < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите число (0 = безлимит):")
        return

    traffic_limit = int(gb * 1024 * 1024 * 1024) if gb > 0 else None
    await state.update_data(traffic_limit=traffic_limit)

    await message.answer(
        f"📊 Лимит: <b>{'♾️ Безлимит' if traffic_limit is None else f'{gb} GB'}</b>\n\n"
        "⏰ Введите срок действия в днях (или 0 для бессрочного):",
    )
    await state.set_state(AddUserStates.waiting_expiry)


@router.message(AddUserStates.waiting_expiry)
async def users_add_expiry(message: Message, state: FSMContext):
    """Receive expiry and create user."""
    try:
        days = int(message.text.strip())
        if days < 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Введите целое число (0 = бессрочно):")
        return

    data = await state.get_data()
    await state.clear()

    # Create user
    mgr = UserManager()
    user = await mgr.create_user(
        name=data["name"],
        traffic_limit=data.get("traffic_limit"),
        expiry_days=days if days > 0 else None,
    )

    if user is None:
        await message.answer("❌ Ошибка создания пользователя.", reply_markup=back_button("menu:users"))
        return

    # Add to Xray
    xray_mgr = XrayConfigManager()
    await xray_mgr.add_client(user.uuid, user.email)

    # Generate VLESS link
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"

    # Generate QR
    qr_bytes = generate_qr_code(vless_url)

    # Send info
    info_text = (
        f"✅ <b>Пользователь создан!</b>\n\n"
        f"{format_user_info(user)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📡 <b>Подписка</b> (рекомендуется):\n"
        f"<code>{sub_url}</code>\n"
        f"<i>↳ Вставьте в клиент как «Подписка». Конфиг обновляется автоматически.</i>\n\n"
        f"🔗 <b>Прямая ссылка</b> (для роутеров/старых клиентов):\n"
        f"<code>{vless_url}</code>\n"
        f"<i>↳ Используйте если клиент не поддерживает подписки.</i>"
    )

    await message.answer(info_text, reply_markup=user_actions(user.id))

    # Send QR code
    qr_file = BufferedInputFile(qr_bytes, filename=f"xshield_{user.name}.png")
    await message.answer_photo(
        qr_file,
        caption=(
            f"📱 QR-код для <b>{user.name}</b>\n\n"
            f"Сканируйте в v2rayNG / FoXray / V2RayTun"
        ),
    )


# ── List Users ──

@router.callback_query(F.data == "users:list")
async def users_list(callback: CallbackQuery):
    """List all users."""
    mgr = UserManager()
    users = await mgr.get_all_users()

    if not users:
        await callback.message.edit_text(
            "👥 <b>Пользователи</b>\n\n"
            "Список пуст. Добавьте первого пользователя!",
            reply_markup=users_menu(),
        )
        await callback.answer()
        return

    lines = ["👥 <b>Список пользователей:</b>\n"]
    for u in users:
        status = "🟢" if u.is_active and not u.is_expired else "🔴"
        traffic = format_traffic(u.traffic_total)
        limit = format_traffic(u.traffic_limit) if u.traffic_limit else "♾️"
        lines.append(f"{status} <b>{u.name}</b> — {traffic}/{limit}")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for u in users:
        status = "🟢" if u.is_active and not u.is_expired else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {u.name}",
                callback_data=f"user:info:{u.id}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:users")])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


# ── User Info ──

@router.callback_query(F.data.startswith("user:info:"))
async def user_info(callback: CallbackQuery):
    """Show user details."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    text = f"👤 <b>Пользователь: {user.name}</b>\n\n{format_user_info(user)}"
    await callback.message.edit_text(text, reply_markup=user_actions(user_id))
    await callback.answer()


# ── Get Link ──

@router.callback_query(F.data.startswith("user:link:"))
async def user_link(callback: CallbackQuery):
    """Get VLESS link for user."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)

    await callback.message.answer(
        f"🔗 <b>Прямая ссылка для {user.name}:</b>\n\n"
        f"<code>{vless_url}</code>\n\n"
        f"<i>💡 Скопируйте и вставьте в клиент (v2rayN, v2rayNG, FoXray).\n"
        f"Если клиент поддерживает подписки — лучше используйте 📡 Подписка.</i>",
        reply_markup=back_button(f"user:info:{user_id}"),
    )
    await callback.answer()


# ── Get QR ──

@router.callback_query(F.data.startswith("user:qr:"))
async def user_qr(callback: CallbackQuery):
    """Get QR code for user."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    qr_bytes = generate_qr_code(vless_url)

    qr_file = BufferedInputFile(qr_bytes, filename=f"xshield_{user.name}.png")
    await callback.message.answer_photo(
        qr_file,
        caption=(
            f"📱 QR-код для <b>{user.name}</b>\n\n"
            f"Сканируйте в v2rayNG / FoXray / V2RayTun"
        ),
    )
    await callback.answer()


# ── Toggle Active ──

@router.callback_query(F.data.startswith("user:toggle:"))
async def user_toggle(callback: CallbackQuery):
    """Toggle user active status."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.toggle_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    status = "🟢 Активирован" if user.is_active else "🔴 Заблокирован"
    await callback.answer(f"{status}: {user.name}", show_alert=True)

    # Update Xray config
    xray_mgr = XrayConfigManager()
    if user.is_active:
        await xray_mgr.add_client(user.uuid, user.email)
    else:
        await xray_mgr.remove_client(user.email)

    # Refresh user info
    text = f"👤 <b>Пользователь: {user.name}</b>\n\n{format_user_info(user)}"
    await callback.message.edit_text(text, reply_markup=user_actions(user_id))


# ── Delete User ──

@router.callback_query(F.data.startswith("user:delete:"))
async def user_delete_confirm(callback: CallbackQuery):
    """Confirm user deletion."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    await callback.message.edit_text(
        f"⚠️ <b>Удалить пользователя {user.name}?</b>\n\n"
        "Это действие необратимо!",
        reply_markup=confirm_action("delete_user", user_id),
    )
    await callback.answer()


# confirm:delete_user is handled by security.py (PIN-protected)


# ── Subscription Link ──

@router.callback_query(F.data.startswith("user:sub:"))
async def user_subscription(callback: CallbackQuery):
    """Get subscription URL for user."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    await callback.message.answer(
        f"📡 <b>Подписка для {user.name}:</b>\n\n"
        f"<code>{sub_url}</code>\n\n"
        f"💡 <b>Как подключить:</b>\n"
        f"• <b>v2rayN</b> (Windows): Подписки → Добавить → URL\n"
        f"• <b>v2rayNG</b> (Android): ☰ → Группа подписок → +\n"
        f"• <b>FoXray/V2RayTun</b> (iOS): + → Subscription → URL\n\n"
        f"<i>Конфигурация обновляется автоматически.</i>",
        reply_markup=back_button(f"user:info:{user_id}"),
    )
    await callback.answer()


# ── User Traffic ──

@router.callback_query(F.data.startswith("user:traffic:"))
async def user_traffic(callback: CallbackQuery):
    """Show detailed traffic for a specific user."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    traffic_up = format_traffic(user.traffic_used_up)
    traffic_down = format_traffic(user.traffic_used_down)
    traffic_total = format_traffic(user.traffic_total)
    traffic_limit = format_traffic(user.traffic_limit) if user.traffic_limit else "♾️"

    text = (
        f"📊 <b>Трафик: {user.name}</b>\n\n"
        f"  ↑ Upload: {traffic_up}\n"
        f"  ↓ Download: {traffic_down}\n"
        f"  Σ Всего: {traffic_total}\n"
        f"  📋 Лимит: {traffic_limit}\n"
    )

    if user.traffic_limit and user.traffic_total > 0:
        pct = min(user.traffic_total / user.traffic_limit * 100, 100)
        from ..utils.formatters import progress_bar
        bar = progress_bar(user.traffic_total, user.traffic_limit, length=12)
        text += f"\n  {bar} {pct:.1f}%\n"

    await callback.message.edit_text(text, reply_markup=user_actions(user_id))
    await callback.answer()


# ── All Users Traffic ──

@router.callback_query(F.data == "users:traffic_all")
async def users_traffic_all(callback: CallbackQuery):
    """Show traffic overview for all users."""
    mgr = UserManager()
    users = await mgr.get_all_users()

    if not users:
        await callback.message.edit_text(
            "📊 <b>Трафик</b>\n\nНет пользователей.",
            reply_markup=back_button("menu:users"),
        )
        await callback.answer()
        return

    lines = ["📊 <b>Трафик всех пользователей:</b>\n"]
    total_up = 0
    total_down = 0

    for u in users:
        total_up += u.traffic_used_up
        total_down += u.traffic_used_down
        limit_str = format_traffic(u.traffic_limit) if u.traffic_limit else "♾️"
        status = "🟢" if u.is_active and not u.is_expired else "🔴"
        lines.append(
            f"{status} <b>{u.name}</b>: "
            f"{format_traffic(u.traffic_total)} / {limit_str}"
        )

    lines.append(
        f"\n📊 <b>Итого:</b>\n"
        f"  ↑ Upload: {format_traffic(total_up)}\n"
        f"  ↓ Download: {format_traffic(total_down)}\n"
        f"  Σ Всего: {format_traffic(total_up + total_down)}"
    )

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_button("menu:users"),
    )
    await callback.answer()

