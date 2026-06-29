"""
Dem1chVPN — Сервис управления WARP
Использует warp-svc в режиме SOCKS5 (127.0.0.1:40000).
Роутинг: сайты РФ → direct, зарубежный трафик → WARP.
"""
import json
import asyncio
import logging
from pathlib import Path
from ..config import config
from .xray_config import XrayConfigManager

logger = logging.getLogger("dem1chvpn.warp")

# Дефолтный порт SOCKS5 для warp-svc
WARP_SOCKS_PORT = 40000


class WarpManager:


    def __init__(self):
        self.xray_config_path = Path(config.XRAY_CONFIG_PATH)
        # тот же конфиг, что и у XrayConfigManager — пишем под общим локом и атомарно
        self._xray = XrayConfigManager()

    def is_enabled(self) -> bool:

        try:
            cfg = self._read_config()
            return any(o.get("tag") == "warp" for o in cfg.get("outbounds", []))
        except Exception:
            return False

    def is_installed(self) -> bool:

        import shutil
        return shutil.which("warp-cli") is not None

    async def enable(self) -> bool:

        if not self.is_installed():
            logger.warning("WARP enable: warp-cli не установлен")
            return False

        try:
            async with self._xray._write_lock:
                cfg = await self._xray._aread_config()

                outbounds = cfg.setdefault("outbounds", [])
                cfg["outbounds"] = [o for o in outbounds if o.get("tag") != "warp"]
                cfg["outbounds"].append({
                    "tag": "warp",
                    "protocol": "socks",
                    "settings": {
                        "servers": [{"address": "127.0.0.1", "port": WARP_SOCKS_PORT}]
                    },
                })

                routing = cfg.setdefault("routing", {})
                rules = [r for r in routing.get("rules", []) if r.get("outboundTag") != "warp"]

                # DNS летит direct (SOCKS5 не проксирует UDP)
                has_dns_direct = any(
                    r.get("port") == "53" and r.get("outboundTag") == "direct"
                    for r in rules
                )
                if not has_dns_direct:
                    rules.append({"type": "field", "outboundTag": "direct", "port": "53"})

                # Замыкающее правило: весь TCP летит в WARP
                rules.append({"type": "field", "outboundTag": "warp", "network": "tcp"})
                routing["rules"] = rules

                await self._xray._awrite_config(cfg)

            await self._ensure_warp_connected()
            await self._xray.reload_xray()
            return True
        except Exception as e:
            logger.error(f"WARP enable failed: {e}")
            return False

    async def disable(self) -> bool:

        try:
            async with self._xray._write_lock:
                cfg = await self._xray._aread_config()
                cfg["outbounds"] = [o for o in cfg.get("outbounds", []) if o.get("tag") != "warp"]

                routing = cfg.get("routing")
                if routing and "rules" in routing:
                    routing["rules"] = [
                        r for r in routing["rules"] if r.get("outboundTag") != "warp"
                    ]

                await self._xray._awrite_config(cfg)

            await self._xray.reload_xray()
            return True
        except Exception as e:
            logger.error(f"WARP disable failed: {e}")
            return False

    async def toggle(self) -> bool:

        if self.is_enabled():
            await self.disable()
        else:
            await self.enable()
        return self.is_enabled()

    async def get_warp_ip(self) -> str:

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
