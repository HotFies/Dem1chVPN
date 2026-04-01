#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  ☁️ Cloudflare WARP — Setup for Dem1chVPN
#  Installs official WARP client in SOCKS5 proxy mode
#  Xray routes specific domains → 127.0.0.1:40000
# ═══════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

WARP_PORT=${WARP_SOCKS_PORT:-40000}

echo ""
echo -e "${GREEN}☁️  Cloudflare WARP — Установка${NC}"
echo ""

# ──── Шаг 1: Определение ОС ────

if [ ! -f /etc/os-release ]; then
    log_error "Не удалось определить ОС"
    exit 1
fi
source /etc/os-release

# ──── Шаг 2: Установка официального WARP клиента ────

if ! command -v warp-cli &> /dev/null; then
    log_info "Устанавливаю Cloudflare WARP клиент..."

    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_error "Неподдерживаемая ОС: $ID. Нужны Ubuntu или Debian."
        exit 1
    fi

    # Добавление GPG ключа Cloudflare
    curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | \
        gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg

    # Добавление репозитория
    echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ ${VERSION_CODENAME} main" \
        > /etc/apt/sources.list.d/cloudflare-client.list

    apt-get update -y
    apt-get install -y cloudflare-warp

    log_info "WARP клиент установлен"
else
    log_info "WARP клиент уже установлен: $(warp-cli --version 2>/dev/null || echo 'unknown')"
fi

# ──── Шаг 3: Ожидание готовности warp-svc ────

log_info "Ожидаю запуск warp-svc..."
for i in $(seq 1 10); do
    if warp-cli status &>/dev/null; then
        break
    fi
    sleep 1
done

# ──── Шаг 4: Регистрация аккаунта ────

# Проверка: если registration show возвращает ошибку -> нужна регистрация
if ! warp-cli --accept-tos registration show &>/dev/null; then
    log_info "Регистрирую WARP аккаунт..."
    
    warp-cli --accept-tos registration new || {
        log_error "Не удалось зарегистрировать WARP аккаунт"
        exit 1
    }
    
    log_info "WARP аккаунт зарегистрирован"
else
    log_info "WARP аккаунт уже зарегистрирован"
fi

# ──── Шаг 5: Настройка режима proxy (SOCKS5) ────

log_info "Настраиваю WARP в режиме proxy (SOCKS5 на порту ${WARP_PORT})..."

# Переключить в режим proxy (не перехватывает весь трафик)
warp-cli --accept-tos mode proxy || {
    log_error "Не удалось переключить WARP в режим proxy"
    exit 1
}

# Установить порт proxy
warp-cli --accept-tos proxy port ${WARP_PORT} || {
    log_warn "Не удалось установить порт ${WARP_PORT}, используется порт по умолчанию (40000)"
}

# ──── Шаг 6: Подключение ────

log_info "Подключаюсь к WARP..."

warp-cli --accept-tos connect || {
    log_error "Не удалось подключиться к WARP"
    exit 1
}

# Ждём подключения (до 15 секунд)
for i in $(seq 1 15); do
    STATUS=$(warp-cli status 2>/dev/null | grep -i "status" | head -1 || echo "")
    if echo "$STATUS" | grep -qi "connected"; then
        break
    fi
    sleep 1
done

# Проверяем статус
FINAL_STATUS=$(warp-cli status 2>/dev/null || echo "unknown")
if echo "$FINAL_STATUS" | grep -qi "connected"; then
    log_info "WARP подключён ✅"
else
    log_warn "WARP может быть не полностью подключён. Статус: ${FINAL_STATUS}"
fi

# ──── Шаг 7: Проверка SOCKS5 proxy ────

log_info "Проверяю SOCKS5 proxy на порту ${WARP_PORT}..."

sleep 2

