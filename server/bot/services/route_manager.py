"""
Dem1chVPN — Route Manager Service
CRUD for routing rules + antifilter sync.
"""
import aiohttp
from typing import Optional
from sqlalchemy import select, func, delete

from ..database import async_session, RouteRule
from ..config import config


class RouteManager:
    """Manages routing rules in DB."""

    async def add_rule(self, domain: str, rule_type: str, added_by: str = "admin") -> bool:
        """Add a routing rule. Returns False if already exists."""
        async with async_session() as session:
            existing = await session.execute(
                select(RouteRule).where(RouteRule.domain == domain)
            )
            if existing.scalar_one_or_none():
                return False
            rule = RouteRule(domain=domain, rule_type=rule_type, added_by=added_by)
            session.add(rule)
            await session.commit()
            return True

    async def delete_rule(self, domain: str) -> bool:
        """Delete a routing rule by domain."""
        async with async_session() as session:
            result = await session.execute(
                select(RouteRule).where(RouteRule.domain == domain)
            )
            rule = result.scalar_one_or_none()
            if rule:
                await session.delete(rule)
                await session.commit()
                return True
            return False

    async def get_rule(self, domain: str) -> Optional[RouteRule]:
        """Get a specific rule."""
        async with async_session() as session:
            result = await session.execute(
                select(RouteRule).where(RouteRule.domain == domain)
            )
            return result.scalar_one_or_none()

    async def get_rules(self, rule_type: Optional[str] = None) -> list[RouteRule]:
        """Get all rules, optionally filtered by type."""
        async with async_session() as session:
            query = select(RouteRule).order_by(RouteRule.domain)
            if rule_type:
                query = query.where(RouteRule.rule_type == rule_type)
            result = await session.execute(query)
            return list(result.scalars().all())

    async def count_rules(self, rule_type: Optional[str] = None) -> int:
        """Count rules."""
        async with async_session() as session:
            query = select(func.count(RouteRule.id))
            if rule_type:
                query = query.where(RouteRule.rule_type == rule_type)
            result = await session.execute(query)
            return result.scalar()

    async def sync_default_domains(self) -> int:
        """Sync default proxy domains from config."""
        count = 0
        for domain in config.DEFAULT_PROXY_DOMAINS:
            if await self.add_rule(domain, "proxy", "default"):
                count += 1
        return count

    async def get_proxy_domains(self) -> list[str]:
        """Get all proxy domains as a flat list."""
        rules = await self.get_rules("proxy")
        return [r.domain for r in rules]

    async def get_direct_domains(self) -> list[str]:
        """Get all direct domains as a flat list."""
        rules = await self.get_rules("direct")
        return [r.domain for r in rules]

    async def check_site(self, domain: str) -> dict:
        """Check if a site is accessible from VPS."""
        result = {"vps_ok": False, "vps_ms": 0}
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                import time
                start = time.monotonic()
                async with session.head(f"https://{domain}", ssl=False) as resp:
                    elapsed = (time.monotonic() - start) * 1000
                    result["vps_ok"] = resp.status < 500
                    result["vps_ms"] = int(elapsed)
        except Exception:
            result["vps_ok"] = False
        return result

    async def generate_client_routing_config(self) -> dict:
        """Generate routing config for client subscription (split-tunneling).

        Russian domains (all TLDs + geosite + CDNs) go DIRECT.
        Blocked/throttled services go through PROXY.
        Everything else — default outbound (proxy in client config).
        """
        proxy_domains = await self.get_proxy_domains()
        direct_domains = await self.get_direct_domains()

        # Fallback to config defaults if DB has no proxy domains yet
        if not proxy_domains:
            proxy_domains = config.DEFAULT_PROXY_DOMAINS

        rules = []

        # ── Rule 1: All Russian domains → DIRECT ──
        direct_domain_list = [
            "geosite:category-ru",
            "regexp:.*\\.ru$",
            "regexp:.*\\.su$",
            "regexp:.*\\.xn--p1ai$",      # .рф
            "regexp:.*\\.xn--p1acf$",     # .рус
            "regexp:.*\\.xn--80adxhks$",  # .москва
            "regexp:.*\\.xn--80asehdb$",  # .онлайн
            "regexp:.*\\.xn--80aswg$",    # .сайт
            "regexp:.*\\.xn--c1avg$",     # .орг
            "regexp:.*\\.xn--d1acj3b$",   # .дети
            "regexp:.*\\.moscow$",
            "regexp:.*\\.tatar$",
            # Russian CDNs & services with non-.ru domains
            "domain:userapi.com", "domain:vk.com", "domain:vk.me",
            "domain:vkuseraudio.net", "domain:vkuservideo.net",
            "domain:vk-cdn.net", "domain:vkontakte.com",
            "domain:yastatic.net", "domain:yastat.net",
            "domain:yandex.net", "domain:yandex.com",
            "domain:yandexcloud.net", "domain:ya.ru",
            "domain:avito.st", "domain:sberbank.com",
            "domain:tbank-online.com", "domain:tochka.com",
            "domain:tochka-tech.com", "domain:boosty.to",
            "domain:donationalerts.com", "domain:ngenix.net",
            "domain:yclients.com", "domain:taxsee.com",
            "domain:t1.cloud", "domain:dbo-dengi.online",
            "domain:moex.com", "domain:turbopages.org",
            "domain:webvisor.com", "domain:naydex.net",
        ]
        if direct_domains:
            direct_domain_list.extend(f"domain:{d}" for d in direct_domains)

        rules.append({
            "type": "field",
            "outboundTag": "direct",
            "domain": direct_domain_list,
        })

        # ── Rule 2: Russian IPs → DIRECT ──
        rules.append({
            "type": "field",
            "outboundTag": "direct",
            "ip": ["geoip:ru", "geoip:private"],
        })

        # ── Rule 3: Blocked/throttled services → PROXY ──
        if proxy_domains:
            rules.append({
                "type": "field",
                "outboundTag": "proxy",
                "domain": [f"domain:{d}" for d in proxy_domains],
            })

        # Split-tunnel: no catch-all rule.
        # Client's first outbound (proxy) handles unmatched traffic by default.

        return {
            "routing": {
                "domainStrategy": "IPIfNonMatch",
                "rules": rules,
            }
        }

