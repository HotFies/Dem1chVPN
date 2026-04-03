"""
Dem1chVPN Bot — User Management Handler
Add/list/delete/toggle users via Telegram bot.
Uses hybrid button approach: actions → new message, navigation → edit.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
import base64
import json
import uuid

from ..config import config
from ..keyboards.menus import (
    users_menu, user_actions, back_button, confirm_action,
    user_list_keyboard, cancel_button,
)
from ..services.user_manager import UserManager
from ..services.xray_config import XrayConfigManager

from ..utils.formatters import format_traffic, format_user_info
from ..utils.telegram_helpers import safe_edit_text, action_reply, remove_keyboard

router = Router()


def _build_routing_deeplink() -> str | None:
    """Build a v2raytun://import_route/{base64} deeplink.

    Generates the routing rules directly (synchronous, no DB needed)
    with core Russian domains + geosite for direct, proxy for blocked.
    """
    try:
        routing = {
            "domainStrategy": "IPIfNonMatch",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.routing")).upper(),
            "balancers": [],
            "domainMatcher": "hybrid",
            "name": "Dem1chVPN",
            "rules": [
                {
                    "type": "field",
                    "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.direct.ru")).upper(),
                    "__name__": "Direct Russia",
                    "outboundTag": "direct",
                    "domain": [
                        "geosite:category-ru",
                        "regexp:.*\\.ru$",
                        "regexp:.*\\.su$",
                        "regexp:.*\\.xn--p1ai$",
                        "regexp:.*\\.xn--p1acf$",
                        "regexp:.*\\.moscow$",
                        "regexp:.*\\.tatar$",
                        "domain:userapi.com", "domain:vk.com", "domain:vk.me",
                        "domain:vkuseraudio.net", "domain:vkuservideo.net",
                        "domain:vk-cdn.net", "domain:vkontakte.com",
                        "domain:yastatic.net", "domain:yastat.net",
                        "domain:yandex.net", "domain:yandex.com",
                        "domain:yandexcloud.net", "domain:ya.ru",
                        "domain:avito.st", "domain:sberbank.com",
                        "domain:tbank-online.com", "domain:tochka.com",
                        "domain:boosty.to", "domain:ngenix.net",
                        "domain:moex.com", "domain:turbopages.org",
                    ],
                },
                {
                    "type": "field",
                    "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.direct.ip")).upper(),
                    "__name__": "RU IP Direct",
                    "outboundTag": "direct",
                    "ip": ["geoip:ru", "geoip:private"],
                },
            ],
        }

        # Add proxy rule from config defaults
        if config.DEFAULT_PROXY_DOMAINS:
            routing["rules"].append({
                "type": "field",
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.proxy")).upper(),
                "__name__": "Proxy Blocked",
                "outboundTag": "proxy",
                "domain": [f"domain:{d}" for d in config.DEFAULT_PROXY_DOMAINS],
            })

        b64 = base64.b64encode(json.dumps(routing).encode()).decode()
        return f"v2raytun://import_route/{b64}"
    except Exception:
        return None


class AddUserStates(StatesGroup):
    """FSM states for adding a user."""
    waiting_name = State()
    waiting_traffic_limit = State()
    waiting_expiry = State()


class ExtendUserStates(StatesGroup):
    """FSM states for extending user."""
    waiting_days = State()


class SetLimitStates(StatesGroup):
    """FSM states for changing traffic limit."""
    waiting_limit = State()


# ── Noop handler (for pagination page counter) ──

@router.callback_query(F.data == "noop")
async def noop(callback: CallbackQuery):
    """Ignore noop presses (e.g. page counter button)."""
    await callback.answer()


# ── Add User Flow ──

@router.callback_query(F.data == "users:add")
async def users_add_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new user."""
    await safe_edit_text(
        callback.message,
        "➕ <b>Добавление пользователя</b>\n\n"
        "Введите имя нового пользователя:\n\n"
        "<i>Или нажмите ❌ Отмена</i>",
        reply_markup=cancel_button("menu:users"),
    )
    await state.set_state(AddUserStates.waiting_name)
    await callback.answer()


