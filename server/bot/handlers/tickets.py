"""
Dem1chVPN Bot — Ticket System Handler
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..services.ticket_manager import TicketManager
from ..services.user_manager import UserManager
from ..keyboards.menus import (
    back_button, cancel_button, ticket_list_keyboard, monitoring_menu,
)
from ..utils.auth import is_admin
from ..utils.telegram_helpers import safe_edit_text, action_reply

router = Router()


class TicketStates(StatesGroup):
    """FSM for creating a ticket."""
    waiting_message = State()


class TicketReplyStates(StatesGroup):
    """FSM for replying to a ticket."""
    waiting_reply = State()




@router.callback_query(F.data == "self:ticket")
async def self_ticket_start(callback: CallbackQuery, state: FSMContext):
    """Start creating a ticket (only for VPN users)."""
    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer(
            "❌ Тикеты доступны только зарегистрированным VPN-пользователям.",
            show_alert=True,
        )
        return

    await safe_edit_text(
        callback.message,
        "🎫 <b>Создание тикета</b>\n\n"
        "Опишите вашу проблему или вопрос:\n\n"
        "<i>Администратор получит уведомление и ответит вам.</i>",
        reply_markup=cancel_button("menu:main"),
    )
    await state.set_state(TicketStates.waiting_message)
    await callback.answer()


@router.callback_query(F.data == "menu:main", TicketStates.waiting_message)
async def self_ticket_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel ticket creation."""
    await state.clear()
    from ..keyboards.menus import main_menu
    admin = is_admin(callback.from_user.id)
    await safe_edit_text(
        callback.message,
        "🛡️ <b>Dem1chVPN — Главное меню</b>\n\nВыберите раздел:",
        reply_markup=main_menu(is_admin=admin),
    )
    await callback.answer()


@router.message(TicketStates.waiting_message)
async def self_ticket_submit(message: Message, state: FSMContext):
    """Submit the ticket."""
    await state.clear()
    text = message.text or ""

    if not text.strip() or len(text) < 5:
        await message.answer(
            "❌ Слишком короткое сообщение. Опишите проблему подробнее.",
            reply_markup=back_button("menu:main"),
        )
        return

    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.create_ticket(
        user_telegram_id=message.from_user.id,
        user_name=message.from_user.full_name,
        message=text[:2000],
    )

    if ticket:
        await message.answer(
            f"✅ <b>Тикет #{ticket.id} создан!</b>\n\n"
            "Администратор получит уведомление и ответит вам в ближайшее время.",
            reply_markup=back_button("menu:main"),
        )

        from ..config import config
        for admin_id in config.ADMIN_IDS:
            try:
                await message.bot.send_message(
                    admin_id,
                    f"🎫 <b>Новый тикет #{ticket.id}</b>\n\n"
                    f"👤 От: <b>{message.from_user.full_name}</b>\n"
                    f"📝 {text[:500]}",
                )
            except Exception:
                pass
    else:
        await message.answer(
            "❌ Ошибка создания тикета. Попробуйте позже.",
            reply_markup=back_button("menu:main"),
        )




@router.callback_query(F.data == "tickets:list")
async def tickets_list(callback: CallbackQuery):
    """Show open tickets (admin only)."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    ticket_mgr = TicketManager()
    tickets = await ticket_mgr.get_open_tickets()

    await safe_edit_text(
        callback.message,
        f"🎫 <b>Открытые тикеты ({len(tickets)}):</b>",
        reply_markup=ticket_list_keyboard(tickets),
    )
    await callback.answer()




@router.callback_query(F.data.startswith("ticket:view:"))
async def ticket_view(callback: CallbackQuery):
    """View a specific ticket."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    ticket_id = int(callback.data.split(":")[2])
    await _show_ticket_view(callback, ticket_id)
    await callback.answer()


