"""
Dem1chVPN Bot — Help Handler
Connection instructions for all platforms (updated for 2025/2026 client versions).
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..keyboards.menus import help_menu, back_button
from ..utils.telegram_helpers import safe_edit_text

router = Router()

INSTRUCTIONS = {
    "windows": (
        "🖥️ <b>Инструкция для Windows</b>\n\n"
        "<b>1. Скачайте v2rayN:</b>\n"
        '   📥 <a href="https://github.com/2dust/v2rayN/releases">GitHub Releases</a>\n'
        "   Файл: <code>v2rayN-windows-64-SelfContained.zip</code>\n\n"
        "<b>2. Установка:</b>\n"
        "   • Распакуйте архив в любую папку\n"
        "   • Запустите <code>v2rayN.exe</code>\n\n"
        "<b>3. Добавьте подписку:</b>\n"
        '   • Верхнее меню: Subscription → Subscription setting\n'
        '   • Нажмите Add\n'
        '   • В поле URL вставьте ссылку подписки → OK\n'
        '   • Subscription → Update subscription\n\n'
        "<b>4. Настройте маршрутизацию (один раз):</b>\n"
        '   • Routing Settings → Import rules from URL\n'
        "   • Вставьте URL маршрутизации из бота\n"
        "   • РФ-сервисы будут работать напрямую\n\n"
        "<b>5. Подключение:</b>\n"
        '   • Выберите сервер → Enter\n'
        '   • В трее появится значок v2rayN'
    ),
    "android": (
        "📱 <b>Инструкция для Android</b>\n\n"
        "<b>1. Скачайте v2rayNG:</b>\n"
        '   📥 <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">Google Play</a>\n\n'
        "<b>2. Добавьте подписку:</b>\n"
        '   • ☰ → Subscription group settings → +\n'
        "   • В поле URL вставьте ссылку подписки → галочка\n"
        '   • ☰ → Update subscription\n\n'
        "<b>3. Настройте маршрутизацию (один раз):</b>\n"
        '   • ☰ → Settings → Routing settings\n'
        '   • Domain strategy: IPIfNonMatch\n'
        '   • Rules → Custom rules → Direct URL\n'
        "   • Вставьте URL маршрутизации из бота\n"
        "   • РФ-сервисы будут работать напрямую\n\n"
        "<b>4. Подключение:</b>\n"
        "   • Нажмите кнопку ▶️ внизу экрана\n"
        "   • Разрешите VPN-подключение"
    ),
    "ios": (
        "🍎 <b>Инструкция для iOS</b>\n\n"
        "<b>1. Скачайте V2RayTun:</b>\n"
        '   📥 <a href="https://apps.apple.com/app/v2raytun/id6476628951">App Store</a>\n\n'
        "<b>2. Подписка (рекомендуется):</b>\n"
        '   • Скопируйте ссылку подписки из бота\n'
        '   • Главный экран → «+» → Вставьте ссылку подписки\n'
        "   • Конфигурация и маршрутизация применятся автоматически\n\n"
        "<b>3. Или добавление вручную:</b>\n"
        "   • Скопируйте VLESS-ссылку\n"
        '   • «+» → Вставьте из буфера\n'
        "   • Или отсканируйте QR-код\n\n"
        "<b>4. Подключение:</b>\n"
        "   • Выберите сервер → нажмите кнопку подключения\n"
        "   • Разрешите добавление VPN-конфигурации\n\n"
        "<b>Альтернативные клиенты:</b>\n"
        '• <a href="https://apps.apple.com/app/streisand/id6450534064">Streisand</a>\n'
        '• <a href="https://apps.apple.com/app/v2box-v2ray-client/id6446814690">V2Box</a>\n'
        '• <a href="https://apps.apple.com/app/shadowrocket/id932747118">Shadowrocket</a> (платный)'
    ),
    "macos": (
        "🍎 <b>Инструкция для macOS</b>\n\n"
        "<b>1. Скачайте V2rayN:</b>\n"
        '   📥 <a href="https://github.com/2dust/v2rayN/releases">GitHub Releases</a>\n'
        "   Скачайте файл <code>v2rayN-macos-64.dmg</code>\n\n"
        "<b>2. Установка:</b>\n"
        "   • Откройте .dmg, перетащите в Applications\n"
        "   • При первом запуске: Системные настройки →\n"
        "     Конфиденциальность → разрешить запуск\n\n"
        "<b>3. Подписка:</b>\n"
        '   • «Subscription» → «Subscription setting» → «Add»\n'
        "   • Вставьте URL подписки → OK\n"
        '   • «Update subscription»\n\n'
        "<b>4. Подключение:</b>\n"
        "   • Выберите сервер → Enter\n"
        "   • Разрешите VPN-конфигурацию\n\n"
        "<b>Альтернативные клиенты:</b>\n"
        '• <a href="https://github.com/MatsuriDayo/nekoray/releases">Nekoray</a>\n'
        '• <a href="https://apps.apple.com/app/v2box-v2ray-client/id6446814690">V2Box</a>'
    ),
    "linux": (
        "🐧 <b>Инструкция для Linux</b>\n\n"
        "<b>Вариант 1: Nekoray (GUI)</b>\n"
        '   📥 <a href="https://github.com/MatsuriDayo/nekoray/releases">GitHub Releases</a>\n'
        "   • Скачайте AppImage или .deb\n"
        "   • Запустите, добавьте подписку или VLESS-ссылку\n"
        "   • Подключитесь через GUI\n\n"
        "<b>Вариант 2: v2rayA (Web-панель)</b>\n"
        '   📥 <a href="https://github.com/v2rayA/v2rayA">GitHub</a>\n'
        "   • Установите v2rayA + xray-core\n"
        "   • Откройте <code>http://localhost:2017</code>\n"
        "   • Добавьте подписку через веб-интерфейс\n\n"
        "<b>Вариант 3: CLI (xray напрямую)</b>\n"
        "   • Установите xray-core\n"
        "   • Создайте config.json с параметрами подключения\n"
        "   • Запустите: <code>xray run -config config.json</code>\n"
        "   • Настройте системный прокси на socks5://127.0.0.1:10808"
    ),
    "router": (
        "📡 <b>Инструкция для роутера</b>\n\n"
        "<b>Поддерживаемые прошивки:</b>\n"
        "• OpenWRT + Passwall2\n"
        "• Keenetic + XKEEN\n\n"
        "<b>OpenWRT + Passwall2:</b>\n"
        "1. Установите пакет <code>passwall2</code> через opkg\n"
        "2. Перейдите в LuCI → Services → Passwall2\n"
        "3. Node List → Add → тип VLESS\n"
        "4. Введите параметры: IP, порт, UUID, Reality\n"
        "5. Main → TCP Node → выберите созданный узел\n"
        "6. Включите и сохраните\n\n"
        "<b>Keenetic + XKEEN:</b>\n"
        "1. Подключитесь по SSH к роутеру\n"
        "2. Установите XKEEN\n"
        "3. Добавьте конфигурацию через веб-интерфейс\n\n"
        "💡 <i>Для роутера лучше использовать подписочную ссылку — "
        "настройки обновляются автоматически.</i>"
    ),
    "general": (
        "📖 <b>Общая инструкция Dem1chVPN</b>\n\n"
        "<b>Как это работает:</b>\n"
        "Dem1chVPN создаёт зашифрованный туннель между вашим устройством "
        "и VPS-сервером за рубежом для ускорения и стабилизации "
        "интернет-соединения.\n\n"
        "<b>Клиенты для подключения:</b>\n"
        "🖥️ Windows: v2rayN\n"
        "📱 Android: v2rayNG\n"
        "🍎 iOS: V2RayTun\n"
        "🐧 Linux: Nekoray / v2rayA\n"
        "📡 Роутер: Passwall2 / XKEEN\n\n"
        "<b>Способы подключения:</b>\n"
        "1. 📡 <b>Подписка</b> — автоматическое обновление (рекомендуется)\n"
        "2. 🔗 <b>Ссылка</b> — скопировать и вставить\n"
        "3. 📱 <b>QR-код</b> — отсканировать камерой\n\n"
        "<b>Маршрутизация:</b>\n"
        "По умолчанию весь трафик идёт через VPN.\n"
        "Рекомендуется настроить раздельную маршрутизацию,\n"
        "чтобы РФ-сервисы (банки, Госуслуги) работали напрямую.\n"
        "Инструкция доступна при нажатии 📡 Подписка.\n\n"
        "<b>Поддержка:</b>\n"
        "Если что-то не работает — напишите администратору."
    ),
}


@router.callback_query(F.data.startswith("help:"))
async def help_handler(callback: CallbackQuery):
    platform = callback.data.split(":")[1]
    text = INSTRUCTIONS.get(platform, "❌ Инструкция не найдена.")
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=back_button("menu:help"),
        disable_web_page_preview=True,
    )
    await callback.answer()
