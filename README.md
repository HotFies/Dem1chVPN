<div align="center">

# 🛡️ Dem1chVPN

**Персональный VPN-сервер с управлением через Telegram**

VLESS + Reality + XTLS-Vision · Cloudflare WARP · DNS-over-HTTPS · Split‑Tunneling

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Xray Core](https://img.shields.io/badge/Xray--core-latest-brightgreen)](https://github.com/XTLS/Xray-core)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://python.org)

</div>

---

## 🤔 Что это?

Dem1chVPN — это готовое решение для разворачивания **собственного VPN** на VPS-сервере. Разработан специально для использования в **России**: обходит блокировки, побеждает -замедление YouTube/Discord/Telegram и даёт доступ к санкционным сервисам (ChatGPT, Gemini, NotebookLM).

Весь трафик шифруется протоколом **VLESS + Reality + XTLS-Vision** — ваш трафик неотличим от обычного HTTPS. Управление полностью через **Telegram-бот** — без веб-панелей и сложных конфигов.

Один скрипт — и через 5 минут у тебя работающий VPN с подпиской, QR-кодами и ботом для управления.

## ✨ Возможности

| | Функция | Описание |
|---|---------|----------|
| 🔒 | **VLESS + Reality + XTLS-Vision** | Неотличимый от HTTPS, не детектируется  |
| 🧬 | **Reality камуфляж** | Трафик неотличим от посещения `dl.google.com` |
| 🌐 | **DNS-over-HTTPS** | DNS-запросы шифрованы, нет DNS-утечек |
| ☁️ | **Cloudflare WARP** | Чистый IP Cloudflare для YouTube, AI, стриминга |
| 🔀 | **Split-Tunneling** | Российские сайты — напрямую, зарубежные — через WARP |
| 🤖 | **Telegram-бот** | Полное управление через inline-кнопки |
| 📡 | **Авто-подписки** | Конфиги обновляются на клиентах автоматически |
| 📱 | **Mini App** | Веб-панель прямо внутри Telegram |
| 🛡️ | **AdGuard Home** | Блокировка рекламы на уровне DNS (опционально) |
| 💬 | **MTProto Proxy** | Telegram работает даже при проблемах с VPN (опционально) |
| 👥 | **Инвайт-система** | Удобное подключение друзей и семьи |
| 📊 | **Мониторинг** | Трафик, нагрузка, проверка доступности IP |
| 🎫 | **Тикет-система** | Поддержка пользователей через Mini App |

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
│         SOCKS5 → warp-svc (localhost)         │
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
- Запустит бота и подписочный сервер

### 3. Готово

Откройте бота в Telegram → `/start` → добавьте пользователей → раздайте ссылки подписок.

## 🏗️ Архитектура

```
┌───────────────────────────────────────────────────┐
│                     VPS                            │
│                                                    │
│   :443  → Xray (VLESS + Reality + XTLS-Vision)     │
│            ├── DNS: port 53 → direct (bypass WARP)  │
│            ├── DNS: DoH (1.1.1.1 + 8.8.8.8)        │
│            ├── RU domains → direct                  │
│            └── Foreign → WARP (SOCKS5 → warp-svc)    │
│                                                    │
│   :8443 → Caddy (HTTPS, auto-cert) → FastAPI (:8080)  │
│            ├── /sub/{token}           — подписки        │
│            ├── /sub/{token}/v2raytun  — deeplinks iOS    │
│            ├── /sub/{token}/routing   — правила         │
│            └── /webapp/              — Mini App          │
│                                                    │
│   Telegram Bot (aiogram 3) ← управление             │
│   SQLite                   ← данные                  │
│   gRPC :10085              ← Xray Stats API          │
└───────────────────────────────────────────────────┘
```

## 📂 Структура проекта

```
dem1chvpn/
├── install.sh              # Установщик (всё-в-одном)
├── requirements.txt        # Python-зависимости
├── .env.example            # Шаблон конфигурации
│
├── server/
│   ├── bot/                # Telegram-бот
│   │   ├── main.py         # Точка входа + background tasks
│   │   ├── config.py       # Конфигурация (Reality, WARP, DNS)
│   │   ├── database.py     # SQLAlchemy модели
│   │   ├── handlers/       # Обработчики команд
│   │   ├── services/       # Бизнес-логика
│   │   │   ├── xray_config.py   # Управление Xray конфигом
│   │   │   ├── user_manager.py  # CRUD пользователей
│   │   │   ├── route_manager.py # Маршрутизация (split-tunnel)
│   │   │   └── warp_manager.py  # WARP SOCKS5 toggle
│   │   ├── keyboards/      # Inline-клавиатуры
│   │   └── utils/          # Утилиты
│   │
│   ├── subscription/       # FastAPI-сервер подписок
│   │   ├── app.py          # Подписки + headers (dns, routing)
│   │   ├── auth.py         # Валидация initData
│   │   └── webapp_api.py   # REST API для Mini App
│   │
│   ├── webapp/             # React Mini App (Vite + TypeScript)
│   ├── warp/               # Cloudflare WARP (SOCKS5 proxy)
│   │   └── setup.sh        # Установка warp-svc + настройка outbound
│   └── xray/               # Шаблон конфига Xray
│       └── config_template.json
│
├── configs/                # Пресеты маршрутизации
│   ├── v2rayn_routing.json    # Windows (v2rayN)
│   ├── v2rayng_routing.json   # Android (v2rayNG)
│   ├── streaming_rules.json   # Стриминг-сервисы
│   └── gaming_rules.json      # Игровые сервисы
└── docs/                   # Документация
```

## 📱 Клиенты для подключения

| Платформа | Клиент | Ссылка |
|-----------|--------|--------|
| Windows | v2rayN | [GitHub](https://github.com/2dust/v2rayN/releases) |
| Android | v2rayNG | [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang) |
| iOS | V2RayTun ⭐ | [App Store](https://apps.apple.com/app/v2raytun/id6476628951) |
| iOS | Streisand | [App Store](https://apps.apple.com/app/streisand/id6450534064) |
| iOS | V2Box | [App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |
| iOS | Shadowrocket | [App Store](https://apps.apple.com/app/shadowrocket/id932747118) |
| macOS | V2Box | [App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |
| Роутер | Passwall2 / XKEEN | OpenWRT / Keenetic |

## 🔀 Маршрутизация (Split-Tunneling)

Dem1chVPN использует **инвертированную маршрутизацию**:

| Трафик | Куда идёт | Почему |
|--------|-----------|--------|
| Сбер, Тинькофф, Госуслуги | 🟢 **DIRECT** | Банки блокируют VPN-IP |
| ВК, Яндекс, Mail.ru, Rutube | 🟢 **DIRECT** | Работают и без VPN |
| `geosite:category-ru` + `geoip:ru` | 🟢 **DIRECT** | Тысячи RU-доменов автоматически |
| YouTube, Discord, Spotify | 🔵 **WARP** | Замедляются  |
| ChatGPT, Gemini, NotebookLM | 🔵 **WARP** | Санкционные блокировки |
| Netflix, Twitch, TikTok | 🔵 **WARP** | Нужен чистый IP |
| Любой новый зарубежный сайт | 🔵 **WARP** | Автоматически, без настройки |

> Не нужно поддерживать списки доменов — **всё зарубежное автоматически идёт через WARP**.

## 🔧 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| 👥 Пользователи | Добавить / удалить / заблокировать |
| 🔀 Маршрутизация | Настройка proxy/direct доменов |
| ☁️ WARP | Включить/выключить Cloudflare WARP |
| 📊 Мониторинг | Статистика, трафик, speedtest |
| ⚙️ Настройки | Обновление, бэкап, Xray |
| 📖 Инструкции | Гайды для всех платформ |
| 🎫 Тикеты | Поддержка через Mini App |

## 🔐 Безопасность

- **Reality + XTLS-Vision** — трафик неотличим от посещения `dl.google.com`
- **DNS-over-HTTPS** — DNS-запросы зашифрованы
- **Chrome TLS Fingerprint** — `fp: chrome` вместо рандомного
- **HMAC-SHA256** валидация для Telegram Mini App
- **PIN-код** для критических операций (удаление, ключи)
- **UFW** — только порты 22, 443, 8443
- **fail2ban** — защита от брутфорса SSH
- **BBR** — оптимизация TCP-стека
- **Rate limiting** — защита API от перебора
- Сервисы работают от **отдельного пользователя** (не root)

## 📝 Лицензия

MIT — используйте как хотите.

---

<div align="center">

**Сделано для тех, кому важна приватность** 🇷🇺→🌍

</div>
