# Dem1chVPN — роутер (OpenWRT)

## Что нужно

- Роутер с OpenWRT 22.03+ или кастомной прошивкой с поддержкой Xray/sing-box
- Пакет `luci-app-passwall2` или `xray-core` напрямую (для Hysteria2 — `sing-box` либо `hysteria`)
- SSH-доступ к роутеру
- Данные подключения из Личного кабинета

---

## Вариант 1: Passwall2 (рекомендуется)

Plugin к LuCI с поддержкой VLESS, Reality, Hysteria2 и продвинутой маршрутизации.

### 1. Установка

```bash
ssh root@192.168.1.1

opkg update
opkg install luci-app-passwall2

reboot
```

### 2. Настройка VLESS

1. Веб-интерфейс роутера (обычно `http://192.168.1.1`).
2. Services → Passwall2.
3. Вкладка Node List, Add.
4. Параметры (берутся из конфига или `vless://` из Личного кабинета):

| Параметр | Значение |
|----------|----------|
| Type | Xray |
| Protocol | VLESS |
| Address | IP вашего VPS |
| Port | 443 |
| UUID | из бота |
| Encryption | none |
| Transport | TCP |
| TLS | Reality |
| SNI | `dl.google.com` |
| Public Key | из бота |
| Short ID | из бота |
| Fingerprint | random или chrome |

5. Сохранить, включить узел (галочка Enable).
6. На главной странице — режим:
   - GFW Mode — через VPN идут только заблокированные сайты;
   - Return to China — российский трафик напрямую, остальной — туннель;
   - Global Mode — всё через VPN.

### 3. Настройка Hysteria2

Тот же раздел Node List → Add.

| Параметр | Значение |
|----------|----------|
| Type | sing-box (или Hysteria2 в новых версиях Passwall2) |
| Protocol | Hysteria2 |
| Address | домен вашего VPS (например, `myshield.duckdns.org`) |
| Port | 8444 |
| Username | email пользователя (в формате `name@dem1chvpn`) |
| Password | hysteria_password из подписки |
| Obfs | salamander |
| Obfs Password | из подписки |
| SNI | домен VPS |
| Insecure | false (Caddy выдаёт валидный сертификат) |

Дальше выбираете в Passwall2, какой узел активный — VLESS или Hysteria2. Если на одном протоколе вдруг начались проблемы (DPI начал резать) — переключаетесь на другой одной галочкой.

### 4. Маршрутизация для России

Advanced Settings → Rules:

1. Включить Bypass LAN.
2. Добавить geosite/geoip-правила, если не включены по умолчанию:
   - `geosite:category-ru` → Direct
   - `geoip:ru` → Direct
   - `geosite:yandex` → Direct
   - всё остальное → Proxy

Так Кинопоиск, Сбер и Госуслуги на телевизорах и телефонах внутри сети будут работать напрямую.

---

## Вариант 2: Xray-core напрямую

Если не хочется городить LuCI-плагины.

### Установка

```bash
ssh root@192.168.1.1
opkg update
opkg install xray-core
```

### Конфиг

Создать `/etc/xray/config.json`:

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
          "encryption": "none",
          "flow": "xtls-rprx-vision"
        }]
      }]
    },
    "streamSettings": {
      "network": "tcp",
      "security": "reality",
      "realitySettings": {
        "serverName": "dl.google.com",
        "publicKey": "ВАШ_PUBLIC_KEY",
        "shortId": "ВАШ_SHORT_ID",
        "fingerprint": "random"
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

### Запуск и проброс

```bash
# Запуск
/usr/bin/xray run -c /etc/xray/config.json &

# Автозапуск
echo '/usr/bin/xray run -c /etc/xray/config.json &' >> /etc/rc.local

# Редирект TCP-трафика на локальный SOCKS
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 1080
iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 1080
```

Xray-core напрямую Hysteria2 не умеет. Если нужен Hysteria2 на роутере — ставьте `sing-box` (он умеет и VLESS+Reality, и Hysteria2) либо отдельный бинарь `hysteria`.

---

## Проблемы

| Симптом | Что попробовать |
|---------|-----------------|
| Passwall2 не находится | Проверить, что в `/etc/opkg/customfeeds.conf` добавлен репозиторий passwall (например, kien) |
| Нет подключения | `logread \| grep xray` (или `sing-box`) — посмотреть, что пишет ядро |
| Медленно | Отключить IPv6 — некоторые провайдеры тормозят на смешанном трафике |
| Роутер перезагружается | VLESS+TLS жрёт CPU. Нужен роутер с нормальным процессором и хотя бы 128 МБ RAM |
| Hysteria2 на роутере не идёт | Проверить, что собран `sing-box` или `hysteria` с поддержкой QUIC, провайдер не режет UDP |

Что нормально работает с этим стеком:

- ПК с x86 OpenWRT;
- Keenetic через [XKEEN](https://github.com/Jenya-developer/xkeen);
- GL.iNet (их кастомный OpenWRT + VPN Dashboard);
- Xiaomi Mi Router 3G / 4 / AX (с прошитым OpenWRT).
