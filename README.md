<div align="center">

# 🛡️ Dem1chVPN

**Персональный VPN-сервер с управлением через Telegram**

VLESS + Reality + TCP · Ускорение интернета · Автоматическая установка

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Xray Core](https://img.shields.io/badge/Xray--core-latest-brightgreen)](https://github.com/XTLS/Xray-core)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://python.org)

</div>

---

## 🤔 Что это?

Dem1chVPN — это готовое решение для разворачивания **собственного VPN** на VPS-сервере. Весь трафик шифруется протоколом **VLESS + Reality**, что обеспечивает стабильное и быстрое соединение. Управление полностью через **Telegram-бот** — без веб-панелей и сложных конфигов.

Один скрипт — и через 5 минут у тебя работающий VPN с подпиской, QR-кодами и ботом для управления.

## ✨ Возможности

| | Функция | Описание |
|---|---------|----------|
| 🔒 | **VLESS + Reality + TCP** | Быстрый и безопасный протокол |
| 🤖 | **Telegram-бот** | Полное управление через inline-кнопки |
| 📡 | **Подписки** | Авто-обновление конфигов на клиентах |
| 🔀 | **Умная маршрутизация** | Российские сайты — напрямую, остальное — через VPN |
| 🛡️ | **AdGuard Home** | Блокировка рекламы на уровне DNS |
| 🌐 | **WARP Double-Hop** | Двойная приватность через Cloudflare |
| 💬 | **MTProto Proxy** | Telegram работает даже при проблемах с VPN |
| 👥 | **Инвайт-система** | Удобное подключение друзей и семьи |
| 📊 | **Мониторинг** | Трафик, нагрузка, проверка доступности IP |
| 📱 | **Mini App** | Веб-панель прямо внутри Telegram |

## 📋 Требования

- **VPS**: 1 vCPU / 1 GB RAM / 10 GB SSD (минимум)
- **ОС**: Debian 12+ или Ubuntu 22.04+
- **Расположение**: за пределами РФ (Нидерланды, Германия и т.д.)
- **Стоимость**: ~400–1000 ₽/мес (например, [VDSina](https://vdsina.com))

## 🚀 Установка

### 1. Подготовка

Перед установкой нужно:
- Зарегистрировать бота через [@BotFather](https://t.me/BotFather) и получить **токен**
- Узнать свой **Telegram ID** через [@userinfobot](https://t.me/userinfobot)
- Создать субдомен на [DuckDNS](https://www.duckdns.org) (бесплатный HTTPS)

### 2. Запуск на сервере

```bash
ssh root@ваш-ip

apt update && apt install -y git
git clone https://github.com/HotFies/Dem1chVPN.git /opt/dem1chvpn
cd /opt/dem1chvpn
chmod +x install.sh
./install.sh
```

Скрипт задаст несколько вопросов (токен, PIN, DuckDNS) и сам всё настроит:
- Установит Xray-core, Python, Caddy
- Захарденит сервер (UFW, fail2ban, BBR)
- Создаст systemd-сервисы
- Настроит HTTPS через DuckDNS
- Запустит бота и подписочный сервер

### 3. Готово

Откройте бота в Telegram → `/start` → добавьте пользователей → раздайте ссылки.

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────┐
│                   VPS                        │
│                                              │
│   :443  → Xray (VLESS + Reality + TCP)       │
│                                              │
│   :8443 → Caddy (HTTPS) → FastAPI (:8080)    │
│            ├── /sub/{token}  — подписки       │
│            └── /webapp/      — Mini App       │
│                                              │
│   Telegram Bot (aiogram 3) ← управление      │
│   SQLite                   ← данные           │
│   gRPC :10085              ← Xray Stats API   │
└─────────────────────────────────────────────┘
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
│   │   ├── main.py         # Точка входа
│   │   ├── config.py       # Конфигурация
│   │   ├── database.py     # SQLAlchemy модели
│   │   ├── handlers/       # Обработчики команд
│   │   ├── services/       # Бизнес-логика
│   │   ├── keyboards/      # Inline-клавиатуры
│   │   └── utils/          # Утилиты
│   │
│   ├── subscription/       # FastAPI-сервер подписок
│   │   ├── app.py          # Эндпоинты подписок
│   │   ├── auth.py         # Валидация initData
│   │   └── webapp_api.py   # REST API для Mini App
│   │
│   ├── webapp/             # React Mini App (Vite + TS)
│   └── xray/               # Шаблон конфига Xray
│
├── configs/                # Пресеты маршрутизации
└── docs/                   # Документация
```

## 📱 Клиенты для подключения

| Платформа | Клиент | Ссылка |
|-----------|--------|--------|
| Windows | v2rayN | [GitHub](https://github.com/2dust/v2rayN/releases) |
| Android | v2rayNG | [Google Play](https://play.google.com/store/apps/details?id=com.v2ray.ang) |
| iOS | Streisand ⭐ | [App Store](https://apps.apple.com/app/streisand/id6450534064) |
| iOS | V2Box | [App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |
| iOS | Shadowrocket | [App Store](https://apps.apple.com/app/shadowrocket/id932747118) |
| macOS | V2Box | [App Store](https://apps.apple.com/app/v2box-v2ray-client/id6446814690) |
| Роутер | Passwall2 / XKEEN | OpenWRT / Keenetic |

> ⚠️ **V2RayTun не рекомендуется** — не поддерживает `xtls-rprx-vision` flow, имеет проблемы с маршрутизацией и стабильностью.

## 🔧 Команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Главное меню |
| 👥 Пользователи | Добавить / удалить / заблокировать |
| 🔀 Маршрутизация | Настройка proxy/direct доменов |
| 📊 Мониторинг | Статистика, трафик, speedtest |
| ⚙️ Настройки | Обновление, бэкап, Xray |
| 📖 Инструкции | Гайды для всех платформ |

## 🔐 Безопасность

- **HMAC-SHA256** валидация для Telegram Mini App
- **PIN-код** для критических операций (удаление, ключи)
- **UFW** — только порты 22, 443, 8443
- **fail2ban** — защита от брутфорса SSH
- **BBR** — оптимизация TCP
- **Rate limiting** — защита API от перебора
- Сервисы работают от **отдельного пользователя** (не root)

## 📝 Лицензия

MIT — используйте как хотите.

---

<div align="center">

**Сделано для тех, кому важна приватность** 🇷🇺→🌍

</div>
