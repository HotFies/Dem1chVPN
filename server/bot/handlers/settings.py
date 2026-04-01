"""
Dem1chVPN Bot — Settings Handler
Server settings management.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from ..config import config
from ..keyboards.menus import settings_menu, back_button
from ..services.xray_config import XrayConfigManager
from ..utils.telegram_helpers import safe_edit_text, try_lock_operation, release_op_lock

router = Router()


@router.callback_query(F.data == "set:update_xray")
async def set_update_xray(callback: CallbackQuery):
    if not await try_lock_operation(callback, "update_xray", "⏳ Обновление Xray уже выполняется..."):
        return

    await callback.answer("🔄 Обновление Xray-core...", show_alert=True)

    try:
        from ..services.updater import XrayUpdater
        updater = XrayUpdater()
        result = await updater.update_xray_core()

        if result["success"]:
            await safe_edit_text(
                callback.message,
                f"✅ Xray-core обновлён до v{result['version']}",
                reply_markup=settings_menu(),
            )
        else:
            await safe_edit_text(
                callback.message,
                f"❌ Ошибка обновления: {result['output'][:200]}",
                reply_markup=settings_menu(),
            )
    except Exception as e:
        await safe_edit_text(
            callback.message,
            f"❌ Ошибка обновления: {e}",
            reply_markup=settings_menu(),
        )
    finally:
        release_op_lock("update_xray")


@router.callback_query(F.data == "set:update_geo")
async def set_update_geo(callback: CallbackQuery):
    if not await try_lock_operation(callback, "update_geo", "⏳ Обновление гео-баз уже выполняется..."):
        return

    await callback.answer("🔄 Обновление гео-баз...", show_alert=True)

    try:
        from ..services.updater import XrayUpdater
        updater = XrayUpdater()
        results = await updater.update_geo_databases()

        geoip = "✅" if results.get("geoip") else "❌"
        geosite = "✅" if results.get("geosite") else "❌"

        await safe_edit_text(
            callback.message,
            f"🌐 <b>Обновление гео-баз</b>\n\n"
            f"{geoip} geoip.dat\n{geosite} geosite.dat",
            reply_markup=settings_menu(),
        )
    except Exception as e:
        await safe_edit_text(
            callback.message,
            f"❌ Ошибка обновления гео-баз: {e}",
            reply_markup=settings_menu(),
        )
    finally:
        release_op_lock("update_geo")


@router.callback_query(F.data == "set:restart")
async def set_restart(callback: CallbackQuery):
    if not await try_lock_operation(callback, "xray_restart", "⏳ Перезапуск уже выполняется..."):
        return

    try:
        xray_mgr = XrayConfigManager()
        await xray_mgr.reload_xray()
        running = await xray_mgr.is_xray_running()

        await safe_edit_text(
            callback.message,
            f"🔁 Xray перезапущен: {'🟢 Работает' if running else '🔴 Ошибка!'}",
            reply_markup=settings_menu(),
        )
    finally:
        release_op_lock("xray_restart")

    await callback.answer()


@router.callback_query(F.data == "set:backup")
async def set_backup(callback: CallbackQuery):
    await callback.answer("💾 Создание бэкапа...", show_alert=True)
    from ..services.backup import BackupManager

    try:
        mgr = BackupManager()
        backup_bytes, filename = mgr.create_backup()

        backup_file = BufferedInputFile(backup_bytes, filename=filename)
        await callback.message.answer_document(
            backup_file,
            caption=(
                f"💾 <b>Бэкап Dem1chVPN</b>\n"
                f"📅 {filename}\n"
                f"📦 {len(backup_bytes) // 1024} KB"
            ),
        )
    except Exception as e:
        from ..utils.telegram_helpers import safe_edit_text
        await safe_edit_text(
            callback.message,
            f"❌ Ошибка создания бэкапа: {e}",
            reply_markup=settings_menu(),
        )


@router.callback_query(F.data == "set:change_sni")
async def set_change_sni(callback: CallbackQuery):
    await safe_edit_text(
        callback.message,
        "📝 <b>Текущие SNI настройки:</b>\n\n"
        f"SNI: <code>{config.REALITY_SNI}</code>\n\n"
        "Доступные SNI:\n"
        "• www.microsoft.com\n"
        "• www.apple.com\n"
        "• dl.google.com\n"
        "• www.amazon.com\n"
        "• www.cloudflare.com\n\n"
        "<i>Для смены SNI используйте команду:</i>\n"
        "<code>/sni домен</code>",
        reply_markup=settings_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "set:regen_keys")
async def set_regen_keys(callback: CallbackQuery):
    from ..keyboards.menus import confirm_action
    await safe_edit_text(
        callback.message,
        "🔑 <b>Пересоздание ключей Reality</b>\n\n"
        "⚠️ Все текущие подключения перестанут работать!\n"
        "Пользователям нужно будет обновить конфигурацию.\n\n"
        "Подтвердите действие:",
        reply_markup=confirm_action("regen_keys"),
    )
    await callback.answer()


@router.callback_query(F.data == "set:restore")
async def set_restore(callback: CallbackQuery):
    from ..keyboards.menus import confirm_action
    await safe_edit_text(
        callback.message,
        "📥 <b>Восстановление из бэкапа</b>\n\n"
        "⚠️ Текущие настройки будут перезаписаны!\n\n"
        "Подтвердите действие:",
        reply_markup=confirm_action("restore"),
    )
    await callback.answer()


# ── WARP Manager (#5) ──

@router.callback_query(F.data == "set:warp_status")
async def set_warp_status(callback: CallbackQuery):
    """Show WARP status."""
    from ..services.warp_manager import WarpManager
    warp = WarpManager()
    installed = warp.is_installed()
    enabled = warp.is_enabled()

    if not installed:
        text = (
            "🌐 <b>Cloudflare WARP</b>\n\n"
            "❌ WARP не установлен.\n"
            "Запустите скрипт установки:\n"
            "<code>bash /opt/dem1chvpn/server/warp/setup.sh</code>"
        )
        await safe_edit_text(callback.message, text, reply_markup=settings_menu())
    else:
        warp_ip = await warp.get_warp_ip() if enabled else "—"
        status = "🟢 Включён" if enabled else "🔴 Выключен"
        text = (
            "🌐 <b>Cloudflare WARP</b>\n\n"
            f"Статус: {status}\n"
            f"WARP IP: <code>{warp_ip}</code>\n\n"
            "WARP перенаправляет трафик через Cloudflare\n"
            "для обхода гео-блокировок (NotebookLM, AI и др.)"
        )
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="🔄 Выключить" if enabled else "✅ Включить",
                callback_data="set:warp_toggle",
            )],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:settings")],
        ])
        await safe_edit_text(callback.message, text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "set:warp_toggle")
async def set_warp_toggle(callback: CallbackQuery):
    """Toggle WARP on/off."""
    from ..services.warp_manager import WarpManager

    if not await try_lock_operation(callback, "warp_toggle", "⏳ WARP уже переключается..."):
        return

    try:
        warp = WarpManager()
        new_state = await warp.toggle()
        status = "🟢 Включён" if new_state else "🔴 Выключен"
        await safe_edit_text(
            callback.message,
            f"🌐 WARP {status}",
            reply_markup=settings_menu(),
        )
    except Exception as e:
        await safe_edit_text(
            callback.message,
            f"❌ Ошибка WARP: {e}",
            reply_markup=settings_menu(),
        )
    finally:
        release_op_lock("warp_toggle")

    await callback.answer()


# ── Broadcast (#7) ──

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message


class BroadcastStates(StatesGroup):
    """FSM for broadcast message."""
    waiting_text = State()


@router.callback_query(F.data == "set:broadcast")
async def set_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Start broadcast message to all users."""
    from ..keyboards.menus import cancel_button
    await safe_edit_text(
        callback.message,
        "📢 <b>Рассылка пользователям</b>\n\n"
        "Введите текст сообщения для всех VPN-пользователей\n"
        "(с привязанным Telegram-аккаунтом):\n\n"
        "<i>Поддерживается HTML-форматирование.</i>",
        reply_markup=cancel_button("menu:settings"),
    )
    await state.set_state(BroadcastStates.waiting_text)
    await callback.answer()


