"""
Dem1chVPN Bot — Monitoring Handler
"""
import psutil
import asyncio
from datetime import datetime, timezone

from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..keyboards.menus import monitoring_menu, back_button
from ..services.xray_config import XrayConfigManager
from ..services.user_manager import UserManager
from ..utils.formatters import format_traffic, format_uptime, progress_bar
from ..utils.telegram_helpers import safe_edit_text, try_lock_operation, release_op_lock

router = Router()


@router.callback_query(F.data == "mon:status")
async def mon_status(callback: CallbackQuery):
    """Show full server status with all services."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage("/")
    except OSError:
        disk = psutil.disk_usage("C:\\")
    boot_time = psutil.boot_time()
    uptime_secs = (datetime.now(timezone.utc) - datetime.fromtimestamp(boot_time, tz=timezone.utc)).total_seconds()


    xray_mgr = XrayConfigManager()
    xray_running = await xray_mgr.is_xray_running()
    xray_version = await xray_mgr.get_xray_version()
    clients = await xray_mgr.get_clients()


    user_mgr = UserManager()
    user_count = await user_mgr.count_users()
    online_users = await user_mgr.get_online_users()
    online_count = len(online_users)

    text = (
        "📊 <b>Статус Dem1chVPN</b>\n\n"
        f"🖥️ <b>Сервер:</b>\n"
        f"  CPU: {progress_bar(cpu, 100)} {cpu}%\n"
        f"  RAM: {progress_bar(mem.used, mem.total)} "
        f"{mem.used // (1024**2)}MB/{mem.total // (1024**2)}MB ({mem.percent}%)\n"
        f"  Disk: {progress_bar(disk.used, disk.total)} "
        f"{disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB ({disk.percent}%)\n"
        f"  Uptime: {format_uptime(uptime_secs)}\n\n"
    )


    net = psutil.net_io_counters()
    text += (
        f"📈 <b>Сеть (с загрузки):</b>\n"
        f"  ↑ {format_traffic(net.bytes_sent)}  ↓ {format_traffic(net.bytes_recv)}\n\n"
    )


    text += "🔌 <b>Сервисы:</b>\n"
    text += (
        f"  {'🟢' if xray_running else '🔴'} Xray v{xray_version}"
        f" ({len(clients)} клиентов)\n"
    )

    try:
        warp_status = "🔴 Отключен"
        from ..services.warp_manager import WarpManager
        warp = WarpManager()
        warp_on = warp.is_enabled()
        text += f"  {'🟢' if warp_on else '🔴'} Cloudflare WARP\n"
    except Exception:
        text += "  ⚪ WARP (не установлен)\n"

    if config.ADGUARD_ENABLED:
        try:
            from ..services.adguard_api import AdGuardAPI
            ag = AdGuardAPI()
            ag_status = await ag.get_status()
            ag_on = ag_status.get("protection_enabled", False)
            ag_stats = await ag.get_stats()
            blocked = ag_stats.get("num_blocked_filtering", 0)
            text += f"  {'🟢' if ag_on else '🔴'} AdGuard Home"
            if blocked:
                text += f" ({blocked:,} заблокировано)"
            text += "\n"
        except Exception:
            text += "  ⚪ AdGuard (не установлен)\n"

    if config.MTPROTO_ENABLED:
        try:
            from ..services.mtproto_manager import MTProtoManager
            mt = MTProtoManager()
            mt_on = await mt.is_running()
            text += f"  {'🟢' if mt_on else '🔴'} MTProto Proxy\n"
        except Exception:
            text += "  ⚪ MTProto (не установлен)\n"

    try:
        caddy_status = "🔴 Off"
        proc = await asyncio.create_subprocess_exec(
            "systemctl", "is-active", "caddy",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=3)
        caddy_on = stdout.decode().strip() == "active"
        text += f"  {'🟢' if caddy_on else '🔴'} Caddy (HTTPS)\n"
    except Exception:
        pass

    text += (
        f"\n👥 <b>Пользователей:</b> {user_count}  "
        f"(🟢 онлайн: {online_count})"
    )

    await safe_edit_text(callback.message, text, reply_markup=monitoring_menu())
    await callback.answer()


@router.callback_query(F.data == "mon:online")
async def mon_online(callback: CallbackQuery):
    """Show currently connected users."""
    user_mgr = UserManager()
    online = await user_mgr.get_online_users(threshold_seconds=120)
    total_users = await user_mgr.count_users()

    if online:
        lines = [f"👁 <b>Онлайн-пользователи ({len(online)}/{total_users}):</b>\n"]
        for u in online:
            lines.append(f"  🟢 <b>{u.name}</b> — {format_traffic(u.traffic_total)}")
    else:
        lines = [f"👁 <b>Онлайн-пользователи (0/{total_users}):</b>\n"]
        lines.append("  Сейчас никто не подключён.")

    await safe_edit_text(
        callback.message,
        "\n".join(lines),
        reply_markup=monitoring_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "mon:traffic_day")
async def mon_traffic_day(callback: CallbackQuery):
    """Show daily traffic for all users with chart."""
    user_mgr = UserManager()
    users = await user_mgr.get_all_users()

    lines = ["📉 <b>Трафик пользователей:</b>\n"]
    total_up = 0
    total_down = 0
    chart_data = []

    for u in users:
        total_up += u.traffic_used_up
        total_down += u.traffic_used_down
        limit_str = format_traffic(u.traffic_limit) if u.traffic_limit else "♾️"
        lines.append(
            f"{'🟢' if u.is_active else '🔴'} <b>{u.name}</b>: "
            f"{format_traffic(u.traffic_total)} / {limit_str}"
        )
        chart_data.append({
            "name": u.name,
            "upload": u.traffic_used_up,
            "download": u.traffic_used_down,
        })

    lines.append(
        f"\n📊 <b>Всего:</b>\n"
        f"  ↑ Upload: {format_traffic(total_up)}\n"
        f"  ↓ Download: {format_traffic(total_down)}\n"
        f"  Σ Итого: {format_traffic(total_up + total_down)}"
    )

    await safe_edit_text(
        callback.message,
        "\n".join(lines),
        reply_markup=monitoring_menu(),
    )

    if chart_data and (total_up + total_down) > 0:
        try:
            from ..services.charts import generate_overview_chart
            from aiogram.types import BufferedInputFile
            chart_bytes = generate_overview_chart(chart_data)
            chart_file = BufferedInputFile(chart_bytes, filename="traffic_chart.png")
            await callback.message.answer_photo(
                chart_file, caption="📊 График трафика пользователей"
            )
        except Exception:
            pass

    await callback.answer()


@router.callback_query(F.data == "mon:speedtest")
async def mon_speedtest(callback: CallbackQuery):
    """Run speedtest on VPS (with operation lock)."""
    if not await try_lock_operation(callback, "speedtest", "⏳ Speedtest уже запущен, подождите..."):
        return

    await callback.answer("⚡ Запуск speedtest... (30–60 сек)", show_alert=True)

    try:
        proc = await asyncio.create_subprocess_exec(
            "speedtest-cli", "--json",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=90)

        import json
        data = json.loads(stdout.decode())

        download = data.get("download", 0) / 1_000_000
        upload = data.get("upload", 0) / 1_000_000
        ping = data.get("ping", 0)
        server = data.get("server", {}).get("name", "Unknown")
        country = data.get("server", {}).get("country", "")

        text = (
            "⚡ <b>Скорость канала VPS</b>\n\n"
            f"  ↓ Download: <b>{download:.1f} Мбит/с</b>\n"
            f"  ↑ Upload: <b>{upload:.1f} Мбит/с</b>\n"
            f"  🏓 Задержка VPS ↔ тест-сервер: <b>{ping:.0f} мс</b>\n"
            f"  🌍 Тест-сервер: {server} ({country})\n\n"
            f"<i>Тест запускается на VPS, не на вашем устройстве.\n"
            f"Показывает пропускную способность и задержку\n"
            f"от VPS до ближайшего тест-сервера.</i>"
        )
    except asyncio.TimeoutError:
        text = "❌ Speedtest: таймаут (>90 сек)"
    except Exception as e:
        text = f"❌ Ошибка speedtest: {e}"
    finally:
        release_op_lock("speedtest")

    await safe_edit_text(callback.message, text, reply_markup=monitoring_menu())
