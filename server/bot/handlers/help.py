"""
Dem1chVPN Bot — Help Handler
"""
from aiogram import Router, F
from aiogram.types import CallbackQuery
from ..keyboards.menus import help_menu, back_button
from ..utils.telegram_helpers import safe_edit_text

router = Router()

INSTRUCTIONS = {
    "windows": (
        "🖥️ <b>Инструкция для Windows</b>\n\n"
        "<b>Вариант 1: Dem1chVPN (рекомендуется)</b>\n\n"
        "<b>1. Скачайте Dem1chVPN:</b>\n"
        '   📥 <a href="https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe">GitHub Releases</a>\n'
        "   Файл: <code>Dem1chVPN-Setup.exe</code>\n\n"
        "<b>2. Установка:</b>\n"
        "   • Запустите установщик и пройдите шаги.\n\n"
        "<b>3. Импорт подписки (любой способ):</b>\n"
        "   • <b>Автоимпорт:</b> в Личном кабинете нажмите «Импорт подписки (Windows)» — "
        "откроется ссылка <code>dem1chvpn://import/…</code>, подписка добавится сама.\n"
        "   • <b>Вручную:</b> скопируйте URL подписки из бота и вставьте в поле подписки в приложении.\n"
        "   • Одиночные <code>vless://</code> / <code>hysteria2://</code> сюда вставлять не нужно — "
        "приложение работает по URL подписки (обе ссылки внутри).\n\n"
        "<b>4. Выбор протокола:</b>\n"
        "   • На главном экране в Dashboard есть переключатель VLESS / Hysteria2.\n"
        "   • По дефолту активен Hysteria2 (UDP/8444, QUIC) — стабильнее под ТСПУ.\n"
        "   • Если провайдер режет UDP — переключитесь на VLESS (TCP/443).\n\n"
        "<b>5. Подключение:</b>\n"
        "   • Нажмите кнопку подключения в приложении.\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "<b>Вариант 2: v2rayN (альтернатива)</b>\n\n"
        "<b>1. Скачайте v2rayN:</b>\n"
        '   📥 <a href="https://github.com/2dust/v2rayN/releases">GitHub Releases</a>\n'
        "   Файл: <code>v2rayN-windows-64-SelfContained.zip</code>\n\n"
        "<b>2. Настройка:</b>\n"
        "   • Распакуйте архив, запустите <code>v2rayN.exe</code>.\n"
        "   • Subscription → Add → URL подписки → сохранить.\n"
        "   • Update subscription. В списке появятся два сервера — VLESS и Hysteria2.\n"
        "   • Выберите тот, что работает в вашей сети."
    ),
    "android": (
        "📱 <b>Инструкция для Android</b>\n\n"
        "<b>Какой клиент брать:</b>\n"
        "• <b>v2rayNG</b> — только VLESS. Hysteria2 из подписки он проигнорирует (работает на Xray-core).\n"
        "• <b>NekoBox for Android</b> — оба протокола, переключаются одним тапом (на sing-box).\n"
        "• <b>Hiddify Next</b> — тоже оба, sing-box.\n\n"
        "Если хотите запас на случай блокировки одного из протоколов — ставьте NekoBox или Hiddify.\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "<b>Вариант 1: NekoBox (рекомендуется)</b>\n\n"
        "<b>1. Скачайте:</b>\n"
        '   📥 <a href="https://github.com/MatsuriDayo/NekoBoxForAndroid/releases">GitHub Releases</a>\n'
        "   Файл: <code>NB4A-*-arm64-v8a.apk</code> (или универсальный).\n"
        "   В Google Play нет — только APK.\n\n"
        "<b>2. Подписка:</b>\n"
        "   • Скопировать URL подписки из бота.\n"
        "   • ≡ → Группы → +.\n"
        "   • Тип «Удалённый профиль», вставить URL → сохранить → обновить.\n"
        "   • В списке появятся VLESS и Hysteria2.\n\n"
        "<b>3. Подключение:</b>\n"
        "   • Выбрать сервер → кнопка подключения снизу.\n"
        "   • Если один протокол отвалится — переключаетесь на другой в списке.\n\n"
        "━━━━━━━━━━━━━━━━━\n\n"
        "<b>Вариант 2: v2rayNG (только VLESS)</b>\n\n"
        "<b>1. Скачайте:</b>\n"
        '   📥 <a href="https://play.google.com/store/apps/details?id=com.v2ray.ang">Google Play</a>\n\n'
        "<b>2. Подписка:</b>\n"
        "   • ☰ → Subscription group settings → +.\n"
        "   • Вставить URL подписки → галочка.\n"
        "   • ☰ → Update subscription.\n"
        "   • В списке будет один сервер — VLESS.\n\n"
        "<b>3. Маршрутизация:</b>\n"
        "   • ☰ → Settings → Routing settings.\n"
        "   • Domain strategy: IPIfNonMatch.\n"
        "   • Bypass LAN and mainland (или свои правила для РФ).\n\n"
        "<b>4. Подключение:</b>\n"
        "   • ▶️ снизу, разрешить VPN."
    ),
    "ios": (
        "🍎 <b>Инструкция для iOS</b>\n\n"
        "<b>1. Скачайте V2RayTun:</b>\n"
        '   📥 <a href="https://apps.apple.com/app/v2raytun/id6476628951">App Store</a>\n\n'
        "<b>2. Подписка (рекомендуется):</b>\n"
        "   • Скопируйте ссылку подписки из бота.\n"
        "   • Главный экран → «+» → вставьте ссылку.\n"
        "   • В подписке два сервера — VLESS (TCP/443) и Hysteria2 (UDP/8444). "
        "Выбирайте в списке тот, что работает у вашего провайдера. "
        "Обычно Hysteria2 устойчивее под ТСПУ, но если режут UDP — берите VLESS.\n\n"
        "<b>3. Или вручную:</b>\n"
        "   • Скопируйте прямую ссылку (vless:// или hysteria2://).\n"
        "   • «+» → вставьте из буфера.\n"
        "   • Или отсканируйте QR-код.\n\n"
        "<b>4. Подключение:</b>\n"
        "   • Выберите сервер → нажмите кнопку подключения.\n"
        "   • Разрешите добавление VPN-конфигурации.\n\n"
        "<b>Альтернативные клиенты:</b>\n"
        '• <a href="https://apps.apple.com/app/streisand/id6450534064">Streisand</a>\n'
        '• <a href="https://apps.apple.com/app/v2box-v2ray-client/id6446814690">V2Box</a>\n'
        '• <a href="https://apps.apple.com/app/shadowrocket/id932747118">Shadowrocket</a> (платный)'
    ),
    "macos": (
        "🍎 <b>Инструкция для macOS</b>\n\n"
        "<b>1. Скачайте V2rayN:</b>\n"
        '   📥 <a href="https://github.com/2dust/v2rayN/releases">GitHub Releases</a>\n'
        "   Файл: <code>v2rayN-macos-64.dmg</code>\n\n"
        "<b>2. Установка:</b>\n"
        "   • Откройте .dmg, перетащите в Applications.\n"
        "   • При первом запуске: Системные настройки → Конфиденциальность → разрешить запуск.\n\n"
        "<b>3. Подписка:</b>\n"
        "   • Subscription → Subscription setting → Add.\n"
        "   • Вставьте URL подписки → OK → Update subscription.\n"
        "   • В списке появятся два сервера — VLESS и Hysteria2. Выбираете тот, что работает.\n\n"
        "<b>4. Подключение:</b>\n"
        "   • Выберите сервер → Enter.\n"
        "   • Разрешите установку VPN-конфигурации.\n\n"
        "<b>Альтернативные клиенты:</b>\n"
        '• <a href="https://github.com/MatsuriDayo/nekoray/releases">Nekoray</a> (поддерживает Hysteria2)\n'
        '• <a href="https://apps.apple.com/app/v2box-v2ray-client/id6446814690">V2Box</a>'
    ),
    "linux": (
        "🐧 <b>Инструкция для Linux</b>\n\n"
        "<b>Вариант 1: Nekoray (GUI)</b>\n"
        '   📥 <a href="https://github.com/MatsuriDayo/nekoray/releases">GitHub Releases</a>\n'
        "   • Скачайте AppImage или .deb.\n"
        "   • Запустите, добавьте подписку или прямую ссылку (vless:// или hysteria2://).\n"
        "   • Подключитесь через GUI. Nekoray поддерживает и VLESS, и Hysteria2.\n\n"
        "<b>Вариант 2: sing-box (CLI)</b>\n"
        '   📥 <a href="https://github.com/SagerNet/sing-box/releases">GitHub Releases</a>\n'
        "   • Поддерживает оба протокола в одном бинаре.\n"
        "   • Конфиг можно сгенерировать через web-конвертер из ссылки подписки.\n\n"
        "<b>Вариант 3: v2rayA (web-панель)</b>\n"
        '   📥 <a href="https://github.com/v2rayA/v2rayA">GitHub</a>\n'
        "   • Установите v2rayA + xray-core.\n"
        "   • Откройте <code>http://localhost:2017</code>.\n"
        "   • Добавьте подписку через веб-интерфейс. VLESS заработает сразу; Hysteria2 — если v2rayA собран с sing-box backend.\n\n"
        "<b>Вариант 4: xray-core напрямую</b>\n"
        "   • Установите xray-core (только VLESS, Hysteria2 не умеет).\n"
        "   • Создайте config.json.\n"
        "   • <code>xray run -config config.json</code>.\n"
        "   • Системный прокси: socks5://127.0.0.1:10808."
    ),
    "router": (
        "📡 <b>Инструкция для роутера</b>\n\n"
        "<b>Поддерживаемые прошивки:</b>\n"
        "• OpenWRT + Passwall2\n"
        "• Keenetic + XKEEN\n\n"
        "<b>OpenWRT + Passwall2:</b>\n"
        "1. Установите <code>passwall2</code> через opkg.\n"
        "2. LuCI → Services → Passwall2.\n"
        "3. Node List → Add. Два варианта:\n"
        "   • Тип VLESS (Xray): IP, порт 443, UUID, Reality, SNI, Public Key, Short ID.\n"
        "   • Тип Hysteria2 (sing-box): домен, порт 8444, username:password, obfs salamander.\n"
        "4. Main → TCP Node → выберите активный узел.\n"
        "5. Включите и сохраните. Между VLESS и Hysteria2 можно переключаться галочкой.\n\n"
        "<b>Keenetic + XKEEN:</b>\n"
        "1. SSH к роутеру.\n"
        "2. Установите XKEEN.\n"
        "3. Конфиг через веб-интерфейс. Параметры VLESS и Hysteria2 — из подписки или из «Прямой ссылки» в боте.\n\n"
        "💡 <i>На роутер лучше отдавать URL подписки — настройки обновляются сами.</i>"
    ),
    "general": (
        "📖 <b>Общая инструкция Dem1chVPN</b>\n\n"
        "<b>Как это работает:</b>\n"
        "Dem1chVPN держит зашифрованный туннель между устройством и VPS за рубежом — "
        "сразу двумя независимыми каналами.\n\n"
        "<b>Протоколы:</b>\n"
        "🛡 <b>VLESS + Reality</b> (TCP/443) — маскируется под HTTPS к dl.google.com.\n"
        "⚡ <b>Hysteria2 + Salamander</b> (UDP/8444) — QUIC, обходит ML-фильтры ТСПУ.\n\n"
        "Подписка содержит обе ссылки. Если на одном протоколе режут — переключаетесь "
        "на второй прямо в клиенте (на Dem1chVPN для Windows это одна кнопка в Dashboard).\n\n"
        "<b>Клиенты:</b>\n"
        "🖥️ Windows: Dem1chVPN (оба) / v2rayN (оба, на sing-box-ядре)\n"
        "📱 Android: NekoBox или Hiddify Next (оба) / v2rayNG (только VLESS)\n"
        "🍎 iOS: V2RayTun, Streisand, V2Box, Shadowrocket — все на sing-box, оба протокола\n"
        "🐧 Linux: Nekoray, sing-box (оба) / xray-core (только VLESS)\n"
        "📡 Роутер: Passwall2 / XKEEN — sing-box-узлы умеют оба\n\n"
        "<b>Способы подключения:</b>\n"
        "1. 📡 <b>Подписка</b> — автообновление, рекомендуется.\n"
        "2. 🔗 <b>Прямая ссылка</b> — vless:// или hysteria2:// в буфер.\n"
        "3. 📱 <b>QR-код</b> — сканировать камерой.\n\n"
        "<b>Маршрутизация:</b>\n"
        "В подписке уже есть split-tunneling: банки, Госуслуги и крупные RU-сервисы идут напрямую, "
        "остальное — через туннель. Списки доменов руками поддерживать не надо.\n\n"
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
