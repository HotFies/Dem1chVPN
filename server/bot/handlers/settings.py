"""
Dem1chVPN Bot — Settings Handler
Server settings management.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile
from pathlib import Path
from ..config import config
from ..keyboards.menus import settings_menu, back_button
from ..services.xray_config import XrayConfigManager

router = Router()


@router.callback_query(F.data == "set:update_xray")
async def set_update_xray(callback: CallbackQuery):
    await callback.answer("🔄 Обновление Xray-core...", show_alert=True)
    import asyncio
    import tempfile, os
    # Step 1: Download installer script
    script_path = "/tmp/xray_install.sh"
    dl_proc = await asyncio.create_subprocess_exec(
        "curl", "-fsSL", "-o", script_path,
        "https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(dl_proc.communicate(), timeout=30)
    if dl_proc.returncode != 0:
        await callback.message.edit_text("❌ Не удалось скачать установщик Xray")
        return
    # Step 2: Execute saved script
    proc = await asyncio.create_subprocess_exec(
        "bash", script_path,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    # Cleanup
    try:
        os.unlink(script_path)
    except OSError:
        pass

    xray_mgr = XrayConfigManager()
    version = await xray_mgr.get_xray_version()

    await callback.message.edit_text(
        f"✅ Xray-core обновлён до v{version}",
        reply_markup=settings_menu(),
    )


@router.callback_query(F.data == "set:update_geo")
async def set_update_geo(callback: CallbackQuery):
    await callback.answer("🔄 Обновление гео-баз...", show_alert=True)
    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "bash", "/opt/dem1chvpn/cron/update_geodata.sh",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=120)

    await callback.message.edit_text(
        "✅ Гео-базы обновлены (geoip.dat, geosite.dat)",
        reply_markup=settings_menu(),
    )


@router.callback_query(F.data == "set:restart")
async def set_restart(callback: CallbackQuery):
    xray_mgr = XrayConfigManager()
    await xray_mgr.reload_xray()
    running = await xray_mgr.is_xray_running()

    await callback.message.edit_text(
        f"🔁 Xray перезапущен: {'🟢 Работает' if running else '🔴 Ошибка!'}",
        reply_markup=settings_menu(),
    )
    await callback.answer()


@router.callback_query(F.data == "set:backup")
async def set_backup(callback: CallbackQuery):
    await callback.answer("💾 Создание бэкапа...", show_alert=True)
    import asyncio, tarfile, io, os
    from datetime import datetime
    from ..config import config

    buf = io.BytesIO()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # Xray config
        if os.path.exists(config.XRAY_CONFIG_PATH):
            tar.add(config.XRAY_CONFIG_PATH, arcname="xray_config.json")
        # Database
        if os.path.exists(config.DB_PATH):
            tar.add(config.DB_PATH, arcname="dem1chvpn.db")
        # .env
        env_path = str(Path(config.DB_PATH).resolve().parent.parent / ".env")
        if os.path.exists(env_path):
            tar.add(env_path, arcname=".env")

    buf.seek(0)
    backup_file = BufferedInputFile(
        buf.getvalue(),
        filename=f"dem1chvpn_backup_{timestamp}.tar.gz",
    )

    await callback.message.answer_document(
        backup_file,
        caption=f"💾 <b>Бэкап Dem1chVPN</b>\n📅 {timestamp}\n📦 {len(buf.getvalue()) // 1024} KB",
    )


@router.callback_query(F.data == "set:change_sni")
async def set_change_sni(callback: CallbackQuery):
    await callback.message.edit_text(
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
    await callback.message.edit_text(
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
    await callback.message.edit_text(
        "📥 <b>Восстановление из бэкапа</b>\n\n"
        "⚠️ Текущие настройки будут перезаписаны!\n\n"
        "Подтвердите действие:",
        reply_markup=confirm_action("restore"),
    )
    await callback.answer()
