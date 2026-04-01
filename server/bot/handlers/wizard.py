"""
Dem1chVPN Bot — Connection Wizard Handler
Step-by-step setup guide for new users.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery, BufferedInputFile

from ..config import config
from ..keyboards.menus import wizard_platform, wizard_connect_method, back_button
from ..services.user_manager import UserManager
from ..services.xray_config import XrayConfigManager
from ..utils.qr_generator import generate_qr_code
from ..utils.telegram_helpers import safe_edit_text, remove_keyboard

router = Router()


@router.callback_query(F.data == "self:link")
async def self_link(callback: CallbackQuery):
    """User gets their own VLESS link."""
    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Аккаунт не найден.", show_alert=True)
        return

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)

    # Remove old keyboard, send new message
    await remove_keyboard(callback.message)
    await callback.message.answer(
        f"🔗 <b>Ваша ссылка подключения:</b>\n\n<code>{vless_url}</code>",
        reply_markup=back_button("menu:main"),
    )
    await callback.answer()


@router.callback_query(F.data == "self:qr")
async def self_qr(callback: CallbackQuery):
    """User gets their own QR code."""
    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Аккаунт не найден.", show_alert=True)
        return

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    qr_bytes = generate_qr_code(vless_url)

    await remove_keyboard(callback.message)
    qr_file = BufferedInputFile(qr_bytes, filename=f"dem1chvpn_{user.name}.png")
    await callback.message.answer_photo(qr_file, caption="📱 Ваш QR-код")
    await callback.answer()


@router.callback_query(F.data == "self:traffic")
async def self_traffic(callback: CallbackQuery):
    """User checks their own traffic."""
    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Аккаунт не найден.", show_alert=True)
        return

    from ..utils.formatters import format_user_info
    await safe_edit_text(
        callback.message,
        f"📊 <b>Ваш аккаунт</b>\n\n{format_user_info(user)}",
        reply_markup=back_button("menu:main"),
    )
    await callback.answer()


# ── Wizard ──

@router.callback_query(F.data.startswith("wiz:"))
async def wizard_step(callback: CallbackQuery):
    """Connection wizard steps."""
    step = callback.data.split(":")[1]

    platform_apps = {
        "windows": ("v2rayN", "https://github.com/2dust/v2rayN/releases"),
        "android": ("v2rayNG", "https://play.google.com/store/apps/details?id=com.v2ray.ang"),
        "ios": ("V2RayTun", "https://apps.apple.com/app/v2raytun/id6476628951"),
        "macos": ("V2RayTun", "https://apps.apple.com/app/v2raytun/id6476628951"),
        "router": ("Passwall2", "https://github.com/xiaorouji/openwrt-passwall2"),
    }

    if step in platform_apps:
        app_name, url = platform_apps[step]
        await safe_edit_text(
            callback.message,
            f"🧙 <b>Мастер подключения — Шаг 2</b>\n\n"
            f"📱 Для вашей платформы нужно:\n\n"
            f"1. Скачайте <b>{app_name}</b>:\n"
            f'   📥 <a href="{url}">Скачать {app_name}</a>\n\n'
            f"Уже скачали?",
            reply_markup=wizard_connect_method(),
            disable_web_page_preview=True,
        )
    elif step.startswith("method_"):
        method = step.replace("method_", "")
        mgr = UserManager()
        user = await mgr.get_user_by_telegram_id(callback.from_user.id)

        if not user:
            await callback.answer("❌ Аккаунт не найден", show_alert=True)
            return

        xray_mgr = XrayConfigManager()
        vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)

        # Remove old keyboard for all methods (send new message)
        await remove_keyboard(callback.message)

        if method == "qr":
            qr_bytes = generate_qr_code(vless_url)
            qr_file = BufferedInputFile(qr_bytes, filename="dem1chvpn.png")
            await callback.message.answer_photo(
                qr_file,
                caption=(
                    "📱 <b>Шаг 3: Сканирование QR-кода</b>\n\n"
                    "1. Откройте приложение\n"
                    '2. Нажмите "+" → "Сканировать QR"\n'
                    "3. Наведите камеру на код выше\n"
                    "4. Включите VPN ▶️\n\n"
                    "Готово? Проверьте: откройте youtube.com 🎉"
                ),
            )
        elif method == "link":
            await callback.message.answer(
                f"🔗 <b>Шаг 3: Импорт ссылки</b>\n\n"
                f"1. Скопируйте ссылку:\n"
                f"<code>{vless_url}</code>\n\n"
                f'2. В приложении: "+" → "Импорт из буфера"\n'
                f"3. Включите VPN ▶️\n\n"
                f"Готово? Проверьте: откройте youtube.com 🎉"
            )
        elif method == "sub":
            sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
            await callback.message.answer(
                f"📡 <b>Шаг 3: Подписка (рекомендуется)</b>\n\n"
                f"1. Скопируйте URL подписки:\n"
                f"<code>{sub_url}</code>\n\n"
                f'2. В приложении: "Подписка" → "Добавить"\n'
                f"3. Вставьте URL → Обновить\n"
                f"4. Включите VPN ▶️\n\n"
                f"✅ Конфигурация обновляется автоматически!"
            )

    await callback.answer()
