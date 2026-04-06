"""
Dem1chVPN — Telegram Helpers
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

    try:
        return await message.edit_text(
            text, reply_markup=reply_markup, **kwargs,
        )
    except TelegramBadRequest as e:
        error_msg = str(e).lower()
        if "message is not modified" in error_msg:

            return message
        if any(s in error_msg for s in (
            "message can't be edited",
            "message to edit not found",
            "message is too old",
        )):

            return await message.answer(
                text, reply_markup=reply_markup, **kwargs,
            )
        raise


async def remove_keyboard(message: Message) -> None:

    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest:
        pass


async def action_reply(
    callback: CallbackQuery,
    text: str,
    reply_markup: Optional[InlineKeyboardMarkup] = None,
    **kwargs,
) -> Message:

    await remove_keyboard(callback.message)
    return await callback.message.answer(
        text, reply_markup=reply_markup, **kwargs,
    )


_op_locks: dict[str, asyncio.Lock] = {}


def get_op_lock(name: str) -> asyncio.Lock:

    if name not in _op_locks:
        _op_locks[name] = asyncio.Lock()
    return _op_locks[name]


async def try_lock_operation(
    callback: CallbackQuery,
    name: str,
    busy_message: str = "⏳ Операция уже выполняется, подождите...",
) -> bool:

    lock = get_op_lock(name)
    if lock.locked():
        await callback.answer(busy_message, show_alert=True)
        return False
    await lock.acquire()
    return True


def release_op_lock(name: str) -> None:

    lock = _op_locks.get(name)
    if lock and lock.locked():
        lock.release()
