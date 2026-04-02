#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  ☁️ Cloudflare WARP — Setup for Dem1chVPN
#  Generates WireGuard keys via wgcf and configures
#  Xray native WireGuard outbound (no SOCKS5 overhead)
# ═══════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

WARP_DATA_DIR="/opt/dem1chvpn/data"
WARP_KEYS_FILE="${WARP_DATA_DIR}/warp_wireguard.json"
XRAY_CONFIG="/usr/local/etc/xray/config.json"

echo ""
echo -e "${GREEN}☁️  Cloudflare WARP — WireGuard Setup${NC}"
echo ""

# ──── Шаг 1: Определение ОС и архитектуры ────

if [ ! -f /etc/os-release ]; then
    log_error "Не удалось определить ОС"
    exit 1
fi
source /etc/os-release

ARCH=$(uname -m)
case "$ARCH" in
    x86_64|amd64) WGCF_ARCH="amd64" ;;
    aarch64|arm64) WGCF_ARCH="arm64" ;;
    armv7*|armhf)  WGCF_ARCH="armv7" ;;
    *)
        log_error "Неподдерживаемая архитектура: $ARCH"
        exit 1
        ;;
esac

log_info "ОС: $PRETTY_NAME, архитектура: $ARCH"

# ──── Шаг 2: Установка wgcf ────

if ! command -v wgcf &> /dev/null; then
    log_info "Устанавливаю wgcf..."

    WGCF_VERSION=$(curl -s https://api.github.com/repos/ViRb3/wgcf/releases/latest 2>/dev/null | grep '"tag_name"' | sed 's/.*"v\([^"]*\)".*/\1/' || echo "2.2.22")

    WGCF_URL="https://github.com/ViRb3/wgcf/releases/download/v${WGCF_VERSION}/wgcf_${WGCF_VERSION}_linux_${WGCF_ARCH}"

    curl -Lo /usr/local/bin/wgcf "$WGCF_URL" 2>/dev/null || {
        # Fallback: try without version
        curl -Lo /usr/local/bin/wgcf "https://github.com/ViRb3/wgcf/releases/latest/download/wgcf_${WGCF_VERSION}_linux_${WGCF_ARCH}" 2>/dev/null || {
            log_error "Не удалось скачать wgcf"
            exit 1
        }
    }
    chmod +x /usr/local/bin/wgcf
    log_info "wgcf установлен: $(wgcf --version 2>/dev/null || echo 'OK')"
else
    log_info "wgcf уже установлен: $(wgcf --version 2>/dev/null || echo 'OK')"
fi

# ──── Шаг 3: Генерация WireGuard ключей через WARP ────

mkdir -p "$WARP_DATA_DIR"
cd "$WARP_DATA_DIR"

if [ ! -f "$WARP_KEYS_FILE" ]; then
    log_info "Регистрирую WARP аккаунт и генерирую ключи..."

    # Регистрация аккаунта
    wgcf register --accept-tos 2>/dev/null || {
        log_error "Не удалось зарегистрировать WARP аккаунт"
        exit 1
    }
    log_info "WARP аккаунт зарегистрирован"

    # Генерация WireGuard профиля
    wgcf generate 2>/dev/null || {
        log_error "Не удалось сгенерировать WireGuard профиль"
        exit 1
    }

    if [ ! -f "${WARP_DATA_DIR}/wgcf-profile.conf" ]; then
        log_error "Файл wgcf-profile.conf не создан"
        exit 1
    fi

    # Парсинг WireGuard конфига и сохранение в JSON для Xray
    python3 << 'PYTHON'
import json, re

with open("/opt/dem1chvpn/data/wgcf-profile.conf") as f:
    conf = f.read()

# Parse WireGuard config
private_key = re.search(r"PrivateKey\s*=\s*(.+)", conf)
address_line = re.search(r"Address\s*=\s*(.+)", conf)
peer_public = re.search(r"PublicKey\s*=\s*(.+)", conf)
endpoint = re.search(r"Endpoint\s*=\s*(.+)", conf)

if not all([private_key, address_line, peer_public]):
    print("ERROR: Failed to parse wgcf-profile.conf")
    exit(1)

# Parse addresses (may contain both v4 and v6)
addresses = [a.strip() for a in address_line.group(1).split(",")]
address_v4 = next((a for a in addresses if "." in a), "172.16.0.2/32")
address_v6 = next((a for a in addresses if ":" in a), "fd01:db8:1111::2/128")

keys = {
    "private_key": private_key.group(1).strip(),
    "address_v4": address_v4,
    "address_v6": address_v6,
    "peer_public_key": peer_public.group(1).strip(),
    "endpoint": endpoint.group(1).strip() if endpoint else "engage.cloudflareclient.com:2408",
    "reserved": [0, 0, 0],
}

with open("/opt/dem1chvpn/data/warp_wireguard.json", "w") as f:
    json.dump(keys, f, indent=2)

print(f"Private key: {keys['private_key'][:10]}...")
print(f"Address v4: {keys['address_v4']}")
print(f"Address v6: {keys['address_v6']}")
print(f"Peer: {keys['peer_public_key'][:20]}...")
print(f"Endpoint: {keys['endpoint']}")
PYTHON

    if [ $? -ne 0 ]; then
        log_error "Не удалось распарсить WireGuard конфиг"
        exit 1
    fi

    log_info "WireGuard ключи сохранены в ${WARP_KEYS_FILE}"
else
    log_info "WireGuard ключи уже существуют: ${WARP_KEYS_FILE}"
fi

# ──── Шаг 4: Обновление Xray конфига (WireGuard outbound) ────

if [ -f "$XRAY_CONFIG" ]; then
    python3 << 'PYTHON'
import json

config_path = "/usr/local/etc/xray/config.json"
keys_path = "/opt/dem1chvpn/data/warp_wireguard.json"

with open(config_path) as f:
    cfg = json.load(f)

with open(keys_path) as f:
    keys = json.load(f)

# Remove old WARP outbound (SOCKS5 or WireGuard)
cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

# Add native WireGuard outbound
warp_outbound = {
    "tag": "warp",
    "protocol": "wireguard",
    "settings": {
        "secretKey": keys["private_key"],
        "address": [keys["address_v4"], keys["address_v6"]],
        "peers": [
            {
                "publicKey": keys["peer_public_key"],
                "endpoint": keys.get("endpoint", "engage.cloudflareclient.com:2408"),
            }
        ],
        "mtu": 1280,
        "reserved": keys.get("reserved", [0, 0, 0]),
    },
}
cfg["outbounds"].append(warp_outbound)

# Inverted routing: Russian sites → direct, ALL foreign traffic → WARP
# This way we don't need to maintain a list of blocked/throttled domains —
# any new service (AI, streaming, etc.) automatically gets a clean Cloudflare IP.
rules = cfg.get("routing", {}).get("rules", [])

# Remove any old WARP domain-based rules
rules = [r for r in rules if r.get("outboundTag") != "warp"]

# Add catch-all WARP rule at the END (after all direct/blocked rules)
# This ensures: API → api, RU domains → direct, geoip:ru → direct, QUIC → blocked, everything else → WARP
warp_catchall = {
    "type": "field",
    "outboundTag": "warp",
    "network": "tcp,udp",
}

# Ensure QUIC blocking rule exists BEFORE the catch-all (force TCP fallback)
has_quic_block = any(
    r.get("network") == "udp" and r.get("port") == "443"
    for r in rules
)
if not has_quic_block:
    quic_rule = {
        "type": "field",
        "outboundTag": "blocked",
        "network": "udp",
        "port": "443",
    }
    rules.append(quic_rule)

# Catch-all WARP goes last
rules.append(warp_catchall)

cfg["routing"]["rules"] = rules

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)