@router.callback_query(F.data == "menu:users", AddUserStates.waiting_name)
@router.callback_query(F.data == "menu:users", AddUserStates.waiting_traffic_limit)
@router.callback_query(F.data == "menu:users", AddUserStates.waiting_expiry)
async def users_add_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel adding a user."""
    await state.clear()
    await safe_edit_text(
        callback.message,
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
        await message.answer(
            "❌ Имя должно быть от 1 до 50 символов. Попробуйте ещё раз:",
            reply_markup=cancel_button("menu:users"),
        )
        return

    await state.update_data(name=name)
    await message.answer(
        f"👤 Имя: <b>{name}</b>\n\n"
        "📊 Введите лимит трафика в ГБ (или 0 для безлимита):",
        reply_markup=cancel_button("menu:users"),
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
        await message.answer(
            "❌ Введите число (0 = безлимит):",
            reply_markup=cancel_button("menu:users"),
        )
        return

    traffic_limit = int(gb * 1024 * 1024 * 1024) if gb > 0 else None
    await state.update_data(traffic_limit=traffic_limit)

    await message.answer(
        f"📊 Лимит: <b>{'♾️ Безлимит' if traffic_limit is None else f'{gb} GB'}</b>\n\n"
        "⏰ Введите срок действия в днях (или 0 для бессрочного):",
        reply_markup=cancel_button("menu:users"),
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
        await message.answer(
            "❌ Введите целое число (0 = бессрочно):",
            reply_markup=cancel_button("menu:users"),
        )
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

    # Audit log
    await mgr.log_action(
        "user_created",
        admin_id=message.from_user.id,
        target_user_id=user.id,
        details=f"Name: {user.name}",
    )

    # Generate VLESS link
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"

    # v2RayTun deeplinks
    sub_deeplink = f"v2raytun://import/{sub_url}"
    route_deeplink = _build_routing_deeplink()

    # Send info
    info_text = (
        f"✅ <b>Пользователь создан!</b>\n\n"
        f"{format_user_info(user)}\n\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 <b>Быстрая настройка v2RayTun (iOS):</b>\n\n"
        f"1️⃣ Подписка — скопируйте и откройте в Safari:\n"
        f"<code>{sub_deeplink}</code>\n\n"
    )
    if route_deeplink:
        info_text += (
            f"2️⃣ Маршрутизация — скопируйте и откройте в Safari:\n"
            f"<code>{route_deeplink}</code>\n\n"
        )
    info_text += (
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📡 <b>Подписка</b> (для других клиентов):\n"
        f"<code>{sub_url}</code>\n"
        f"<i>↳ v2rayN / v2rayNG / Streisand</i>\n\n"
        f"🔗 <b>Прямая ссылка</b> (для роутеров):\n"
        f"<code>{vless_url}</code>"
    )

    await message.answer(info_text, reply_markup=user_actions(user.id, has_telegram=bool(user.telegram_id)))


# ── List Users (Paginated) ──

@router.callback_query(F.data.startswith("users:list"))
async def users_list(callback: CallbackQuery, state: FSMContext):
    """List all users with pagination. Clears stale FSM state."""
    await state.clear()

    try:
        # Parse page number from callback_data: "users:list:0", "users:list:1", etc.
        parts = callback.data.split(":")
        page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

        mgr = UserManager()
        per_page = 8
        users_on_page, total = await mgr.get_users_page(page=page, per_page=per_page)

        if total == 0:
            await safe_edit_text(
                callback.message,
                "👥 <b>Пользователи</b>\n\n"
                "Список пуст. Добавьте первого пользователя!",
                reply_markup=users_menu(),
            )
            return

        lines = [f"👥 <b>Список пользователей</b> ({total}):\n"]
        for u in users_on_page:
            status = "🟢" if u.is_active and not u.is_expired else "🔴"
            traffic = format_traffic(u.traffic_total)
            limit = format_traffic(u.traffic_limit) if u.traffic_limit else "♾️"
            lines.append(f"{status} <b>{u.name}</b> — {traffic}/{limit}")

        await safe_edit_text(
            callback.message,
            "\n".join(lines),
            reply_markup=user_list_keyboard(users_on_page, page, total, per_page),
        )
    except Exception as e:
        import logging
        logging.getLogger("dem1chvpn").error(f"users_list error: {e}")
    finally:
        await callback.answer()


# ── User Info ──

@router.callback_query(F.data.startswith("user:info:"))
async def user_info(callback: CallbackQuery, state: FSMContext):
    """Show user details. Clears any stale FSM state first."""
    # Clear any stale FSM state (e.g. leftover extend/limit dialogs)
    await state.clear()
    answered = False

    try:
        user_id = int(callback.data.split(":")[2])
        mgr = UserManager()
        user = await mgr.get_user(user_id)

        if not user:
            await callback.answer("❌ Пользователь не найден", show_alert=True)
            answered = True
            return

        text = f"👤 <b>Пользователь: {user.name}</b>\n\n{format_user_info(user)}"
        await safe_edit_text(callback.message, text, reply_markup=user_actions(user_id, has_telegram=bool(user.telegram_id)))
    except Exception as e:
        import logging
        logging.getLogger("dem1chvpn").error(f"user_info error: {e}")
    finally:
        if not answered:
            await callback.answer()


# ── Get Link (action → new message) ──

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

    await action_reply(
        callback,
        f"🔗 <b>Прямая ссылка для {user.name}:</b>\n\n"
        f"<code>{vless_url}</code>\n\n"
        f"<i>💡 Скопируйте и вставьте в клиент (v2rayN / v2rayNG / V2RayTun).\n"
        f"Если клиент поддерживает подписки — лучше используйте 📡 Подписка.</i>",
        reply_markup=back_button(f"user:info:{user_id}"),
    )
    await callback.answer()





# ── Toggle Active (action → new message + notification) ──

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

    # Update Xray config
    xray_mgr = XrayConfigManager()
    if user.is_active:
        await xray_mgr.add_client(user.uuid, user.email)
    else:
        await xray_mgr.remove_client(user.email)

    # Audit log
    await mgr.log_action(
        "user_activated" if user.is_active else "user_blocked",
        admin_id=callback.from_user.id,
        target_user_id=user.id,
    )

    # Send new message with updated info (hybrid approach)
    text = (
        f"{status}: <b>{user.name}</b>\n\n"
        f"👤 <b>Пользователь: {user.name}</b>\n\n{format_user_info(user)}"
    )
    await action_reply(callback, text, reply_markup=user_actions(user_id, has_telegram=bool(user.telegram_id)))

    # Notify user if they have a linked Telegram account
    if user.telegram_id:
        try:
            if user.is_active:
                await callback.bot.send_message(
                    user.telegram_id,
                    "🟢 <b>Аккаунт активирован!</b>\n\n"
                    "Ваш VPN-аккаунт снова активен. Подключайтесь!",
                )
            else:
                await callback.bot.send_message(
                    user.telegram_id,
                    "🔴 <b>Аккаунт приостановлен</b>\n\n"
                    "Ваш VPN-аккаунт временно заблокирован.\n"
                    "Обратитесь к администратору.",
                )
        except Exception:
            pass

    await callback.answer(f"{status}: {user.name}", show_alert=True)


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

    await safe_edit_text(
        callback.message,
        f"⚠️ <b>Удалить пользователя {user.name}?</b>\n\n"
        "Это действие необратимо!",
        reply_markup=confirm_action("delete_user", user_id),
    )
    await callback.answer()


# confirm:delete_user is handled by security.py (PIN-protected)


# ── Subscription Link (action → new message) ──

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

    # v2RayTun deeplinks
    sub_deeplink = f"v2raytun://import/{sub_url}"
    route_deeplink = _build_routing_deeplink()

    # Remove old keyboard
    await remove_keyboard(callback.message)

    text = (
        f"📡 <b>Подписка для {user.name}:</b>\n\n"
        f"📱 <b>v2RayTun (iOS) — автоимпорт:</b>\n\n"
        f"1️⃣ Подписка:\n"
        f"<code>{sub_deeplink}</code>\n\n"
    )
    if route_deeplink:
        text += (
            f"2️⃣ Маршрутизация:\n"
            f"<code>{route_deeplink}</code>\n\n"
        )
    text += (
        f"━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📋 <b>Для других клиентов</b> (скопируйте URL):\n"
        f"<code>{sub_url}</code>\n\n"
        f"💡 <b>Инструкция:</b>\n"
        f"• <b>v2rayN</b> (Windows): Subscription → Add → URL\n"
        f"• <b>v2rayNG</b> (Android): ☰ → Subscription → + → URL\n"
        f"• <b>Streisand</b> (iOS): + → вставьте URL\n\n"
        f"<i>Конфигурация обновляется автоматически.</i>"
    )

    await callback.message.answer(
        text,
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

    await safe_edit_text(callback.message, text, reply_markup=user_actions(user_id, has_telegram=bool(user.telegram_id)))
    await callback.answer()


# ── All Users Traffic ──

@router.callback_query(F.data == "users:traffic_all")
async def users_traffic_all(callback: CallbackQuery):
    """Show traffic overview for all users."""
    mgr = UserManager()
    users = await mgr.get_all_users()

    if not users:
        await safe_edit_text(
            callback.message,
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

    await safe_edit_text(
        callback.message,
        "\n".join(lines),
        reply_markup=back_button("menu:users"),
    )
    await callback.answer()


# ── Extend User Expiry (#2) ──

@router.callback_query(F.data.startswith("user:extend:"))
async def user_extend_start(callback: CallbackQuery, state: FSMContext):
    """Start extending a user's expiry."""
    user_id = int(callback.data.split(":")[2])
    await state.update_data(extend_user_id=user_id)
    await safe_edit_text(
        callback.message,
        "📆 <b>Продление срока</b>\n\n"
        "На сколько дней продлить? Введите число:\n"
        "<i>(Например: 30)</i>",
        reply_markup=cancel_button(f"user:info:{user_id}"),
    )
    await state.set_state(ExtendUserStates.waiting_days)
    await callback.answer()


