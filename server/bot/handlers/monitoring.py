"""
Dem1chVPN Bot — Monitoring Handler
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
from ..utils.telegram_helpers import safe_edit_text, try_lock_operation, release_op_lock

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

    # User count + online
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
        f"🌐 <b>Xray:</b> {'🟢 Работает' if xray_running else '🔴 Остановлен'}"
        f" (v{xray_version})\n"
        f"👥 <b>Пользователей:</b> {user_count}  "
        f"(🟢 онлайн: {online_count})\n"
    )

    # Network stats
    net = psutil.net_io_counters()
    text += (
        f"\n📈 <b>Сеть (с момента загрузки):</b>\n"
        f"  ↑ Отправлено: {format_traffic(net.bytes_sent)}\n"
        f"  ↓ Получено: {format_traffic(net.bytes_recv)}\n"
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
        f"  Протокол: VLESS + TCP + Reality\n"
        f"  Порт: {config.SERVER_PORT}\n"
        f"  SNI: {config.REALITY_SNI}\n"
        f"  Клиентов в конфиге: {len(clients)}\n"
    )

    await safe_edit_text(callback.message, text, reply_markup=monitoring_menu())
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
    finally:
        release_op_lock("speedtest")

    await safe_edit_text(callback.message, text, reply_markup=monitoring_menu())


@router.callback_query(F.data == "mon:alerts")
async def mon_alerts(callback: CallbackQuery):
    """Alert settings."""
    await safe_edit_text(
        callback.message,
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Автоматические уведомления:\n"
        "  ✅ Xray упал → автоперезапуск\n"
        "  ✅ Трафик 80% лимита → предупреждение\n"
        "  ✅ Лимит трафика → автоблокировка\n"
        "  ✅ Срок аккаунта истёк → автоблокировка\n"
        "  ✅ Гео-базы обновлены\n"
        "  ✅ IP недоступен из региона\n\n"
        "Уведомления пользователям:\n"
        "  ✅ Блокировка / разблокировка\n"
        "  ✅ Истечение срока / лимита\n\n"
        "<i>Уведомления всегда отправляются администраторам.\n"
        "Пользователям — если привязан Telegram-аккаунт.</i>",
        reply_markup=monitoring_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "mon:ip_check")
async def mon_ip_check(callback: CallbackQuery):
    """Check if VPS IP is blocked by TSPU."""
    from ..config import config
    from ..services.ip_checker import IPBlockChecker

    if not await try_lock_operation(callback, "ip_check", "⏳ Проверка IP уже выполняется..."):
        return

    await callback.answer("🔍 Проверяю IP... (10-15 сек)", show_alert=True)

    try:
        checker = IPBlockChecker(config.SERVER_IP)
        text = await checker.get_formatted_status()
    finally:
        release_op_lock("ip_check")

    await safe_edit_text(callback.message, text, reply_markup=monitoring_menu())
