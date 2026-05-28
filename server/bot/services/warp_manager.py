"""
Dem1chVPN — Сервис управления WARP
Использует warp-svc в режиме SOCKS5 (127.0.0.1:40000).
Роутинг: сайты РФ → direct, зарубежный трафик → WARP.
"""
import json
import asyncio
from pathlib import Path
from ..config import config


# Дефолтный порт SOCKS5 для warp-svc
WARP_SOCKS_PORT = 40000


class WarpManager:


    def __init__(self):
        self.xray_config_path = Path(config.XRAY_CONFIG_PATH)

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
            return False

        try:
            cfg = self._read_config()

            # Сносим старый WARP аутбаунд
            cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

            # Добавляем SOCKS5, который смотрит на локальный warp-svc
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

            # Прокидываем все неопознанное в WARP, кроме сайтов РФ (direct)
            rules = cfg.get("routing", {}).get("rules", [])
            # Сносим старые правила WARP
            rules = [r for r in rules if r.get("outboundTag") != "warp"]

            # DNS летит direct (SOCKS5 не проксирует UDP)
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

            # Замыкающее правило: весь TCP летит в WARP
            rules.append({
                "type": "field",
                "outboundTag": "warp",
                "network": "tcp",
            })
            cfg["routing"]["rules"] = rules

            self._write_config(cfg)

            # Пинаем warp-svc, чтобы точно был подключен
            await self._ensure_warp_connected()

            await self._restart_xray()
            return True
        except Exception:
            return False

    async def disable(self) -> bool:

        try:
            cfg = self._read_config()
            cfg["outbounds"] = [o for o in cfg["outbounds"] if o.get("tag") != "warp"]

            # Вычищаем роуты, которые ссылаются на WARP
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

        if self.is_enabled():
            await self.disable()
            return False
        else:
            await self.enable()
            return True

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
