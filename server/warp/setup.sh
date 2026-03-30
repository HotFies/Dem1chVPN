#!/usr/bin/env bash
# Cloudflare WARP Setup for XShield (Double-Hop Privacy)
# Adds WireGuard outbound to Xray config
set -euo pipefail

source /opt/xshield/.env

echo "☁️ Setting up Cloudflare WARP..."

# Install wgcf (WARP credential generator)
ARCH=$(uname -m)
case $ARCH in
    x86_64) WGCF_ARCH="amd64" ;;
    aarch64) WGCF_ARCH="arm64" ;;
    *) echo "Unsupported arch: $ARCH"; exit 1 ;;
esac

wget -qO /usr/local/bin/wgcf \
    "https://github.com/ViRb3/wgcf/releases/latest/download/wgcf_linux_${WGCF_ARCH}"
chmod +x /usr/local/bin/wgcf

# Register WARP account
cd /opt/xshield/server/warp

if [ ! -f wgcf-account.toml ]; then
    wgcf register --accept-tos
    echo "✅ WARP account registered"
fi

# Generate WireGuard config
wgcf generate
echo "✅ WireGuard config generated"

# Parse WireGuard config
WG_PRIVATE_KEY=$(grep "PrivateKey" wgcf-profile.conf | awk '{print $3}')
WG_ADDRESS_V4=$(grep "Address" wgcf-profile.conf | head -1 | awk '{print $3}')
WG_ADDRESS_V6=$(grep "Address" wgcf-profile.conf | tail -1 | awk '{print $3}')
WG_PUBLIC_KEY=$(grep "PublicKey" wgcf-profile.conf | awk '{print $3}')
WG_ENDPOINT=$(grep "Endpoint" wgcf-profile.conf | awk '{print $3}')

# Create Xray WARP outbound config
cat > /opt/xshield/server/warp/warp_config.json << JSON
{
    "tag": "warp",
    "protocol": "wireguard",
    "settings": {
        "secretKey": "${WG_PRIVATE_KEY}",
        "address": ["${WG_ADDRESS_V4}", "${WG_ADDRESS_V6}"],
        "peers": [
            {
                "publicKey": "${WG_PUBLIC_KEY}",
                "allowedIPs": ["0.0.0.0/0", "::/0"],
                "endpoint": "${WG_ENDPOINT}"
            }
        ],
        "reserved": [0, 0, 0],
        "mtu": 1280
    }
}
JSON

# Add WARP outbound to Xray config
python3 << 'PYTHON'
import json

config_path = "/usr/local/etc/xray/config.json"
warp_path = "/opt/xshield/server/warp/warp_config.json"

with open(config_path) as f:
    cfg = json.load(f)

with open(warp_path) as f:
    warp_outbound = json.load(f)

# Remove old WARP outbound if exists
cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

# Add WARP outbound
cfg["outbounds"].append(warp_outbound)

# Add routing rule for streaming domains via WARP
warp_rule = {
    "type": "field",
    "outboundTag": "warp",
    "domain": [
        "domain:netflix.com", "domain:nflxvideo.net",
        "domain:disneyplus.com", "domain:disney.com",
        "domain:hulu.com", "domain:spotify.com",
        "domain:deezer.com",
    ]
}

# Insert WARP rule before the last catch-all rule
rules = cfg.get("routing", {}).get("rules", [])
# Add after API rule but before blocking rules
rules.insert(2, warp_rule)
cfg["routing"]["rules"] = rules

with open(config_path, "w") as f:
    json.dump(cfg, f, indent=2)

print("✅ WARP outbound added to Xray config")
print("   Streaming domains routed through Cloudflare WARP")
PYTHON

systemctl restart xray

# Update .env
sed -i 's/WARP_ENABLED=false/WARP_ENABLED=true/' /opt/xshield/.env

echo "☁️ WARP Double-Hop setup complete!"
echo "   Private Key: ${WG_PRIVATE_KEY:0:20}..."
echo "   Endpoint: ${WG_ENDPOINT}"
echo "   Streaming traffic → Cloudflare WARP → Internet"
