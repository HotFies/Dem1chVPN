"""
Dem1chVPN — API-клиент для AdGuard Home
"""
import asyncio
import aiohttp
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class AdGuardAPI:
    # API-клиент к собственному AdGuard Home

    COMPOSE_DIR = "/opt/dem1chvpn/server/adguard"
    CONTAINER_NAME = "dem1chvpn-adguard"

    def __init__(self, host: str = "127.0.0.1", port: int = 8053,
                 username: str = "admin", password: str = "dem1chvpn"):
        self.base_url = f"http://{host}:{port}"
        self.auth = aiohttp.BasicAuth(username, password)

    # ── Управление контейнером ──

    async def is_container_running(self) -> bool:

        try:
            proc = await asyncio.create_subprocess_exec(
                "sudo", "docker", "inspect", "-f", "{{.State.Running}}", self.CONTAINER_NAME,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            return stdout.decode().strip() == "true"
        except Exception as e:
            logger.warning(f"Failed to check AdGuard container: {e}")
            return False

    async def start_container(self) -> bool:

        try:
            proc = await asyncio.create_subprocess_exec(
                "sudo", "docker", "compose", "up", "-d",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.COMPOSE_DIR,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if proc.returncode != 0:
                logger.error(f"AdGuard start failed (rc={proc.returncode}): {stderr.decode()}")
                return False
            # Ждем пока поднимется HTTP API
            await asyncio.sleep(3)
            return True
        except Exception as e:
            logger.error(f"AdGuard start exception: {e}")
            return False

    async def stop_container(self) -> bool:

        try:
            proc = await asyncio.create_subprocess_exec(
                "sudo", "docker", "compose", "down",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.COMPOSE_DIR,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            if proc.returncode != 0:
                logger.error(f"AdGuard stop failed (rc={proc.returncode}): {stderr.decode()}")
                return False
            return True
        except Exception as e:
            logger.error(f"AdGuard stop exception: {e}")
            return False

    async def get_status(self) -> dict:

        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(f"{self.base_url}/control/status") as resp:
                    if resp.status == 200:
                        return await resp.json()
            return {"running": False}
        except Exception:
            return {"running": False}

    async def get_stats(self) -> dict:

        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(f"{self.base_url}/control/stats") as resp:
                    if resp.status == 200:
                        return await resp.json()
            return {}
        except Exception:
            return {}

    async def toggle_protection(self, enabled: bool) -> bool:

        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.post(
                    f"{self.base_url}/control/dns_config",
                    json={"protection_enabled": enabled},
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def get_query_log(self, limit: int = 10) -> list:

        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(
                    f"{self.base_url}/control/querylog",
                    params={"limit": limit},
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", [])
            return []
        except Exception:
            return []

    async def add_filter_url(self, name: str, url: str) -> bool:

        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.post(
                    f"{self.base_url}/control/filtering/add_url",
                    json={"name": name, "url": url, "enabled": True},
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False

    async def get_formatted_stats(self) -> str:

        stats = await self.get_stats()
        status = await self.get_status()

        if not status.get("running", False) and not stats:
            return "🛡️ AdGuard Home: ❌ Не запущен"

        total = sum(stats.get("num_dns_queries_arr", [0])) or stats.get("num_dns_queries", 0)
        blocked = sum(stats.get("num_blocked_filtering_arr", [0])) or stats.get("num_blocked_filtering", 0)
        pct = (blocked / total * 100) if total > 0 else 0
        avg_time = stats.get("avg_processing_time", 0) * 1000  # sec → ms

        protection = status.get("protection_enabled", False)

        return (
            f"🛡️ <b>AdGuard Home</b>\n\n"
            f"  Защита: {'🟢 Включена' if protection else '🔴 Выключена'}\n"
            f"  📊 Запросов: {total:,}\n"
            f"  🚫 Заблокировано: {blocked:,} ({pct:.1f}%)\n"
            f"  ⏱️ Среднее время: {avg_time:.0f}ms"
        )
