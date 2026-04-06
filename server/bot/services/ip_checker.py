"""
Dem1chVPN — Сервис проверки блокировок IP
Через API Globalping стучимся на сервер из РФ.
"""
import aiohttp
import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("dem1chvpn.ip_checker")

# Стейт-файл для трекинга неудачных проверок
_STATE_FILE = Path("/tmp/dem1chvpn_ip_check_state.json")


class IPBlockChecker:


    def __init__(self, server_ip: str):
        self.server_ip = server_ip
        self._load_state()

    def _load_state(self):

        try:
            if _STATE_FILE.exists():
                data = json.loads(_STATE_FILE.read_text())
                self.consecutive_failures = data.get("consecutive_failures", 0)
                self.is_blocked = data.get("is_blocked", False)
            else:
                self.consecutive_failures = 0
                self.is_blocked = False
        except Exception:
            self.consecutive_failures = 0
            self.is_blocked = False

    def _save_state(self):

        try:
            _STATE_FILE.write_text(json.dumps({
                "consecutive_failures": self.consecutive_failures,
                "is_blocked": self.is_blocked,
            }))
        except Exception as e:
            logger.warning(f"Could not save IP check state: {e}")

    async def check_from_globalping(self) -> Optional[bool]:
        """Стучимся из РФ через API Globalping"""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=30)
            ) as session:

                async with session.post(
                    "https://api.globalping.io/v1/measurements",
                    json={
                        "type": "http",
                        "target": f"https://{self.server_ip}",
                        "locations": [{"country": "RU", "limit": 3}],
                        "measurementOptions": {
                            "request": {"method": "HEAD"},
                        },
                    },
                ) as resp:
                    if resp.status not in (200, 201, 202):
                        return None
                    data = await resp.json()
                    measurement_id = data.get("id")

                if not measurement_id:
                    return None


                await asyncio.sleep(10)

                async with session.get(
                    f"https://api.globalping.io/v1/measurements/{measurement_id}"
                ) as resp:
                    if resp.status != 200:
                        return None
                    data = await resp.json()

                results = data.get("results", [])
                if not results:
                    return None

                # Если все пинги отвалились — скорее всего блокировка
                successful = sum(
                    1 for r in results
                    if r.get("result", {}).get("statusCode", 0) > 0
                )
                return successful > 0

        except Exception as e:
            logger.warning(f"Globalping check failed: {e}")
            return None

    async def check_simple(self) -> bool:

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=5)
            ) as session:
                async with session.head(
                    f"https://{self.server_ip}:443", ssl=False
                ) as resp:
                    return resp.status > 0
        except Exception:
            return False

    async def run_check(self) -> dict:

        vps_ok = await self.check_simple()
        russia_ok = await self.check_from_globalping()

        result = {
            "vps_reachable": vps_ok,
            "from_russia": russia_ok,
            "ip": self.server_ip,
        }

        if russia_ok is False:
            self.consecutive_failures += 1
        else:
            self.consecutive_failures = 0

        # 3 фейла подряд = блок
        if self.consecutive_failures >= 3:
            self.is_blocked = True
            result["blocked"] = True
        else:
            self.is_blocked = False
            result["blocked"] = False


        self._save_state()

        return result

    async def get_formatted_status(self) -> str:

        result = await self.run_check()

        vps = "✅" if result["vps_reachable"] else "❌"
        russia = "✅" if result.get("from_russia") else (
            "❌" if result.get("from_russia") is False else "❓"
        )

        text = (
            f"🚨 <b>Проверка доступности IP</b>\n\n"
            f"  IP: <code>{self.server_ip}</code>\n"
            f"  Доступность VPS: {vps}\n"
            f"  Доступность из РФ: {russia}\n"
        )

        if result.get("blocked"):
            text += (
                f"\n  ⚠️ <b>IP НЕДОСТУПЕН ИЗ РЕГИОНА!</b>\n"
                f"  Неудачных проверок подряд: {self.consecutive_failures}\n\n"
                f"  Рекомендации:\n"
                f"  • Включить WARP double-hop\n"
                f"  • Сменить VPS/IP\n"
                f"  • Сменить SNI"
            )
        else:
            text += f"\n  🟢 IP доступен"

        return text
