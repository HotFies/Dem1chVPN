"""
Dem1chVPN — Hysteria2 конфигуратор
"""
import asyncio
import logging
import urllib.parse
from pathlib import Path

import yaml

from ..config import config

logger = logging.getLogger("dem1chvpn.hysteria_config")


class HysteriaConfigManager:

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config_path = Path(config.HYSTERIA_CONFIG_PATH)
            # без него два параллельных add/remove перетрут друг друга
            cls._instance._write_lock = asyncio.Lock()
        return cls._instance

    def __init__(self):
        pass

    def _read_config(self) -> dict:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _write_config(self, cfg: dict):
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True, sort_keys=False)

    async def _aread_config(self) -> dict:
        return await asyncio.to_thread(self._read_config)

    async def _awrite_config(self, cfg: dict):
        await asyncio.to_thread(self._write_config, cfg)

    async def add_client(self, username: str, password: str) -> bool:
        if not config.HYSTERIA_ENABLED:
            return True
        async with self._write_lock:
            try:
                cfg = await self._aread_config()
                auth = cfg.setdefault("auth", {"type": "userpass"})
                # userpass у hysteria2 — словарь {username: password}
                users = auth.setdefault("userpass", {}) or {}
                users[username] = password
                auth["userpass"] = users
                await self._awrite_config(cfg)
                return await self.reload_hysteria()
            except Exception as e:
                logger.error(f"Error adding hysteria client: {e}")
                return False

    async def remove_client(self, username: str) -> bool:
        if not config.HYSTERIA_ENABLED:
            return True
        async with self._write_lock:
            try:
                cfg = await self._aread_config()
                users = cfg.get("auth", {}).get("userpass", {}) or {}
                if username in users:
                    users.pop(username)
                    cfg["auth"]["userpass"] = users
                    await self._awrite_config(cfg)
                    return await self.reload_hysteria()
                return True
            except Exception as e:
                logger.error(f"Error removing hysteria client: {e}")
                return False

    async def get_clients(self) -> list[str]:
        try:
            cfg = await self._aread_config()
            return list((cfg.get("auth", {}).get("userpass") or {}).keys())
        except Exception:
            return []

    def generate_hysteria_url(self, username: str, password: str, remark: str) -> str:
        # см. https://v2.hysteria.network/docs/developers/URI-Scheme/
        # без домена — IP-only, тогда insecure=1 (само-подписанный/нет TLS-валидации по hostname)
        host = config.HYSTERIA_DOMAIN or config.SERVER_IP
        insecure = "0" if config.HYSTERIA_DOMAIN else "1"
        auth = f"{urllib.parse.quote(username, safe='')}:{urllib.parse.quote(password, safe='')}"
        params = {
            "obfs": "salamander",
            "obfs-password": config.HYSTERIA_OBFS_PASSWORD,
            "sni": config.HYSTERIA_DOMAIN or config.SERVER_IP,
            "insecure": insecure,
        }
        query = urllib.parse.urlencode(params)
        encoded_remark = urllib.parse.quote(f"⚡ {remark}")
        return (
            f"hysteria2://{auth}@{host}:{config.HYSTERIA_PORT}"
            f"?{query}#{encoded_remark}"
        )

    async def reload_hysteria(self) -> bool:
        try:
            # -n чтобы sudo сразу падал без NOPASSWD, а не висел на вводе пароля
            proc = await asyncio.create_subprocess_exec(
                "sudo", "-n", "systemctl", "restart", "dem1chvpn-hysteria",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            _, stderr = await asyncio.wait_for(proc.communicate(), timeout=10)
            if proc.returncode != 0:
                logger.error(f"Error restarting Hysteria: {stderr.decode()}")
                return False
            return True
        except asyncio.TimeoutError:
            logger.error("Error restarting Hysteria: timeout")
            return False
        except Exception as e:
            logger.error(f"Error restarting Hysteria: {e}")
            return False

    async def get_hysteria_version(self) -> str:
        try:
            proc = await asyncio.create_subprocess_exec(
                config.HYSTERIA_BINARY, "version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            # hysteria выводит "Version:  v2.x.x" одной из первых строк
            for line in stdout.decode().splitlines():
                if line.lower().startswith("version"):
                    parts = line.split()
                    if len(parts) >= 2:
                        return parts[-1]
            return "unknown"
        except Exception:
            return "unknown"

    async def is_hysteria_running(self) -> bool:
        try:
            proc = await asyncio.create_subprocess_exec(
                "systemctl", "is-active", "dem1chvpn-hysteria",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            return stdout.decode().strip() == "active"
        except Exception:
            return False
