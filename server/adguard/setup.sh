#!/usr/bin/env bash
# AdGuard Home Setup for XShield
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source /opt/xshield/.env

echo "🛡️ Setting up AdGuard Home..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Disable systemd-resolved if it occupies port 53
if systemctl is-active --quiet systemd-resolved; then
    echo "Disabling systemd-resolved..."
    systemctl stop systemd-resolved
    systemctl disable systemd-resolved
    rm -f /etc/resolv.conf
    echo "nameserver 8.8.8.8" > /etc/resolv.conf
fi

# Create directories
mkdir -p "${SCRIPT_DIR}/work" "${SCRIPT_DIR}/conf"

# Start container
cd "$SCRIPT_DIR"
docker compose up -d

# Wait for AdGuard to start
sleep 5

# Auto-configure via API (initial setup)
curl -s -X POST "http://127.0.0.1:3000/control/install/configure" \
    -H "Content-Type: application/json" \
    -d '{
        "web": {"ip": "127.0.0.1", "port": 8053},
        "dns": {"ip": "127.0.0.1", "port": 53},
        "username": "admin",
        "password": "xshield"
    }' 2>/dev/null || true

# Configure upstream DNS (DNS-over-HTTPS)
sleep 2
curl -s -X POST "http://127.0.0.1:8053/control/dns_config" \
    -u "admin:xshield" \
    -H "Content-Type: application/json" \
    -d '{
        "upstream_dns": [
            "https://dns.google/dns-query",
            "https://cloudflare-dns.com/dns-query"
        ],
        "bootstrap_dns": ["8.8.8.8", "1.1.1.1"],
        "protection_enabled": true,
        "blocking_mode": "default"
    }' 2>/dev/null || true

# Add filter lists
for url in \
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_1.txt" \
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_2.txt" \
    "https://adguardteam.github.io/HostlistsRegistry/assets/filter_24.txt"; do
    curl -s -X POST "http://127.0.0.1:8053/control/filtering/add_url" \
        -u "admin:xshield" \
        -H "Content-Type: application/json" \
        -d "{\"name\": \"$(basename $url)\", \"url\": \"$url\", \"enabled\": true}" \
        2>/dev/null || true
done

# Update Xray DNS to use AdGuard
python3 << 'PYTHON'
import json
config_path = "/usr/local/etc/xray/config.json"
with open(config_path) as f:
    cfg = json.load(f)

cfg["dns"] = {
    "servers": [
        {"address": "127.0.0.1", "port": 5353},
        {"address": "https+local://dns.google/dns-query", "skipFallback": True}
    ],
    "queryStrategy": "UseIPv4"
}

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)
print("Xray DNS config updated to use AdGuard Home")
PYTHON

systemctl restart xray

# Update .env
if ! grep -q "ADGUARD_ENABLED=true" /opt/xshield/.env; then
    sed -i 's/ADGUARD_ENABLED=false/ADGUARD_ENABLED=true/' /opt/xshield/.env
fi

echo "✅ AdGuard Home installed"
echo "   DNS: 127.0.0.1:5353"
echo "   Admin: http://127.0.0.1:8053 (admin/xshield)"
echo "   Ad blocking: ACTIVE"
