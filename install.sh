#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════
#  🛡️ Dem1chVPN — Автоматический установочный скрипт
#  Устанавливает и настраивает:
#    - Защиту сервера (SSH, UFW, fail2ban, BBR)
#    - Xray-core (VLESS + Reality + TCP)
#    - Telegram-бот Dem1chVPN (Python + aiogram 3)
#    - Сервер подписок (FastAPI + Caddy HTTPS)
#    - Cron-задачи (обновление гео-баз, мониторинг, бэкапы)
# ═══════════════════════════════════════════════════════

set -euo pipefail

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Пути
DEM1CHVPN_DIR="/opt/dem1chvpn"
XRAY_CONFIG="/usr/local/etc/xray/config.json"
XRAY_BIN="/usr/local/bin/xray"
LOG_DIR="/var/log/dem1chvpn"
DATA_DIR="${DEM1CHVPN_DIR}/data"
VENV_DIR="${DEM1CHVPN_DIR}/venv"
ENV_FILE="${DEM1CHVPN_DIR}/.env"

# ──── Вспомогательные функции ────

log_info()  { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }
log_step()  { echo -e "\n${CYAN}═══ $1 ═══${NC}\n"; }

check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "Этот скрипт нужно запускать от root!"
        exit 1
    fi
}

check_os() {
    log_step "Проверка совместимости ОС"

    if [ ! -f /etc/os-release ]; then
        log_error "Не удалось определить ОС. Файл /etc/os-release не найден."
        exit 1
    fi

    source /etc/os-release

    if [[ "$ID" != "ubuntu" && "$ID" != "debian" ]]; then
        log_error "Неподдерживаемая ОС: $ID. Поддерживаются только Ubuntu и Debian."
        exit 1
    fi

    # Проверка версии
    if [[ "$ID" == "debian" ]]; then
        if [[ "${VERSION_ID:-0}" -lt 11 ]]; then
            log_error "Требуется Debian 11+. Обнаружен: $VERSION_ID"
            exit 1
        fi
    elif [[ "$ID" == "ubuntu" ]]; then
        MAJOR_VER=$(echo "${VERSION_ID:-0}" | cut -d. -f1)
        if [[ "$MAJOR_VER" -lt 22 ]]; then
            log_error "Требуется Ubuntu 22.04+. Обнаружен: $VERSION_ID"
            exit 1
        fi
    fi

    log_info "ОС: $PRETTY_NAME ✓"
}

get_public_ip() {
    curl -s4 https://ifconfig.me || curl -s4 https://api.ipify.org || echo "UNKNOWN"
}

# ──── Освобождение занятых портов ────

free_ports() {
    log_step "Проверка занятости портов"

    local PORTS_TO_CHECK=("80" "8080" "443")
    local SERVICES_TO_STOP=("nginx" "apache2" "httpd" "lighttpd")

    # Остановка конфликтующих веб-серверов
    for svc in "${SERVICES_TO_STOP[@]}"; do
        if systemctl is-active --quiet "$svc" 2>/dev/null; then
            log_warn "Обнаружен запущенный $svc — останавливаю..."
            systemctl stop "$svc" 2>/dev/null || true
            systemctl disable "$svc" 2>/dev/null || true
            log_info "$svc остановлен и отключен"
        fi
    done

    # Проверка что порты освободились
    for port in "${PORTS_TO_CHECK[@]}"; do
        local pids=""
        pids=$(ss -tlnp 2>/dev/null | grep ":${port} " 2>/dev/null | grep -oP 'pid=\K[0-9]+' 2>/dev/null | sort -u || true)
        if [ -n "$pids" ]; then
            log_warn "Порт $port всё ещё занят (PID: $pids) — убиваю процессы..."
            for pid in $pids; do
                kill "$pid" 2>/dev/null || true
            done
            sleep 1
        fi
    done

    log_info "Порты 80, 443, 8080 свободны"
}

validate_bot_token() {
    # Формат токена: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    if [[ ! "$1" =~ ^[0-9]+:[A-Za-z0-9_-]{35}$ ]]; then
        return 1
    fi
    return 0
}

validate_numeric() {
    if [[ ! "$1" =~ ^[0-9]+$ ]]; then
        return 1
    fi
    return 0
}

validate_pin() {
    if [[ ! "$1" =~ ^[0-9]{4,8}$ ]]; then
        return 1
    fi
    return 0
}

# ──── Шаг 1: Обновление системы и зависимости ────

install_dependencies() {
    log_step "Шаг 1: Установка системных зависимостей"

    apt update -y && apt upgrade -y
    apt install -y \
        curl wget unzip git jq \
        python3 python3-pip python3-venv \
        ufw fail2ban \
        cron logrotate \
        ca-certificates gnupg \
        speedtest-cli \
        fonts-dejavu-core

    # Установка Node.js 20 LTS (для сборки Mini App)
    if ! command -v node &> /dev/null; then
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt install -y nodejs
        log_info "Node.js $(node -v) установлен"
    fi

    # Установка Docker (для MTProto, AdGuard)
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com | sh
        systemctl enable docker
        systemctl start docker
        log_info "Docker установлен"
    fi

    log_info "Зависимости установлены"
}

# ──── Шаг 2: Защита сервера ────

harden_system() {
    log_step "Шаг 2: Защита сервера"

    # Включение BBR + сетевая оптимизация (единый блок)
    if ! grep -q "Dem1chVPN Performance" /etc/sysctl.conf 2>/dev/null; then
        cat >> /etc/sysctl.conf << 'SYSCTL'
# ═══ Dem1chVPN Performance Tuning ═══

# --- BBR (контроль перегрузки) ---
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr

# --- Буферы TCP (64MB для высокоскоростных соединений) ---
net.core.rmem_max=67108864
net.core.wmem_max=67108864
net.core.rmem_default=1048576
net.core.wmem_default=1048576
net.ipv4.tcp_rmem=4096 87380 67108864
net.ipv4.tcp_wmem=4096 65536 67108864

# --- Оптимизация TCP ---
net.ipv4.tcp_fastopen=3
net.ipv4.tcp_slow_start_after_idle=0
net.ipv4.tcp_mtu_probing=1
net.ipv4.tcp_notsent_lowat=16384

# --- Очереди и соединения ---
net.core.netdev_max_backlog=16384
net.core.somaxconn=8192
net.ipv4.tcp_max_syn_backlog=8192
net.ipv4.tcp_tw_reuse=1
net.ipv4.tcp_fin_timeout=15
net.ipv4.tcp_keepalive_time=300
net.ipv4.tcp_keepalive_intvl=30
net.ipv4.tcp_keepalive_probes=5

# --- Системные лимиты ---
fs.file-max=1048576
SYSCTL
        log_info "TCP BBR + сетевая оптимизация включены"
    else
        log_info "Оптимизация сети уже настроена"
    fi
    sysctl -p 2>/dev/null || true

    # Настройка файрвола UFW
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow 22/tcp       # SSH
    ufw allow 443/tcp      # Xray (VLESS + Reality)
    ufw allow 8443/tcp     # Caddy (Подписка + Mini App HTTPS)
    ufw --force enable
    log_info "Файрвол UFW настроен"

    # Настройка fail2ban
    systemctl enable fail2ban
    systemctl start fail2ban
    log_info "fail2ban включён"

    # Опционально: смена порта SSH
    echo ""
    read -rp "$(echo -e "${PURPLE}Сменить порт SSH? (введите новый порт или нажмите Enter для 22): ${NC}")" NEW_SSH_PORT
    if [[ -n "$NEW_SSH_PORT" ]] && validate_numeric "$NEW_SSH_PORT"; then
        if [[ "$NEW_SSH_PORT" -ge 1024 && "$NEW_SSH_PORT" -le 65535 ]]; then
            sed -i "s/^#\?Port .*/Port ${NEW_SSH_PORT}/" /etc/ssh/sshd_config
            ufw allow "${NEW_SSH_PORT}/tcp"
            systemctl restart sshd
            log_info "Порт SSH изменён на ${NEW_SSH_PORT}"
            log_warn "Не забудьте подключаться по новому порту: ssh -p ${NEW_SSH_PORT} root@ваш-сервер"
        else
            log_warn "Недопустимый диапазон портов. Оставляем порт 22."
        fi
    fi

    log_info "Сервер защищён"
}

