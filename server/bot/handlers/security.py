"""
Dem1chVPN Bot — Security Handler (PIN-protection middleware)
Protects critical operations with PIN code confirmation.
"""
import logging
from aiogram import Router, F, BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..config import config
from ..utils.auth import is_admin

router = Router()
logger = logging.getLogger("dem1chvpn.security")

# Actions that require PIN
PROTECTED_PREFIXES = [
    "confirm:delete_user",
    "confirm:regen_keys",
    "confirm:restore",
]


class PinStates(StatesGroup):
    waiting_pin = State()



class AdminCheckMiddleware(BaseMiddleware):
    """Middleware that checks admin access for all callback queries."""

    async def __call__(self, handler, event: TelegramObject, data: dict):
        if isinstance(event, CallbackQuery):
            # Admin-only callback prefixes
            admin_prefixes = (
                "users:", "user:", "route:", "mon:", "set:", "confirm:",
                "menu:users", "menu:routing", "menu:monitoring", "menu:settings",
                "mode:",
            )
            cb_data = event.data or ""

            # Self-service and help are available to all
            if cb_data.startswith(("self:", "help:", "menu:help", "menu:main", "wiz:")):
                return await handler(event, data)

            # Admin-only checks
            if any(cb_data.startswith(p) for p in admin_prefixes):
                if not is_admin(event.from_user.id):
                    await event.answer("⛔ Нет доступа", show_alert=True)
                    return

        return await handler(event, data)


# Register middleware on the router
router.callback_query.middleware(AdminCheckMiddleware())


@router.callback_query(lambda c: any(c.data.startswith(a) for a in PROTECTED_PREFIXES))
async def pin_protect(callback: CallbackQuery, state: FSMContext):
    """Intercept protected actions and ask for PIN."""
    # Save the original callback data so we can replay it
    await state.update_data(
        pending_action=callback.data,
        pending_message_id=callback.message.message_id,
        pending_chat_id=callback.message.chat.id,
    )
    await callback.message.answer(
        "🔐 <b>Требуется PIN-код</b>\n\n"
        "Введите PIN для подтверждения операции:"
    )
    await state.set_state(PinStates.waiting_pin)
    await callback.answer()


@router.message(PinStates.waiting_pin)
async def pin_verify(message: Message, state: FSMContext):
    """Verify PIN and execute pending action."""
    if message.text.strip() != config.PIN_CODE:
        await state.clear()
        await message.answer("❌ Неверный PIN. Операция отменена.")
        return

    data = await state.get_data()
    pending = data.get("pending_action", "")
    await state.clear()

    # Parse action: format is "confirm:ACTION:TARGET_ID"
    parts = pending.split(":")
    action = parts[1] if len(parts) > 1 else ""
    target_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    if action == "delete_user":
        await _execute_delete_user(message, target_id)
    elif action == "regen_keys":
        await _execute_regen_keys(message)
    elif action == "restore":
        await message.answer(
            "📥 <b>Восстановление из бэкапа</b>\n\n"
            "✅ PIN принят. Отправьте файл бэкапа (.tar.gz) в чат."
        )
    else:
        await message.answer(f"✅ PIN принят. Операция выполнена.")


async def _execute_delete_user(message: Message, user_id: int):
    """Execute user deletion after PIN verification."""
    from ..services.user_manager import UserManager
    from ..services.xray_config import XrayConfigManager
    from ..keyboards.menus import back_button

    mgr = UserManager()
    user = await mgr.get_user(user_id)

    if user:
        xray_mgr = XrayConfigManager()
        await xray_mgr.remove_client(user.email)
        await mgr.delete_user(user_id)
        await message.answer(
            f"✅ Пользователь <b>{user.name}</b> удалён.",
            reply_markup=back_button("users:list"),
        )
    else:
        await message.answer(
            "❌ Пользователь не найден.",
            reply_markup=back_button("users:list"),
        )


async def _execute_regen_keys(message: Message):
    """Regenerate Reality keys after PIN verification."""
    import asyncio
    from ..services.xray_config import XrayConfigManager
    from ..keyboards.menus import settings_menu

    try:
        proc = await asyncio.create_subprocess_exec(
            config.XRAY_BINARY, "x25519",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
        output = stdout.decode()

        private_key = ""
        public_key = ""
        for line in output.strip().split("\n"):
            if "Private" in line:
                private_key = line.split()[-1]
            elif "Public" in line:
                public_key = line.split()[-1]

        if not private_key or not public_key:
            await message.answer("❌ Ошибка генерации ключей.", reply_markup=settings_menu())
            return

        xray_mgr = XrayConfigManager()
        xray_mgr.update_reality_settings(private_key=private_key)
        await xray_mgr.reload_xray()

        await message.answer(
            f"🔑 <b>Ключи Reality пересозданы!</b>\n\n"
            f"Public Key: <code>{public_key}</code>\n\n"
            f"⚠️ Все клиенты должны обновить конфигурацию!\n"
            f"При использовании подписки — обновится автоматически.",
            reply_markup=settings_menu(),
        )
    except Exception as e:
        logger.error(f"Key regeneration failed: {e}")
        await message.answer(f"❌ Ошибка: {e}", reply_markup=settings_menu())
