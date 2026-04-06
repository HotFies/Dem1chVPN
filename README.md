<div align="center">

# 🛡️ Dem1chVPN

**Персональный VPN-сервер с управлением через Telegram**

VLESS + Reality + XTLS-Vision · Cloudflare WARP · DNS-over-HTTPS · Split‑Tunneling · Mini App

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Xray Core](https://img.shields.io/badge/Xray--core-latest-brightgreen)](https://github.com/XTLS/Xray-core)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://python.org)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)

</div>

---

## 🤔 Что это?

Dem1chVPN — это готовое решение для разворачивания **собственного VPN** на VPS-сервере. Разработан специально для использования в **России**: обходит блокировки, побеждает замедление YouTube/Discord/Telegram и даёт доступ к санкционным сервисам (ChatGPT, Gemini, NotebookLM).

Весь трафик шифруется протоколом **VLESS + Reality + XTLS-Vision** — ваш трафик неотличим от обычного HTTPS. Управление полностью через **Telegram-бот** и **Mini App** — без веб-панелей и сложных конфигов.

Один скрипт — и через 5 минут у тебя работающий VPN с подпиской, личным кабинетом и ботом для управления.

## ✨ Возможности

### Ядро VPN

| | Функция | Описание |
|---|---------|----------|
| 🔒 | **VLESS + Reality + XTLS-Vision** | Неотличимый от HTTPS, не детектируется |
| 🧬 | **Reality камуфляж** | Трафик неотличим от посещения `dl.google.com` |
| 🌐 | **DNS-over-HTTPS** | DNS-запросы шифрованы, нет DNS-утечек |
| ☁️ | **Cloudflare WARP** | Чистый IP Cloudflare для YouTube, AI, стриминга |
| 🔀 | **Split-Tunneling** | Российские сайты — напрямую, зарубежные — через WARP |

### Управление и UX

| | Функция | Описание |
|---|---------|----------|
| 🤖 | **Telegram-бот** | Полное управление через inline-кнопки |
| 📱 | **Mini App** | Premium веб-панель прямо внутри Telegram |
| 🏠 | **Личный кабинет** | Статус, трафик, ссылки, инструкции — в одном месте |
| 📡 | **Авто-подписки** | Конфиги обновляются на клиентах автоматически |
| 📲 | **iOS Deeplinks** | Импорт подписки и маршрутов одним нажатием (V2RayTun) |
| 🖥️ | **Windows Deeplinks** | Импорт подписки одним нажатием (Dem1chVPN) |
| 💻 | **Windows Desktop Client** | Нативный клиент Dem1chVPN с автоимпортом подписки |
| 🎫 | **Тикет-система** | Поддержка пользователей через Mini App |
| 👥 | **Инвайт-система** | Удобное подключение друзей и семьи |
| 📊 | **Мониторинг** | Трафик, нагрузка, проверка доступности IP |

### Дополнительные сервисы

| | Функция | Описание |
|---|---------|----------|
| 🛡️ | **AdGuard Home** | Блокировка рекламы на уровне DNS (опционально) |
| 💬 | **MTProto Proxy** | Telegram работает даже при проблемах с VPN (опционально) |

## 🚀 Как это работает?

```
Пользователь (Россия)
    │
    │ VLESS + Reality + XTLS-Vision (порт 443)
    │ TLS Fingerprint: Chrome  ← неотличим от обычного браузера
    │ Reality камуфляж         ← трафик выглядит как dl.google.com
    │ DNS-over-HTTPS           ← нет DNS-утечек
    │
    ▼
┌─────────────── VPS (Европа) ───────────────┐
│                                             │
│   Xray-core                                 │
│     ├── Российские сайты → DIRECT           │
│     │   (geosite:ru + банки + ВК + Яндекс)  │
│     │                                       │
│     └── Всё остальное → Cloudflare WARP     │
│         (YouTube, Discord, AI, стриминг)    │
│         SOCKS5 → warp-svc (localhost)       │
│                                             │
│   ▼ Чистый IP Cloudflare                    │
│   YouTube ✅ Discord ✅ ChatGPT ✅           │
│   Gemini ✅ Spotify ✅ WhatsApp ✅           │
└─────────────────────────────────────────────┘
```

### Почему это быстрее обычного VPN?

| Проблема обычных VPN | Решение в Dem1chVPN |
|---|---|
| Весь трафик идёт через VPN — Сбер тормозит | **Split-Tunneling**: RU-сайты идут напрямую |
| YouTube замедляется по SNI | **Reality**: трафик выглядит как dl.google.com |
| DNS-запросы видны провайдеру | **DoH**: DNS зашифрован через HTTPS |
| VPS IP заблокирован сервисами | **WARP SOCKS5**: чистый IP Cloudflare |
| `fp: random` = экзотический fingerprint | **`fp: chrome`**: самый популярный TLS |

## 📋 Требования

- **VPS**: 1 vCPU / 1 GB RAM / 10 GB SSD (минимум)
- **ОС**: Debian 12+ или Ubuntu 22.04+
- **Расположение**: за пределами РФ (Нидерланды, Германия и т.д.)
- **Стоимость**: ~400–1500 ₽/мес (например, [VDSina](https://vdsina.com))

## 🚀 Установка

### 1. Подготовка

Перед установкой нужно:
- Зарегистрировать бота через [@BotFather](https://t.me/BotFather) и получить **токен**
- Узнать свой **Telegram ID** через [@userinfobot](https://t.me/userinfobot)

### 2. Запуск на сервере

```bash
ssh root@ваш-ip

apt update && apt install -y git
git clone https://github.com/HotFies/Dem1chVPN.git /opt/dem1chvpn
cd /opt/dem1chvpn
chmod +x install.sh
./install.sh
```

Скрипт задаст несколько вопросов (токен, PIN) и сам всё настроит:
- Установит Xray-core, Python, Caddy, Node.js
- Захарденит сервер (UFW, fail2ban, BBR, sysctl)
- Настроит VLESS + Reality с `dl.google.com` камуфляжем
- Установит Cloudflare WARP (SOCKS5 proxy, автоматически)
- Настроит DNS-over-HTTPS
- Создаст systemd-сервисы
- Автоматически определит hostname VPS для HTTPS-подписки
- Настроит Caddy с автоматическим SSL-сертификатом (HTTP-01)
- Соберёт React Mini App (Vite + TypeScript)
- Запустит бота и подписочный сервер

### 3. Готово

Откройте бота в Telegram → `/start` → добавьте пользователей → раздайте ссылки подписок.

Пользователи получают кнопку **📱 Личный кабинет** в боте — там всё: статус, трафик, ссылки, инструкции, iOS deeplinks.

## 🏗️ Архитектура

```
┌──────────────────────────────────────────────────────┐
│                         VPS                          │
│                                                      │
│   :443  → Xray (VLESS + Reality + XTLS-Vision)       │
│            ├── DNS: port 53 → direct (bypass WARP)   │
│            ├── DNS: DoH (1.1.1.1 + 8.8.8.8)         │
│            ├── RU domains → direct                   │
│            └── Foreign → WARP (SOCKS5 → warp-svc)   │
│                                                      │
│   :8443 → Caddy (HTTPS, auto-cert) → FastAPI (:8080)│
│            ├── /sub/{token}            — подписки    │
│            ├── /sub/{token}/v2raytun   — deeplinks   │
│            ├── /sub/{token}/routing    — правила     │
│            ├── /api/my/account         — кабинет     │
│            ├── /api/my/links           — ссылки      │
│            ├── /api/users/*            — упр-ние     │
│            ├── /api/tickets/*          — тикеты      │
│            ├── /api/routes/*           — маршруты    │
│            ├── /api/server/status      — мониторинг  │
│            └── /webapp/                — Mini App    │
│                                                      │
│   Telegram Bot (aiogram 3) ← управление              │
│   SQLite                   ← данные                  │
│   gRPC :10085              ← Xray Stats API          │
└──────────────────────────────────────────────────────┘
```

### Mini App — Архитектура

```
┌── Telegram Bot ──────────────────────────────────────┐
│                                                      │
│  Админ                      Пользователь             │
│  ┌──────────────┐           ┌──────────────────┐     │
│  │ 📱 Открыть   │           │ 📱 Личный        │     │
│  │    панель     │           │    кабинет       │     │
│  └──────┬───────┘           └───────┬──────────┘     │
│         │                           │                │
│         ▼                           ▼                │
│  ┌─── Mini App (React + Vite) ──────────────────┐    │
│  │                                               │   │
│  │  Admin Pages:          User Pages:            │   │
│  │  ├── Dashboard         ├── MyAccount (home)   │   │
│  │  ├── UserList          ├── Tickets            │   │
│  │  ├── RouteManager      └── HelpCenter         │   │
│  │  ├── Settings                                 │   │
│  │  ├── Tickets                                  │   │
│  │  └── HelpCenter                               │   │
│  │                                               │   │
│  │  API: X-Telegram-Init-Data → HMAC-SHA256      │   │
│  └───────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## 📂 Структура проекта

```
dem1chvpn/
├── install.sh                  # Установщик (всё-в-одном)
├── requirements.txt            # Python-зависимости
├── .env.example                # Шаблон конфигурации
│
├── server/
│   ├── bot/                    # Telegram-бот (aiogram 3)
│   │   ├── main.py             # Точка входа + background tasks
│   │   ├── config.py           # Конфигурация (Reality, WARP, DNS)
│   │   ├── database.py         # SQLAlchemy модели (SQLite)
│   │   ├── handlers/           # Обработчики команд
│   │   │   ├── start.py        #   /start + навигация + FSM clear
│   │   │   ├── users.py        #   CRUD пользователей (FSM-safe)
│   │   │   ├── routing.py      #   Управление маршрутами
│   │   │   ├── monitoring.py   #   Статистика + speedtest
│   │   │   ├── settings.py     #   Настройки сервера
│   │   │   ├── tickets.py      #   Система тикетов
│   │   │   ├── invite.py       #   Инвайт-ссылки
│   │   │   ├── security.py     #   PIN-код + критич. операции
│   │   │   ├── help.py         #   Инструкции
│   │   │   └── wizard.py       #   Self-service (fallback)
│   │   ├── services/           # Бизнес-логика
│   │   │   ├── user_manager.py    # CRUD + трафик + подписки
│   │   │   ├── xray_config.py     # Управление Xray конфигом
│   │   │   ├── xray_api.py        # gRPC Stats API
│   │   │   ├── route_manager.py   # Маршрутизация (split-tunnel)
│   │   │   ├── warp_manager.py    # WARP SOCKS5 toggle
│   │   │   ├── ticket_manager.py  # Тикет-система
│   │   │   ├── invite_manager.py  # Инвайт-логика
│   │   │   ├── adguard_api.py     # AdGuard Home API
│   │   │   ├── mtproto_manager.py # MTProto Proxy
│   │   │   ├── ip_checker.py      # Проверка IP / доступности
│   │   │   ├── charts.py          # Генерация графиков (PIL)
│   │   │   ├── backup.py          # Бэкап / восстановление
│   │   │   └── updater.py         # Авто-обновление проекта
│   │   ├── keyboards/          # Inline-клавиатуры
│   │   │   └── menus.py        #   Все меню (admin + user + MiniApp)
│   │   └── utils/              # Утилиты
│   │       ├── auth.py            # Проверка is_admin
│   │       ├── formatters.py      # Форматирование трафика/дат
│   │       ├── validators.py      # Валидация имён/лимитов
│   │       ├── qr_generator.py    # QR-коды для подписок
│   │       └── telegram_helpers.py # safe_edit_text и т.п.
│   │
│   ├── subscription/           # FastAPI-сервер подписок + API
│   │   ├── app.py              #   Подписки + headers (dns, routing, deeplinks)
│   │   ├── auth.py             #   HMAC-SHA256 валидация initData
│   │   └── webapp_api.py       #   REST API для Mini App
│   │                           #     /api/my/account — личный кабинет
│   │                           #     /api/my/links   — ссылки пользователя
│   │                           #     /api/users/*    — управление юзерами
│   │                           #     /api/routes/*   — маршрутизация
│   │                           #     /api/tickets/*  — тикеты
│   │                           #     /api/server/*   — мониторинг
│   │
│   ├── webapp/                 # React Mini App (Vite + TypeScript)
│   │   └── src/
│   │       ├── App.tsx            # Роутер (admin/user pages)
│   │       ├── api/client.ts      # API-клиент + типы
│   │       ├── components/
│   │       │   ├── MyAccount.tsx      # 🏠 Личный кабинет пользователя
│   │       │   ├── Dashboard.tsx      # 📊 Панель администратора
│   │       │   ├── UserList.tsx       # 👥 Управление пользователями
│   │       │   ├── RouteManager.tsx   # 🔀 Маршрутизация
│   │       │   ├── Settings.tsx       # ⚙️ Настройки сервера
│   │       │   ├── Tickets.tsx        # 🎫 Тикет-система
│   │       │   ├── TrafficChart.tsx   # 📈 Графики трафика
│   │       │   └── HelpCenter.tsx     # 📖 Помощь и инструкции
│   │       └── styles/
│   │           └── index.css          # Dark Cyber-Glass Design System
│   │
│   ├── warp/                   # Cloudflare WARP (SOCKS5 proxy)
│   │   └── setup.sh            #   Установка warp-svc + настройка outbound
│   ├── adguard/                # AdGuard Home (DNS-блокировка рекламы)
│   ├── mtproto/                # MTProto Proxy для Telegram
│   └── xray/                   # Шаблон конфига Xray
│       └── config_template.json
│
├── configs/                    # Пресеты маршрутизации
│   ├── v2rayn_routing.json     #   Windows (v2rayN)
│   ├── v2rayng_routing.json    #   Android (v2rayNG)
│   ├── streaming_rules.json    #   Стриминг-сервисы
│   └── gaming_rules.json       #   Игровые сервисы
└── docs/                       # Документация
```

## 📱 Mini App — Личный кабинет

Пользователи получают доступ к **Personal Cabinet** прямо внутри Telegram:

### Для пользователей

| Раздел | Функции |
|--------|---------|
| **🏠 Кабинет** | Статус аккаунта, оставшийся срок, трафик (upload/download), прогресс-бар лимита |
| **🔗 Подключение** | URL подписки, VLESS-ссылка, кнопки deeplink для iOS |
| **📲 Быстрый импорт** | Одно нажатие → V2RayTun импортирует подписку и маршруты |
| **📖 Инструкции** | Пошаговые гайды для iOS, Android, Windows, macOS, роутеров |
| **❓ FAQ** | Частые вопросы с интерактивным аккордеоном |
| **🎫 Тикеты** | Создание обращений к админу |

### Для администратора

| Раздел | Функции |
|--------|---------|
| **📊 Панель** | CPU, RAM, Disk, общий трафик, статус Xray/WARP |
| **👥 Юзеры** | Список, статусы, блокировка, продление, лимиты, QR |
| **🔀 Роуты** | Добавление доменов/IP в proxy/direct/block |
| **⚙️ Настройки** | WARP toggle, AdGuard, MTProto, бэкап/обновление |
| **🎫 Тикеты** | Просмотр и ответ на обращения |

### Дизайн

Mini App использует **Dark Cyber-Glass Design System**:
- Glassmorphism с `backdrop-filter: blur`
- Градиентные accent-цвета (cyan → violet)
- Animated progress bars с shimmer-эффектом
- Micro-анимации для переходов и hover-состояний
- Мобильная оптимизация для Telegram WebApp
- Типографика: DM Sans + JetBrains Mono

## 💻 Windows — Desktop Client

Для пользователей Windows доступен **нативный клиент Dem1chVPN** — Electron-приложение с встроенным Xray-core и автоматической настройкой:

### Установка

1. Скачайте инсталлятор: [📥 Dem1chVPN-Setup.exe](https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe)
2. Запустите установщик
3. Импортируйте подписку через deeplink `dem1chvpn://sub/...` или вставьте URL вручную
4. Подключитесь одним нажатием

### Windows Deeplinks

```
📱 Личный кабинет → «Импорт подписки» (Windows) → dem1chvpn://sub/...
```

Подписка автоматически импортируется в приложение.

> Также поддерживается подключение через **v2rayN** (альтернативный клиент).

## 📲 iOS — Быстрый импорт

Для пользователей iOS реализован **one-tap import** через deeplinks V2RayTun:

```
📱 Личный кабинет → «Импорт подписки» → v2raytun://import/...
📱 Личный кабинет → «Импорт маршрутов» → v2raytun://import_route/...
```

Маршруты передаются в формате base64-кодированного JSON и автоматически применяют split-tunneling правила (RU — direct, foreign — proxy).

## 📱 Клиенты для подключения

| Платформа | Клиент | Ссылка |
|-----------|--------|--------|
| iOS | V2RayTun ⭐ | [App Store](https://apps.apple.com/app/v2raytun/id6476628951) |
| iOS | Streisand | [App Store](https://apps.apple.com/app/streisand/id6450534064) |
| iOS | V2Box | [App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |
| Android | v2rayNG | [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang) |
| Windows | Dem1chVPN ⭐ | [GitHub Releases](https://github.com/HotFies/Dem1chVPN/releases/download/demichvpn-win-v.1.0.0/Dem1chVPN-1.0.0-Setup.exe) |
| Windows | v2rayN | [GitHub](https://github.com/2dust/v2rayN/releases) |
| macOS | V2RayTun / V2Box | [App Store](https://apps.apple.com/app/v2raytun/id6476628951) |
| Роутер | Passwall2 / XKEEN | OpenWRT / Keenetic |

## 🔀 Маршрутизация (Split-Tunneling)

Dem1chVPN использует **инвертированную маршрутизацию**:

| Трафик | Куда идёт | Почему |
|--------|-----------|--------|
| Сбер, Тинькофф, Госуслуги | 🟢 **DIRECT** | Банки блокируют VPN-IP |
| ВК, Яндекс, Mail.ru, Rutube | 🟢 **DIRECT** | Работают и без VPN |
| `geosite:category-ru` + `geoip:ru` | 🟢 **DIRECT** | Тысячи RU-доменов автоматически |
| YouTube, Discord, Spotify | 🔵 **WARP** | Замедляются |
| ChatGPT, Gemini, NotebookLM | 🔵 **WARP** | Санкционные блокировки |
| Netflix, Twitch, TikTok | 🔵 **WARP** | Нужен чистый IP |
| Любой новый зарубежный сайт | 🔵 **WARP** | Автоматически, без настройки |

> Не нужно поддерживать списки доменов — **всё зарубежное автоматически идёт через WARP**.

## 🔧 Управление

### Бот — Команды

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |

### Бот — Админ-меню

| Кнопка | Описание |
|--------|----------|
| 👥 Пользователи | Добавить / удалить / заблокировать / продлить / лимиты |
| 🔀 Маршрутизация | Настройка proxy/direct/block доменов и IP |
| 📊 Мониторинг | Статистика, трафик, speedtest, проверка IP |
| ⚙️ Настройки | WARP, AdGuard, MTProto, бэкап, обновление |
| 📱 Открыть панель | Mini App (веб-панель администратора) |
| 📖 Помощь | Инструкции для всех платформ |

### Бот — Меню пользователя

| Кнопка | Описание |
|--------|----------|
| 📱 Личный кабинет | Mini App — статус, трафик, ссылки, инструкции |
| 🎫 Тикет | Создать обращение к администратору |
| 📖 Помощь | Инструкции по подключению |

> При отсутствии домена (fallback) — пользователи видят кнопки «🔗 Моя ссылка» и «📊 Мой трафик» вместо Mini App.

## 🔐 Безопасность

### Протокол
- **Reality + XTLS-Vision** — трафик неотличим от посещения `dl.google.com`
- **DNS-over-HTTPS** — DNS-запросы зашифрованы (1.1.1.1 + 8.8.8.8)
- **Chrome TLS Fingerprint** — `fp: chrome` вместо рандомного

### Сервер
- **UFW** — только порты 22, 443, 8443
- **fail2ban** — защита от брутфорса SSH
- **BBR** — оптимизация TCP-стека
- Сервисы работают от **отдельного пользователя** (не root)

### API и Mini App
- **HMAC-SHA256** валидация Telegram initData
- **PIN-код** для критических операций (удаление, ключи)
- **Rate limiting** — защита API от перебора
- **FSM state management** — предотвращение зависания callback'ов бота

## 📝 Лицензия

MIT — используйте как хотите.

---

<div align="center">

**Сделано для тех, кому важна приватность** 🇷🇺→🌍

</div>