# ──── Шаг 3: Установка Xray-core ────

install_xray() {
    log_step "Шаг 3: Установка Xray-core"

    bash <(curl -Ls https://raw.githubusercontent.com/XTLS/Xray-install/main/install-release.sh)

    # Создание директории логов
    mkdir -p /var/log/xray
    chown nobody:nogroup /var/log/xray 2>/dev/null || true

    # Скачивание гео-баз (Loyalsoldier — полные и актуальные)
    log_info "Скачиваю гео-базы..."
    wget -qO /usr/local/share/xray/geoip.dat \
        "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat" || \
        wget -qO /usr/local/share/xray/geoip.dat \
        "https://github.com/v2fly/geoip/releases/latest/download/geoip.dat"

    wget -qO /usr/local/share/xray/geosite.dat \
        "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat" || \
        wget -qO /usr/local/share/xray/geosite.dat \
        "https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat"

    # Проверка что файлы не пустые
    if [ ! -s /usr/local/share/xray/geosite.dat ]; then
        log_warn "geosite.dat пустой, скачиваю из запасного источника..."
        wget -qO /usr/local/share/xray/geosite.dat \
            "https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat"
    fi

    log_info "Xray-core установлен"
}

# ──── Шаг 4: Генерация ключей и настройка Xray ────

configure_xray() {
    log_step "Шаг 4: Настройка Xray-core"

    # Генерация ключей Reality
    KEYS=$($XRAY_BIN x25519)
    # Xray 25+ выводит "PrivateKey: xxx" и "Password (PublicKey): xxx"
    # Старые версии: "Private key: xxx" и "Public key: xxx"
    PRIVATE_KEY=$(echo "$KEYS" | grep -i "private" | awk '{print $NF}')
    PUBLIC_KEY=$(echo "$KEYS" | grep -i "public" | awk '{print $NF}')

    if [ -z "$PRIVATE_KEY" ] || [ -z "$PUBLIC_KEY" ]; then
        log_error "Не удалось сгенерировать ключи Reality!"
        log_error "Вывод xray x25519: $KEYS"
        exit 1
    fi
    SHORT_ID=$(openssl rand -hex 4)
    SERVER_IP=$(get_public_ip)

    log_info "Ключи Reality сгенерированы"
    log_info "Публичный ключ: ${PUBLIC_KEY}"

    # Создание конфига из шаблона
    TEMPLATE="${DEM1CHVPN_DIR}/server/xray/config_template.json"
    cp "$TEMPLATE" "$XRAY_CONFIG"

    # Подстановка значений
    sed -i "s|REALITY_DEST_PLACEHOLDER|dl.google.com:443|g" "$XRAY_CONFIG"
    sed -i "s|REALITY_SNI_PLACEHOLDER|dl.google.com|g" "$XRAY_CONFIG"
    sed -i "s|REALITY_PRIVATE_KEY_PLACEHOLDER|${PRIVATE_KEY}|g" "$XRAY_CONFIG"
    sed -i "s|REALITY_SHORT_ID_PLACEHOLDER|${SHORT_ID}|g" "$XRAY_CONFIG"

    # Сохранение ключей для .env
    echo "XRAY_PRIVATE_KEY=${PRIVATE_KEY}" > /tmp/dem1chvpn_keys
    echo "XRAY_PUBLIC_KEY=${PUBLIC_KEY}" >> /tmp/dem1chvpn_keys
    echo "XRAY_SHORT_ID=${SHORT_ID}" >> /tmp/dem1chvpn_keys
    echo "SERVER_IP=${SERVER_IP}" >> /tmp/dem1chvpn_keys

    # Включение и запуск Xray
    systemctl enable xray
    systemctl restart xray

    if systemctl is-active --quiet xray; then
        log_info "Xray запущен успешно"
    else
        log_error "Xray не удалось запустить! Проверьте: journalctl -u xray"
        exit 1
    fi
}

# ──── Шаг 5: Установка бота Dem1chVPN ────

install_bot() {
    log_step "Шаг 5: Установка бота Dem1chVPN"

    # Создание директорий
    mkdir -p "$DATA_DIR" "$LOG_DIR" "${DEM1CHVPN_DIR}/backups"

    # Создание Python venv
    python3 -m venv "$VENV_DIR"
    source "${VENV_DIR}/bin/activate"
    pip install --upgrade pip
    pip install -r "${DEM1CHVPN_DIR}/requirements.txt"
    deactivate

    log_info "Python-зависимости установлены"

    # Загрузка сохранённых ключей
    source /tmp/dem1chvpn_keys

    # Запрос токена бота с валидацией
    echo ""
    while true; do
        read -rp "$(echo -e "${PURPLE}Введите токен Telegram-бота: ${NC}")" BOT_TOKEN
        if validate_bot_token "$BOT_TOKEN"; then
            break
        fi
        log_warn "Неверный формат токена. Ожидается: 123456789:ABCdefGHI..."
    done

    while true; do
        read -rp "$(echo -e "${PURPLE}Введите ваш Telegram ID (администратор): ${NC}")" ADMIN_ID
        if validate_numeric "$ADMIN_ID"; then
            break
        fi
        log_warn "ID должен быть числом"
    done

    while true; do
        read -rp "$(echo -e "${PURPLE}Введите PIN-код (4-8 цифр): ${NC}")" PIN_CODE
        if validate_pin "$PIN_CODE"; then
            break
        fi
        log_warn "PIN должен быть от 4 до 8 цифр"
    done
    PIN_CODE=${PIN_CODE:-0000}

    # Автодетект хостнейма VPS для подписки
    VPS_HOSTNAME=$(hostname -f 2>/dev/null || hostname 2>/dev/null || echo "")
    if [ -z "$VPS_HOSTNAME" ] || [ "$VPS_HOSTNAME" = "localhost" ]; then
        VPS_HOSTNAME="$SERVER_IP"
    fi
    log_info "Хостнейм VPS: ${VPS_HOSTNAME}"
    echo -e "${CYAN}  Нажмите Enter чтобы использовать хостнейм VPS.${NC}"
    echo -e "${CYAN}  Или введите свой домен (например: vpn.example.com)${NC}"
    read -rp "$(echo -e "${PURPLE}Домен для подписки [${VPS_HOSTNAME}]: ${NC}")" CUSTOM_DOMAIN
    SUB_DOMAIN=${CUSTOM_DOMAIN:-$VPS_HOSTNAME}
    log_info "Домен подписки: ${SUB_DOMAIN}"

    # Создание файла .env
    cat > "$ENV_FILE" << ENVFILE
# Конфигурация Dem1chVPN
BOT_TOKEN=${BOT_TOKEN}
ADMIN_IDS=${ADMIN_ID}
PIN_CODE=${PIN_CODE}

# Сервер
SERVER_IP=${SERVER_IP}
SERVER_PORT=443

# Reality
REALITY_DEST=dl.google.com:443
REALITY_SNI=dl.google.com
REALITY_PRIVATE_KEY=${XRAY_PRIVATE_KEY}
REALITY_PUBLIC_KEY=${XRAY_PUBLIC_KEY}
REALITY_SHORT_ID=${XRAY_SHORT_ID}

# База данных
DB_PATH=${DATA_DIR}/dem1chvpn.db

# Xray
XRAY_CONFIG_PATH=${XRAY_CONFIG}
XRAY_BINARY=${XRAY_BIN}
XRAY_INBOUND_TAG=vless-reality

# Сервер подписок
SUB_HOST=127.0.0.1
SUB_PORT=8080
SUB_DOMAIN=${SUB_DOMAIN}
SUB_EXTERNAL_PORT=8443

# WARP (обязательный — маршрутизация зарубежного трафика)
WARP_ENABLED=true

# Дополнительные модули (включить позже)
ADGUARD_ENABLED=false
MTPROTO_ENABLED=false

# Автоматика
TRAFFIC_RESET_DAY=1
XRAY_AUTO_UPDATE=true
ENVFILE

    chmod 600 "$ENV_FILE"
    log_info "Файл .env создан"

    # Очистка временных данных
    rm -f /tmp/dem1chvpn_keys
}

# ──── Шаг 6: Установка Caddy (HTTPS обратный прокси) ────

install_caddy() {
    log_step "Шаг 6: Установка Caddy (HTTPS для подписок)"

    apt install -y debian-keyring debian-archive-keyring apt-transport-https
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | \
        gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
    curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | \
        tee /etc/apt/sources.list.d/caddy-stable.list
    apt update -y
    apt install -y caddy

    # Загрузка переменных из .env
    set -a
    source "$ENV_FILE"
    set +a

    # Настройка Caddy — HTTP-01 challenge (автоматически, без DuckDNS)
    cat > /etc/caddy/Caddyfile << CADDYFILE
{
    http_port 80
}

${SUB_DOMAIN}:8443 {
    reverse_proxy 127.0.0.1:8080

    header {
        -Server
        X-Content-Type-Options nosniff
        X-Frame-Options SAMEORIGIN
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        Referrer-Policy strict-origin-when-cross-origin
    }

    log {
        output file /var/log/caddy/dem1chvpn.log
    }
}
CADDYFILE

    mkdir -p /var/log/caddy

    # Стандартный Caddy — никаких плагинов не нужно
    # HTTP-01 challenge работает автоматически через порт 80

    systemctl enable caddy
    systemctl restart caddy || {
        log_warn "Caddy не смог стартовать. Возможно порт 80 занят."
        log_warn "Попытка освободить порт 80..."
        for svc in nginx apache2 httpd; do
            systemctl stop "$svc" 2>/dev/null || true
            systemctl disable "$svc" 2>/dev/null || true
        done
        sleep 2
        systemctl restart caddy || log_warn "Caddy всё ещё не стартует — починим после установки"
    }

    if systemctl is-active --quiet caddy; then
        log_info "Caddy установлен и запущен"
    else
        log_warn "Caddy установлен, но не запущен. Проверьте: systemctl status caddy"
    fi
}

# (build_webapp определена ниже — шаг 6.9)

# ──── Шаг 6.6: Установка MTProto Proxy ────

setup_mtproto() {
    log_step "Шаг 6.6: Установка MTProto Proxy"

    MTPROTO_DIR="${DEM1CHVPN_DIR}/server/mtproto"

    if [ -f "${MTPROTO_DIR}/setup.sh" ]; then
        chmod +x "${MTPROTO_DIR}/setup.sh"
        bash "${MTPROTO_DIR}/setup.sh" || {
            log_warn "Установка MTProto не удалась (необязательный компонент)"
            return 0
        }
    fi
}

# ──── Шаг 6.7: Установка AdGuard Home ────

setup_adguard() {
    log_step "Шаг 6.7: Установка AdGuard Home"

    ADGUARD_DIR="${DEM1CHVPN_DIR}/server/adguard"

    if [ -f "${ADGUARD_DIR}/setup.sh" ]; then
        chmod +x "${ADGUARD_DIR}/setup.sh"
        bash "${ADGUARD_DIR}/setup.sh" || {
            log_warn "Установка AdGuard не удалась (необязательный компонент)"
            return 0
        }
    fi
}

# ──── Шаг 6.8: Установка Cloudflare WARP ────

setup_warp() {
    log_step "Шаг 6.8: Установка Cloudflare WARP"

    WARP_DIR="${DEM1CHVPN_DIR}/server/warp"
    mkdir -p "$WARP_DIR"

    if [ -f "${WARP_DIR}/setup.sh" ]; then
        chmod +x "${WARP_DIR}/setup.sh"
        bash "${WARP_DIR}/setup.sh"
        # Возвращаем exit code как есть — WARP обязателен
    else
        log_error "WARP setup.sh не найден: ${WARP_DIR}/setup.sh"
        return 1
    fi
}

# ──── Шаг 6.9: Сборка Mini App (React) ────

build_webapp() {
    log_step "Шаг 6.9: Сборка Mini App"

    WEBAPP_DIR="${DEM1CHVPN_DIR}/server/webapp"

    if [ ! -f "${WEBAPP_DIR}/package.json" ]; then
        log_warn "Mini App не найден (${WEBAPP_DIR}/package.json отсутствует)"
        return 0
    fi

    # Установка Node.js 20 LTS (если не установлен)
    if ! command -v node &> /dev/null; then
        log_info "Установка Node.js 20 LTS..."
        curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
        apt-get install -y nodejs
    fi

    NODE_VER=$(node --version 2>/dev/null || echo "unknown")
    log_info "Node.js: ${NODE_VER}"

    # Сборка
    cd "${WEBAPP_DIR}"
    npm install --production=false 2>&1 | tail -3
    npm run build 2>&1 | tail -5

    if [ -d "${WEBAPP_DIR}/dist" ]; then
        log_info "Mini App собран: ${WEBAPP_DIR}/dist"
        # Права для dem1chvpn
        chown -R dem1chvpn:dem1chvpn "${WEBAPP_DIR}/dist" 2>/dev/null || true
    else
        log_warn "Сборка Mini App не удалась (dist/ не создана)"
    fi

    cd "${DEM1CHVPN_DIR}"
}

# ──── Шаг 7: Создание systemd-сервисов ────

create_services() {
    log_step "Шаг 7: Создание systemd-сервисов"

    # Сервис бота
    cat > /etc/systemd/system/dem1chvpn-bot.service << SERVICE
[Unit]
Description=Dem1chVPN Telegram Bot
After=network.target xray.service
Wants=xray.service

[Service]
Type=simple
User=dem1chvpn
Group=dem1chvpn
WorkingDirectory=${DEM1CHVPN_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_DIR}/bin/python -m server.bot.main
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

    # Сервис подписок
    cat > /etc/systemd/system/dem1chvpn-sub.service << SERVICE
[Unit]
Description=Dem1chVPN Subscription Server
After=network.target

[Service]
Type=simple
User=dem1chvpn
Group=dem1chvpn
WorkingDirectory=${DEM1CHVPN_DIR}
EnvironmentFile=${ENV_FILE}
ExecStart=${VENV_DIR}/bin/python -m server.subscription.app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

    # Создание системного пользователя dem1chvpn (если не существует)
    if ! id -u dem1chvpn &>/dev/null; then
        useradd -r -s /usr/sbin/nologin -d "${DEM1CHVPN_DIR}" dem1chvpn
        log_info "Пользователь dem1chvpn создан"
    fi

    # Права на необходимые директории
    chown -R dem1chvpn:dem1chvpn "${DEM1CHVPN_DIR}/data" "${LOG_DIR}" "${DEM1CHVPN_DIR}/backups"
    chown dem1chvpn:dem1chvpn "${ENV_FILE}"
    # Xray конфиг — dem1chvpn должен иметь доступ на запись (для добавления/удаления клиентов)
    chown dem1chvpn:dem1chvpn "${XRAY_CONFIG}"
    chmod 664 "${XRAY_CONFIG}"

    systemctl daemon-reload
    systemctl enable dem1chvpn-bot dem1chvpn-sub
    systemctl start dem1chvpn-bot dem1chvpn-sub

    log_info "Сервисы созданы и запущены (пользователь: dem1chvpn)"
}

# ──── Шаг 8: Настройка Cron-задач ────

setup_cron() {
    log_step "Шаг 8: Настройка cron-задач"

    # Скрипт обновления DuckDNS
    cat > /opt/dem1chvpn/cron/update_duckdns.sh << 'SCRIPT'
#!/bin/bash
# DuckDNS update script — disabled (using VPS hostname now)
# Kept as placeholder for users who manually set up DuckDNS
set -a
source /opt/dem1chvpn/.env
set +a
if [ -n "${DUCKDNS_SUBDOMAIN:-}" ] && [ -n "${DUCKDNS_TOKEN:-}" ]; then
    curl -s "https://www.duckdns.org/update?domains=${DUCKDNS_SUBDOMAIN}&token=${DUCKDNS_TOKEN}&ip=" > /dev/null
fi
SCRIPT

    # Скрипт обновления гео-баз
    cat > /opt/dem1chvpn/cron/update_geodata.sh << 'SCRIPT'
#!/bin/bash
echo "[$(date)] Обновление гео-баз..."

# Бэкап текущих файлов
cp /usr/local/share/xray/geoip.dat /usr/local/share/xray/geoip.dat.bak 2>/dev/null
cp /usr/local/share/xray/geosite.dat /usr/local/share/xray/geosite.dat.bak 2>/dev/null

# geoip.dat — Loyalsoldier (primary), v2fly (fallback)
wget -qO /usr/local/share/xray/geoip.dat \
    "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geoip.dat" && \
    echo "geoip.dat обновлён (Loyalsoldier)" || \
    wget -qO /usr/local/share/xray/geoip.dat \
        "https://github.com/v2fly/geoip/releases/latest/download/geoip.dat" && \
        echo "geoip.dat обновлён (v2fly)" || {
            echo "Ошибка обновления geoip.dat — восстанавливаю бэкап"
            cp /usr/local/share/xray/geoip.dat.bak /usr/local/share/xray/geoip.dat 2>/dev/null
        }

# geosite.dat — Loyalsoldier (primary, содержит category-ru), v2fly (fallback)
wget -qO /usr/local/share/xray/geosite.dat \
    "https://github.com/Loyalsoldier/v2ray-rules-dat/releases/latest/download/geosite.dat" && \
    echo "geosite.dat обновлён (Loyalsoldier)" || \
    wget -qO /usr/local/share/xray/geosite.dat \
        "https://github.com/v2fly/domain-list-community/releases/latest/download/dlc.dat" && \
        echo "geosite.dat обновлён (v2fly)" || {
            echo "Ошибка обновления geosite.dat — восстанавливаю бэкап"
            cp /usr/local/share/xray/geosite.dat.bak /usr/local/share/xray/geosite.dat 2>/dev/null
        }

# Проверить конфиг перед рестартом (чтобы не уронить Xray)
if /usr/local/bin/xray run -test -config /usr/local/etc/xray/config.json >/dev/null 2>&1; then
    systemctl restart xray
    echo "[$(date)] Xray перезапущен с новыми гео-базами"
else
    echo "[$(date)] ОШИБКА: конфиг невалиден после обновления гео-баз! Восстанавливаю бэкап..."
    cp /usr/local/share/xray/geoip.dat.bak /usr/local/share/xray/geoip.dat 2>/dev/null
    cp /usr/local/share/xray/geosite.dat.bak /usr/local/share/xray/geosite.dat 2>/dev/null
    systemctl restart xray
fi

echo "[$(date)] Обновление гео-баз завершено"
SCRIPT

    # Скрипт обновления антифильтра
    cat > /opt/dem1chvpn/cron/update_antifilter.sh << 'SCRIPT'
#!/bin/bash
echo "[$(date)] Обновление списков антифильтра..."
ANTIFILTER_DIR="/opt/dem1chvpn/data/antifilter"
mkdir -p "$ANTIFILTER_DIR"

wget -qO "${ANTIFILTER_DIR}/domains.lst" \
    "https://antifilter.download/list/domains.lst" && \
    echo "Список доменов обновлён" || echo "Ошибка обновления списка доменов"

wget -qO "${ANTIFILTER_DIR}/ips.lst" \
    "https://antifilter.download/list/ips.lst" && \
    echo "Список IP обновлён" || echo "Ошибка обновления списка IP"

echo "[$(date)] Обновление антифильтра завершено"
SCRIPT

    # Скрипт проверки доступности IP
    cat > /opt/dem1chvpn/cron/ip_block_check.sh << 'SCRIPT'
#!/bin/bash
set -a
source /opt/dem1chvpn/.env
set +a

# Проверка доступности IP VPS
FAIL_COUNT=0
CHECK_FILE="/tmp/dem1chvpn_ip_check_fail"

for endpoint in \
    "https://check-host.net/check-ping?host=${SERVER_IP}" \
    "https://ifconfig.me"; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$endpoint" 2>/dev/null)
    if [[ "$HTTP_CODE" -ge 500 ]] || [[ "$HTTP_CODE" -eq 0 ]]; then
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
done

if [[ $FAIL_COUNT -ge 2 ]]; then
    PREV_FAILS=$(cat "$CHECK_FILE" 2>/dev/null || echo "0")
    NEW_FAILS=$((PREV_FAILS + 1))
    echo "$NEW_FAILS" > "$CHECK_FILE"

    if [[ $NEW_FAILS -ge 3 ]]; then
        echo "[$(date)] ВНИМАНИЕ: IP ${SERVER_IP} возможно недоступен из региона! (${NEW_FAILS} последовательных сбоев)"
    fi
else
    echo "0" > "$CHECK_FILE"
fi
SCRIPT

    # Скрипт проверки здоровья сервисов
    cat > /opt/dem1chvpn/cron/health_check.sh << 'SCRIPT'
#!/bin/bash
if ! systemctl is-active --quiet xray; then
    echo "[$(date)] Xray упал! Перезапускаю..."
    systemctl restart xray
    sleep 2
    if systemctl is-active --quiet xray; then
        echo "[$(date)] Xray перезапущен успешно"
    else
        echo "[$(date)] Перезапуск Xray НЕ УДАЛСЯ!"
    fi
fi

if ! systemctl is-active --quiet dem1chvpn-bot; then
    echo "[$(date)] Бот упал! Перезапускаю..."
    systemctl restart dem1chvpn-bot
fi

if ! systemctl is-active --quiet dem1chvpn-sub; then
    echo "[$(date)] Сервер подписок упал! Перезапускаю..."
    systemctl restart dem1chvpn-sub
fi
SCRIPT

    # Скрипт бэкапа
    cat > /opt/dem1chvpn/cron/backup.sh << 'SCRIPT'
#!/bin/bash
BACKUP_DIR="/opt/dem1chvpn/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/dem1chvpn_${TIMESTAMP}.tar.gz"

mkdir -p "$BACKUP_DIR"
tar -czf "$BACKUP_FILE" \
    /usr/local/etc/xray/config.json \
    /opt/dem1chvpn/data/dem1chvpn.db \
    /opt/dem1chvpn/.env \
    2>/dev/null

# Оставляем только последние 7 бэкапов
ls -t "${BACKUP_DIR}"/dem1chvpn_*.tar.gz | tail -n +8 | xargs rm -f 2>/dev/null

echo "[$(date)] Бэкап создан: ${BACKUP_FILE}"
SCRIPT

    # Скрипт проверки обновлений Xray
    cat > /opt/dem1chvpn/cron/check_xray_update.sh << 'SCRIPT'
#!/bin/bash
CURRENT=$(/usr/local/bin/xray version 2>/dev/null | head -1 | awk '{print $2}')
LATEST=$(curl -s https://api.github.com/repos/XTLS/Xray-core/releases/latest 2>/dev/null | grep '"tag_name"' | sed 's/.*"v\([^"]*\)".*/\1/')

if [ -n "$LATEST" ] && [ "$CURRENT" != "$LATEST" ]; then
    echo "[$(date)] Доступно обновление Xray: v${CURRENT} -> v${LATEST}"
else
    echo "[$(date)] Xray v${CURRENT} — актуальная версия"
fi
SCRIPT

    chmod +x /opt/dem1chvpn/cron/*.sh

    # Установка crontab
    cat > /etc/cron.d/dem1chvpn << CRON
# Автоматические задачи Dem1chVPN
# Обновление гео-баз каждые 6 часов
0 */6 * * * root /opt/dem1chvpn/cron/update_geodata.sh >> /var/log/dem1chvpn/cron.log 2>&1
# Обновление антифильтра каждые 6 часов (со сдвигом 30 мин)
30 */6 * * * root /opt/dem1chvpn/cron/update_antifilter.sh >> /var/log/dem1chvpn/cron.log 2>&1
# Проверка здоровья каждые 5 минут
*/5 * * * * root /opt/dem1chvpn/cron/health_check.sh >> /var/log/dem1chvpn/health.log 2>&1
# Проверка доступности IP каждые 5 минут
*/5 * * * * root /opt/dem1chvpn/cron/ip_block_check.sh >> /var/log/dem1chvpn/ip_check.log 2>&1
# Ежедневный бэкап в 3:00
0 3 * * * root /opt/dem1chvpn/cron/backup.sh >> /var/log/dem1chvpn/backup.log 2>&1
# Обновление DuckDNS (если настроен)
*/5 * * * * root /opt/dem1chvpn/cron/update_duckdns.sh >> /var/log/dem1chvpn/duckdns.log 2>&1
# Проверка обновлений Xray (ежедневно в 4:00)
0 4 * * * root /opt/dem1chvpn/cron/check_xray_update.sh >> /var/log/dem1chvpn/cron.log 2>&1
CRON

    log_info "Cron-задачи настроены"
}

# ──── Шаг 9: Создание первого пользователя ────

create_first_user() {
    log_step "Шаг 9: Создание первого VPN-пользователя"

    set -a
    source "$ENV_FILE"
    set +a

    echo ""
    read -rp "$(echo -e "${PURPLE}Введите имя первого VPN-пользователя (например 'Админ'): ${NC}")" FIRST_USER_NAME
    FIRST_USER_NAME=${FIRST_USER_NAME:-Админ}

    # Создание пользователя через Python (heredoc — без конфликтов с bash)
    "${VENV_DIR}/bin/python" - "${FIRST_USER_NAME}" "${SUB_DOMAIN:-}" "${SUB_EXTERNAL_PORT:-8443}" <<'PYEOF' > /tmp/dem1chvpn_first_user 2>&1
import asyncio, sys
sys.path.insert(0, '/opt/dem1chvpn')
async def main():
    from server.bot.database import init_db
    from server.bot.services.user_manager import UserManager
    from server.bot.services.xray_config import XrayConfigManager
    await init_db()
    user = await UserManager().create_user(sys.argv[1])
    if not user:
        print('ERROR: failed')
        return
    xray = XrayConfigManager()
    await xray.add_client(user.uuid, user.email)
    vless = xray.generate_vless_url(user.uuid, user.name)
    sub = f'https://{sys.argv[2]}:{sys.argv[3]}/sub/{user.subscription_token}'

    print(f"USER_UUID='{user.uuid}'")
    print(f"USER_EMAIL='{user.email}'")
    print(f'VLESS_URL="{vless}"')
    print(f'SUB_URL="{sub}"')

asyncio.run(main())
PYEOF

    if grep -q "USER_UUID=" /tmp/dem1chvpn_first_user; then
        eval "$(cat /tmp/dem1chvpn_first_user)"
        log_info "Пользователь '${FIRST_USER_NAME}' создан"
        echo ""
        echo -e "  ${CYAN}VLESS-ссылка:${NC}"
        echo -e "  ${VLESS_URL}"
        echo ""
        echo -e "  ${CYAN}URL подписки:${NC}"
        echo -e "  ${SUB_URL}"
    else
        log_warn "Не удалось создать пользователя (можно создать через бота позже)"
        cat /tmp/dem1chvpn_first_user 2>/dev/null || true
    fi
    rm -f /tmp/dem1chvpn_first_user
}

# ──── Шаг 9.5: Добавление дефолтных правил маршрутизации ────

seed_default_routes() {
    log_step "Добавление правил маршрутизации для популярных сервисов"

    "${VENV_DIR}/bin/python" -c "
import asyncio, sys
sys.path.insert(0, '${DEM1CHVPN_DIR}')

# ═══ PROXY — сервисы для ускорения (вкл. мобильные приложения) ═══
PROXY_DOMAINS = [
    # --- AI-сервисы ---
    'openai.com', 'chat.openai.com', 'api.openai.com', 'chatgpt.com',
    'cdn.oaistatic.com', 'files.oaiusercontent.com',
    'claude.ai', 'anthropic.com', 'api.anthropic.com',
    'gemini.google.com', 'bard.google.com', 'notebooklm.google.com',
    'notebooklm-pa.googleapis.com', 'alkalimakersuite-pa.googleapis.com',
    'generativelanguage.googleapis.com', 'aistudio.google.com',
    'copilot.microsoft.com', 'perplexity.ai',

    # --- YouTube (сайт + мобильное приложение) ---
    'youtube.com', 'www.youtube.com', 'm.youtube.com',
    'googlevideo.com', 'ytimg.com', 'youtu.be',
    'youtube-nocookie.com', 'yt3.ggpht.com',
    'music.youtube.com', 'tv.youtube.com',

    # --- TikTok (все домены: сайт, приложение, DM видео, CDN) ---
    # Основные домены TikTok
    'tiktok.com', 'tiktokv.com', 'tiktokcdn.com', 'musical.ly',
    # Региональные CDN (видео в DM, стримы)
    'tiktokcdn-us.com', 'tiktokcdn-eu.com', 'ttcdn-us.com',
    'tiktokeu-cdn.com', 'tiktokrow-cdn.com',
    # DM-серверы и API
    'tiktokd.net', 'tiktokd.org', 'tiktok-row.net',
    'tik-tokapi.com', 'tiktok-minis.com',
    # Видео CDN и стримы
    'ttlivecdn.com', 'ttwstatic.com', 'ttoverseaus.net',
    'tiktokv.eu', 'tiktokv.us', 'tiktokw.eu', 'tiktokw.us',
    # ByteDance инфраструктура (CDN, API, SDK)
    'byteoversea.com', 'byteoversea.net',
    'ibytedtos.com', 'byteimg.com', 'ibyteimg.com',
    'bytecdn.com', 'bytegecko.com', 'bytedance.com',
    'muscdn.com', 'bytedapm.com',
    # SDK и аналитика
    'isnssdk.com', 'snssdk.com', 'pstatp.com',
    # Akamai CDN для TikTok
    'tiktokcdn.com.akamaized.net',
    'tiktokcdn-us.com.edgesuite.net',

    # --- Instagram / Facebook (мобильные API) ---
    'instagram.com', 'www.instagram.com', 'i.instagram.com',
    'graph.instagram.com', 'scontent.cdninstagram.com',
    'facebook.com', 'www.facebook.com', 'm.facebook.com',
    'graph.facebook.com', 'connect.facebook.net',

    # --- Twitter/X ---
    'twitter.com', 'x.com', 'api.twitter.com', 'api.x.com',
    'abs.twimg.com', 'pbs.twimg.com', 'mobile.twitter.com',

    # --- Telegram ---
    'telegram.org', 'web.telegram.org', 't.me',
    'core.telegram.org', 'api.telegram.org',

    # --- Discord ---
    'discord.com', 'discordapp.com', 'gateway.discord.gg',
    'cdn.discordapp.com', 'media.discordapp.net',

    # --- Spotify (сайт + приложение) ---
    'spotify.com', 'open.spotify.com', 'api.spotify.com',
    'apresolve.spotify.com', 'spclient.wg.spotify.com',
    'audio-ak-spotify-com.akamaized.net',

    # --- Прочие ---
    'medium.com', 'linkedin.com', 'www.linkedin.com',
    'notion.so', 'api.notion.com',
    'soundcloud.com', 'api-v2.soundcloud.com',
    'quora.com', 'reddit.com', 'www.reddit.com',
    'imgur.com', 'i.imgur.com',

    # --- Meta CDN (Instagram/Facebook приложения) ---
    'fbcdn.net', 'scontent.fbcdn.net', 'video.fbcdn.net',
    'static.cdninstagram.com', 'lookaside.fbsbx.com',
    'z-m-scontent.fbcdn.net',

    # --- Google (AI-сервисы приложения) ---
    'accounts.google.com', 'bard-google.appspot.com',
]

# ═══ DIRECT — сервисы РФ (блокируют зарубежные IP) ═══
DIRECT_DOMAINS = [
    # --- Банки (сайт + мобильные приложения + API) ---
    'sberbank.ru', 'sber.ru', 'sberbank.com',
    'online.sberbank.ru', 'api.sberbank.ru',
    'tinkoff.ru', 'tbank.ru', 'cdn-tinkoff.ru', 'tbank-online.com',
    'api.tinkoff.ru', 'id.tinkoff.ru', 'sso.tinkoff.ru',
    'vtb.ru', 'online.vtb.ru',
    'alfabank.ru', 'api.alfabank.ru', 'sense.alfabank.ru',
    'gazprombank.ru', 'gpb.ru', 'online.gazprombank.ru',
    'raiffeisen.ru', 'online.raiffeisen.ru',
    'sovcombank.ru', 'online.sovcombank.ru',
    'rosbank.ru', 'bankline.ru',
    'psbank.ru', 'online.psbank.ru',
    'uralsib.ru', 'mtsbank.ru', 'mkb.ru',
    'pochtabank.ru', 'open.ru', 'openbank.ru',
    'tochka.com', 'tochka-tech.com',
    'ozon.bank', 'rshb.ru', 'abr.ru',
    'homecredit.ru', 'otpbank.ru',
    'mtsdengi.ru', 'dbo-dengi.online',
    'nspk.ru', 'mir.ru',

    # --- VK Мессенджер + VK экосистема ---
    'vk.com', 'vk.ru', 'vk.me', 'vk.cc', 'vk.link',
    'vkmessenger.com', 'vkmessenger.app',
    'userapi.com', 'vk-cdn.net', 'vk-cdn.me', 'cdn-vk.ru',
    'vkuservideo.net', 'vkuservideo.com', 'vkuservideo.ru', 'vkvideo.ru',
    'vkuseraudio.net', 'vkuseraudio.com', 'vkuseraudio.ru',
    'vkuserphoto.ru', 'vkuser.net', 'vkusercdn.ru',
    'vkuserlive.net', 'vkcache.com',
    'vk-apps.com', 'vk-apps.ru', 'vkgo.app', 'vklive.app',
    'vkontakte.ru', 'vk-portal.net', 'mvk.com',

    # --- MAX + Mail.ru мессенджеры ---
    'max.ru', 'tamtam.chat', 'icq.com', 'vkteams.com',

    # --- Mail.ru + Одноклассники (приложения + CDN) ---
    'mail.ru', 'imgsmail.ru', 'mrgcdn.ru',
    'ok.ru', 'okcdn.ru', 'mycdn.me',
    'boosty.to', 'dzen.ru',

    # --- Яндекс (все сервисы + мобильные SDK) ---
    'yandex.ru', 'yandex.com', 'ya.ru', 'yandex.net', 'yastatic.net',
    'yandexcloud.net', 'yastat.net', 'admetrica.ru',
    'yandex.cloud', 'yandex-bank.net', 'turbopages.org',
    'passport.yandex.ru', 'mail.yandex.ru',
    'music.yandex.ru', 'market.yandex.ru',
    'disk.yandex.ru', 'cloud.yandex.ru',
    'taxi.yandex.ru', 'eda.yandex.ru',
    'lavka.yandex.ru', 'go.yandex.ru',
    'maps.yandex.ru', 'navigator.yandex.ru',
    'kinopoisk.ru', 'hd.kinopoisk.ru',
    'plus.yandex.ru', 'alice.yandex.ru',
    'appmetrica.yandex.ru', 'api.yandex.ru',
    'yandexmarket.ru',

    # --- Государство + налоги ---
    'gosuslugi.ru', 'esia.gosuslugi.ru', 'gu-st.ru',
    'nalog.ru', 'nalog.gov.ru',
    'government.ru', 'gov.ru',
    'mos.ru', 'emias.info',
    'cbr.ru', 'goskey.ru', 'pfr.gov.ru',

    # --- Операторы связи (сайт + приложения) ---
    'mts.ru', 'mymts.ru', 'login.mts.ru',
    'megafon.ru', 'lk.megafon.ru',
    'beeline.ru', 'my.beeline.ru',
    'tele2.ru', 't2.ru',
    'yota.ru', 'rostelecom.ru', 'rt.ru', 'dom.ru',

    # --- Маркетплейсы (сайт + CDN + приложения) ---
    'ozon.ru', 'api.ozon.ru',
    'wildberries.ru', 'wb.ru', 'wbstatic.net', 'wbbasket.ru', 'wbx-geo.ru',
    'avito.ru',
    'sbermegamarket.ru', 'kazanexpress.ru',
    'dns-shop.ru', 'mvideo.ru', 'eldorado.ru',
    'lamoda.ru', 'detmir.ru', 'leroymerlin.ru',
    '1c.ru',

    # --- Доставка и такси ---
    'delivery-club.ru', 'sbermarket.ru', 'samokat.ru',
    'magnit.ru', 'perekrestok.ru', 'lenta.com',
    'taxsee.com',

    # --- Развлечения (стриминг приложения) ---
    'ivi.ru', 'okko.tv', 'more.tv', 'wink.ru',
    'start.ru', 'premier.one', 'rutube.ru', 'litres.ru',

    # --- Транспорт, карты, доставка ---
    '2gis.ru', '2gis.com', 'rzd.ru', 'tutu.ru',
    'aviasales.ru', 'pochta.ru', 'cdek.ru',

    # --- Работа и HR ---
    'hh.ru', 'superjob.ru',

    # --- Недвижимость и авто ---
    'cian.ru', 'domclick.ru', 'auto.ru', 'drom.ru',

    # --- Прочие ---
    'rustore.ru', 'ngenix.net',
    'banki.ru', 'finuslugi.ru', 'sravni.ru',
    'moex.com', 'rbc.ru',
]

async def main():
    from server.bot.database import init_db
    from server.bot.services.route_manager import RouteManager

    await init_db()
    mgr = RouteManager()
    proxy_added = 0
    direct_added = 0
    for domain in PROXY_DOMAINS:
        if await mgr.add_rule(domain, 'proxy', 'install'):
            proxy_added += 1
    for domain in DIRECT_DOMAINS:
        if await mgr.add_rule(domain, 'direct', 'install'):
            direct_added += 1
    print(f'PROXY={proxy_added} DIRECT={direct_added}')

asyncio.run(main())
" > /tmp/dem1chvpn_routes 2>&1

    if grep -q "PROXY=" /tmp/dem1chvpn_routes; then
        eval "$(cat /tmp/dem1chvpn_routes)"
        log_info "Маршрутизация: ${PROXY} правил PROXY (ChatGPT, TikTok и др.) + ${DIRECT} правил DIRECT (банки, Яндекс)"
    else
        log_warn "Не удалось добавить правила (можно добавить через бота)"
    fi
    rm -f /tmp/dem1chvpn_routes
}

# ──── Шаг 10: Итоговая сводка ────

show_summary() {
    set -a
    source "$ENV_FILE"
    set +a

    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  🛡️  Установка Dem1chVPN завершена!${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "  ${CYAN}IP сервера:${NC}      ${SERVER_IP}"
    echo -e "  ${CYAN}Порт Xray:${NC}       443 (VLESS + Reality)"
    echo -e "  ${CYAN}SNI:${NC}             ${REALITY_SNI}"
    echo -e "  ${CYAN}Публичный ключ:${NC}  ${REALITY_PUBLIC_KEY}"
    echo -e "  ${CYAN}Short ID:${NC}        ${REALITY_SHORT_ID}"
    echo ""
    echo -e "  ${CYAN}Подписка:${NC}        https://${SUB_DOMAIN}:8443/sub/<токен>"
    echo -e "  ${CYAN}Mini App:${NC}        https://${SUB_DOMAIN}:8443/webapp/"
    echo ""
    echo -e "  ${CYAN}Токен бота:${NC}      ${BOT_TOKEN:0:10}..."
    echo -e "  ${CYAN}ID админа:${NC}       ${ADMIN_IDS}"
    echo ""
    echo -e "  ${YELLOW}Статус сервисов:${NC}"
    echo -e "    Xray:            $(systemctl is-active xray)"
    echo -e "    Бот:             $(systemctl is-active dem1chvpn-bot)"
    echo -e "    Подписки:        $(systemctl is-active dem1chvpn-sub)"
    echo -e "    Caddy:           $(systemctl is-active caddy)"
    echo ""
    echo -e "  ${YELLOW}Полезные команды:${NC}"
    echo -e "    journalctl -u dem1chvpn-bot -f    # Логи бота"
    echo -e "    journalctl -u xray -f              # Логи Xray"
    echo -e "    systemctl restart dem1chvpn-bot    # Перезапуск бота"
    echo -e "    systemctl restart xray              # Перезапуск Xray"
    echo ""
    echo -e "  ${GREEN}🤖 Откройте Telegram и отправьте /start вашему боту!${NC}"
    echo ""
}

# ──── Главная функция ────

main() {
    clear
    echo -e "${BLUE}"
    echo "  ╔═══════════════════════════════════════╗"
    echo "  ║   🛡️  Dem1chVPN — Установщик v1.1     ║"
    echo "  ║   VLESS + Reality + Telegram Bot      ║"
    echo "  ╚═══════════════════════════════════════╝"
    echo -e "${NC}"

    check_root
    check_os

    # Копирование/клонирование проекта если ещё не на месте
    if [ ! -d "${DEM1CHVPN_DIR}/server" ]; then
        mkdir -p "$DEM1CHVPN_DIR"
        SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
        if [ -d "${SCRIPT_DIR}/server" ]; then
            # Запуск из локальной копии — копируем файлы
            log_info "Копирую файлы проекта из ${SCRIPT_DIR}..."
            cp -r "${SCRIPT_DIR}/"* "$DEM1CHVPN_DIR/" 2>/dev/null || true
        else
            # Запуск через curl — клонируем из git
            log_info "Клонирую Dem1chVPN из GitHub..."
            git clone https://github.com/HotFies/Dem1chVPN.git "${DEM1CHVPN_DIR}" || {
                log_error "Не удалось клонировать репозиторий. Запустите скрипт из каталога проекта."
                exit 1
            }
        fi
    else
        log_info "Файлы проекта уже на месте в ${DEM1CHVPN_DIR}"
    fi

    mkdir -p "${DEM1CHVPN_DIR}/cron"

    install_dependencies
    harden_system
    free_ports                   # Остановить nginx/apache2 и освободить порты
    install_xray
    configure_xray
    install_bot
    install_caddy
    build_webapp || true         # Необязательно — Mini App можно собрать позже
    setup_warp || {
        log_warn "WARP не установился с первой попытки, повтор через 10 сек..."
        sleep 10
        setup_warp || {
            log_error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            log_error "WARP НЕ УСТАНОВЛЕН! Это обязательный компонент."
            log_error "Без WARP YouTube, Discord, AI-сервисы работать не будут!"
            log_error "Установите вручную: bash /opt/dem1chvpn/server/warp/setup.sh"
            log_error "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            # Не прерываем установку, но ясно сообщаем что это критично
        }
    }
    create_services
    setup_cron
    create_first_user || true    # Пользователя можно создать через бота
    seed_default_routes || true  # Правила маршрутизации

    # Sudoers для dem1chvpn — позволяет боту перезапускать сервисы и обновлять Xray
    log_info "Настраиваю sudoers для dem1chvpn..."
    cat > /etc/sudoers.d/dem1chvpn << 'SUDOERS'
# Dem1chVPN — allow bot user to manage services
dem1chvpn ALL=(root) NOPASSWD: /bin/bash /tmp/xray_install.sh
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/bash /tmp/xray_install.sh
dem1chvpn ALL=(root) NOPASSWD: /bin/bash /opt/dem1chvpn/cron/*
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/bash /opt/dem1chvpn/cron/*
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/systemctl restart xray
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/systemctl restart caddy
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/systemctl restart dem1chvpn-bot
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/systemctl restart dem1chvpn-sub
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/systemctl is-active *
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/docker *
dem1chvpn ALL=(root) NOPASSWD: /usr/bin/docker-compose *
dem1chvpn ALL=(root) NOPASSWD: /usr/local/bin/docker-compose *
SUDOERS
    chmod 440 /etc/sudoers.d/dem1chvpn
    visudo -c -f /etc/sudoers.d/dem1chvpn && log_info "sudoers OK" || {
        log_warn "sudoers невалиден, удаляю"
        rm -f /etc/sudoers.d/dem1chvpn
    }

    # Опциональные компоненты (запрос у пользователя)
    echo ""
    read -rp "$(echo -e "${PURPLE}Установить MTProto Proxy? (y/n): ${NC}")" INSTALL_MTPROTO
    if [[ "$INSTALL_MTPROTO" =~ ^[Yy]$ ]]; then
        if setup_mtproto; then
            # Включить MTProto в конфигурации
            sed -i 's/^MTPROTO_ENABLED=false/MTPROTO_ENABLED=true/' "$ENV_FILE" 2>/dev/null || true
            grep -q '^MTPROTO_ENABLED=' "$ENV_FILE" || echo 'MTPROTO_ENABLED=true' >> "$ENV_FILE"
            log_info "MTProto включён в конфигурации"
            # Убедимся, что контейнер запущен
            if docker inspect -f '{{.State.Running}}' dem1chvpn-mtproto 2>/dev/null | grep -q true; then
                log_info "MTProto контейнер работает ✓"
            else
                log_warn "MTProto контейнер не запустился, запускаю..."
                if (cd "${DEM1CHVPN_DIR}/server/mtproto" && docker compose up -d); then
                    log_info "MTProto запущен ✓"
                else
                    log_warn "MTProto не удалось запустить"
                fi
            fi
        else
            log_warn "MTProto не установлен (можно позже)"
        fi
    fi

    read -rp "$(echo -e "${PURPLE}Установить AdGuard Home (блокировка рекламы)? (y/n): ${NC}")" INSTALL_ADGUARD
    if [[ "$INSTALL_ADGUARD" =~ ^[Yy]$ ]]; then
        if setup_adguard; then
            # Включить AdGuard в конфигурации
            sed -i 's/^ADGUARD_ENABLED=false/ADGUARD_ENABLED=true/' "$ENV_FILE" 2>/dev/null || true
            grep -q '^ADGUARD_ENABLED=' "$ENV_FILE" || echo 'ADGUARD_ENABLED=true' >> "$ENV_FILE"
            log_info "AdGuard Home включён в конфигурации"
            # Убедимся, что контейнер запущен
            if docker inspect -f '{{.State.Running}}' dem1chvpn-adguard 2>/dev/null | grep -q true; then
                log_info "AdGuard контейнер работает ✓"
            else
                log_warn "AdGuard контейнер не запустился, запускаю..."
                if (cd "${DEM1CHVPN_DIR}/server/adguard" && docker compose up -d); then
                    log_info "AdGuard запущен ✓"
                else
                    log_warn "AdGuard не удалось запустить"
                fi
            fi
        else
            log_warn "AdGuard не установлен (можно позже)"
        fi
    fi

    # Перезапустить сервисы, чтобы подхватить новые значения .env
    if [[ "$INSTALL_MTPROTO" =~ ^[Yy]$ ]] || [[ "$INSTALL_ADGUARD" =~ ^[Yy]$ ]]; then
        log_info "Перезапускаю сервисы для применения конфигурации..."
        systemctl restart dem1chvpn-bot 2>/dev/null || true
        systemctl restart dem1chvpn-sub 2>/dev/null || true
        log_info "Сервисы перезапущены ✓"
    fi

    show_summary
}

main "$@"

