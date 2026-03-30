"""
XShield — AdGuard Home API Service
Interact with AdGuard Home REST API.
"""
import aiohttp
from typing import Optional


class AdGuardAPI:
    """Manage AdGuard Home via REST API."""

    def __init__(self, host: str = "127.0.0.1", port: int = 8053,
                 username: str = "admin", password: str = "xshield"):
        self.base_url = f"http://{host}:{port}"
        self.auth = aiohttp.BasicAuth(username, password)

    async def get_status(self) -> dict:
        """Get AdGuard Home status."""
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(f"{self.base_url}/control/status") as resp:
                    if resp.status == 200:
                        return await resp.json()
            return {"running": False}
        except Exception:
            return {"running": False}

    async def get_stats(self) -> dict:
        """Get filtering statistics."""
        try:
            async with aiohttp.ClientSession(auth=self.auth) as session:
                async with session.get(f"{self.base_url}/control/stats") as resp:
                    if resp.status == 200:
                        return await resp.json()
            return {}
        except Exception:
            return {}

    async def toggle_protection(self, enabled: bool) -> bool:
        """Enable/disable DNS protection."""
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
        """Get recent DNS query log."""
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
        """Add a filter list URL."""
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
        """Get formatted stats text for bot."""
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