async def _show_ticket_view(callback: CallbackQuery, ticket_id: int):
    """Render ticket view (shared helper for ticket_view and ticket_reply_cancel)."""
    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.get_ticket(ticket_id)

    if not ticket:
        await callback.answer("❌ Тикет не найден", show_alert=True)
        return

    created = ticket.created_at.strftime("%d.%m.%Y %H:%M") if ticket.created_at else "—"
    status = "✅ Решён" if ticket.is_resolved else "🔵 Открыт"

    text = (
        f"🎫 <b>Тикет #{ticket.id}</b>\n\n"
        f"👤 От: <b>{ticket.user_name or 'User'}</b>\n"
        f"📅 Создан: {created}\n"
        f"📋 Статус: {status}\n\n"
        f"📝 <b>Сообщение:</b>\n{ticket.message}\n"
    )
    if ticket.reply:
        text += f"\n💬 <b>Ответ:</b>\n{ticket.reply}"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    if not ticket.is_resolved:
        buttons.append([
            InlineKeyboardButton(text="💬 Ответить", callback_data=f"ticket:reply:{ticket_id}"),
            InlineKeyboardButton(text="✅ Закрыть", callback_data=f"ticket:close:{ticket_id}"),
        ])
    buttons.append([InlineKeyboardButton(text="◀️ К тикетам", callback_data="tickets:list")])

    await safe_edit_text(
        callback.message, text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )




@router.callback_query(F.data.startswith("ticket:reply:"))
async def ticket_reply_start(callback: CallbackQuery, state: FSMContext):
    """Start replying to a ticket."""
    ticket_id = int(callback.data.split(":")[2])
    await state.update_data(reply_ticket_id=ticket_id)
    await safe_edit_text(
        callback.message,
        f"💬 <b>Ответ на тикет #{ticket_id}</b>\n\n"
        "Введите текст ответа:",
        reply_markup=cancel_button(f"ticket:view:{ticket_id}"),
    )
    await state.set_state(TicketReplyStates.waiting_reply)
    await callback.answer()


@router.callback_query(F.data.startswith("ticket:view:"), TicketReplyStates.waiting_reply)
async def ticket_reply_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel reply."""
    await state.clear()
    ticket_id = int(callback.data.split(":")[2])
    await _show_ticket_view(callback, ticket_id)
    await callback.answer()


@router.message(TicketReplyStates.waiting_reply)
async def ticket_reply_send(message: Message, state: FSMContext):
    """Send reply and close ticket."""
    data = await state.get_data()
    ticket_id = data.get("reply_ticket_id")
    await state.clear()

    reply_text = message.text or ""
    if not reply_text.strip():
        await message.answer("❌ Пустой ответ", reply_markup=back_button("tickets:list"))
        return

    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.resolve_ticket(ticket_id, reply_text)

    if ticket:
        await message.answer(
            f"✅ Тикет #{ticket_id} закрыт с ответом.",
            reply_markup=back_button("tickets:list"),
        )

        try:
            await message.bot.send_message(
                ticket.user_telegram_id,
                f"💬 <b>Ответ на ваш тикет #{ticket_id}</b>\n\n"
                f"{reply_text}\n\n"
                f"<i>— Администратор Dem1chVPN</i>",
            )
        except Exception:
            pass
    else:
        await message.answer("❌ Тикет не найден", reply_markup=back_button("tickets:list"))


# ── Admin: Close Ticket ──

@router.callback_query(F.data.startswith("ticket:close:"))
async def ticket_close(callback: CallbackQuery):
    """Close a ticket without reply."""
    if not is_admin(callback.from_user.id):
        await callback.answer("⛔ Нет доступа", show_alert=True)
        return

    ticket_id = int(callback.data.split(":")[2])
    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.resolve_ticket(ticket_id)

    if ticket:
        await action_reply(
            callback,
            f"✅ Тикет #{ticket_id} закрыт.",
            reply_markup=back_button("tickets:list"),
        )
    else:
        await callback.answer("❌ Тикет не найден", show_alert=True)
