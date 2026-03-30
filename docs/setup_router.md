# 📡 XShield — Подключение на роутере (OpenWRT)

## Что нужно

- Роутер с **OpenWRT** 22.03+ (или совместимый)
- Пакеты: `xray-core` или `passwall2`
- SSH-доступ к роутеру
- Данные подключения от бота XShield

---

## Способ 1: Passwall2 (рекомендуется)

Passwall2 — это плагин для LuCI (веб-интерфейс OpenWRT) с поддержкой VLESS + Reality.

### Установка Passwall2

```bash
# SSH в роутер
ssh root@192.168.1.1

# Добавьте репозиторий Passwall
opkg update
opkg install luci-app-passwall2

# Перезагрузите роутер
reboot
```

### Настройка

1. Откройте веб-интерфейс роутера (обычно `http://192.168.1.1`)
2. Перейдите в `Services` → `Passwall2`
3. На вкладке `Node List` нажмите `Add`
4. Заполните:

| Параметр | Значение |
|----------|----------|
| Type | Xray |
| Protocol | VLESS |
| Address | IP вашего VPS |
| Port | 443 |
| UUID | ваш UUID из бота |
| Encryption | none |
| Transport | XHTTP |
| TLS | Reality |
| SNI | www.microsoft.com |
| Public Key | ваш public key из бота |
| Short ID | ваш short ID из бота |
| Fingerprint | chrome |

5. Сохраните и включите узел
6. На главной вкладке Passwall2 выберите режим:
   - **GFW Mode** — только заблокированные сайты через VPN
   - **Global Mode** — всё через VPN
   - **Return to China** — китайский трафик напрямую (аналог для РФ)

### Настройка маршрутизации для России

В Passwall2 → `Advanced Settings` → `Rules`:

1. Включите `Bypass LAN`
2. Добавьте geosite и geoip правила:
   - `geosite:category-ru` → Direct
   - `geoip:ru` → Direct
   - Всё остальное → Proxy

---

## Способ 2: Xray-core напрямую

Для продвинутых пользователей.

### Установка

```bash
ssh root@192.168.1.1
opkg update
opkg install xray-core
```

### Конфигурация

Создайте файл `/etc/xray/config.json`:

```json
{
  "inbounds": [{
    "port": 1080,
    "listen": "0.0.0.0",
    "protocol": "socks",
    "settings": { "udp": true }
  }],
  "outbounds": [{
    "tag": "proxy",
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "ВАШ_IP",
        "port": 443,
        "users": [{
          "id": "ВАШ_UUID",
          "encryption": "none"
        }]
      }]
    },
    "streamSettings": {
      "network": "xhttp",
      "security": "reality",
      "realitySettings": {
        "serverName": "www.microsoft.com",
        "publicKey": "ВАШ_PUBLIC_KEY",
        "shortId": "ВАШ_SHORT_ID",
        "fingerprint": "chrome"
      }
    }
  }, {
    "tag": "direct",
    "protocol": "freedom"
  }],
  "routing": {
    "domainStrategy": "IPIfNonMatch",
    "rules": [
      { "type": "field", "outboundTag": "direct", "domain": ["geosite:category-ru"] },
      { "type": "field", "outboundTag": "direct", "ip": ["geoip:ru", "geoip:private"] },
      { "type": "field", "outboundTag": "proxy", "port": "0-65535" }
    ]
  }
}
```

### Запуск

```bash
# Запустите Xray
/usr/bin/xray run -c /etc/xray/config.json &

# Автозапуск
echo '/usr/bin/xray run -c /etc/xray/config.json &' >> /etc/rc.local
```

### Настройка прозрачного прокси

Для перенаправления всего трафика через Xray используйте iptables:

```bash
# Перенаправление TCP
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 1080
iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 1080
```

---

## Решение проблем

| Проблема | Решение |
|----------|---------|
| Passwall2 недоступен | Убедитесь, что подключён правильный репозиторий |
| Нет подключения | Проверьте логи: `logread \| grep xray` |
| Медленная скорость | Отключите IPv6, если не используется |
| Роутер перегружается | VLESS + Reality требует мощности — рекомендуем роутеры с ≥128MB RAM |

## Поддерживаемые роутеры

- TP-Link с OpenWRT (TL-WR841, Archer C7 и др.)
- Xiaomi с OpenWRT
- GL.iNet (с предустановленным OpenWRT)
- Любой роутер с OpenWRT 22.03+
