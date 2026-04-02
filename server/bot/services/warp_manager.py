"""
Dem1chVPN — WARP Manager Service
Toggle Cloudflare WARP on/off.
Uses warp-svc in SOCKS5 proxy mode (127.0.0.1:40000).
Routing strategy: RU sites → direct, ALL foreign traffic → WARP.
"""
import json
import asyncio
from pathlib import Path
from ..config import config


# Default SOCKS5 port for warp-svc proxy mode
WARP_SOCKS_PORT = 40000


class WarpManager:
    """Manages Cloudflare WARP outbound in Xray (SOCKS5 proxy)."""

    def __init__(self):
        self.xray_config_path = Path(config.XRAY_CONFIG_PATH)

    def is_enabled(self) -> bool:
        """Check if WARP outbound exists in Xray config."""
        try:
            cfg = self._read_config()
            return any(o.get("tag") == "warp" for o in cfg.get("outbounds", []))
        except Exception:
            return False

    def is_installed(self) -> bool:
        """Check if warp-cli is installed."""
        import shutil
        return shutil.which("warp-cli") is not None

    async def enable(self) -> bool:
        """Add WARP SOCKS5 outbound to Xray config and set catch-all routing."""
        if not self.is_installed():
            return False

        try:
            cfg = self._read_config()

            # Remove existing WARP outbound
            cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

            # Add SOCKS5 outbound (connects to local warp-svc)
            warp_outbound = {
                "tag": "warp",
                "protocol": "socks",
                "settings": {
                    "servers": [
                        {
                            "address": "127.0.0.1",
                            "port": WARP_SOCKS_PORT,
                        }
                    ]
                },
            }
            cfg["outbounds"].append(warp_outbound)

            # Ensure WARP catch-all routing rule exists at the end
            # Strategy: RU sites → direct (already in config), everything else → WARP
            rules = cfg.get("routing", {}).get("rules", [])
            # Remove old WARP rules
            rules = [r for r in rules if r.get("outboundTag") != "warp"]

            # DNS must go direct (SOCKS5 can't proxy UDP)
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

            # Add catch-all TCP at the end (UDP handled by DNS-direct + QUIC-block)
            rules.append({
                "type": "field",
                "outboundTag": "warp",
                "network": "tcp",
            })
            cfg["routing"]["rules"] = rules

            self._write_config(cfg)

            # Ensure warp-svc is connected
            await self._ensure_warp_connected()

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
        """Get current WARP exit IP."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "warp-cli", "status",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            output = stdout.decode().strip()
            if "connected" in output.lower():
                return "warp-connected"
            return output.split("\n")[0] if output else "unknown"
        except Exception:
            pass

        if self.is_enabled():
            return "warp-socks5"
        return "unknown"

    async def _ensure_warp_connected(self):
        """Make sure warp-svc is running and connected."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "warp-cli", "connect",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await asyncio.wait_for(proc.communicate(), timeout=10)
        except Exception:
            pass

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
