"""
XShield Bot — Inline Keyboards
All bot menus and inline keyboards.
"""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from ..config import config


def main_menu(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Main menu keyboard."""
    buttons = []

    if is_admin:
        buttons.append([
            InlineKeyboardButton(text="👥 Пользователи", callback_data="menu:users"),
        ])
        buttons.append([
            InlineKeyboardButton(text="🔀 Маршрутизация", callback_data="menu:routing"),
        ])
        buttons.append([
            InlineKeyboardButton(text="📊 Мониторинг", callback_data="menu:monitoring"),
        ])
        buttons.append([
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

    buttons.append([
        InlineKeyboardButton(text="❓ Помощь", callback_data="menu:help"),
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
        [InlineKeyboardButton(text="➕ Добавить пользователя", callback_data="users:add")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="users:list")],
        [InlineKeyboardButton(text="🎟️ Создать приглашение", callback_data="users:invite")],
        [InlineKeyboardButton(text="📊 Трафик всех", callback_data="users:traffic_all")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


def user_actions(user_id: int) -> InlineKeyboardMarkup:
    """Actions for a specific user."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔗 Ссылка", callback_data=f"user:link:{user_id}"),
            InlineKeyboardButton(text="📱 QR", callback_data=f"user:qr:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="📊 Трафик", callback_data=f"user:traffic:{user_id}"),
            InlineKeyboardButton(text="📡 Подписка", callback_data=f"user:sub:{user_id}"),
        ],
        [
            InlineKeyboardButton(text="⏸️ Блок/Разблок", callback_data=f"user:toggle:{user_id}"),
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"user:delete:{user_id}"),
        ],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="users:list")],
    ])


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
    """Monitoring menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Статус сервера", callback_data="mon:status")],
        [InlineKeyboardButton(text="🌐 Статус Xray", callback_data="mon:xray")],
        [InlineKeyboardButton(text="📉 Трафик за день", callback_data="mon:traffic_day")],
        [InlineKeyboardButton(text="⚡ Speedtest", callback_data="mon:speedtest")],
        [InlineKeyboardButton(text="🚨 Проверка IP", callback_data="mon:ip_check")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="mon:alerts")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:main")],
    ])


def settings_menu() -> InlineKeyboardMarkup:
    """Settings menu."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Обновить Xray-core", callback_data="set:update_xray")],
        [InlineKeyboardButton(text="🔄 Обновить гео-базы", callback_data="set:update_geo")],
        [InlineKeyboardButton(text="📝 Изменить SNI", callback_data="set:change_sni")],
        [InlineKeyboardButton(text="🔑 Ключи Reality", callback_data="set:regen_keys")],
        [
            InlineKeyboardButton(text="💾 Бэкап", callback_data="set:backup"),
            InlineKeyboardButton(text="📥 Восстановить", callback_data="set:restore"),
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
    ])


def wizard_connect_method() -> InlineKeyboardMarkup:
    """Connection wizard — connection method."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 QR-код", callback_data="wiz:method_qr")],
        [InlineKeyboardButton(text="🔗 Ссылка", callback_data="wiz:method_link")],
        [InlineKeyboardButton(text="📡 Подписка (автообновление)", callback_data="wiz:method_sub")],
    ])
