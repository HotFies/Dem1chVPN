"""
Dem1chVPN Bot — Start Handler
Main menu and navigation.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command

from ..config import config
from ..utils.auth import is_admin
from ..keyboards.menus import (
    main_menu, users_menu, routing_menu,
    monitoring_menu, settings_menu, help_menu,
)

router = Router()



@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id
    admin = is_admin(user_id)

    if admin:
        text = (
            "🛡️ <b>Dem1chVPN — Панель управления</b>\n\n"
            f"👤 Привет, <b>{message.from_user.first_name}</b>!\n"
            f"🔑 Статус: <b>Администратор</b>\n\n"
            "Выберите раздел:"
        )
    else:
        # Check if user exists in DB (will be implemented with user_manager)
        text = (
            "🛡️ <b>Dem1chVPN</b>\n\n"
            f"👤 Привет, <b>{message.from_user.first_name}</b>!\n\n"
            "Выберите действие:"
        )

    await message.answer(text, reply_markup=main_menu(is_admin=admin))


# ── Navigation callbacks ──

@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery):
    """Return to main menu."""
    admin = is_admin(callback.from_user.id)
    text = "🛡️ <b>Dem1chVPN — Главное меню</b>\n\nВыберите раздел:"
    await callback.message.edit_text(text, reply_markup=main_menu(is_admin=admin))
    await callback.answer()


@router.callback_query(F.data == "menu:users")
async def menu_users(callback: CallbackQuery):
    """Users management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\nВыберите действие:",
        reply_markup=users_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:routing")
async def menu_routing(callback: CallbackQuery):
    """Routing menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "🔀 <b>Управление маршрутизацией</b>\n\nВыберите действие:",
        reply_markup=routing_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:monitoring")
async def menu_monitoring(callback: CallbackQuery):
    """Monitoring menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "📊 <b>Мониторинг</b>\n\nВыберите действие:",
        reply_markup=monitoring_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery):
    """Settings menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await callback.message.edit_text(
        "⚙️ <b>Настройки сервера</b>\n\nВыберите действие:",
        reply_markup=settings_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery):
    """Help menu."""
    await callback.message.edit_text(
        "❓ <b>Помощь и инструкции</b>\n\n"
        "Выберите платформу для получения инструкции по подключению:",
        reply_markup=help_menu(),
    )
    await callback.answer()
