#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  ☁️ Cloudflare WARP — Setup for Dem1chVPN
#  Installs warp-svc in SOCKS5 proxy mode and configures
#  Xray to route foreign traffic through WARP.
#
#  Routing strategy (inverted):
#    Russian sites → DIRECT (from VPS IP)
#    Everything else → WARP SOCKS5 (clean Cloudflare IP)
# ═══════════════════════════════════════════════════════
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

XRAY_CONFIG="/usr/local/etc/xray/config.json"
WARP_SOCKS_PORT=40000

echo ""
echo -e "${GREEN}☁️  Cloudflare WARP — SOCKS5 Proxy Setup${NC}"
echo ""

# ──── Шаг 1: Определение ОС ────

if [ ! -f /etc/os-release ]; then
    log_error "Не удалось определить ОС"
    exit 1
fi
source /etc/os-release

ARCH=$(uname -m)
log_info "ОС: $PRETTY_NAME, архитектура: $ARCH"

# ──── Шаг 2: Установка cloudflare-warp ────

if ! command -v warp-cli &> /dev/null; then
    log_info "Устанавливаю Cloudflare WARP..."

    # Добавляем GPG ключ
    curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg \
        | gpg --yes --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg

    # Определяем кодовое имя дистрибутива
    CODENAME="${VERSION_CODENAME:-$(lsb_release -cs 2>/dev/null || echo 'noble')}"

    # Добавляем репозиторий
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ ${CODENAME} main" \
        > /etc/apt/sources.list.d/cloudflare-client.list

    apt-get update -qq
    apt-get install -y cloudflare-warp || {
        log_error "Не удалось установить cloudflare-warp"
        exit 1
    }

    log_info "cloudflare-warp установлен: $(warp-cli --version 2>/dev/null || echo 'OK')"
else
    log_info "cloudflare-warp уже установлен: $(warp-cli --version 2>/dev/null || echo 'OK')"
fi

# ──── Шаг 3: Ожидание запуска warp-svc ────

log_info "Ожидаю запуск warp-svc..."
for i in $(seq 1 15); do
    if warp-cli status &>/dev/null; then
        log_info "warp-svc демон запущен"
        break
    fi
    if [ "$i" -eq 15 ]; then
        log_warn "warp-svc долго запускается, пробую перезапуск..."
        systemctl restart warp-svc 2>/dev/null || true
        sleep 5
    fi
    sleep 1
done

# ──── Шаг 4: Отключение (если уже был подключён) ────

warp-cli disconnect 2>/dev/null || true
sleep 1

# ──── Шаг 5: Настройка режима SOCKS5 ────
# ВАЖНО: mode proxy ПЕРЕЗАПУСКАЕТ демон и СБРАСЫВАЕТ регистрацию!
# Поэтому сначала ставим режим, потом регистрируемся.

log_info "Настраиваю SOCKS5 proxy режим (порт ${WARP_SOCKS_PORT})..."
warp-cli mode proxy 2>/dev/null || {
    log_warn "Не удалось установить mode proxy, повтор..."
    sleep 2
    warp-cli mode proxy
}
warp-cli proxy port ${WARP_SOCKS_PORT} 2>/dev/null || {
    log_warn "Не удалось установить порт, повтор..."
    sleep 2
    warp-cli proxy port ${WARP_SOCKS_PORT}
}

# Ждём перезапуск демона после смены режима
log_info "Ожидаю перезапуск warp-svc после смены режима..."
sleep 5
for i in $(seq 1 10); do
    if warp-cli status &>/dev/null; then
        break
    fi
    sleep 1
done

# ──── Шаг 6: Регистрация (ПОСЛЕ смены режима) ────

log_info "Регистрирую WARP аккаунт..."
yes | warp-cli registration new 2>/dev/null || {
    log_warn "Первая попытка регистрации не удалась, повтор..."
    sleep 3
    yes | warp-cli registration new 2>/dev/null || {
        log_error "Не удалось зарегистрироваться в WARP"
        exit 1
    }
}
log_info "WARP аккаунт зарегистрирован"
sleep 3

# ──── Шаг 7: Подключение ────

warp-cli connect 2>/dev/null || true

# Проверяем подключение с ретраями (до 30 секунд)
CONNECTED=false
for i in $(seq 1 10); do
    sleep 3
    WARP_STATUS=$(warp-cli status 2>/dev/null || echo "")
    if echo "$WARP_STATUS" | grep -qi "connected"; then
        # Убедимся что это не "Disconnected" а именно "Connected"
        if ! echo "$WARP_STATUS" | grep -qi "disconnected"; then
            log_info "WARP подключён (SOCKS5 на 127.0.0.1:${WARP_SOCKS_PORT})"
            CONNECTED=true
            break
        fi
    fi
    log_warn "Ожидание WARP... попытка $i/10 (статус: $(echo "$WARP_STATUS" | grep -i 'status' | head -1 || echo 'unknown'))"
done

if [ "$CONNECTED" = false ]; then
    # Полный сброс: отключить → удалить регистрацию → заново
    log_warn "WARP не подключился, полный сброс..."
    warp-cli disconnect 2>/dev/null || true
    sleep 2
    warp-cli registration delete 2>/dev/null || true
    sleep 2
    yes | warp-cli registration new 2>/dev/null || true
    sleep 2
    warp-cli mode proxy 2>/dev/null || true
    warp-cli proxy port ${WARP_SOCKS_PORT} 2>/dev/null || true
    sleep 2
    warp-cli connect 2>/dev/null || true
    sleep 5
    WARP_STATUS=$(warp-cli status 2>/dev/null || echo "")
    if echo "$WARP_STATUS" | grep -qi "connected" && ! echo "$WARP_STATUS" | grep -qi "disconnected"; then
        log_info "WARP подключён после полного сброса"
        CONNECTED=true
    else
        log_warn "WARP не подключился. Статус: $WARP_STATUS"
        log_warn "Попробуйте вручную: warp-cli disconnect && warp-cli connect && warp-cli status"
    fi
