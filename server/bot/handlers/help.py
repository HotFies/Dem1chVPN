"""
XShield Bot — Help Handler
Connection instructions for all platforms.
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..keyboards.menus import help_menu, back_button

router = Router()

INSTRUCTIONS = {
    "windows": (
        "🖥️ <b>Инструкция для Windows</b>\n\n"
        "<b>1. Скачайте v2rayN:</b>\n"
        '   📥 <a href="https://github.com/2dust/v2rayN/releases">GitHub Releases</a>\n'
        "   Скачайте файл <code>v2rayN-With-Core.zip</code>\n\n"
        "<b>2. Установка:</b>\n"
        "   • Распакуйте архив в любую папку\n"
        "   • Запустите <code>v2rayN.exe</code>\n"
        "   • Если требуется .NET — установите\n\n"
        "<b>3. Добавление сервера:</b>\n"
        '   • В меню нажмите "Серверы" → "Добавить сервер из буфера"\n'
        "   • Или: скопируйте VLESS-ссылку → она добавится автоматически\n\n"
        "<b>4. Подписка (рекомендуется):</b>\n"
        '   • "Подписка" → "Настройка подписки" → Добавить\n'
        "   • Вставьте URL подписки\n"
        "   • Конфигурация будет обновляться автоматически\n\n"
        "<b>5. Подключение:</b>\n"
        '   • Выберите сервер → Нажмите "Подключить"\n'
        '   • В трее появится значок v2rayN'
    ),
    "android": (
        "📱 <b>Инструкция для Android</b>\n\n"
        "<b>1. Скачайте v2rayNG:</b>\n"
        '   📥 <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">Google Play</a>\n'
        '   📥 <a href="https://github.com/2dust/v2rayNG/releases">GitHub APK</a>\n\n'
        "<b>2. Добавление сервера:</b>\n"
        '   • Нажмите "+" → "Импорт из буфера обмена"\n'
        "   • Или отсканируйте QR-код камерой\n\n"
        "<b>3. Подписка (рекомендуется):</b>\n"
        '   • "☰" → "Группа подписки" → "+"\n'
        "   • Вставьте URL подписки\n"
        '   • Нажмите "Обновить подписку"\n\n'
        "<b>4. Подключение:</b>\n"
        "   • Нажмите кнопку ▶️ внизу экрана\n"
        "   • Разрешите VPN-подключение"
    ),
    "ios": (
        "🍎 <b>Инструкция для iOS</b>\n\n"
        "<b>1. Скачайте FoXray:</b>\n"
        '   📥 <a href="https://apps.apple.com/app/foxray/id6448898396">App Store</a>\n\n'
        "<b>2. Добавление сервера:</b>\n"
        "   • Скопируйте VLESS-ссылку\n"
        '   • Откройте FoXray → "+" → "Импорт из буфера"\n'
        "   • Или отсканируйте QR-код\n\n"
        "<b>3. Подписка:</b>\n"
        '   • "Настройки" → "Подписки" → "+"\n'
        "   • Вставьте URL подписки\n\n"
        "<b>4. Подключение:</b>\n"
        "   • Выберите профиль → Включите VPN"
    ),
    "router": (
        "📡 <b>Инструкция для роутера (OpenWRT)</b>\n\n"
        "<b>Поддерживаемые прошивки:</b>\n"
        "• OpenWRT + Passwall2\n"
        "• Keenetic + XKEEN\n\n"
        "<b>OpenWRT + Passwall2:</b>\n"
        "1. Установите пакет <code>passwall2</code>\n"
        "2. Перейдите в LuCI → Services → Passwall2\n"
        "3. Добавьте сервер типа VLESS\n"
        "4. Введите параметры подключения\n"
        "5. Включите режим Global/GFW List\n\n"
        "<b>Keenetic:</b>\n"
        "1. Установите XKEEN через SSH\n"
        "2. Добавьте конфигурацию через веб-интерфейс\n\n"
        "💡 <i>Для роутера лучше использовать подписочную ссылку — "
        "настройки обновляются автоматически.</i>"
    ),
    "general": (
        "📖 <b>Общая инструкция XShield</b>\n\n"
        "<b>Как это работает:</b>\n"
        "XShield создаёт зашифрованный туннель между вашим устройством "
        "и VPS-сервером за рубежом. Для ТСПУ трафик выглядит как "
        "обычное HTTPS-соединение с сайтом Microsoft.\n\n"
        "<b>Клиенты для подключения:</b>\n"
        "🖥️ Windows: v2rayN\n"
        "📱 Android: v2rayNG\n"
        "🍎 iOS: FoXray\n"
        "📡 Роутер: Passwall2 / XKEEN\n\n"
        "<b>Способы подключения:</b>\n"
        "1. 🔗 <b>Ссылка</b> — скопировать и вставить\n"
        "2. 📱 <b>QR-код</b> — отсканировать камерой\n"
        "3. 📡 <b>Подписка</b> — автоматическое обновление (рекомендуется)\n\n"
        "<b>Поддержка:</b>\n"
        "Если что-то не работает — напишите администратору."
    ),
}


@router.callback_query(F.data.startswith("help:"))
async def help_handler(callback: CallbackQuery):
    platform = callback.data.split(":")[1]
    text = INSTRUCTIONS.get(platform, "❌ Инструкция не найдена.")
    await callback.message.edit_text(
        text,
        reply_markup=back_button("menu:help"),
        disable_web_page_preview=True,
    )
    await callback.answer()
