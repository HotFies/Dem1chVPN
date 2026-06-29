# Dem1chVPN — установка и использование

Dem1chVPN — self-hosted VPN на базе Xray-core (VLESS+Reality, TCP/443) и Hysteria2 (UDP/8444, QUIC), с управлением через Telegram-бота. Разворачивается на зарубежном VPS одним скриптом.

---

## Оглавление

1. [Требования](#требования)
2. [Подготовка](#подготовка)
3. [Установка на VPS](#установка-на-vps)
4. [Настройка Telegram-бота](#настройка-telegram-бота)
5. [Управление через бота](#управление-через-бота)
6. [Подключение клиентов](#подключение-клиентов)
   - [Windows (Dem1chVPN)](#windows-dem1chvpn)
   - [Android (v2rayNG)](#android-v2rayng)
   - [iOS (V2RayTun)](#ios-v2raytun)
   - [Роутер (OpenWRT)](#роутер-openwrt)
7. [Дополнительные компоненты](#дополнительные-компоненты)
   - [MTProto Proxy](#mtproto-proxy)
   - [AdGuard Home](#adguard-home)
   - [Cloudflare WARP](#cloudflare-warp)
8. [Подписка и автообновление](#подписка-и-автообновление)
9. [Telegram Mini App](#telegram-mini-app)
10. [Обслуживание](#обслуживание)
11. [Устранение неполадок](#устранение-неполадок)
12. [Безопасность](#безопасность)

---

## Требования

### VPS

| Параметр | Минимум | Рекомендуется |
|----------|---------|---------------|
| ОС | Debian 11 / Ubuntu 22.04 | Ubuntu 24.04 |
| CPU | 1 vCPU | 2 vCPU |
| RAM | 1 GB | 2–4 GB |
| Диск | 10 GB SSD | 20 GB SSD |
| Сеть | 500 Мбит/с | 1 Гбит/с |
| IP | 1 IPv4 | 1 IPv4 (чистый) |

Хостинги, которые нормально работают:

- Нидерланды: VDSina, TimeWeb Cloud, Aeza
- Германия: Hetzner, Contabo
- Финляндия: UpCloud
- Сингапур: Oracle Cloud (есть Free Tier)

Бюджет — примерно 400–1000 ₽/мес.

### Что нужно собрать перед установкой

1. Telegram Bot Token — создать бота у [@BotFather](https://t.me/BotFather).
2. Свой Telegram ID — узнать через [@userinfobot](https://t.me/userinfobot).
3. Поддомен на [duckdns.org](https://www.duckdns.org) — бесплатно.
4. SSH-доступ к VPS под root.

---

## Подготовка

### 1. Бот в Telegram

1. Открыть [@BotFather](https://t.me/BotFather).
2. Отправить `/newbot`.
3. Ввести имя (например, `Dem1chVPN`).
4. Ввести username (например, `my_dem1chvpn_bot`).
5. Сохранить токен (вида `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`).

### 2. Свой Telegram ID

1. Открыть [@userinfobot](https://t.me/userinfobot).
2. `/start`.
3. Сохранить число — это ваш ID.

### 3. DuckDNS (для HTTPS)

1. Зайти на [duckdns.org](https://www.duckdns.org).
2. Войти через GitHub/Google/Twitter.
3. Создать поддомен (например, `myshield`).
4. Сохранить Token (наверху страницы).
5. IP обновится автоматически на этапе установки.

### 4. SSH к VPS

```bash
ssh root@ВАШ_IP_VPS
```

Или через PuTTY (Windows) / Terminal (macOS, Linux).

---

## Установка на VPS

### Одной командой

```bash
apt update && apt install -y git
git clone https://github.com/HotFies/Dem1chVPN.git /opt/dem1chvpn
cd /opt/dem1chvpn
chmod +x install.sh
bash install.sh
```

### Что делает скрипт

| Шаг | Действие | Время |
|:---:|----------|:-----:|
| 1 | Обновление системы и зависимостей | ~3 мин |
| 2 | Харденинг (BBR, UFW, fail2ban) | ~1 мин |
| 3 | Установка Xray-core | ~1 мин |
| 4 | Ключи Reality и конфиг | ~30 сек |
| 5 | Установка Hysteria2 + конфиг | ~30 сек |
| 6 | Python venv и зависимости | ~2 мин |
| 7 | Caddy (HTTPS, ACME) | ~1 мин |
| 8 | Сборка Mini App (React) | ~1 мин |
| 9 | systemd-юниты | ~30 сек |
| 10 | cron-задачи | ~30 сек |

### Что спросит во время установки

| Запрос | Что ввести | Пример |
|--------|------------|--------|
| Telegram Bot Token | Токен от @BotFather | `1234567890:ABC...` |
| Admin Telegram ID | Ваш ID | `123456789` |
| PIN | 4 цифры для критических операций | `4829` |
| DuckDNS subdomain | Ваш поддомен | `myshield` |
| DuckDNS token | Токен с duckdns.org | `a1b2c3d4-...` |
| MTProto Proxy | y/n | `n` |
| AdGuard Home | y/n | `n` |
| WARP | y/n | `n` |

### После установки

Скрипт покажет сводку:

```
═══════════════════════════════════════════════════
  Dem1chVPN — установка завершена
═══════════════════════════════════════════════════

  Server IP:       123.45.67.89
  Xray Port:       443/tcp (VLESS + Reality)
  Hysteria Port:   8444/udp (Hysteria2 + Salamander)
  SNI:             dl.google.com
  Public Key:      XXXXX...
  Short ID:        XXXXX

  Subscription:    https://<ваш-домен>.duckdns.org:8443/sub/<token>
  Mini App:        https://<ваш-домен>.duckdns.org:8443/webapp/
```

Сохраните где-нибудь, пригодится.

---

## Настройка Telegram-бота

### Первый запуск

1. Открыть бота в Telegram.
2. `/start`.
3. Увидите главное меню админа:

```
Dem1chVPN — панель управления

Привет, [имя]
Статус: Администратор

[Пользователи]
[Маршрутизация]
[Мониторинг]
[Настройки]
[Помощь]
[Открыть панель]   ← Mini App
```

### Первый пользователь

1. Нажать «Пользователи».
2. Нажать «Добавить пользователя».
3. Имя (например, `Мой_телефон`).
4. Лимит трафика в ГБ (0 — безлимит).
5. Срок в днях (0 — бессрочно).
6. Бот пришлёт все данные для подключения: параметры аккаунта, VLESS- и Hysteria2-ссылки, URL подписки (для автообновления) и QR-код.
7. Скопируйте **URL подписки** и импортируйте его в VPN-клиент (см. инструкции по платформам). Подписка содержит обе ссылки и обновляется сама.

---

## Управление через бота

### Структура меню

```
Dem1chVPN Bot
├── Пользователи
│   ├── Добавить
│   ├── Список
│   ├── Создать приглашение
│   └── Трафик всех
│
├── Маршрутизация
│   ├── Текущие правила
│   ├── В PROXY
│   ├── В DIRECT
│   ├── Удалить правило
│   ├── Обновить списки
│   ├── Проверить сайт
│   └── Режимы
│
├── Мониторинг
│   ├── Статус сервера
│   ├── Статус Xray
│   ├── Статус Hysteria2
│   ├── Трафик за день
│   ├── Speedtest
│   └── Уведомления
│
├── Настройки
│   ├── Обновить Xray-core
│   ├── Обновить гео-базы
│   ├── Изменить SNI
│   ├── Ключи Reality
│   ├── Бэкап / Восстановить
│   └── Перезапуск Xray
│
└── Помощь
    ├── Общая инструкция
    ├── Windows
    ├── Android
    ├── iOS
    └── Роутер
```

### Юзеры

- Добавить: Пользователи → Добавить → имя → лимит → срок.
- Заблокировать/разблокировать: Пользователи → Список → выбрать → Блок/Разблок.
- Инвайт: Пользователи → Приглашение → имя → лимит → срок → ссылка `t.me/bot?start=inv_XXXX`. Друг тыкает — бот сам всё создаёт.

### Маршрутизация

В PROXY (через VPN):

```
Маршрутизация → В PROXY → youtube.com
```

В DIRECT (мимо VPN):

```
Маршрутизация → В DIRECT → gosuslugi.ru
```

Из коробки уже в PROXY: YouTube, Discord, Telegram, WhatsApp, Instagram, TikTok, ChatGPT, Claude, Gemini и ещё около 20 сервисов.

### Проверка сайта

```
Маршрутизация → Проверить сайт → youtube.com

Доступность с VPS: OK (142 ms)
Маршрутизация: PROXY
```

---

## Подключение клиентов

### Windows (Dem1chVPN)

#### Нативный клиент

Рекомендуемый вариант. Внутри уже sing-box и автоимпорт.

1. Скачать `Dem1chVPN-Setup.exe` со страницы [GitHub Releases](https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe).
2. Поставить.

#### Импорт подписки (deeplink)

1. В Личном кабинете в Telegram нажать «Импорт подписки (Windows)».
2. Браузер спросит, открыть ли `dem1chvpn://import/...` в приложении — разрешить.
3. Маршруты применятся сами.

Альтернатива: скопировать URL подписки и вставить в настройках приложения.

#### Выбор протокола

В подписке всегда обе ссылки — VLESS и Hysteria2. На Dashboard есть переключатель: VLESS (TCP/443, маска `dl.google.com`) или Hysteria2 (UDP/8444, QUIC). По дефолту активен Hysteria2.

Если один протокол перестал работать (DPI начал резать), переключаетесь на другой — клиент сам перегенерирует sing-box-конфиг и переподключится.

#### Альтернатива: v2rayN

Если нужны ручные настройки — `v2rayN-With-Core.zip` с [github.com/2dust/v2rayN](https://github.com/2dust/v2rayN/releases). Добавить URL подписки через «Подписки», включить «Обход адресов РФ» в Routing Settings.

### Android

Тонкий момент: **v2rayNG работает на Xray-core и не умеет Hysteria2** — из подписки он подхватит только VLESS. Если хотите оба протокола в одном приложении (на случай, если ТСПУ начнёт резать какой-то из них), нужен клиент на sing-box: **NekoBox for Android** или **Hiddify Next**.

#### NekoBox (рекомендуется, оба протокола)

1. APK с [GitHub Releases](https://github.com/MatsuriDayo/NekoBoxForAndroid/releases). В Google Play нет.
2. Разрешить установку из неизвестных источников.
3. ≡ → Группы → `+` → «Удалённый профиль», вставить URL подписки.
4. Обновить — в списке появятся VLESS и Hysteria2.
5. Выбрать сервер, кнопка подключения снизу.

Если один протокол отвалился — переключаетесь в списке на второй и переподключаетесь.

#### Hiddify Next (тоже оба)

1. [Google Play](https://play.google.com/store/apps/details?id=app.hiddify.com) или [GitHub Releases](https://github.com/hiddify/hiddify-next/releases).
2. Главный экран → `+` → вставить URL подписки.

#### v2rayNG (только VLESS)

Если устраивает VLESS и не хочется ставить sing-box-клиенты:

1. [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang) или [APK с GitHub](https://github.com/2dust/v2rayNG/releases).
2. `☰` → «Группа подписки» → `+`, вставить URL.
3. «Обновить подписку», нажать ▶.

Hysteria2-ссылка из подписки тут просто проигнорируется.

### iOS (V2RayTun)

#### Установка

[V2RayTun в App Store](https://apps.apple.com/app/v2raytun/id6476628951). Если в вашем регионе приложение недоступно, поменяйте регион Apple ID на любой не-РФ (это бесплатно).

#### Импорт через deeplinks

1. Открыть Личный кабинет в Telegram.
2. «Импорт подписки из Telegram (V2RayTun)» — ссылка `v2raytun://import/...`. Разрешить открыть приложение.
3. «Импорт маршрутов» — ссылка `v2raytun://import_route/...`. Это включит обход для российских банков и Яндекса.

#### Подключение

1. В V2RayTun потянуть список вниз для обновления.
2. Выбрать сервер, нажать ▶.
3. Разрешить установку VPN-профиля.

#### Альтернативы

Если V2RayTun не подходит — [Streisand](https://apps.apple.com/app/streisand/id6450534064) или [V2Box](https://apps.apple.com/app/v2box-v2ray-client/id6446814690). Подписку вставлять вручную через настройки.

### Роутер (OpenWRT)

#### OpenWRT + Passwall2

1. Поставить `passwall2` через LuCI.
2. LuCI → Services → Passwall2.
3. Добавить сервер:
   - Type: VLESS
   - Address: IP вашего VPS
   - Port: 443
   - UUID: из бота
   - Transport: TCP
   - TLS: Reality
   - SNI: `dl.google.com`
   - Public Key: из бота
   - Short ID: из бота
4. Включить режим Global / GFW List.

Hysteria2 на OpenWRT тоже поднимается, но через отдельный пакет `hysteria` или sing-box. Конкретные параметры — host, порт 8444/udp, пароль `user:hysteria_password`, obfs Salamander с паролем — берутся из подписки или у админа.

#### Keenetic + XKEEN

1. Поставить [XKEEN](https://github.com/Jenya-developer/xkeen) через SSH.
2. Конфигурация — через веб-интерфейс роутера.

Совет: для роутера лучше использовать URL подписки, тогда настройки обновляются сами.

---

## Дополнительные компоненты

### MTProto Proxy

Прокси для Telegram. Если с основным VPN что-то не так, бот всё равно достижим через MTProto.

Установка:

```bash
bash /opt/dem1chvpn/server/mtproto/setup.sh
```

Использование:

1. Бот выдаст ссылку вида `tg://proxy?server=IP&port=443&secret=...`.
2. Отправить себе/друзьям.
3. По нажатию Telegram сам предложит добавить прокси.

### AdGuard Home

DNS-блокировщик рекламы и трекеров. Все устройства, ходящие через Dem1chVPN, получают блокировку без AdBlock.

Установка:

```bash
bash /opt/dem1chvpn/server/adguard/setup.sh
```

Что блокируется:

- баннеры и видеореклама;
- Google Analytics, Facebook Pixel и прочие трекеры;
- фишинговые и вредоносные домены.

Панель: `http://127.0.0.1:8053` (admin / dem1chvpn).

AdGuard занимает 53/udp. Скрипт отключит `systemd-resolved` автоматически.

### Cloudflare WARP

Double-hop: Устройство → VPS → Cloudflare → Интернет. Наружу торчит IP Cloudflare, а не вашего VPS.

Зачем:

- IP VPS не светится в трекинге;
- доступ к стримингу (Netflix, Disney+);
- IP Cloudflare не в чёрных списках.

Установка:

```bash
bash /opt/dem1chvpn/server/warp/setup.sh
```

Управление: Настройки в боте или Mini App → toggle WARP On/Off.

---

## Подписка и автообновление

Подписка — это URL, который клиент периодически дёргает и сам обновляет конфигурацию. Не надо менять настройки руками при ротации ключей.

### URL подписки

Формат:

```
https://<ваш-домен>.duckdns.org:8443/sub/ТОКЕН
```

Внутри base64, после декодирования — список ссылок: `vless://...` и (если включён Hysteria) `hysteria2://...`. Клиенты, поддерживающие multi-line подписки, импортируют оба сервера.

У каждого пользователя свой токен. Получить:

- автоматически при создании юзера (бот пришлёт);
- Пользователи → выбрать → Подписка.

### Что обновляется само

- параметры серверов (IP, ключи, SNI, обфускация);
- статистика трафика;
- срок аккаунта;
- обновление обычно каждые 6 часов.

### Правила маршрутизации

Отдельный эндпоинт:

```
https://<ваш-домен>.duckdns.org:8443/sub/ТОКЕН/routing
```

JSON со списком proxy/direct/block.

---

## Telegram Mini App

Веб-панель управления внутри Telegram, вместо текстовых команд.

### Как открыть

В боте — «Открыть панель» (для админа) или «Личный кабинет» (для пользователя).

### Что внутри

| Раздел | Что есть |
|--------|----------|
| Dashboard | CPU, RAM, диск, статус Xray, Hysteria2 и WARP, трафик |
| Users | Список юзеров, статусы, трафик |
| Routes | Управление доменами (proxy/direct/block) |
| Settings | Toggle WARP, AdGuard, MTProto, перезапуск Xray |

Mini App доступен, только если домен (DuckDNS) настроен и Caddy получил TLS-сертификат.

---

## Обслуживание

### Cron

| Задача | Расписание | Что делает |
|--------|------------|------------|
| Обновление гео-баз | каждые 6 часов | `geoip.dat` + `geosite.dat` |
| Health check | каждые 5 минут | Xray, бот, sub-сервер, Hysteria. Перезапуск при падении |
| Бэкап | ежедневно в 3:00 | `tar.gz` с конфигами, БД, .env |
| DuckDNS | каждые 5 минут | обновление IP |
| Hysteria cert refresh | раз в неделю | перезапуск, чтобы подхватить обновлённый сертификат Caddy |

### Полезные команды

```bash
# Логи
journalctl -u dem1chvpn-bot -f
journalctl -u xray -f
journalctl -u dem1chvpn-hysteria -f
journalctl -u dem1chvpn-sub -f
journalctl -u caddy -f

# Перезапуск
systemctl restart dem1chvpn-bot
systemctl restart xray
systemctl restart dem1chvpn-hysteria
systemctl restart dem1chvpn-sub

# Статус
systemctl status dem1chvpn-bot dem1chvpn-sub dem1chvpn-hysteria xray caddy

# Ручное обновление гео-баз
/opt/dem1chvpn/cron/update_geodata.sh

# Ручной бэкап
/opt/dem1chvpn/cron/backup.sh
```

### Обновление Xray-core

Через бота: Настройки → Обновить Xray-core.

Руками:

```bash
bash <(curl -Ls https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh)
systemctl restart xray
```

### Бэкап и восстановление

Через бота: Настройки → Бэкап. Бот пришлёт `.tar.gz` в чат.

Внутри:

- `xray_config.json`
- `hysteria/config.yaml`
- `dem1chvpn.db`
- `.env`

Восстановление руками:

```bash
cd /opt/dem1chvpn
tar -xzf dem1chvpn_backup_ДАТА.tar.gz
systemctl restart xray dem1chvpn-hysteria dem1chvpn-bot dem1chvpn-sub
```

---

## Устранение неполадок

### Бот молчит

```bash
systemctl status dem1chvpn-bot
journalctl -u dem1chvpn-bot --no-pager -n 50
systemctl restart dem1chvpn-bot
```

Часто причина:

- неверный `BOT_TOKEN` в `.env`;
- VPS без интернета;
- сломан Python venv → пересоздать: `python3 -m venv /opt/dem1chvpn/venv`.

### VPN не подключается

VLESS (TCP/443):

```bash
systemctl status xray
journalctl -u xray --no-pager -n 30
ss -tlnp | grep 443
ufw status | grep 443
```

Hysteria2 (UDP/8444):

```bash
systemctl status dem1chvpn-hysteria
journalctl -u dem1chvpn-hysteria --no-pager -n 30
ss -ulnp | grep 8444
ufw status | grep 8444
```

В клиенте на Windows можно попробовать переключиться на другой протокол — если режется только один.

Проверить, доступен ли вообще IP: в боте Мониторинг → проверка IP.

### Подписка не обновляется

```bash
systemctl status dem1chvpn-sub
systemctl status caddy
journalctl -u caddy --no-pager -n 20
curl -k https://localhost:8443/health
# должно быть {"status": "ok"}
```

### Mini App не открывается

1. DuckDNS должен указывать на IP VPS.
2. Caddy должен получить сертификат.
3. Webapp должен быть собран:

```bash
ls /opt/dem1chvpn/server/webapp/dist/
```

Если пусто — пересобрать:

```bash
cd /opt/dem1chvpn/server/webapp
npm install && npm run build
```

### IP недоступен из России

Симптом: SSH работает, а VPN — нет (оба протокола).

Что делать:

1. Включить WARP — наружу будет торчать IP Cloudflare.
2. Сменить SNI в боте: Настройки → Изменить SNI.
3. Сменить VPS — переустановить Dem1chVPN на новом сервере, восстановиться из бэкапа.

---

## Безопасность

### Что прикручено по умолчанию

| Мера | Описание |
|------|----------|
| UFW | Открыты только 22, 80, 443/tcp, 8443/tcp, 8444/udp |
| fail2ban | Защита SSH от брутфорса |
| TCP BBR | Конджешен-контрол |
| Reality | Трафик визуально неотличим от HTTPS |
| Hysteria + Salamander | QUIC с обфускацией пакетов |
| PIN | На критические операции в боте |

### Рекомендации

1. Не ставить PIN типа `0000` или `1234`.
2. В `ADMIN_IDS` держать только свой ID.
3. Регулярно обновлять Xray-core и гео-базы.
4. Бэкапы — автоматические каждый день плюс руками перед изменениями.
5. VLESS-ссылки не светить в публичных чатах.
6. Предпочитать подписку прямым ссылкам — при компрометации можно пересоздать токен.

### `.env`

`/opt/dem1chvpn/.env` содержит секреты. Права `600`, только root.

```bash
ls -la /opt/dem1chvpn/.env
# -rw------- 1 root root ... .env
```

---

## Схема стека (справочно)

```
Dem1chVPN на VPS
├── Xray-core             :443    VLESS + Reality + TCP
├── Hysteria2             :8444   QUIC + Salamander obfs
├── Telegram Bot                  aiogram 3 + SQLite
├── Subscription Server   :8080   FastAPI + uvicorn
├── Caddy                 :8443   HTTPS reverse proxy → :8080
├── Cron                          обновления, health check, бэкапы
│
└── Опционально:
    ├── MTProto Proxy     :8800   Docker, для Telegram
    ├── AdGuard Home      :5353   Docker, DNS-блокировка
    └── WARP                      SOCKS5 outbound в Xray
```

---

## FAQ

**Это бесплатно?**
Софт open-source. Платите только за VPS — примерно 400–1000 ₽/мес.

**Сколько пользователей тянет?**
На 1 vCPU и 2 GB RAM комфортно 10–20 человек.

**Нужен ли свой домен?**
Нет, DuckDNS бесплатный. Свой домен можно подключить, если хочется.

**Если VPS заблокируют — что делать?**
Включить WARP, сменить SNI, либо переехать на новый VPS из бэкапа.

**На роутере работает?**
Да — OpenWRT (Passwall2), Keenetic (XKEEN).

**VPN тормозит интернет?**
Минимально. Российские сайты идут напрямую, остальное — через VPN. И с Hysteria2 over QUIC задержки заметно ниже, чем у классических TCP-VPN.

---

> Версия: 1.2
> Дата: 27.05.2026
> Проект: Dem1chVPN