fi

# ──── Шаг 8: Тест SOCKS5 proxy ────

if [ "$CONNECTED" = true ]; then
    log_info "Тестирую SOCKS5 proxy..."
    SOCKS_TEST=$(curl -x socks5h://127.0.0.1:${WARP_SOCKS_PORT} -sI --max-time 10 https://cloudflare.com 2>/dev/null | head -1 || echo "FAIL")

    if echo "$SOCKS_TEST" | grep -qi "HTTP"; then
        log_info "SOCKS5 proxy работает: $SOCKS_TEST"
    else
        log_warn "SOCKS5 тест не прошёл, WARP может ещё инициализироваться"
        log_warn "Проверьте через минуту: curl -x socks5h://127.0.0.1:${WARP_SOCKS_PORT} https://ifconfig.me"
    fi
else
    log_warn "Пропускаю тест SOCKS5 — WARP не подключён"
fi

# ──── Шаг 9: Обновление Xray конфига ────

if [ -f "$XRAY_CONFIG" ]; then
    python3 << PYTHON
import json

config_path = "${XRAY_CONFIG}"
socks_port = ${WARP_SOCKS_PORT}

with open(config_path) as f:
    cfg = json.load(f)

# Remove old WARP outbound (WireGuard or SOCKS5)
cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

# Add SOCKS5 WARP outbound (connects to local warp-svc)
warp_outbound = {
    "tag": "warp",
    "protocol": "socks",
    "settings": {
        "servers": [
            {
                "address": "127.0.0.1",
                "port": socks_port,
            }
        ]
    },
}
cfg["outbounds"].append(warp_outbound)

# Inverted routing: Russian sites → direct, ALL foreign traffic → WARP
rules = cfg.get("routing", {}).get("rules", [])

# Remove old WARP rules
rules = [r for r in rules if r.get("outboundTag") != "warp"]

# Ensure DNS goes direct (SOCKS5 can't proxy UDP)
has_dns_direct = any(
    r.get("port") == "53" and r.get("outboundTag") == "direct"
    for r in rules
)
if not has_dns_direct:
    rules.append({
        "type": "field",
        "outboundTag": "direct",
        "port": "53",
    })

# Ensure QUIC blocking exists before catch-all
has_quic_block = any(
    r.get("network") == "udp" and r.get("port") == "443"
    for r in rules
)
if not has_quic_block:
    rules.append({
        "type": "field",
        "outboundTag": "blocked",
        "network": "udp",
        "port": "443",
    })

# Catch-all: everything else → WARP (TCP only, since UDP is handled above)
rules.append({
    "type": "field",
    "outboundTag": "warp",
    "network": "tcp",
})

cfg["routing"]["rules"] = rules

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)

print("✅ Xray config updated:")
print(f"   WARP outbound: SOCKS5 → 127.0.0.1:{socks_port}")
print("   Routing: RU sites → direct, ALL foreign → WARP")
print("   QUIC (UDP:443): blocked → forces TCP fallback")
PYTHON

    systemctl restart xray
    sleep 2

    if systemctl is-active --quiet xray; then
        log_info "Xray перезапущен с WARP SOCKS5"
    else
        log_error "Xray не запустился! Проверьте: journalctl -u xray --no-pager -n 20"
        exit 1
    fi
fi

# ──── Шаг 10: Обновление .env ────

ENV_FILE="/opt/dem1chvpn/.env"
if [ -f "$ENV_FILE" ]; then
    # Обновляем или добавляем WARP_ENABLED
    if grep -q "WARP_ENABLED" "$ENV_FILE"; then
        sed -i 's/WARP_ENABLED=.*/WARP_ENABLED=true/' "$ENV_FILE"
    else
        echo "WARP_ENABLED=true" >> "$ENV_FILE"
    fi

    # Обновляем или добавляем WARP_SOCKS_PORT
    if grep -q "WARP_SOCKS_PORT" "$ENV_FILE"; then
        sed -i "s/WARP_SOCKS_PORT=.*/WARP_SOCKS_PORT=${WARP_SOCKS_PORT}/" "$ENV_FILE"
    else
        echo "WARP_SOCKS_PORT=${WARP_SOCKS_PORT}" >> "$ENV_FILE"
    fi

    log_info "WARP_ENABLED=true, WARP_SOCKS_PORT=${WARP_SOCKS_PORT} в .env"
fi

# ──── Итог ────

echo ""
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo -e "${GREEN}  ☁️  WARP SOCKS5 установлен!${NC}"
echo -e "${GREEN}═══════════════════════════════════════${NC}"
echo ""
echo -e "  Режим:        SOCKS5 Proxy (warp-svc)"
echo -e "  Порт:         127.0.0.1:${WARP_SOCKS_PORT}"
echo -e "  Маршрутизация: RU → direct, всё остальное → WARP"
echo ""
echo -e "  ${YELLOW}Полезные команды:${NC}"
echo -e "    warp-cli status             # Статус WARP"
echo -e "    warp-cli disconnect         # Отключить"
echo -e "    warp-cli connect            # Подключить"
echo -e "    journalctl -u xray -f       # Логи Xray"
echo -e "    systemctl restart xray      # Перезапуск Xray"
echo ""
echo -e "  ${YELLOW}Тест:${NC}"
echo -e "    curl -x socks5h://127.0.0.1:${WARP_SOCKS_PORT} https://ifconfig.me"
echo ""