@router.callback_query(F.data.startswith("user:info:"), ExtendUserStates.waiting_days)
async def user_extend_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel extend."""
    await state.clear()
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)
    if user:
        text = f"👤 <b>Пользователь: {user.name}</b>\n\n{format_user_info(user)}"
        await safe_edit_text(callback.message, text, reply_markup=user_actions(user_id, has_telegram=bool(user.telegram_id)))
    await callback.answer()


@router.message(ExtendUserStates.waiting_days)
async def user_extend_process(message: Message, state: FSMContext):
    """Process extend days input."""
    data = await state.get_data()
    user_id = data.get("extend_user_id")
    await state.clear()

    try:
        days = int(message.text.strip())
        if days <= 0 or days > 3650:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("❌ Введите число от 1 до 3650",
                             reply_markup=back_button(f"user:info:{user_id}"))
        return

    mgr = UserManager()
    xray_mgr = XrayConfigManager()
    user = await mgr.extend_user(user_id, days)

    if user:
        # Re-add to Xray if user was reactivated
        if user.is_active:
            await xray_mgr.add_client(user.uuid, user.email)

        await mgr.log_action(
            "user_extended",
            admin_id=message.from_user.id,
            target_user_id=user_id,
            details=f"+{days} days",
        )
        await message.answer(
            f"✅ Пользователь <b>{user.name}</b> продлён на {days} дней.\n"
            f"⏰ Новый срок: {user.expiry_date.strftime('%d.%m.%Y') if user.expiry_date else '♾️'}",
            reply_markup=back_button(f"user:info:{user_id}"),
        )
    else:
        await message.answer("❌ Пользователь не найден",
                             reply_markup=back_button("menu:users"))


# ── Reset Traffic (#2) ──

@router.callback_query(F.data.startswith("user:reset_traffic:"))
async def user_reset_traffic(callback: CallbackQuery):
    """Reset a user's traffic counters and unblock."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    xray_mgr = XrayConfigManager()
    user = await mgr.reset_traffic(user_id)

    if user:
        # Re-activate if was blocked by limit
        if not user.is_active and user.traffic_limit:
            await mgr.set_user_active(user_id, True)
            await xray_mgr.add_client(user.uuid, user.email)

        # Reset warning flag
        await mgr.set_warning_sent(user_id, False)

        await mgr.log_action(
            "traffic_reset",
            admin_id=callback.from_user.id,
            target_user_id=user_id,
        )
        await action_reply(
            callback,
            f"🔄 Трафик <b>{user.name}</b> сброшен!\n"
            f"{'🟢 Пользователь разблокирован.' if user.is_active else ''}",
            reply_markup=back_button(f"user:info:{user_id}"),
        )
        await callback.answer()
    else:
        await callback.answer("❌ Пользователь не найден", show_alert=True)


