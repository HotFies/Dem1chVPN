"""
Dem1chVPN Bot — Start Handler
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext

from ..config import config
from ..utils.auth import is_admin
from ..utils.telegram_helpers import safe_edit_text
from ..keyboards.menus import (
    main_menu, users_menu, routing_menu,
    monitoring_menu, settings_menu, help_menu,
)

router = Router()



@router.message(CommandStart())
async def cmd_start(message: Message):
    """Handle /start command."""
    user_id = message.from_user.id

    if is_admin(user_id):
        text = (
            "🛡️ <b>Dem1chVPN — Панель управления</b>\n\n"
            f"👤 Привет, <b>{message.from_user.first_name}</b>!\n"
            f"🔑 Статус: <b>Администратор</b>\n\n"
            "Выберите раздел:"
        )
        await message.answer(text, reply_markup=main_menu(is_admin=True))
        return

    from ..services.user_manager import UserManager
    mgr = UserManager()
    vpn_user = await mgr.get_user_by_telegram_id(user_id)

    if vpn_user:
        text = (
            "🛡️ <b>Dem1chVPN</b>\n\n"
            f"👤 Привет, <b>{message.from_user.first_name}</b>!\n\n"
            "Выберите действие:"
        )
        await message.answer(text, reply_markup=main_menu(is_admin=False))
    else:
        await message.answer(
            "🛡️ <b>Dem1chVPN</b>\n\n"
            "⛔ Вы не являетесь пользователем VPN.\n\n"
            "Для получения доступа обратитесь к администратору."
        )




@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery, state: FSMContext):
    """Return to main menu. Clears any stale FSM state."""
    await state.clear()
    admin = is_admin(callback.from_user.id)
    text = "🛡️ <b>Dem1chVPN — Главное меню</b>\n\nВыберите раздел:"
    await safe_edit_text(callback.message, text, reply_markup=main_menu(is_admin=admin))
    await callback.answer()


@router.callback_query(F.data == "menu:users")
async def menu_users(callback: CallbackQuery):
    """Users management menu."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return
    await safe_edit_text(
        callback.message,
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
    await safe_edit_text(
        callback.message,
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
    await safe_edit_text(
        callback.message,
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
    await safe_edit_text(
        callback.message,
        "⚙️ <b>Настройки сервера</b>\n\nВыберите действие:",
        reply_markup=settings_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery):
    """Help menu."""
    await safe_edit_text(
        callback.message,
        "❓ <b>Помощь и инструкции</b>\n\n"
        "Нажмите кнопку ниже для открытия инструкций:",
        reply_markup=help_menu(),
    )
    await callback.answer()
