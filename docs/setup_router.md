# 📡 Dem1chVPN — Подключение на роутере (OpenWRT)

## Что нужно

- **ОС:** Роутер с прошивкой **OpenWRT** 22.03+ (или кастомная с поддержкой Xray)
- Пакеты: `luci-app-passwall2` или `xray-core` напрямую
- SSH-доступ к роутеру (через PuTTY/Терминал)
- Данные подключения из **Личного кабинета** Dem1chVPN

---

## Вариант 1: Через Passwall2 (Рекомендуется)

Passwall2 — это удобный плагин для веб-интерфейса LuCI с поддержкой VLESS, Reality и продвинутой маршрутизации.

### 1. Установка Passwall2

```bash
# Подключитесь по SSH к роутеру
ssh root@192.168.1.1

# Добавьте репозиторий Passwall
opkg update
opkg install luci-app-passwall2

# Перезагрузите роутер
reboot
```

### 2. Настройка подключения

1. Откройте веб-интерфейс роутера в браузере (обычно `http://192.168.1.1`).
2. Перейдите в раздел `Services` → `Passwall2`.
3. На вкладке `Node List` нажмите `Add` (Добавить).
4. Заполните параметры сервера (возьмите их конфигурационного `.json` или из `vless://` ссылки из Личного кабинета):

| Параметр | Устанавливаемое Значение |
|----------|----------|
| Type | Xray |
| Protocol | VLESS |
| Address | `IP` вашего VPS-сервера |
| Port | `443` |
| UUID | ваш `ID` (UUID) из интерфейса |
| Encryption | `none` |
| Transport | `TCP` |
| TLS | `Reality` |
| SNI | `www.microsoft.com` |
| Public Key | ваш `Public Key` |
| Short ID | ваш `Short ID` |
| Fingerprint | `random` (или chrome) |

5. Сохраните и включите этот узел (галочка *Enable*).
6. Выберите режим работы на главной странице TCP:
   - **GFW Mode** — через VPN идут только заблокированные сайты (списки).
   - **Return to China** — аналогичная логика, китайский/русский трафик идет напрямую, остальной — туннель.
   - **Global Mode** — весь трафик жестко идет через VPN.

### 3. Настройка маршрутизации (Для России)

В Passwall2 перейдите в меню `Advanced Settings` → `Rules`:

1. Включите опцию `Bypass LAN`.
2. Добавьте вручную geosite и geoip правила, если они не включены по дефолту:
   - `geosite:category-ru` → **Direct**
   - `geoip:ru` → **Direct**
   - `geosite:yandex` → **Direct**
   - Всё остальное → **Proxy**

*(Этот шаг гарантирует, что Кинопоиск, Сбербанк и Госуслуги на ваших телевизорах и телефонах дома будут работать напрямую)*

---

## Вариант 2: Xray-core напрямую (Для гиков)

Используйте этот метод, если вы не хотите засорять роутер GUI-пакетами.

### Установка

```bash
ssh root@192.168.1.1
opkg update
opkg install xray-core
```

### Конфигурация

Отредактируйте/создайте файл `/etc/xray/config.json`:

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
        "serverName": "www.microsoft.com",
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

### Запуск и проброс портов

```bash
# Запустите сам Xray демон 
/usr/bin/xray run -c /etc/xray/config.json &

# Добавьте в автозапуск при перезагрузке
echo '/usr/bin/xray run -c /etc/xray/config.json &' >> /etc/rc.local

# Перенаправьте TCP-трафик локальной сети на Socks Xray через iptables
iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 1080
iptables -t nat -A PREROUTING -p tcp --dport 443 -j REDIRECT --to-ports 1080
```

---

## ❗️ Решение проблем

| Проблема | Решение |
|----------|---------|
| Passwall2 недоступен | Проверьте, что в `/etc/opkg/customfeeds.conf` добавлен репозиторий passwall (kien). |
| Нет подключения | Проверьте логи Xray командой: `logread \| grep xray` |
| Медленная скорость | Отключите IPv6 в настройках сети роутера. Некоторые провайдеры замедляют смешанный трафик. |
| Роутер перезагружается от нагрузки | VLESS (TLS шифрование) требует ресурсы CPU. Рекомендуются роутеры с ≥128MB RAM и нормальными процессорами. |

**Официально поддерживаемые или тестированные роутеры:**
- Полноценные ПК с x86 OpenWRT 
- Keenetic (через расширение [XKEEN](https://github.com/Jenya-developer/xkeen))
- Роутеры GL.iNet (с их дефолтным кастомным OpenWRT и установленным плагином VPN Dashboard)
- Xiaomi Mi Router серии 3G / 4 / AX (с прошитым OpenWRT)