print("✅ Xray config updated:")
print("   WARP outbound: WireGuard (native, no SOCKS5 overhead)")
print("   Routing: RU sites → direct, ALL foreign → WARP (clean Cloudflare IP)")
print("   QUIC (UDP:443): blocked → forces TCP fallback")
PYTHON

    systemctl restart xray
    log_info "Xray перезапущен с WireGuard WARP"
fi

# ──── Шаг 5: Обновление .env ────

ENV_FILE="/opt/dem1chvpn/.env"
if [ -f "$ENV_FILE" ]; then
    sed -i 's/WARP_ENABLED=false/WARP_ENABLED=true/' "$ENV_FILE"
    log_info "WARP_ENABLED=true в .env"
fi

# ──── Шаг 6: Опционально — остановить WARP SOCKS5 сервис ────

# Если был установлен warp-svc (SOCKS5 proxy mode), он больше не нужен
# Xray теперь использует WireGuard напрямую через сгенерированные ключи
if command -v warp-cli &> /dev/null; then
    WARP_STATUS=$(warp-cli status 2>/dev/null || echo "")
    if echo "$WARP_STATUS" | grep -qi "connected"; then
        log_info "Отключаю старый WARP SOCKS5 proxy (больше не нужен)..."
        warp-cli disconnect 2>/dev/null || true
    fi
    # Не удаляем warp-svc — может пригодиться для диагностики
    log_info "warp-svc оставлен для диагностики (можно удалить: apt remove cloudflare-warp)"
fi

# ──── Шаг 7: Тест WireGuard через Xray ────

log_info "Тестирую WARP через Xray WireGuard outbound..."
sleep 3

# Проверяем что Xray запустился без ошибок
if systemctl is-active --quiet xray; then
    log_info "Xray запущен с WireGuard outbound ✅"
else
    log_error "Xray не запустился! Проверьте: journalctl -u xray --no-pager -n 20"
    exit 1
fi

# ──── Итог ────

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  ☁️  WARP WireGuard установлен!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "  Outbound:     WireGuard (native, нет SOCKS5 overhead)"
echo -e "  Ключи:        ${WARP_KEYS_FILE}"
echo -e "  Маршруты:     YouTube CDN, TikTok, Discord, Spotify, WhatsApp → WARP"
echo ""
echo -e "  ${YELLOW}Преимущества WireGuard vs SOCKS5:${NC}"
echo -e "    • Нет TCP-over-TCP overhead"
echo -e "    • Меньше задержка (latency)"
echo -e "    • Лучше для видео-стриминга"
echo ""
echo -e "  ${YELLOW}Полезные команды:${NC}"
echo -e "    journalctl -u xray -f          # Логи Xray"
echo -e "    systemctl restart xray          # Перезапуск"
echo -e "    cat ${WARP_KEYS_FILE}    # Ключи WARP"
echo ""