@router.callback_query(F.data == "menu:settings", BroadcastStates.waiting_text)
async def set_broadcast_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast."""
    await state.clear()
    await safe_edit_text(
        callback.message,
        "⚙️ <b>Настройки сервера</b>\n\nВыберите действие:",
        reply_markup=settings_menu(),
    )
    await callback.answer()


@router.message(BroadcastStates.waiting_text)
async def set_broadcast_send(message: Message, state: FSMContext):
    """Send broadcast to all users with Telegram ID."""
    await state.clear()
    text = message.text or message.caption or ""

    if not text.strip():
        await message.answer("❌ Пустое сообщение", reply_markup=settings_menu())
        return

    from ..services.user_manager import UserManager
    mgr = UserManager()
    users = await mgr.get_users_with_telegram()

    sent = 0
    failed = 0
    for user in users:
        try:
            await message.bot.send_message(
                user.telegram_id,
                f"📢 <b>Dem1chVPN — Уведомление</b>\n\n{text}",
            )
            sent += 1
        except Exception:
            failed += 1

    await mgr.log_action(
        "broadcast",
        admin_id=message.from_user.id,
        details=f"Sent to {sent}, failed {failed}",
    )

    await message.answer(
        f"📢 <b>Рассылка завершена</b>\n\n"
        f"✅ Доставлено: {sent}\n"
        f"❌ Ошибок: {failed}\n"
        f"👥 Всего: {len(users)}",
        reply_markup=settings_menu(),
    )