# Тест через WARP
WARP_IP=$(curl -s --socks5 127.0.0.1:${WARP_PORT} https://ifconfig.me --max-time 10 2>/dev/null || echo "FAIL")

if [ "$WARP_IP" != "FAIL" ] && [ -n "$WARP_IP" ]; then
    log_info "WARP SOCKS5 работает! IP через WARP: ${WARP_IP}"
    
    # Тест NotebookLM через WARP
    NB_STATUS=$(curl -s --socks5 127.0.0.1:${WARP_PORT} -o /dev/null -w "%{http_code}" https://notebooklm.google.com --max-time 10 2>/dev/null || echo "000")
    if [ "$NB_STATUS" = "200" ] || [ "$NB_STATUS" = "302" ]; then
        log_info "NotebookLM доступен через WARP ✅ (HTTP ${NB_STATUS})"
    else
        log_warn "NotebookLM вернул HTTP ${NB_STATUS} через WARP"
    fi
else
    log_error "SOCKS5 proxy не отвечает на порту ${WARP_PORT}"
    log_warn "Попробуйте: warp-cli status && ss -tlnp | grep ${WARP_PORT}"
    exit 1
fi

# ──── Шаг 8: Обновление Xray конфига (warp routing) ────

XRAY_CONFIG="/usr/local/etc/xray/config.json"

if [ -f "$XRAY_CONFIG" ]; then
    # Убедиться что warp outbound — socks5 на правильном порту
    python3 << 'PYTHON'
import json

config_path = "/usr/local/etc/xray/config.json"

with open(config_path) as f:
    cfg = json.load(f)

# Ensure WARP outbound exists and points to the right port
warp_outbound = {
    "tag": "warp",
    "protocol": "socks",
    "settings": {
        "servers": [{"address": "127.0.0.1", "port": 40000}]
    }
}

# Remove old warp outbound if exists
cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]
cfg["outbounds"].append(warp_outbound)

# Full list of WARP-routed domains (geo-blocked CDNs)
WARP_DOMAINS = [
    # Google AI (geo-restricted)
    "domain:notebooklm.google.com",
    "domain:notebooklm-pa.googleapis.com",
    "domain:aistudio.google.com",
    "domain:generativelanguage.googleapis.com",
    "domain:alkalimakersuite-pa.googleapis.com",
    # YouTube CDN (throttles datacenter IPs)
    "domain:googlevideo.com",
    "domain:ytimg.com",
    "domain:yt3.ggpht.com",
    "domain:youtube-nocookie.com",
    # TikTok (CDN blocks datacenter IPs)
    "domain:tiktok.com", "domain:tiktokv.com", "domain:tiktokcdn.com",
    "domain:tiktokcdn-us.com", "domain:tiktokcdn-eu.com",
    "domain:tiktokd.net", "domain:tiktokd.org",
    "domain:tiktok-row.net", "domain:tik-tokapi.com",
    "domain:tiktokrow-cdn.com", "domain:tiktokeu-cdn.com",
    "domain:ttlivecdn.com", "domain:ttcdn-us.com",
    "domain:ttwstatic.com", "domain:ttoverseaus.net",
    "domain:tiktokv.eu", "domain:tiktokv.us",
    "domain:musical.ly", "domain:muscdn.com",
    "domain:byteoversea.com", "domain:byteoversea.net",
    "domain:ibytedtos.com", "domain:byteimg.com", "domain:ibyteimg.com",
    "domain:bytecdn.com", "domain:bytedance.com",
    "domain:bytegecko.com", "domain:bytedapm.com",
    "domain:isnssdk.com", "domain:snssdk.com", "domain:pstatp.com",
    # Instagram / Meta CDN (throttles datacenter IPs)
    "domain:cdninstagram.com",
    "domain:static.cdninstagram.com",
    "domain:scontent.cdninstagram.com",
    "domain:fbcdn.net",
    "domain:scontent.fbcdn.net",
    "domain:video.fbcdn.net",
    "domain:z-m-scontent.fbcdn.net",
    "domain:lookaside.fbsbx.com",
    # Twitter/X CDN
    "domain:pbs.twimg.com",
    "domain:video.twimg.com",
    "domain:abs.twimg.com",
]

# Update or create WARP routing rule
rules = cfg.get("routing", {}).get("rules", [])
warp_rule_idx = next((i for i, r in enumerate(rules) if r.get("outboundTag") == "warp"), -1)

if warp_rule_idx >= 0:
    rules[warp_rule_idx]["domain"] = WARP_DOMAINS
else:
    # Find any rule with notebooklm and change to warp
    changed = False
    for rule in rules:
        domains = rule.get("domain", [])
        if any("notebooklm" in d for d in domains):
            rule["outboundTag"] = "warp"
            rule["domain"] = WARP_DOMAINS
            changed = True
            break

    if not changed:
        warp_rule = {
            "type": "field",
            "outboundTag": "warp",
            "domain": WARP_DOMAINS,
        }
        api_idx = next((i for i, r in enumerate(rules) if r.get("inboundTag") == ["api"]), 0)
        rules.insert(api_idx + 1, warp_rule)

# Add QUIC blocking rule (force TCP fallback for TikTok/YouTube)
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
    # Insert before geoip:private rule
    private_idx = next((i for i, r in enumerate(rules) if "geoip:private" in r.get("ip", [])), len(rules))
    rules.insert(private_idx, quic_rule)

cfg["routing"]["rules"] = rules

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)

print("✅ Xray config updated:")
print(f"   WARP domains: {len(WARP_DOMAINS)} (NotebookLM + TikTok)")
print("   QUIC (UDP:443): blocked → forces TCP fallback")
PYTHON

    systemctl restart xray
    log_info "Xray перезапущен с WARP-маршрутизацией"
fi

# ──── Шаг 9: Обновление .env ────

ENV_FILE="/opt/dem1chvpn/.env"
if [ -f "$ENV_FILE" ]; then
    sed -i 's/WARP_ENABLED=false/WARP_ENABLED=true/' "$ENV_FILE"
    log_info "WARP_ENABLED=true в .env"
fi

# ──── Шаг 10: Автозапуск ────

# warp-svc уже управляется systemd при установке из пакета
systemctl enable warp-svc 2>/dev/null || true

# ──── Итог ────

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  ☁️  WARP установлен и подключён!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "  SOCKS5 proxy:  127.0.0.1:${WARP_PORT}"
echo -e "  WARP IP:       ${WARP_IP}"
echo -e "  Маршруты:      NotebookLM, AI Studio → WARP"
echo ""
echo -e "  ${YELLOW}Полезные команды:${NC}"
echo -e "    warp-cli status            # Статус WARP"
echo -e "    warp-cli disconnect        # Отключить"
echo -e "    warp-cli connect           # Подключить"
echo -e "    systemctl restart warp-svc # Перезапуск сервиса"
echo ""
