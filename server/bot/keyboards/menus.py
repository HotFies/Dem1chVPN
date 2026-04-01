"""
Dem1chVPN Bot — Inline Keyboards
All bot menus and inline keyboards.
"""
import math
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..config import config


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    buttons = []

    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="👥 Пользователи", callback_data="menu:users"),
            InlineKeyboardButton(text="🔀 Маршрутизация", callback_data="menu:routing"),
        ])
        buttons.append([
            InlineKeyboardButton(text="📊 Мониторинг", callback_data="menu:monitoring"),
            InlineKeyboardButton(text="⚙️ Настройки", callback_data="menu:settings"),
        ])
    else:
        # User self-service menu
        buttons.append([
            InlineKeyboardButton(text="🔗 Моя ссылка", callback_data="self:link"),
            InlineKeyboardButton(text="📱 QR-код", callback_data="self:qr"),
        ])
        buttons.append([
            InlineKeyboardButton(text="📊 Мой трафик", callback_data="self:traffic"),
        ])
        # Ticket button → Mini App
        if config.SUB_DOMAIN:
            buttons.append([
                InlineKeyboardButton(
                    text="🎫 Тикет",
                    web_app=WebAppInfo(url=f"{config.sub_base_url}/webapp/#tickets"),
                ),
            ])

    buttons.append([
        InlineKeyboardButton(text="📖 Помощь", callback_data="menu:help"),
    ])

    # Mini App button (if domain configured)
    if config.SUB_DOMAIN and is_admin:
        buttons.append([
            InlineKeyboardButton(
                text="📱 Открыть панель",
                web_app=WebAppInfo(url=f"{config.sub_base_url}/webapp/"),
            ),
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def users_menu() -> InlineKeyboardMarkup:
    """Users management menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data="users:add"),
            InlineKeyboardButton(text="📋 Список", callback_data="users:list:0"),
        ],
        [
            InlineKeyboardButton(text="🎟️ Приглашение", callback_data="users:invite"),
            InlineKeyboardButton(text="📊 Трафик всех", callback_data="users:traffic_all"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


def user_list_keyboard(
    users_on_page: list,
    page: int,
    total_count: int,
    per_page: int = 8,
) -> InlineKeyboardMarkup:
    """Paginated user list keyboard."""
    buttons = []
    for u in users_on_page:
        status = "🟢" if u.is_active and not u.is_expired else "🔴"
        buttons.append([
            InlineKeyboardButton(
                text=f"{status} {u.name}",
                callback_data=f"user:info:{u.id}",
            )
        ])

    # Pagination row
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    if total_pages > 1:
        nav = []
        if page > 0:
            nav.append(InlineKeyboardButton(text="◀️", callback_data=f"users:list:{page - 1}"))
        nav.append(InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}",
            callback_data="noop",
        ))
        if page < total_pages - 1:
            nav.append(InlineKeyboardButton(text="▶️", callback_data=f"users:list:{page + 1}"))
        buttons.append(nav)

    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:users")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def user_actions(user_id: int, has_telegram: bool = False) -> InlineKeyboardMarkup:
    """Actions for a specific user."""
    buttons = [
        [
            InlineKeyboardButton(text="🔗 Ссылка", callback_data=f"user:link:{user_id}"),
            InlineKeyboardButton(text="📱 QR", callback_data=f"user:qr:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="📊 Трафик", callback_data=f"user:traffic:{user_id}"),
            InlineKeyboardButton(text="📡 Подписка", callback_data=f"user:sub:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="📆 Продлить", callback_data=f"user:extend:{user_id}"),
            InlineKeyboardButton(text="🔄 Сброс трафика", callback_data=f"user:reset_traffic:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="📊 Лимит", callback_data=f"user:set_limit:{user_id}"),
            InlineKeyboardButton(text="📈 График", callback_data=f"user:chart:{user_id}"),
        ],
    ]
    # Link Telegram button (only if not linked)
    if not has_telegram:
        buttons.append([
            InlineKeyboardButton(text="🔗 Привязать Telegram", callback_data=f"user:link_tg:{user_id}"),
        ])
    buttons.append([
        InlineKeyboardButton(text="⏸️ Блок/Разблок", callback_data=f"user:toggle:{user_id}"),
        InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"user:delete:{user_id}"),
    ])
    buttons.append([InlineKeyboardButton(text="◀️ К списку", callback_data="users:list:0")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def routing_menu() -> InlineKeyboardMarkup:
    """Routing management menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Текущие правила", callback_data="route:list")],
        [
            InlineKeyboardButton(text="➕ В PROXY", callback_data="route:add_proxy"),
            InlineKeyboardButton(text="➕ В DIRECT", callback_data="route:add_direct"),
        ],
        [InlineKeyboardButton(text="🗑️ Удалить правило", callback_data="route:delete")],
        [InlineKeyboardButton(text="🔄 Обновить списки", callback_data="route:update")],
        [InlineKeyboardButton(text="🧪 Проверить сайт", callback_data="route:check")],
        [
            InlineKeyboardButton(text="🎬 Режимы", callback_data="route:modes"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


def monitoring_menu() -> InlineKeyboardMarkup:
    """Мониторинг menu."""
    buttons = [
        [
            InlineKeyboardButton(text="📈 Статус", callback_data="mon:status"),
            InlineKeyboardButton(text="🌐 Xray", callback_data="mon:xray"),
        ],
        [
            InlineKeyboardButton(text="👁 Онлайн", callback_data="mon:online"),
            InlineKeyboardButton(text="📉 Трафик", callback_data="mon:traffic_day"),
        ],
        [
            InlineKeyboardButton(text="⚡ Speedtest", callback_data="mon:speedtest"),
            InlineKeyboardButton(text="🚨 Проверка IP", callback_data="mon:ip_check"),
        ],
    ]
    # Tickets → Mini App (if domain configured)
    ticket_row = []
    if config.SUB_DOMAIN:
        ticket_row.append(InlineKeyboardButton(
            text="🎫 Тикеты",
            web_app=WebAppInfo(url=f"{config.sub_base_url}/webapp/#tickets"),
        ))
    else:
        ticket_row.append(InlineKeyboardButton(text="🎫 Тикеты", callback_data="tickets:list"))
    ticket_row.append(InlineKeyboardButton(text="🔔 Уведомления", callback_data="mon:alerts"))
    buttons.append(ticket_row)
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def settings_menu() -> InlineKeyboardMarkup:
    """Settings menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Xray-core", callback_data="set:update_xray"),
            InlineKeyboardButton(text="🔄 Гео-базы", callback_data="set:update_geo"),
        ],
        [
            InlineKeyboardButton(text="📝 Изменить SNI", callback_data="set:change_sni"),
            InlineKeyboardButton(text="🔑 Ключи", callback_data="set:regen_keys"),
        ],
        [
            InlineKeyboardButton(text="💾 Бэкап", callback_data="set:backup"),
            InlineKeyboardButton(text="📥 Восстановить", callback_data="set:restore"),
        ],
        [
            InlineKeyboardButton(text="🌐 WARP", callback_data="set:warp_status"),
            InlineKeyboardButton(text="📢 Рассылка", callback_data="set:broadcast"),
        ],
        [InlineKeyboardButton(text="🔁 Перезапуск Xray", callback_data="set:restart")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


def help_menu() -> InlineKeyboardMarkup:
    """Help menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Общая инструкция", callback_data="help:general")],
        [InlineKeyboardButton(text="🖥️ Windows", callback_data="help:windows")],
        [InlineKeyboardButton(text="📱 Android", callback_data="help:android")],
        [InlineKeyboardButton(text="🍎 iOS", callback_data="help:ios")],
        [InlineKeyboardButton(text="🍎 macOS", callback_data="help:macos")],
        [InlineKeyboardButton(text="🐧 Linux", callback_data="help:linux")],
        [InlineKeyboardButton(text="📡 Роутер", callback_data="help:router")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


def confirm_action(action: str, target_id: int = 0) -> InlineKeyboardMarkup:
    """Confirmation dialog."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}:{target_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data="menu:main"),
        ],
    ])


def back_button(target: str = "menu:main") -> InlineKeyboardMarkup:
    """Single back button."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀️ Назад", callback_data=target)],
    ])


def cancel_button(target: str = "menu:main") -> InlineKeyboardMarkup:
    """Single cancel button for FSM states."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data=target)],
    ])


def ticket_list_keyboard(tickets: list) -> InlineKeyboardMarkup:
    """Keyboard with list of open tickets."""
    buttons = []
    for t in tickets:
        status = "🔵" if not t.is_resolved else "✅"
        label = f"{status} #{t.id} — {(t.user_name or 'User')[:20]}"
        buttons.append([
            InlineKeyboardButton(text=label, callback_data=f"ticket:view:{t.id}")
        ])
    buttons.append([InlineKeyboardButton(text="◀️ Назад", callback_data="menu:monitoring")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def wizard_platform() -> InlineKeyboardMarkup:
    """Connection wizard — platform selection."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🖥️ Windows", callback_data="wiz:windows"),
            InlineKeyboardButton(text="🍎 macOS", callback_data="wiz:macos"),
        ],
        [
            InlineKeyboardButton(text="📱 Android", callback_data="wiz:android"),
            InlineKeyboardButton(text="🍎 iOS", callback_data="wiz:ios"),
        ],
        [InlineKeyboardButton(text="📡 Роутер", callback_data="wiz:router")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:help")],
    ])


def wizard_connect_method() -> InlineKeyboardMarkup:
    """Connection wizard — connection method."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 QR-код", callback_data="wiz:method_qr")],
        [InlineKeyboardButton(text="🔗 Ссылка", callback_data="wiz:method_link")],
        [InlineKeyboardButton(text="📡 Подписка (рекомендуется)", callback_data="wiz:method_sub")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:help")],
    ])