# ── Set Traffic Limit (#2) ──

@router.callback_query(F.data.startswith("user:set_limit:"))
async def user_set_limit_start(callback: CallbackQuery, state: FSMContext):
    """Start changing user traffic limit."""
    user_id = int(callback.data.split(":")[2])
    await state.update_data(limit_user_id=user_id)
    await safe_edit_text(
        callback.message,
        "📊 <b>Изменить лимит трафика</b>\n\n"
        "Введите новый лимит в ГБ:\n"
        "<i>(Например: 50 для 50 ГБ, или 0 для безлимита)</i>",
        reply_markup=cancel_button(f"user:info:{user_id}"),
    )
    await state.set_state(SetLimitStates.waiting_limit)
    await callback.answer()


@router.callback_query(F.data.startswith("user:info:"), SetLimitStates.waiting_limit)
async def user_set_limit_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel limit change."""
    await state.clear()
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)
    if user:
        text = f"👤 <b>Пользователь: {user.name}</b>\n\n{format_user_info(user)}"
        await safe_edit_text(callback.message, text, reply_markup=user_actions(user_id, has_telegram=bool(user.telegram_id)))
    await callback.answer()


@router.message(SetLimitStates.waiting_limit)
async def user_set_limit_process(message: Message, state: FSMContext):
    """Process new limit input."""
    data = await state.get_data()
    user_id = data.get("limit_user_id")
    await state.clear()

    try:
        gb = float(message.text.strip())
        if gb < 0:
            raise ValueError
    except (ValueError, TypeError):
        await message.answer("❌ Введите число ≥ 0",
                             reply_markup=back_button(f"user:info:{user_id}"))
        return

    limit_bytes = int(gb * 1024 ** 3) if gb > 0 else None

    mgr = UserManager()
    user = await mgr.set_traffic_limit(user_id, limit_bytes)

    if user:
        await mgr.log_action(
            "limit_changed",
            admin_id=message.from_user.id,
            target_user_id=user_id,
            details=f"{gb} GB" if gb > 0 else "unlimited",
        )
        await message.answer(
            f"✅ Лимит <b>{user.name}</b> изменён на "
            f"<b>{format_traffic(limit_bytes) if limit_bytes else '♾️ Безлимит'}</b>",
            reply_markup=back_button(f"user:info:{user_id}"),
        )
    else:
        await message.answer("❌ Пользователь не найден",
                             reply_markup=back_button("menu:users"))


# ── User Traffic Chart (#8) ──

@router.callback_query(F.data.startswith("user:chart:"))
async def user_chart(callback: CallbackQuery):
    """Show traffic chart for a user."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    history = await mgr.get_traffic_history(user_id, hours=168)  # 7 days

    if not history:
        await action_reply(
            callback,
            f"📈 <b>График трафика: {user.name}</b>\n\n"
            "Пока нет данных. История начнёт записываться при активности.",
            reply_markup=back_button(f"user:info:{user_id}"),
        )
        return

    try:
        from ..services.charts import generate_user_traffic_chart

        upload_data = [(h.recorded_at, h.upload) for h in history]
        download_data = [(h.recorded_at, h.download) for h in history]

        chart_bytes = generate_user_traffic_chart(user.name, upload_data, download_data)

        await remove_keyboard(callback.message)
        chart_file = BufferedInputFile(chart_bytes, filename=f"chart_{user.name}.png")
        await callback.message.answer_photo(
            chart_file,
            caption=f"📈 Трафик <b>{user.name}</b> за 7 дней",
        )
    except Exception:
        await action_reply(
            callback,
            "❌ Ошибка генерации графика",
            reply_markup=back_button(f"user:info:{user_id}"),
        )

    await callback.answer()


# ── Link Telegram Account (#link) ──

@router.callback_query(F.data.startswith("user:link_tg:"))
async def user_link_tg(callback: CallbackQuery):
    """Generate a deep link to bind Telegram account to a VPN user."""
    user_id = int(callback.data.split(":")[2])
    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if not user:
        await callback.answer("❌ Пользователь не найден", show_alert=True)
        return

    if user.telegram_id:
        await callback.answer("✅ Telegram уже привязан", show_alert=True)
        return

    # Generate link
    bot_info = await callback.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=link_{user_id}"

    await action_reply(
        callback,
        f"🔗 <b>Привязка Telegram</b>\n\n"
        f"Отправьте эту ссылку пользователю <b>{user.name}</b>:\n\n"
        f"<code>{link}</code>\n\n"
        "При переходе по ссылке Telegram привяжется\n"
        "автоматически. После этого пользователь сможет:\n"
        "• Видеть свой трафик\n"
        "• Создавать тикеты\n"
        "• Получать уведомления",
        reply_markup=back_button(f"user:info:{user_id}"),
    )
    await callback.answer()
