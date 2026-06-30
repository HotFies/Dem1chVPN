#!/usr/bin/env bash
# Обновляет /etc/hysteria/cert.{crt,key} симлинки на актуальный cert Caddy.
# Запускается systemd при старте dem1chvpn-hysteria — позволяет менять домен без правки конфига Hysteria.
set -e

ENV_FILE=/opt/dem1chvpn/.env

if [ ! -f "$ENV_FILE" ]; then
    echo "Нет $ENV_FILE — нечего делать" >&2
    exit 0
fi

# shellcheck disable=SC1090
source "$ENV_FILE"

if [ -z "${SUB_DOMAIN:-}" ]; then
    echo "SUB_DOMAIN не задан в $ENV_FILE" >&2
    exit 1
fi

CADDY_STORE=/var/lib/caddy/.local/share/caddy/certificates
# Ищем cert от prod LE/ZeroSSL, не staging
CERT=$(find "$CADDY_STORE" -name "${SUB_DOMAIN}.crt" -not -path "*staging*" 2>/dev/null | head -1)
KEY=$(find "$CADDY_STORE"  -name "${SUB_DOMAIN}.key" -not -path "*staging*" 2>/dev/null | head -1)

if [ -z "$CERT" ] || [ -z "$KEY" ]; then
    echo "Серт для ${SUB_DOMAIN} ещё не выпущен Caddy — пропускаю обновление симлинков" >&2
    echo "Hysteria крэш-лупит без серта; dem1chvpn-hysteria-cert.path поднимет её, как только Caddy выпустит серт" >&2
    exit 0
fi

mkdir -p /etc/hysteria
ln -sf "$CERT" /etc/hysteria/cert.crt
ln -sf "$KEY"  /etc/hysteria/cert.key

# Группа caddy уже владеет сертификатами; права на симлинки роли не играют — Hysteria идёт по симлинку
echo "OK: /etc/hysteria/cert.{crt,key} → ${SUB_DOMAIN}"
