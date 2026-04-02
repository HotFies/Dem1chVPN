"""
Dem1chVPN — WARP Manager Service
Toggle Cloudflare WARP on/off.
Supports native WireGuard outbound (no SOCKS5 overhead).
Routing strategy: RU sites → direct, ALL foreign traffic → WARP.
"""
import json
import asyncio
from pathlib import Path
from ..config import config


class WarpManager:
    """Manages Cloudflare WARP outbound in Xray (native WireGuard)."""

    def __init__(self):
        self.xray_config_path = Path(config.XRAY_CONFIG_PATH)
        self.warp_keys_path = Path("/opt/dem1chvpn/data/warp_wireguard.json")

    def is_enabled(self) -> bool:
        """Check if WARP outbound exists in Xray config."""
        try:
            cfg = self._read_config()
            return any(o.get("tag") == "warp" for o in cfg.get("outbounds", []))
        except Exception:
            return False

    def is_installed(self) -> bool:
        """Check if WARP WireGuard keys exist."""
        return self.warp_keys_path.exists()

    async def enable(self) -> bool:
        """Add WARP WireGuard outbound to Xray config and ensure routing rules exist."""
        if not self.is_installed():
            return False

        try:
            cfg = self._read_config()

            # Load WireGuard keys
            with open(self.warp_keys_path) as f:
                warp_keys = json.load(f)

            # Remove existing WARP outbound
            cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

            # Add WireGuard outbound
            warp_outbound = {
                "tag": "warp",
                "protocol": "wireguard",
                "settings": {
                    "secretKey": warp_keys["private_key"],
                    "address": [
                        warp_keys.get("address_v4", "172.16.0.2/32"),
                        warp_keys.get("address_v6", "fd01:db8:1111::2/128"),
                    ],
                    "peers": [
                        {
                            "publicKey": warp_keys.get(
                                "peer_public_key",
                                "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo7+J23rXt0Q=",
                            ),
                            "endpoint": warp_keys.get(
                                "endpoint", "engage.cloudflareclient.com:2408"
                            ),
                        }
                    ],
                    "mtu": 1280,
                    "reserved": warp_keys.get("reserved", [0, 0, 0]),
                },
            }
            cfg["outbounds"].append(warp_outbound)

            # Ensure WARP catch-all routing rule exists at the end
            # Strategy: RU sites → direct (already in config), everything else → WARP
            rules = cfg.get("routing", {}).get("rules", [])
            has_warp_rule = any(r.get("outboundTag") == "warp" for r in rules)
            if not has_warp_rule:
                warp_catchall = {
                    "type": "field",
                    "outboundTag": "warp",
                    "network": "tcp,udp",
                }
                # Append at the end — after all direct/blocked rules
                rules.append(warp_catchall)
                cfg["routing"]["rules"] = rules

            self._write_config(cfg)
            await self._restart_xray()
            return True
        except Exception:
            return False

    async def disable(self) -> bool:
        """Remove WARP outbound from Xray config."""
        try:
            cfg = self._read_config()
            cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

            # Also remove routing rules pointing to WARP
            if "routing" in cfg:
                cfg["routing"]["rules"] = [
                    r for r in cfg["routing"]["rules"]
                    if r.get("outboundTag") != "warp"
                ]

            self._write_config(cfg)
            await self._restart_xray()
            return True
        except Exception:
            return False

    async def toggle(self) -> bool:
        """Toggle WARP status. Returns new state (True=enabled)."""
        if self.is_enabled():
            await self.disable()
            return False
        else:
            await self.enable()
            return True

    async def get_warp_ip(self) -> str:
        """Get current WARP exit IP by testing through Xray's WARP outbound.

        Since WARP uses native WireGuard in Xray (not a system wg0 interface),
        we test via a temporary SOCKS proxy or by checking Xray logs.
        Fallback: read from stored WARP config.
        """
        try:
            # Try via warp-cli if still installed
            proc = await asyncio.create_subprocess_exec(
                "warp-cli", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            output = stdout.decode().strip()
            # Try to extract IP from status
            for line in output.split("\n"):
                if "endpoint" in line.lower() or "ip" in line.lower():
                    return line.split(":")[-1].strip() or "warp-active"
            if "connected" in output.lower():
                return "warp-active"
        except Exception:
            pass

        # Fallback: check if WireGuard outbound exists
        if self.is_enabled():
            return "warp-wireguard"
        return "unknown"

    def _read_config(self) -> dict:
        with open(self.xray_config_path) as f:
            return json.load(f)

    def _write_config(self, cfg: dict):
        with open(self.xray_config_path, "w") as f:
            json.dump(cfg, f, indent=2)

    async def _restart_xray(self):
        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "restart", "xray",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=10)
        except Exception:
            pass
