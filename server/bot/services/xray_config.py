"""
Dem1chVPN — Xray Config Manager
Manages Xray configuration file and generates VLESS URLs.
"""
import json
import logging
import subprocess
import urllib.parse
from pathlib import Path
from typing import Optional

from ..config import config

logger = logging.getLogger("dem1chvpn.xray_config")


class XrayConfigManager:
    """Manages Xray JSON config and generates client URLs."""

    def __init__(self):
        self.config_path = Path(config.XRAY_CONFIG_PATH)

    def _read_config(self) -> dict:
        """Read Xray config file."""
        with open(self.config_path, "r") as f:
            return json.load(f)

    def _write_config(self, cfg: dict):
        """Write Xray config file and reload Xray."""
        with open(self.config_path, "w") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)

    async def add_client(self, uuid: str, email: str) -> bool:
        """Add a client to Xray config."""
        try:
            cfg = self._read_config()
            for inbound in cfg.get("inbounds", []):
                if inbound.get("tag") == config.XRAY_INBOUND_TAG:
                    clients = inbound.get("settings", {}).get("clients", [])
                    # Check if already exists
                    if any(c.get("id") == uuid for c in clients):
                        return True
                    clients.append({
                        "id": uuid,
                        "email": email,
                        "flow": "xtls-rprx-vision",
                    })
                    inbound["settings"]["clients"] = clients
                    break

            self._write_config(cfg)
            await self.reload_xray()
            return True
        except Exception as e:
            logger.error(f"Error adding client: {e}")
            return False

    async def remove_client(self, email: str) -> bool:
        """Remove a client from Xray config by email."""
        try:
            cfg = self._read_config()
            for inbound in cfg.get("inbounds", []):
                if inbound.get("tag") == config.XRAY_INBOUND_TAG:
                    clients = inbound.get("settings", {}).get("clients", [])
                    inbound["settings"]["clients"] = [
                        c for c in clients if c.get("email") != email
                    ]
                    break

            self._write_config(cfg)
            await self.reload_xray()
            return True
        except Exception as e:
            logger.error(f"Error removing client: {e}")
            return False

    async def get_clients(self) -> list[dict]:
        """Get list of all clients from config."""
        try:
            cfg = self._read_config()
            for inbound in cfg.get("inbounds", []):
                if inbound.get("tag") == config.XRAY_INBOUND_TAG:
                    return inbound.get("settings", {}).get("clients", [])
            return []
        except Exception:
            return []

    def generate_vless_url(self, uuid: str, remark: str = "Dem1chVPN") -> str:
        """Generate a VLESS connection URL."""
        params = {
            "encryption": "none",
            "security": "reality",
            "sni": config.REALITY_SNI,
            "fp": "random",
            "pbk": config.REALITY_PUBLIC_KEY,
            "sid": config.REALITY_SHORT_ID,
            "type": "tcp",
            "flow": "xtls-rprx-vision",
        }

        query = urllib.parse.urlencode(params)
        encoded_remark = urllib.parse.quote(f"🛡️ {remark}")

        return (
            f"vless://{uuid}@{config.SERVER_IP}:{config.SERVER_PORT}"
            f"?{query}#{encoded_remark}"
        )

    async def reload_xray(self):
        """Reload Xray service."""
        import asyncio
        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "restart", "xray",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            if proc.returncode != 0:
                logger.error(f"Error restarting Xray: {stderr.decode()}")
        except asyncio.TimeoutError:
            logger.error("Error restarting Xray: timeout")
        except Exception as e:
            logger.error(f"Error restarting Xray: {e}")

    async def get_xray_version(self) -> str:
        """Get Xray-core version."""
        import asyncio
        try:
            proc = await asyncio.create_subprocess_exec(
                config.XRAY_BINARY, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            first_line = stdout.decode().strip().split("\n")[0]
            return first_line.split(" ")[1] if " " in first_line else "unknown"
        except Exception:
            return "unknown"

    async def is_xray_running(self) -> bool:
        """Check if Xray service is running."""
        import asyncio
        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "is-active", "xray",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            return stdout.decode().strip() == "active"
        except Exception:
            return False

    def update_reality_settings(
        self,
        dest: Optional[str] = None,
        sni: Optional[str] = None,
        private_key: Optional[str] = None,
        short_id: Optional[str] = None,
    ):
        """Update Reality settings in config."""
        cfg = self._read_config()
        for inbound in cfg.get("inbounds", []):
            if inbound.get("tag") == config.XRAY_INBOUND_TAG:
                reality = inbound.get("streamSettings", {}).get("realitySettings", {})
                if dest:
                    reality["dest"] = dest
                if sni:
                    reality["serverNames"] = [sni]
                if private_key:
                    reality["privateKey"] = private_key
                if short_id:
                    reality["shortIds"] = [short_id]
                break
        self._write_config(cfg)
