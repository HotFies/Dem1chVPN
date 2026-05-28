<div align="center">

# Dem1chVPN

Персональный VPN-сервер с управлением через Telegram.

VLESS+Reality, Hysteria2/QUIC, Cloudflare WARP, DoH, split-tunneling, Mini App.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Xray Core](https://img.shields.io/badge/Xray--core-latest-brightgreen)](https://github.com/XTLS/Xray-core)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)

</div>

---

## Что это

Dem1chVPN — готовый стек для своего VPN на VPS. Заточен под Россию: обходит блокировки, лечит замедление YouTube/Discord/Telegram, открывает санкционные сервисы вроде ChatGPT, Gemini, NotebookLM.

Трафик идёт двумя независимыми каналами: VLESS+Reality+XTLS-Vision (TCP/443, маскировка под `dl.google.com`) и Hysteria2+Salamander (UDP/8444, QUIC). Если ТСПУ начнёт резать один транспорт — переключаешься на другой в один тап в клиенте. Управление — через Telegram-бот и Mini App, без веб-панелей и ручных правок конфигов.

Один скрипт `install.sh` поднимает рабочий VPN с подпиской, личным кабинетом и ботом примерно за 5 минут.

## Возможности

### Ядро VPN

| Функция | Описание |
|---------|----------|
| VLESS + Reality + XTLS-Vision | Неотличим от HTTPS, не палится по сигнатуре. TCP/443 |
| Hysteria2 + Salamander obfs | QUIC поверх UDP, параллельный канал на случай блокировки VLESS |
| Reality-камуфляж | Трафик выглядит как обращение к `dl.google.com` |
| DNS-over-HTTPS | DNS-запросы шифруются, провайдер не видит, что вы открываете |
| Cloudflare WARP | Чистый IP Cloudflare для YouTube, AI-сервисов, стриминга |
| Split-tunneling | Российские сайты идут напрямую, остальные через WARP |
| Переключение протокола | Toggle VLESS / Hysteria2 прямо в Windows-клиенте, без перенастройки |

### Управление и UX

| Функция | Описание |
|---------|----------|
| Telegram-бот | Управление через inline-кнопки |
| Mini App | Веб-панель внутри Telegram |
| Личный кабинет | Статус, трафик, ссылки, инструкции в одном месте |
| Авто-подписки | Конфиги на клиентах обновляются сами |
| iOS deeplinks | Подписка и маршруты в V2RayTun одним нажатием |
| Windows deeplinks | Импорт подписки в Dem1chVPN одним нажатием |
| Windows desktop client | Нативный клиент с автоимпортом подписки |
| Тикет-система | Поддержка пользователей внутри Mini App |
| Инвайт-система | Удобно подключать друзей и семью |
| Мониторинг | Трафик, нагрузка, проверка доступности IP |

### Опции

| Функция | Описание |
|---------|----------|
| AdGuard Home | Блокировка рекламы на уровне DNS |
| MTProto Proxy | Запасной канал для Telegram, если с VPN что-то не так |

## Как это работает

```
Пользователь (Россия)
    │
    ├─ VLESS + Reality + XTLS-Vision (TCP/443)  ← маскируется под dl.google.com
    └─ Hysteria2 + Salamander obfs   (UDP/8444) ← QUIC, обходит DPI 2026 года
    │
    │ DoH, TLS-fingerprint: chrome
    ▼
┌─────────────── VPS (Европа) ───────────────┐
│                                             │
│   Xray-core         (TCP/443)  ← VLESS      │
│   hysteria-server   (UDP/8444) ← Hysteria2  │
│                                             │
│     ├── Российские сайты    → DIRECT        │
│     │   (geosite:ru, банки, ВК, Яндекс)     │
│     │                                       │
│     └── Всё остальное       → WARP          │
│         (YouTube, Discord, AI, стриминг)    │
│         SOCKS5 → warp-svc на localhost      │
│                                             │
│   Наружу: чистый IP Cloudflare              │
└─────────────────────────────────────────────┘
```

### Почему быстрее обычного VPN

| Проблема обычных VPN | Что делает Dem1chVPN |
|---|---|
| Весь трафик через VPN — Сбер тормозит | Split-tunneling: российские сайты идут напрямую |
| YouTube замедляется по SNI | Reality: трафик выглядит как `dl.google.com` |
| ТСПУ режет VLESS+TCP по ML-паттернам (с 02.2026) | Hysteria2/QUIC: альтернативный UDP-канал в одной подписке |
| DNS запросы видны провайдеру | DoH: DNS зашифрован через HTTPS |
| IP VPS заблокирован сервисами | WARP SOCKS5: чистый IP Cloudflare |
| `fp: random` — экзотический fingerprint | `fp: chrome` — самый массовый TLS |

## Требования

- VPS: 1 vCPU, 1 GB RAM, 10 GB SSD (минимум)
- ОС: Debian 12+ или Ubuntu 22.04+
- Расположение: за пределами РФ (Нидерланды, Германия и т.п.)
- Стоимость: примерно 400–1500 ₽/мес (например, [VDSina](https://vdsina.com))

## Установка

### 1. Подготовка

- Завести бота у [@BotFather](https://t.me/BotFather), сохранить токен
- Узнать свой Telegram ID через [@userinfobot](https://t.me/userinfobot)

### 2. Запуск на сервере

```bash
ssh root@ваш-ip

apt update && apt install -y git
git clone https://github.com/HotFies/Dem1chVPN.git /opt/dem1chvpn
cd /opt/dem1chvpn
chmod +x install.sh
./install.sh
```

Скрипт спросит токен и PIN, дальше всё сам:

- ставит Xray-core, Hysteria2, Python, Caddy, Node.js
- хардерит сервер (UFW, fail2ban, BBR, sysctl)
- настраивает VLESS+Reality с маской `dl.google.com` (TCP/443)
- настраивает Hysteria2 с Salamander-обфускацией (UDP/8444), сертификат — общий с Caddy
- ставит Cloudflare WARP (SOCKS5 proxy)
- настраивает DNS-over-HTTPS
- создаёт systemd-юниты: `xray`, `dem1chvpn-hysteria`, `dem1chvpn-bot`, `dem1chvpn-sub`
- определяет hostname VPS и выпускает TLS-сертификат через Caddy (HTTP-01)
- собирает React Mini App (Vite + TypeScript)
- запускает бота и subscription-сервер

### 3. Готово

Открываете бота в Telegram, `/start`, добавляете пользователей, раздаёте ссылки.

У пользователя в боте есть кнопка «Личный кабинет» — там статус, трафик, ссылки, инструкции, deeplinks для iOS.

## Архитектура

```
┌──────────────────────────────────────────────────────┐
│                         VPS                          │
│                                                      │
│   :443  → Xray (VLESS + Reality + XTLS-Vision) TCP   │
│            ├── DNS: порт 53 → direct (мимо WARP)     │
│            ├── DNS: DoH (1.1.1.1 + 8.8.8.8)          │
│            ├── RU-домены → direct                    │
│            └── остальное → WARP (SOCKS5 → warp-svc)  │
│                                                      │
│   :8444 → Hysteria2 (Salamander obfs) UDP/QUIC       │
│            ├── auth.userpass читается из SQLite      │
│            ├── TLS-сертификат общий с Caddy          │
│            └── masquerade → news.ycombinator.com     │
│                                                      │
│   :8443 → Caddy (HTTPS, auto-cert) → FastAPI :8080   │
│            ├── /sub/{token}            подписки      │
│            ├── /sub/{token}/v2raytun   deeplinks     │
│            ├── /sub/{token}/routing    правила       │
│            ├── /api/my/account         кабинет       │
│            ├── /api/my/links           ссылки        │
│            ├── /api/users/*            упр. юзерами  │
│            ├── /api/tickets/*          тикеты        │
│            ├── /api/routes/*           маршруты      │
│            ├── /api/server/status      мониторинг    │
│            └── /webapp/                Mini App      │
│                                                      │
│   Telegram Bot (aiogram 3)  ← управление             │
│   SQLite                    ← данные                 │
│   gRPC :10085               ← Xray Stats API         │
└──────────────────────────────────────────────────────┘
```

### Mini App

```
┌── Telegram Bot ──────────────────────────────────────┐
│                                                      │
│  Админ                      Пользователь             │
│  ┌──────────────┐           ┌──────────────────┐     │
│  │ Открыть      │           │ Личный           │     │
│  │ панель       │           │ кабинет          │     │
│  └──────┬───────┘           └───────┬──────────┘     │
│         │                           │                │
│         ▼                           ▼                │
│  ┌─── Mini App (React + Vite) ──────────────────┐    │
│  │                                              │    │
│  │  Admin pages:          User pages:           │    │
│  │  ├── Dashboard         ├── MyAccount (home)  │    │
│  │  ├── UserList          ├── Tickets           │    │
│  │  ├── RouteManager      └── HelpCenter        │    │
│  │  ├── Settings                                │    │
│  │  ├── Tickets                                 │    │
│  │  └── HelpCenter                              │    │
│  │                                              │    │
│  │  API: X-Telegram-Init-Data → HMAC-SHA256     │    │
│  └──────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────┘
```

## Структура проекта

```
dem1chvpn/
├── install.sh                  установщик
├── requirements.txt            python-зависимости
├── .env.example                шаблон конфигурации
│
├── server/
│   ├── bot/                    Telegram-бот (aiogram 3)
│   │   ├── main.py             точка входа, фоновые задачи
│   │   ├── config.py           конфиг (Reality, WARP, DNS, Hysteria)
│   │   ├── database.py         SQLAlchemy-модели (SQLite)
│   │   ├── handlers/           обработчики команд
│   │   │   ├── start.py          /start, навигация, FSM clear
│   │   │   ├── users.py          CRUD юзеров (FSM-safe)
│   │   │   ├── routing.py        маршруты
│   │   │   ├── monitoring.py     статистика, speedtest, статус Hysteria
│   │   │   ├── settings.py       настройки сервера
│   │   │   ├── tickets.py        тикеты
│   │   │   ├── invite.py         инвайты
│   │   │   ├── security.py       PIN, критические операции
│   │   │   ├── help.py           инструкции
│   │   │   └── wizard.py         self-service fallback
│   │   ├── services/             бизнес-логика
│   │   │   ├── user_manager.py     CRUD + трафик + подписки
│   │   │   ├── xray_config.py      управление Xray-конфигом
│   │   │   ├── hysteria_config.py  управление Hysteria2 userpass (YAML)
│   │   │   ├── xray_api.py         gRPC Stats API
│   │   │   ├── route_manager.py    split-tunnel
│   │   │   ├── warp_manager.py     toggle WARP SOCKS5
│   │   │   ├── ticket_manager.py   тикеты
│   │   │   ├── invite_manager.py   инвайты
│   │   │   ├── adguard_api.py      AdGuard Home API
│   │   │   ├── mtproto_manager.py  MTProto Proxy
│   │   │   ├── ip_checker.py       проверка IP/доступности
│   │   │   ├── charts.py           графики (PIL)
│   │   │   ├── backup.py           бэкап и восстановление
│   │   │   └── updater.py          авто-обновление проекта
│   │   ├── keyboards/
│   │   │   └── menus.py            все меню
│   │   └── utils/
│   │       ├── auth.py             is_admin
│   │       ├── formatters.py       форматирование
│   │       ├── validators.py       валидация
│   │       ├── qr_generator.py     QR
│   │       └── telegram_helpers.py safe_edit_text и т.п.
│   │
│   ├── subscription/             FastAPI: подписки и REST API
│   │   ├── app.py                  /sub/{token} (VLESS + Hysteria2)
│   │   ├── auth.py                 HMAC-SHA256 initData
│   │   └── webapp_api.py           REST API для Mini App
│   │
│   ├── webapp/                   React Mini App (Vite + TS)
│   ├── warp/                     Cloudflare WARP setup
│   ├── adguard/                  AdGuard Home
│   ├── mtproto/                  MTProto Proxy
│   ├── hysteria/                 шаблон конфига Hysteria2
│   │   └── config_template.yaml
│   └── xray/                     шаблон конфига Xray
│       └── config_template.json
│
├── configs/                      пресеты маршрутизации
└── docs/                         документация
```

## Mini App — личный кабинет

### Пользователь

| Раздел | Что внутри |
|--------|------------|
| Кабинет | Статус аккаунта, оставшийся срок, трафик up/down, прогресс лимита |
| Подключение | URL подписки, VLESS-ссылка, deeplinks для iOS |
| Быстрый импорт | Одно нажатие — V2RayTun импортирует подписку и маршруты |
| Инструкции | Гайды для iOS, Android, Windows, macOS, роутеров |
| FAQ | Частые вопросы с аккордеоном |
| Тикеты | Создание обращений к админу |

### Админ

| Раздел | Что внутри |
|--------|------------|
| Панель | CPU, RAM, диск, общий трафик, статус Xray и Hysteria2/WARP |
| Юзеры | Список, статусы, блок, продление, лимиты, QR |
| Роуты | Добавление доменов и IP в proxy/direct/block |
| Настройки | WARP toggle, AdGuard, MTProto, бэкап, обновление |
| Тикеты | Просмотр и ответ |

### Дизайн

Dark cyber-glass: glassmorphism с `backdrop-filter: blur`, градиенты cyan→violet, анимированные прогресс-бары, мобильная оптимизация под Telegram WebApp. Шрифты: DM Sans + JetBrains Mono.

## Windows — desktop-клиент

Нативный клиент Dem1chVPN — Electron с встроенным sing-box и автонастройкой.

### Установка

1. Скачать [Dem1chVPN-Setup.exe](https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe).
2. Поставить.
3. Импортировать подписку через deeplink `dem1chvpn://sub/...` либо вставить URL руками.
4. В Dashboard выбрать протокол (VLESS или Hysteria2) и подключиться.

Подписка содержит обе ссылки — VLESS и Hysteria2. По дефолту активен Hysteria2, он сейчас стабильнее в РФ. Если на одном что-то идёт не так, второй обычно работает.

### Windows deeplinks

```
Личный кабинет → «Импорт подписки» (Windows) → dem1chvpn://sub/...
```

Подписка добавляется автоматически.

Альтернативно работает связка с **v2rayN**.

## iOS — быстрый импорт

One-tap import через V2RayTun:

```
Личный кабинет → «Импорт подписки» → v2raytun://import/...
Личный кабинет → «Импорт маршрутов» → v2raytun://import_route/...
```

Маршруты идут как base64-кодированный JSON и автоматически выставляют split-tunneling: RU — direct, остальное — proxy.

## Клиенты

Поддержка Hysteria2 есть только у клиентов на sing-box. Xray-core (на нём v2rayNG, v2rayN, чистый xray-core) умеет только VLESS.

| Платформа | Клиент | VLESS | Hysteria2 | Ссылка |
|-----------|--------|:-----:|:---------:|--------|
| iOS | V2RayTun | да | да | [App Store](https://apps.apple.com/app/v2raytun/id6476628951) |
| iOS | Streisand | да | да | [App Store](https://apps.apple.com/app/streisand/id6450534064) |
| iOS | V2Box | да | да | [App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |
| Android | NekoBox | да | да | [GitHub](https://github.com/MatsuriDayo/NekoBoxForAndroid/releases) |
| Android | Hiddify Next | да | да | [GitHub](https://github.com/hiddify/hiddify-next/releases) |
| Android | v2rayNG | да | нет | [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang) |
| Windows | Dem1chVPN | да | да | [GitHub Releases](https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe) |
| Windows | v2rayN | да | нет | [GitHub](https://github.com/2dust/v2rayN/releases) |
| macOS | V2RayTun, V2Box | да | да | [App Store](https://apps.apple.com/app/v2raytun/id6476628951) |
| Linux | Nekoray, sing-box | да | да | [Nekoray](https://github.com/MatsuriDayo/nekoray/releases) |
| Роутер | Passwall2, XKEEN | да | да (через sing-box node) | OpenWRT / Keenetic |

## Маршрутизация (split-tunneling)

В Dem1chVPN маршрутизация инвертированная: через VPN идёт только то, что без него не работает.

| Трафик | Куда | Почему |
|--------|------|--------|
| Сбер, Тинькофф, Госуслуги | DIRECT | банки часто блокируют VPN-IP |
| ВК, Яндекс, Mail.ru, Rutube | DIRECT | работают и без VPN |
| `geosite:category-ru` + `geoip:ru` | DIRECT | тысячи RU-доменов автоматически |
| YouTube, Discord, Spotify | WARP | замедления |
| ChatGPT, Gemini, NotebookLM | WARP | санкционные блокировки |
| Netflix, TikTok | WARP | нужен чистый IP |
| Twitch | DIRECT | видео хуже грузится через VPN |
| Любой новый зарубежный сайт | WARP | по дефолту, без ручной настройки |

Списки доменов вручную поддерживать не надо — всё зарубежное автоматически уходит через WARP.

## Управление

### Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |

### Админ-меню

| Кнопка | Описание |
|--------|----------|
| Пользователи | Добавить / удалить / заблокировать / продлить / лимиты |
| Маршрутизация | proxy/direct/block для доменов и IP |
| Мониторинг | Статистика, трафик, speedtest, проверка IP |
| Настройки | WARP, AdGuard, MTProto, бэкап, обновление |
| Открыть панель | Mini App (админ) |
| Помощь | Инструкции |

### Меню пользователя

| Кнопка | Описание |
|--------|----------|
| Личный кабинет | Mini App: статус, трафик, ссылки, инструкции |
| Тикет | Обращение к админу |
| Помощь | Инструкции по подключению |

Если домен не настроен, пользователь видит fallback-кнопки «Моя ссылка» и «Мой трафик» вместо Mini App.

## Безопасность

### Протокол

- Reality + XTLS-Vision — трафик визуально неотличим от обращения к `dl.google.com`.
- Hysteria2 + Salamander obfs — QUIC поверх UDP, обфусцированные пакеты, masquerade под обычный HTTPS.
- DNS-over-HTTPS — DNS-запросы шифруются (1.1.1.1 + 8.8.8.8).
- TLS-fingerprint Chrome — `fp: chrome` вместо рандомного.

### Сервер

- UFW: открыты только порты 22 (SSH), 80 (Caddy ACME), 443/tcp (Xray), 8443/tcp (Caddy), 8444/udp (Hysteria2).
- fail2ban — против брутфорса SSH.
- BBR — TCP-конджешен.
- Бот и subscription-сервис работают под отдельным пользователем `dem1chvpn`. Hysteria запускается под root, потому что иначе не прочитать сертификат Caddy. Конфиг Hysteria закрыт ACL под бота.

### API и Mini App

- HMAC-SHA256 валидация Telegram initData.
- PIN на критические операции (удаление, ключи).
- Rate limiting на API.
- FSM-state management в боте, чтобы callback'и не зависали.

## Лицензия

MIT.

---

<div align="center">

Сделано для тех, кому важна приватность.

</div>
