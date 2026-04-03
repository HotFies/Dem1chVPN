"""
Dem1chVPN — Subscription Server
Provides auto-updating VPN configs for clients via HTTPS.
"""
import base64
import json
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Ensure project root is in path for imports
PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.bot.config import config
from server.bot.services.user_manager import UserManager
from server.bot.services.xray_config import XrayConfigManager
from server.bot.services.route_manager import RouteManager
from server.bot.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle handler."""
    await init_db()
    # Auto-sync default proxy domains so routing rules exist immediately
    route_mgr = RouteManager()
    synced = await route_mgr.sync_default_domains()
    if synced:
        import logging
        logging.getLogger("dem1chvpn.subscription").info(
            f"Auto-synced {synced} default proxy domains"
        )
    yield


limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Dem1chVPN Subscription",
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS for Mini App — restrict to configured domain
_cors_origins = []
if config.SUB_DOMAIN:
    _cors_origins.append(f"https://{config.SUB_DOMAIN}:{config.SUB_EXTERNAL_PORT}")
    _cors_origins.append(f"https://{config.SUB_DOMAIN}")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins or ["*"],
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Telegram-Init-Data"],
)


# ── Health Check ──

@app.get("/health")
async def health():
    return {"status": "ok"}


# ── Subscription Endpoint ──

@app.get("/sub/{token}")
@limiter.limit("30/minute")
async def get_subscription(request: Request, token: str):
    """
    Subscription endpoint for V2Ray/Xray clients.
    Returns Base64-encoded VLESS link(s) with appropriate headers.
    """
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)

    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    if user.is_expired:
        raise HTTPException(status_code=403, detail="Account expired")

    if user.is_traffic_exceeded:
        raise HTTPException(status_code=403, detail="Traffic limit exceeded")

    # Generate VLESS link
    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)

    # Base64 encode (standard for V2Ray subscription format)
    encoded = base64.b64encode(vless_url.encode()).decode()

    # Build V2RayTun routing header (base64-encoded routing rules)
    routing_header = await _build_routing_header()

    # Build subscription response with proper headers
    headers = {
        "Subscription-Userinfo": _build_userinfo(user),
        "Content-Disposition": f'attachment; filename="{user.name}.txt"',
        "Profile-Update-Interval": "6",
        "Profile-Title": f"base64:{base64.b64encode(f'Dem1chVPN - {user.name}'.encode()).decode()}",
    }
    if routing_header:
        headers["routing"] = routing_header


    # Fragment header removed — it was breaking connections to Russian sites
    # that go through the `direct` outbound on the server.
    # DPI bypass is handled by Reality protocol itself.

    # DNS header — override client DNS to DoH (bypass TSPU DNS interception)
    dns_config = {
        "servers": [
            {"address": "https://1.1.1.1/dns-query", "domains": []},
            {"address": "https://8.8.8.8/dns-query", "domains": []},
        ],
        "queryStrategy": "UseIPv4",
    }
    headers["dns"] = base64.b64encode(
        json.dumps(dns_config).encode()
    ).decode()

    return Response(
        content=encoded,
        media_type="text/plain",
        headers=headers,
    )


@app.get("/sub/{token}/routing")
async def get_routing_config(request: Request, token: str):
    """Return client-side routing rules for split tunneling.

    Supports two formats:
    - JSON (default): /sub/{token}/routing
    - Base64 text: /sub/{token}/routing?format=b64
      (for iOS clients like V2RayTun/Streisand that import routing by URL)
    """
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)

    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    route_mgr = RouteManager()
    routing = await route_mgr.generate_client_routing_config()

    # Return base64 for clients that request it (V2RayTun URL import)
    fmt = request.query_params.get("format", "")
    accept = request.headers.get("accept", "")

    if fmt == "b64" or "text/plain" in accept:
        routing_json = json.dumps(routing.get("routing", routing))
        encoded = base64.b64encode(routing_json.encode()).decode()
        return Response(
            content=encoded,
            media_type="text/plain",
            headers={"Content-Disposition": 'inline; filename="routing.txt"'},
        )

    return routing


@app.get("/sub/{token}/direct")
async def get_direct_domains(token: str):
    """Plain-text list of direct domains (one per line).

    For v2rayNG: Settings → Routing → Custom rules → Direct URL.
    """
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    route_mgr = RouteManager()
    direct = await route_mgr.get_direct_domains()

    # Always include Russian geosite for split tunneling
    lines = ["geosite:category-ru"]
    lines.extend(f"domain:{d}" for d in direct)

    return Response(
        content="\n".join(lines),
        media_type="text/plain",
    )


@app.get("/sub/{token}/proxy")
async def get_proxy_domains(token: str):
    """Plain-text list of proxy domains (one per line).

    For v2rayNG: Settings → Routing → Custom rules → Proxy URL.
    """
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    route_mgr = RouteManager()
    proxy = await route_mgr.get_proxy_domains()

    # Fallback to defaults
    if not proxy:
        proxy = config.DEFAULT_PROXY_DOMAINS

    lines = [f"domain:{d}" for d in proxy]
    return Response(
        content="\n".join(lines),
        media_type="text/plain",
    )


@app.get("/sub/{token}/v2raytun")
async def get_v2raytun_deeplinks(request: Request, token: str):
    """Return v2RayTun deeplinks for one-tap subscription + routing import.

    URL Schemes:
    - v2raytun://import/{subscription_url} — add subscription
    - v2raytun://import_route/{base64} — import routing preset
    """
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)

    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    sub_deeplink = f"v2raytun://import/{sub_url}"

    # Build routing deeplink
    routing_header = await _build_routing_header()
    route_deeplink = f"v2raytun://import_route/{routing_header}" if routing_header else None

    return {
        "subscription": sub_deeplink,
        "routing": route_deeplink,
        "instructions": "Откройте ссылки в Safari на iPhone для автоимпорта в v2RayTun",
    }


def _build_userinfo(user) -> str:
    """Build Subscription-Userinfo header value."""
    parts = [
        f"upload={user.traffic_used_up}",
        f"download={user.traffic_used_down}",
    ]
    if user.traffic_limit:
        parts.append(f"total={user.traffic_limit}")
    if user.expiry_date:
        import time
        parts.append(f"expire={int(user.expiry_date.timestamp())}")
    return "; ".join(parts)


async def _build_routing_header() -> str | None:
    """Build base64-encoded routing JSON for V2RayTun header.

    V2RayTun reads the 'routing' HTTP header from the subscription response
    and auto-applies the routing rules on the client.
    Format must match v2RayTun's internal preset structure exactly:
    - Root: id, name, balancers, domainStrategy, domainMatcher, rules
    - Each rule: id, __name__, type, outboundTag, domain/ip
    Docs: https://v2raytun.gitbook.io/overview/supported-headers#routing
    """
    try:
        import uuid

        route_mgr = RouteManager()
        direct_domains = await route_mgr.get_direct_domains()
        proxy_domains = await route_mgr.get_proxy_domains()

        # Fallback to config defaults if DB has no proxy domains yet
        if not proxy_domains:
            proxy_domains = config.DEFAULT_PROXY_DOMAINS

        if not direct_domains and not proxy_domains:
            return None

        # v2RayTun preset format — must include id, name, balancers
        routing = {
            "domainStrategy": "IPIfNonMatch",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.routing")).upper(),
            "balancers": [],
            "domainMatcher": "hybrid",
            "name": "Dem1chVPN",
            "rules": [],
        }

        # ── Rule 1: All Russian domains → DIRECT ──
        # Comprehensive coverage of Russian TLDs, geosite, CDNs, and services
        direct_domain_list = [
            # Geosite database (includes Yandex, Mail.ru, VK, banks, telecom, etc.)
            "geosite:category-ru",
            # All Russian TLD zones via regexp
            "regexp:.*\\.ru$",          # .ru
            "regexp:.*\\.su$",          # .su (Soviet legacy, still active)
            "regexp:.*\\.xn--p1ai$",    # .рф (Cyrillic)
            "regexp:.*\\.xn--p1acf$",   # .рус
            "regexp:.*\\.xn--80adxhks$",  # .москва
            "regexp:.*\\.xn--80asehdb$",  # .онлайн
            "regexp:.*\\.xn--80aswg$",    # .сайт
            "regexp:.*\\.xn--c1avg$",     # .орг
            "regexp:.*\\.xn--d1acj3b$",   # .дети
            "regexp:.*\\.moscow$",        # .moscow
            "regexp:.*\\.tatar$",         # .tatar
            # Russian CDNs & infrastructure (non-.ru domains)
            "domain:userapi.com",       # VK CDN
            "domain:vk.com",            # VK main
            "domain:vk.me",             # VK messenger
            "domain:vkuseraudio.net",   # VK audio CDN
            "domain:vkuservideo.net",   # VK video CDN
            "domain:vk-cdn.net",        # VK CDN
            "domain:vkontakte.com",     # VK alt
            "domain:yastatic.net",      # Yandex static CDN
            "domain:yastat.net",        # Yandex stats
            "domain:yandex.net",        # Yandex infra
            "domain:yandex.com",        # Yandex global
            "domain:yandexcloud.net",   # Yandex Cloud
            "domain:ya.ru",             # Yandex short
            "domain:avito.st",          # Avito CDN
            "domain:sberbank.com",      # Sber global
            "domain:tbank-online.com",  # T-Bank
            "domain:tochka.com",        # Tochka Bank
            "domain:tochka-tech.com",   # Tochka tech
            "domain:boosty.to",         # VK Boosty
            "domain:donationalerts.com",  # Donation Alerts
            "domain:ngenix.net",        # NGENIX CDN (Russian CDN provider)
            "domain:yclients.com",      # yCients SaaS
            "domain:taxsee.com",        # Taxsee
            "domain:t1.cloud",          # T1 Cloud
            "domain:dbo-dengi.online",  # MTS Dengi
            "domain:moex.com",          # Moscow Exchange
            "domain:turbopages.org",    # Yandex Turbo
            "domain:webvisor.com",      # Yandex Webvisor
            "domain:naydex.net",        # Yandex Ads
            # Государство + налоги (критичные API-домены)
            "domain:nalog.ru",
            "domain:nalog.gov.ru",
            "domain:gosuslugi.ru",
            "domain:esia.gosuslugi.ru",
            "domain:gu-st.ru",
            "domain:gov.ru",
            "domain:government.ru",
            "domain:mos.ru",
            "domain:emias.info",
            "domain:cbr.ru",
            "domain:goskey.ru",
            "domain:pfr.gov.ru",
            # Платёжные системы
            "domain:nspk.ru",
            "domain:mir.ru",
        ]
        # Add admin-configured direct domains from DB
        if direct_domains:
            direct_domain_list.extend(f"domain:{d}" for d in direct_domains)

        routing["rules"].append({
            "type": "field",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.direct.ru")).upper(),
            "__name__": "🇷🇺 Россия — напрямую",
            "outboundTag": "direct",
            "domain": direct_domain_list,
        })

        # ── Rule 2: Russian IPs → DIRECT ──
        routing["rules"].append({
            "type": "field",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.direct.ip")).upper(),
            "__name__": "🇷🇺 RU IP — напрямую",
            "outboundTag": "direct",
            "ip": ["geoip:ru", "geoip:private"],
        })

        # ── Rule 3: Blocked/throttled services → PROXY ──
        if proxy_domains:
            routing["rules"].append({
                "type": "field",
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.proxy")).upper(),
                "__name__": "🌍 Заблокированные — через VPN",
                "outboundTag": "proxy",
                "domain": [f"domain:{d}" for d in proxy_domains],
            })

        # Split-tunnel: no catch-all. Unknown domains go through proxy by
        # default outbound (first outbound in client config = proxy).
        # Russian domains matched by rules above go direct.

        return base64.b64encode(json.dumps(routing).encode()).decode()
    except Exception:
        return None


# ── WebApp API ──

from server.subscription.webapp_api import api as webapp_api
app.include_router(webapp_api)


# ── Static files (Mini App) ──

WEBAPP_DIR = Path(__file__).resolve().parent.parent / "webapp" / "dist"
if WEBAPP_DIR.exists():
    app.mount("/webapp", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="webapp")


# ── Entry Point ──

def main():
    uvicorn.run(
        "server.subscription.app:app",
        host=config.SUB_HOST,
        port=config.SUB_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
