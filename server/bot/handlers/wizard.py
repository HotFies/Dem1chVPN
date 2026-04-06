"""
Dem1chVPN Bot — Connection Wizard Handler
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery

from ..config import config
from ..keyboards.menus import wizard_platform, wizard_connect_method, back_button
from ..services.user_manager import UserManager
from ..services.xray_config import XrayConfigManager
from ..utils.telegram_helpers import safe_edit_text, remove_keyboard

router = Router()


@router.callback_query(F.data == "self:link")
async def self_link(callback: CallbackQuery):
    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("❌ Аккаунт не найден.", show_alert=True)
        return

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    sub_deeplink = f"v2raytun://import/{sub_url}"
    win_sub_deeplink = f"dem1chvpn://import/{sub_url}"

    await remove_keyboard(callback.message)
    await callback.message.answer(
        f"🔗 <b>Ваши ссылки подключения:</b>\n\n"
        f"📱 <b>v2RayTun (iOS) — автоимпорт:</b>\n"
        f"<code>{sub_deeplink}</code>\n\n"
        f"🖥️ <b>Dem1chVPN (Windows) — автоимпорт:</b>\n"
        f"<code>{win_sub_deeplink}</code>\n\n"
        f"📡 <b>Подписка</b> (v2rayN / v2rayNG / Streisand):\n"
        f"<code>{sub_url}</code>\n\n"
        f"🔗 <b>Прямая ссылка</b> (роутеры):\n"
        f"<code>{vless_url}</code>",
        reply_markup=back_button("menu:main"),
    )
    await callback.answer()


@router.callback_query(F.data == "self:traffic")
async def self_traffic(callback: CallbackQuery):
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




@router.callback_query(F.data.startswith("wiz:"))
async def wizard_step(callback: CallbackQuery):
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

        await remove_keyboard(callback.message)

        if method == "link":
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
            sub_deeplink = f"v2raytun://import/{sub_url}"
            win_sub_deeplink = f"dem1chvpn://import/{sub_url}"
            await callback.message.answer(
                f"📡 <b>Шаг 3: Подписка (рекомендуется)</b>\n\n"
                f"📱 <b>iOS (v2RayTun):</b>\n"
                f"Скопируйте и откройте в Safari:\n"
                f"<code>{sub_deeplink}</code>\n\n"
                f"🖥️ <b>Windows (Dem1chVPN):</b>\n"
                f"Скопируйте и откройте в браузере:\n"
                f"<code>{win_sub_deeplink}</code>\n\n"
                f"📋 <b>Другие клиенты:</b>\n"
                f"1. Скопируйте URL подписки:\n"
                f"<code>{sub_url}</code>\n\n"
                f'2. В приложении: "Подписка" → "Добавить"\n'
                f"3. Вставьте URL → Обновить\n"
                f"4. Включите VPN ▶️\n\n"
                f"✅ Конфигурация обновляется автоматически!"
            )

    await callback.answer()
