"""
XShield Bot — Monitoring Handler
Server status, traffic stats, speedtest.
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

router = Router()


@router.callback_query(F.data == "mon:status")
async def mon_status(callback: CallbackQuery):
    """Show server status."""
    cpu = psutil.cpu_percent(interval=1)
    mem = psutil.virtual_memory()
    try:
        disk = psutil.disk_usage("/")
    except OSError:
        disk = psutil.disk_usage("C:\\")
    boot_time = psutil.boot_time()
    uptime_secs = (datetime.now(timezone.utc) - datetime.fromtimestamp(boot_time, tz=timezone.utc)).total_seconds()

    # Xray status
    xray_mgr = XrayConfigManager()
    xray_running = await xray_mgr.is_xray_running()
    xray_version = await xray_mgr.get_xray_version()

    # User count
    user_mgr = UserManager()
    user_count = await user_mgr.count_users()

    text = (
        "📊 <b>Статус XShield</b>\n\n"
        f"🖥️ <b>Сервер:</b>\n"
        f"  CPU: {progress_bar(cpu, 100)} {cpu}%\n"
        f"  RAM: {progress_bar(mem.used, mem.total)} "
        f"{mem.used // (1024**2)}MB/{mem.total // (1024**2)}MB ({mem.percent}%)\n"
        f"  Disk: {progress_bar(disk.used, disk.total)} "
        f"{disk.used // (1024**3)}GB/{disk.total // (1024**3)}GB ({disk.percent}%)\n"
        f"  Uptime: {format_uptime(uptime_secs)}\n\n"
        f"🌐 <b>Xray:</b> {'🟢 Работает' if xray_running else '🔴 Остановлен'}"
        f" (v{xray_version})\n"
        f"👥 <b>Пользователей:</b> {user_count}\n"
    )

    # Network stats
    net = psutil.net_io_counters()
    text += (
        f"\n📈 <b>Сеть (с момента загрузки):</b>\n"
        f"  ↑ Отправлено: {format_traffic(net.bytes_sent)}\n"
        f"  ↓ Получено: {format_traffic(net.bytes_recv)}\n"
    )

    await callback.message.edit_text(text, reply_markup=monitoring_menu())
    await callback.answer()


@router.callback_query(F.data == "mon:xray")
async def mon_xray(callback: CallbackQuery):
    """Show detailed Xray status."""
    xray_mgr = XrayConfigManager()
    running = await xray_mgr.is_xray_running()
    version = await xray_mgr.get_xray_version()
    clients = await xray_mgr.get_clients()

    from ..config import config
    text = (
        "🌐 <b>Статус Xray-core</b>\n\n"
        f"  Статус: {'🟢 Работает' if running else '🔴 Остановлен'}\n"
        f"  Версия: v{version}\n"
        f"  Протокол: VLESS + XHTTP + Reality\n"
        f"  Порт: {config.SERVER_PORT}\n"
        f"  SNI: {config.REALITY_SNI}\n"
        f"  Клиентов в конфиге: {len(clients)}\n"
    )

    await callback.message.edit_text(text, reply_markup=monitoring_menu())
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

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=monitoring_menu(),
    )

    # Send chart if there's data
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
            pass  # Chart generation is optional

    await callback.answer()


@router.callback_query(F.data == "mon:speedtest")
async def mon_speedtest(callback: CallbackQuery):
    """Run speedtest on VPS."""
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

        download = data.get("download", 0) / 1_000_000  # bits to Mbps
        upload = data.get("upload", 0) / 1_000_000
        ping = data.get("ping", 0)
        server = data.get("server", {}).get("name", "Unknown")
        country = data.get("server", {}).get("country", "")

        text = (
            "⚡ <b>Speedtest результаты</b>\n\n"
            f"  ↓ Download: <b>{download:.1f} Мбит/с</b>\n"
            f"  ↑ Upload: <b>{upload:.1f} Мбит/с</b>\n"
            f"  🏓 Ping: <b>{ping:.0f} мс</b>\n"
            f"  🌍 Сервер: {server} ({country})"
        )
    except asyncio.TimeoutError:
        text = "❌ Speedtest: таймаут (>90 сек)"
    except Exception as e:
        text = f"❌ Ошибка speedtest: {e}"

    await callback.message.edit_text(text, reply_markup=monitoring_menu())


@router.callback_query(F.data == "mon:alerts")
async def mon_alerts(callback: CallbackQuery):
    """Alert settings."""
    await callback.message.edit_text(
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Автоматические уведомления:\n"
        "  ✅ Xray упал → автоперезапуск\n"
        "  ✅ Трафик 80% лимита → предупреждение\n"
        "  ✅ Гео-базы обновлены\n"
        "  ✅ IP заблокирован ТСПУ\n\n"
        "<i>Уведомления всегда отправляются администраторам.</i>",
        reply_markup=monitoring_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "mon:ip_check")
async def mon_ip_check(callback: CallbackQuery):
    """Check if VPS IP is blocked by TSPU."""
    from ..config import config
    from ..services.ip_checker import IPBlockChecker

    await callback.answer("🔍 Проверяю IP... (10-15 сек)", show_alert=True)

    checker = IPBlockChecker(config.SERVER_IP)
    text = await checker.get_formatted_status()

    await callback.message.edit_text(text, reply_markup=monitoring_menu())

