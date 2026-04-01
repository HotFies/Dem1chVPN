"""
Dem1chVPN Bot — Routing Handler
Manage proxy/direct domain routing rules.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from ..config import config
from ..keyboards.menus import routing_menu, back_button, cancel_button
from ..services.route_manager import RouteManager
from ..utils.validators import validate_domain, sanitize_domain
from ..utils.telegram_helpers import safe_edit_text

router = Router()


class RouteStates(StatesGroup):
    waiting_proxy_domain = State()
    waiting_direct_domain = State()
    waiting_delete_domain = State()
    waiting_check_domain = State()


# ── Cancel FSM for routing ──

@router.callback_query(F.data == "menu:routing", RouteStates.waiting_proxy_domain)
@router.callback_query(F.data == "menu:routing", RouteStates.waiting_direct_domain)
@router.callback_query(F.data == "menu:routing", RouteStates.waiting_delete_domain)
@router.callback_query(F.data == "menu:routing", RouteStates.waiting_check_domain)
async def route_cancel(callback: CallbackQuery, state: FSMContext):
    """Cancel routing FSM state."""
    await state.clear()
    await safe_edit_text(
        callback.message,
        "🔀 <b>Управление маршрутизацией</b>\n\n❌ Отменено.",
        reply_markup=routing_menu(),
    )
    await callback.answer()


# ── Add to PROXY ──

@router.callback_query(F.data == "route:add_proxy")
async def route_add_proxy(callback: CallbackQuery, state: FSMContext):
    await safe_edit_text(
        callback.message,
        "🔵 <b>Добавить домен в PROXY</b>\n\n"
        "Введите домен (например: <code>example.com</code>):\n"
        "Все поддомены будут включены автоматически.",
        reply_markup=cancel_button("menu:routing"),
    )
    await state.set_state(RouteStates.waiting_proxy_domain)
    await callback.answer()


@router.message(RouteStates.waiting_proxy_domain)
async def route_add_proxy_domain(message: Message, state: FSMContext):
    domain = sanitize_domain(message.text)
    await state.clear()

    if not validate_domain(domain):
        await message.answer(
            f"❌ Некорректный домен: <b>{domain}</b>\n"
            "Пример: <code>youtube.com</code>",
            reply_markup=back_button("menu:routing"),
        )
        return

    mgr = RouteManager()
    result = await mgr.add_rule(domain, "proxy", "admin")

    if result:
        count = await mgr.count_rules("proxy")
        await message.answer(
            f"✅ Домен <b>{domain}</b> добавлен в PROXY.\n\n"
            f"Всего доменов через туннель: {count}",
            reply_markup=back_button("menu:routing"),
        )
    else:
        await message.answer(
            f"⚠️ Домен <b>{domain}</b> уже в списке.",
            reply_markup=back_button("menu:routing"),
        )


# ── Add to DIRECT ──

@router.callback_query(F.data == "route:add_direct")
async def route_add_direct(callback: CallbackQuery, state: FSMContext):
    await safe_edit_text(
        callback.message,
        "🟢 <b>Добавить домен в DIRECT</b>\n\n"
        "Введите домен (например: <code>gosuslugi.ru</code>):\n"
        "Трафик будет идти напрямую, без туннеля.",
        reply_markup=cancel_button("menu:routing"),
    )
    await state.set_state(RouteStates.waiting_direct_domain)
    await callback.answer()


@router.message(RouteStates.waiting_direct_domain)
async def route_add_direct_domain(message: Message, state: FSMContext):
    domain = sanitize_domain(message.text)
    await state.clear()

    if not validate_domain(domain):
        await message.answer(
            f"❌ Некорректный домен: <b>{domain}</b>\n"
            "Пример: <code>gosuslugi.ru</code>",
            reply_markup=back_button("menu:routing"),
        )
        return

    mgr = RouteManager()
    result = await mgr.add_rule(domain, "direct", "admin")

    if result:
        await message.answer(
            f"✅ Домен <b>{domain}</b> добавлен в DIRECT.",
            reply_markup=back_button("menu:routing"),
        )
    else:
        await message.answer(
            f"⚠️ Домен <b>{domain}</b> уже в списке.",
            reply_markup=back_button("menu:routing"),
        )


# ── List Rules ──

@router.callback_query(F.data == "route:list")
async def route_list(callback: CallbackQuery):
    mgr = RouteManager()
    proxy_rules = await mgr.get_rules("proxy")
    direct_rules = await mgr.get_rules("direct")

    lines = ["📋 <b>Правила маршрутизации:</b>\n"]

    lines.append("🔵 <b>PROXY (через туннель):</b>")
    if proxy_rules:
        for r in proxy_rules[:30]:  # Limit display
            lines.append(f"  • {r.domain} <i>({r.added_by})</i>")
        if len(proxy_rules) > 30:
            lines.append(f"  ... и ещё {len(proxy_rules) - 30}")
    else:
        lines.append("  <i>Пусто</i>")

    lines.append(f"\n🟢 <b>DIRECT (напрямую):</b>")
    if direct_rules:
        for r in direct_rules[:20]:
            lines.append(f"  • {r.domain} <i>({r.added_by})</i>")
        if len(direct_rules) > 20:
            lines.append(f"  ... и ещё {len(direct_rules) - 20}")
    else:
        lines.append("  <i>Пусто</i>")

    lines.append(f"\n📊 <b>Итого:</b> {len(proxy_rules)} proxy / {len(direct_rules)} direct")
    lines.append("+ geosite:category-ru и geoip:ru (автоматически)")

    await safe_edit_text(
        callback.message,
        "\n".join(lines),
        reply_markup=routing_menu(),
    )
    await callback.answer()


# ── Delete Rule ──

@router.callback_query(F.data == "route:delete")
async def route_delete(callback: CallbackQuery, state: FSMContext):
    await safe_edit_text(
        callback.message,
        "🗑️ <b>Удалить правило</b>\n\n"
        "Введите домен для удаления:",
        reply_markup=cancel_button("menu:routing"),
    )
    await state.set_state(RouteStates.waiting_delete_domain)
    await callback.answer()


@router.message(RouteStates.waiting_delete_domain)
async def route_delete_domain(message: Message, state: FSMContext):
    domain = message.text.strip().lower()
    await state.clear()

    mgr = RouteManager()
    result = await mgr.delete_rule(domain)

    if result:
        await message.answer(
            f"✅ Правило для <b>{domain}</b> удалено.",
            reply_markup=back_button("menu:routing"),
        )
    else:
        await message.answer(
            f"❌ Домен <b>{domain}</b> не найден в правилах.",
            reply_markup=back_button("menu:routing"),
        )


# ── Check Site ──

@router.callback_query(F.data == "route:check")
async def route_check(callback: CallbackQuery, state: FSMContext):
    await safe_edit_text(
        callback.message,
        "🧪 <b>Проверка доступности</b>\n\n"
        "Введите домен для проверки (например: <code>youtube.com</code>):",
        reply_markup=cancel_button("menu:routing"),
    )
    await state.set_state(RouteStates.waiting_check_domain)
    await callback.answer()


@router.message(RouteStates.waiting_check_domain)
async def route_check_domain(message: Message, state: FSMContext):
    domain = sanitize_domain(message.text)
    await state.clear()

    status_msg = await message.answer(f"🧪 Проверяю <b>{domain}</b>...")

    mgr = RouteManager()
    result = await mgr.check_site(domain)

    # Determine routing status
    rule = await mgr.get_rule(domain)
    route_status = "🔵 PROXY" if rule and rule.rule_type == "proxy" else (
        "🟢 DIRECT" if rule and rule.rule_type == "direct" else "⚪ По умолчанию"
    )

    await safe_edit_text(
        status_msg,
        f"🧪 <b>Проверка {domain}</b>\n\n"
        f"🌐 Доступность с VPS: {'✅ OK' if result.get('vps_ok') else '❌ Недоступен'}"
        f" ({result.get('vps_ms', '—')}ms)\n"
        f"📋 Маршрутизация: {route_status}\n\n"
        f"{'💡 Совет: добавьте в PROXY для доступа через туннель' if not result.get('vps_ok') else ''}",
        reply_markup=back_button("menu:routing"),
    )


# ── Update Lists ──

@router.callback_query(F.data == "route:update")
async def route_update(callback: CallbackQuery):
    await callback.answer("🔄 Обновление списков...", show_alert=False)

    mgr = RouteManager()
    count = await mgr.sync_default_domains()

    await safe_edit_text(
        callback.message,
        f"✅ <b>Списки обновлены!</b>\n\n"
        f"Синхронизировано доменов: {count}",
        reply_markup=routing_menu(),
    )


# ── Routing Modes ──

@router.callback_query(F.data == "route:modes")
async def route_modes(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    await safe_edit_text(
        callback.message,
        "🎬 <b>Режимы маршрутизации</b>\n\n"
        "Выберите предустановленный режим.\n"
        "Он определяет, как маршрутизируется трафик по умолчанию:\n\n"
        "🎬 <b>Стриминг</b> — YouTube, Netflix, Twitch → через WARP (чистый IP)\n"
        "🎮 <b>Гейминг</b> — Steam, Discord, Epic → через PROXY\n"
        "🔒 <b>Полная защита</b> — весь трафик через туннель\n"
        "⚡ <b>Экономия</b> — только нужные сайты",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🎬 Стриминг", callback_data="mode:streaming")],
            [InlineKeyboardButton(text="🎮 Гейминг", callback_data="mode:gaming")],
            [InlineKeyboardButton(text="🔒 Полная защита", callback_data="mode:full")],
            [InlineKeyboardButton(text="⚡ Экономия", callback_data="mode:economy")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="menu:routing")],
        ]),
    )
    await callback.answer()


# Mode domain presets
MODE_DOMAINS = {
    "streaming": [
        "youtube.com", "googlevideo.com", "ytimg.com",
        "netflix.com", "nflxvideo.net",
        "twitch.tv", "ttvnw.net", "jtvnw.net",
        "disneyplus.com", "disney.com",
        "hulu.com", "spotify.com", "deezer.com",
        "notebooklm.google.com", "aistudio.google.com",
    ],
    "gaming": [
        "store.steampowered.com", "steamcommunity.com", "steamcdn-a.akamaihd.net",
        "discord.com", "discord.gg", "discordapp.com",
        "epicgames.com", "unrealengine.com",
        "riotgames.com", "leagueoflegends.com",
    ],
    "full": [],  # All traffic via proxy
    "economy": [
        "youtube.com", "googlevideo.com",
        "instagram.com", "cdninstagram.com",
        "tiktok.com", "tiktokcdn.com", "tiktokv.com",
        "musical.ly", "byteoversea.com", "byteimg.com",
        "discord.com", "discordapp.com",
        "web.telegram.org",
    ],
}

MODE_NAMES = {
    "streaming": "🎬 Стриминг",
    "gaming": "🎮 Гейминг",
    "full": "🔒 Полная защита",
    "economy": "⚡ Экономия",
}


@router.callback_query(F.data.startswith("mode:"))
async def mode_apply(callback: CallbackQuery):
    """Apply a routing mode preset."""
    mode = callback.data.split(":")[1]
    if mode not in MODE_DOMAINS:
        await callback.answer("❌ Неизвестный режим", show_alert=True)
        return

    mode_name = MODE_NAMES.get(mode, mode)
    domains = MODE_DOMAINS[mode]

    mgr = RouteManager()

    if mode == "full":
        # Full protection: set a flag, no specific domains needed
        count = await mgr.count_rules("proxy")
        await safe_edit_text(
            callback.message,
            f"✅ Режим <b>{mode_name}</b> активирован!\n\n"
            f"Весь трафик маршрутизируется через туннель.\n"
            f"Для этого установите в клиенте маршрутизацию «Global».",
            reply_markup=routing_menu(),
        )
    else:
        added = 0
        for domain in domains:
            result = await mgr.add_rule(domain, "proxy", f"mode:{mode}")
            if result:
                added += 1

        await safe_edit_text(
            callback.message,
            f"✅ Режим <b>{mode_name}</b> активирован!\n\n"
            f"Добавлено доменов в PROXY: {added}\n"
            f"(Уже имевшиеся — пропущены)",
            reply_markup=routing_menu(),
        )

    await callback.answer()
