"""
Dem1chVPN — WARP Manager Service
Toggle Cloudflare WARP on/off.
"""
import json
import asyncio
from pathlib import Path
from ..config import config


class WarpManager:
    """Manages Cloudflare WARP double-hop."""

    def __init__(self):
        self.xray_config_path = Path(config.XRAY_CONFIG_PATH)
        self.warp_config_path = Path("/opt/dem1chvpn/server/warp/warp_config.json")

    def is_enabled(self) -> bool:
        """Check if WARP outbound exists in Xray config."""
        try:
            cfg = self._read_config()
            return any(o.get("tag") == "warp" for o in cfg.get("outbounds", []))
        except Exception:
            return False

    def is_installed(self) -> bool:
        """Check if WARP config exists."""
        return self.warp_config_path.exists()

    async def enable(self) -> bool:
        """Add WARP outbound to Xray config and ensure routing rules exist."""
        if not self.is_installed():
            return False

        try:
            cfg = self._read_config()

            # Remove existing WARP outbound
            cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

            # Add WARP outbound
            with open(self.warp_config_path) as f:
                warp = json.load(f)
            cfg["outbounds"].append(warp)

            # Ensure WARP routing rules exist
            rules = cfg.get("routing", {}).get("rules", [])
            has_warp_rule = any(r.get("outboundTag") == "warp" for r in rules)
            if not has_warp_rule:
                warp_rule = {
                    "type": "field",
                    "outboundTag": "warp",
                    "domain": [
                        "domain:notebooklm.google.com",
                        "domain:notebooklm-pa.googleapis.com",
                        "domain:aistudio.google.com",
                        "domain:generativelanguage.googleapis.com",
                    ]
                }
                # Insert after API rule
                api_idx = next(
                    (i for i, r in enumerate(rules) if r.get("inboundTag") == ["api"]),
                    0
                )
                rules.insert(api_idx + 1, warp_rule)
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
        """Get current WARP exit IP."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "curl", "-s", "--max-time", "5",
                "--interface", "wg0", "https://ifconfig.me",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            return stdout.decode().strip() or "unknown"
        except Exception:
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
