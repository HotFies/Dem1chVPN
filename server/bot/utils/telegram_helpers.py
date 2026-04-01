"""
Dem1chVPN — Telegram Helpers
Safe message editing, stale-button protection, and operation locking.
"""
import asyncio
import logging
from functools import wraps
from typing import Optional

from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger("dem1chvpn.helpers")


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    **kwargs,
) -> Message:
    """
    Try to edit an existing message.
    Falls back to sending a new message on common errors:
    - MessageNotModified (same content)
    - Message can't be edited (too old / deleted)
    """
    try:
        return await message.edit_text(
            text, reply_markup=reply_markup, **kwargs,
        )
    except TelegramBadRequest as e:
        error_msg = str(e).lower()
        if "message is not modified" in error_msg:
            # Content unchanged — silently ignore
            return message
        if any(s in error_msg for s in (
            "message can't be edited",
            "message to edit not found",
            "message is too old",
        )):
            # Message too old — send new
            return await message.answer(
                text, reply_markup=reply_markup, **kwargs,
            )
        raise  # Unknown error — re-raise


async def remove_keyboard(message: Message) -> None:
    """Remove inline keyboard from a message (best-effort)."""
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass  # Message too old or already modified — ignore


async def action_reply(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    **kwargs,
) -> Message:
    """
    Send a **new** message as a reply to an action button press,
    and remove the inline keyboard from the old message.

    Use for destructive/one-shot actions (delete, toggle, link, qr, sub).
    The old message keeps its text (as a history record) but loses buttons.
    """
    await remove_keyboard(callback.message)
    return await callback.message.answer(
        text, reply_markup=reply_markup, **kwargs,
    )


# ─── Operation Lock ─────────────────────────────────

# Global locks for heavy operations (speedtest, update, restart, etc.)
_op_locks: dict[str, asyncio.Lock] = {}


def get_op_lock(name: str) -> asyncio.Lock:
    """Get or create a named operation lock."""
    if name not in _op_locks:
        _op_locks[name] = asyncio.Lock()
    return _op_locks[name]


async def try_lock_operation(
    callback: CallbackQuery,
    name: str,
    busy_message: str = "⏳ Операция уже выполняется, подождите...",
) -> bool:
    """
    Try to acquire a lock for a heavy operation.
    If already locked — answer callback with busy_message and return False.
    Caller must release the lock when done.
    """
    lock = get_op_lock(name)
    if lock.locked():
        await callback.answer(busy_message, show_alert=True)
        return False
    await lock.acquire()
    return True


def release_op_lock(name: str) -> None:
    """Release a named operation lock."""
    lock = _op_locks.get(name)
    if lock and lock.locked():
        lock.release()
