#!/usr/bin/env bash
# MTProto Proxy Setup for XShield
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source /opt/xshield/.env

echo "🔧 Setting up MTProto Proxy..."

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    curl -fsSL https://get.docker.com | sh
    systemctl enable docker
    systemctl start docker
fi

# Install docker-compose plugin
apt install -y docker-compose-plugin 2>/dev/null || pip3 install docker-compose

# Generate MTProto secret
MTPROTO_SECRET=$(docker run --rm nineseconds/mtg:2 generate-secret tls -c www.microsoft.com 2>/dev/null || openssl rand -hex 16)

# Create config
cat > "${SCRIPT_DIR}/config.toml" << TOML
# mtg configuration
secret = "${MTPROTO_SECRET}"

[network]
bind-to = "0.0.0.0:8800"

[defense.anti-replay]
enabled = true
max-size = "128mib"

[stats]
enabled = false
TOML

# Start container
cd "$SCRIPT_DIR"
docker compose up -d

# Save secret to .env
if ! grep -q "MTPROTO_SECRET" /opt/xshield/.env; then
    echo "" >> /opt/xshield/.env
    echo "# MTProto Proxy" >> /opt/xshield/.env
    echo "MTPROTO_SECRET=${MTPROTO_SECRET}" >> /opt/xshield/.env
    echo "MTPROTO_ENABLED=true" >> /opt/xshield/.env
fi

echo "✅ MTProto Proxy started"
echo "   Secret: ${MTPROTO_SECRET}"
echo "   Port: 8800 (local), exposed via Xray fallback on 443"
echo ""
echo "   Telegram link:"
echo "   tg://proxy?server=${SERVER_IP}&port=443&secret=${MTPROTO_SECRET}"
