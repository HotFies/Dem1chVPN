"""
Dem1chVPN — Subscription Server
"""
import base64
import json
import sys
from pathlib import Path
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded


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

    await init_db()
    
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



@app.get("/health")
async def health():
    return {"status": "ok"}



@app.get("/sub/{token}")
@limiter.limit("30/minute")
async def get_subscription(request: Request, token: str):
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

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)

    encoded = base64.b64encode(vless_url.encode()).decode()

    routing_header = await _build_routing_header()

    headers = {
        "Subscription-Userinfo": _build_userinfo(user),
        "Content-Disposition": f'attachment; filename="{user.name}.txt"',
        "Profile-Update-Interval": "6",
        "Profile-Title": f"base64:{base64.b64encode(f'Dem1chVPN - {user.name}'.encode()).decode()}",
    }
    if routing_header:
        headers["routing"] = routing_header

    return Response(
        content=encoded,
        media_type="text/plain",
        headers=headers,
    )


@app.get("/sub/{token}/routing")
async def get_routing_config(request: Request, token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)

    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    route_mgr = RouteManager()
    routing = await route_mgr.generate_client_routing_config()

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
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    route_mgr = RouteManager()
    direct = await route_mgr.get_direct_domains()


    lines = ["geosite:category-ru"]
    lines.extend(f"domain:{d}" for d in direct)

    return Response(
        content="\n".join(lines),
        media_type="text/plain",
    )


@app.get("/sub/{token}/proxy")
async def get_proxy_domains(token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    route_mgr = RouteManager()
    proxy = await route_mgr.get_proxy_domains()

    if not proxy:
        proxy = config.DEFAULT_PROXY_DOMAINS

    lines = [f"domain:{d}" for d in proxy]
    return Response(
        content="\n".join(lines),
        media_type="text/plain",
    )


@app.get("/sub/{token}/v2raytun")
async def get_v2raytun_deeplinks(request: Request, token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)

    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    sub_deeplink = f"v2raytun://import/{sub_url}"
    win_sub_deeplink = f"dem1chvpn://import/{sub_url}"

    routing_header = await _build_routing_header()
    route_deeplink = f"v2raytun://import_route/{routing_header}" if routing_header else None
    win_route_deeplink = f"dem1chvpn://import_route/{routing_header}" if routing_header else None

    return {
        "subscription": sub_deeplink,
        "routing": route_deeplink,
        "win_subscription": win_sub_deeplink,
        "win_routing": win_route_deeplink,
        "instructions": "iOS: откройте ссылки в Safari для автоимпорта в v2RayTun. Windows: используйте win_ ссылки для импорта в Dem1chVPN.",
    }


def _build_userinfo(user) -> str:
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
    """Собирает JSON маршрутов в Base64 для заголовка.

    V2RayTun читает заголовок 'routing' из ответа подписки и 
    автоматом применяет правила на клиенте.
    Формат должен один в один совпадать с их структурой пресетов:
    - Root: id, name, balancers, domainStrategy, domainMatcher, rules
    - В каждом rule: id, __name__, type, outboundTag, domain/ip
    Документация: https://v2raytun.gitbook.io/overview/supported-headers#routing
    """
    try:
        import uuid

        route_mgr = RouteManager()
        direct_domains = await route_mgr.get_direct_domains()
        proxy_domains = await route_mgr.get_proxy_domains()

        if not proxy_domains:
            proxy_domains = config.DEFAULT_PROXY_DOMAINS

        if not direct_domains and not proxy_domains:
            return None

        routing = {
            "domainStrategy": "AsIs",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.routing")).upper(),
            "balancers": [],
            "domainMatcher": "hybrid",
            "name": "Dem1chVPN",
            "rules": [],
        }

        direct_domain_list = [
            "geosite:category-ru",
            "regexp:.*\\.ru$",
            "regexp:.*\\.su$",
            "regexp:.*\\.xn--p1ai$",    # .рф (Cyrillic)
            "regexp:.*\\.xn--p1acf$",   # .рус
            "regexp:.*\\.xn--80adxhks$",  # .москва
            "regexp:.*\\.xn--80asehdb$",  # .онлайн
            "regexp:.*\\.xn--80aswg$",    # .сайт
            "regexp:.*\\.xn--c1avg$",     # .орг
            "regexp:.*\\.xn--d1acj3b$",   # .дети
            "regexp:.*\\.moscow$",        # .moscow
            "regexp:.*\\.tatar$",

            "domain:userapi.com",
            "domain:vk.com",            # VK main
            "domain:vk.me",             # VK messenger
            "domain:vkuseraudio.net",   # VK audio CDN
            "domain:vkuservideo.net",   # VK video CDN
            "domain:vk-cdn.net",        # VK CDN
            "domain:vk-cdn.me",         # VK CDN alt
            "domain:vkontakte.com",     # VK alt
            "domain:vkmessenger.com",   # VK Messenger
            "domain:vkmessenger.app",   # VK Messenger app
            "domain:vkteams.com",       # VK Teams
            "domain:vkcache.com",

            "domain:mail.ru",
            "domain:imgsmail.ru",       # Mail.ru images CDN
            "domain:mrgcdn.ru",         # Mail.ru CDN
            "domain:mycdn.me",          # OK.ru/Mail CDN
            "domain:ok.ru",             # Одноклассники
            "domain:okcdn.ru",          # OK CDN
            "domain:tamtam.chat",       # TamTam
            "domain:icq.com",

            "domain:yastatic.net",
            "domain:yastat.net",        # Yandex stats
            "domain:yandex.net",        # Yandex infra
            "domain:yandex.com",        # Yandex global
            "domain:yandex.cloud",      # Yandex Cloud
            "domain:yandexcloud.net",   # Yandex Cloud CDN
            "domain:ya.ru",             # Yandex short
            "domain:turbopages.org",    # Yandex Turbo
            "domain:webvisor.com",      # Yandex Webvisor
            "domain:naydex.net",

            "domain:avito.st",
            "domain:wbstatic.net",      # Wildberries CDN
            "domain:okko.tv",           # Okko стриминг
            "domain:boosty.to",         # VK Boosty
            "domain:donationalerts.com",

            "domain:ngenix.net",
            "domain:cdnvideo.net",      # CDNvideo
            "domain:selcdn.net",        # Selectel CDN
            "domain:selectel.cloud",

            "domain:sberbank.com",
            "domain:sber.me",           # Сбер короткие ссылки
            "domain:sberbank.ru",       # Сбер
            "domain:sber.ru",           # Сбер
            "domain:online.sberbank.ru",  # Сбер Онлайн
            "domain:tinkoff.ru",        # Тинькофф/Т-Банк
            "domain:tbank.ru",          # Т-Банк
            "domain:cdn-tinkoff.ru",    # Тинькофф CDN
            "domain:tbank-online.com",  # T-Bank CDN
            "domain:tochka.com",        # Точка Банк
            "domain:tochka-tech.com",   # Точка tech
            "domain:vtb.ru",            # ВТБ
            "domain:alfabank.ru",       # Альфа-Банк
            "domain:alfa.me",           # Альфа короткие ссылки
            "domain:alfaclick.ru",      # Альфа-Клик
            "domain:gazprombank.ru",    # Газпромбанк
            "domain:gpb.ru",            # Газпромбанк short
            "domain:raiffeisen.ru",     # Райффайзен
            "domain:rshb.ru",           # Россельхозбанк
            "domain:rosbank.ru",        # Росбанк
            "domain:psbank.ru",         # ПСБ
            "domain:open.ru",           # Открытие
            "domain:mkb.ru",            # МКБ
            "domain:sovcombank.ru",     # Совкомбанк
            "domain:pochtabank.ru",     # Почта Банк
            "domain:homecredit.ru",     # Хоум Кредит
            "domain:uralsib.ru",        # Уралсиб
            "domain:akbars.ru",         # Ак Барс
            "domain:bnkv.ru",

            "domain:nalog.ru",
            "domain:nalog.gov.ru",      # ФНС gov
            "domain:lkfl.nalog.ru",     # ЛК физлица
            "domain:lkfl2.nalog.ru",    # ЛК физлица v2
            "domain:lknpd.nalog.ru",    # Мой налог (самозанятые)
            "domain:api.nalog.ru",      # ФНС API
            "domain:service.nalog.ru",  # ФНС сервис
            "domain:auth.nalog.ru",     # ФНС авторизация
            "domain:gosuslugi.ru",      # Госуслуги
            "domain:esia.gosuslugi.ru", # ЕСИА авторизация
            "domain:gu-st.ru",          # Госуслуги статика
            "domain:gov.ru",            # Правительство
            "domain:government.ru",     # Правительство
            "domain:mos.ru",            # Мэрия Москвы
            "domain:emias.info",        # ЕМИАС здравоохранение
            "domain:cbr.ru",            # Центробанк
            "domain:goskey.ru",         # Госключ
            "domain:pfr.gov.ru",        # ПФР/СФР
            "domain:sfr.gov.ru",        # Социальный фонд
            "domain:fss.ru",            # ФСС
            "domain:rosreestr.ru",      # Росреестр
            "domain:rosreestr.gov.ru",  # Росреестр gov
            "domain:mvd.ru",            # МВД
            "domain:mvd.gov.ru",        # МВД gov
            "domain:fssp.gov.ru",       # ФССП (приставы)
            "domain:zakupki.gov.ru",    # Госзакупки
            "domain:bus.gov.ru",        # Бюджет
            "domain:rpn.gov.ru",        # Росприроднадзор
            "domain:fas.gov.ru",        # ФАС
            "domain:rostrud.gov.ru",    # Роструд
            "domain:fns.su",

            "domain:nspk.ru",
            "domain:mir.ru",            # МИР
            "domain:qiwi.com",          # QIWI
            "domain:yoomoney.ru",

            "domain:mts.ru",
            "domain:mymts.ru",          # МТС ЛК
            "domain:megafon.ru",        # Мегафон
            "domain:beeline.ru",        # Билайн
            "domain:tele2.ru",          # Tele2
            "domain:t2.ru",             # Tele2 alt
            "domain:yota.ru",           # Yota
            "domain:rt.ru",             # Ростелеком
            "domain:rostelecom.ru",     # Ростелеком
            "domain:ttk.ru",            # ТТК
            "domain:dom.ru",

            "domain:rzd.ru",
            "domain:aeroflot.ru",       # Аэрофлот
            "domain:s7.ru",             # S7 Airlines
            "domain:utair.ru",          # Utair
            "domain:pochta.ru",         # Почта России
            "domain:cdek.ru",

            "domain:yclients.com",
            "domain:taxsee.com",        # Taxsee
            "domain:t1.cloud",          # T1 Cloud
            "domain:dbo-dengi.online",  # MTS Dengi
            "domain:moex.com",          # Мосбиржа
            "domain:2gis.com",          # 2ГИС
        ]
        if direct_domains:
            direct_domain_list.extend(f"domain:{d}" for d in direct_domains)

        routing["rules"].append({
            "type": "field",
            "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.direct.ru")).upper(),
            "__name__": "🇷🇺 Россия — напрямую",
            "outboundTag": "direct",
            "domain": direct_domain_list,
            "ip": ["geoip:ru", "geoip:private"],
        })

        # ── Rule 3: Заблокированные сервисы → PROXY ──
        if proxy_domains:
            routing["rules"].append({
                "type": "field",
                "id": str(uuid.uuid5(uuid.NAMESPACE_DNS, "dem1chvpn.proxy")).upper(),
                "__name__": "🌍 Заблокированные — через VPN",
                "outboundTag": "proxy",
                "domain": [f"domain:{d}" for d in proxy_domains],
            })

        # Сплит-туннелинг: дефолтного правила "всё подряд" здесь нет.
        # Все домены, не попавшие в direct-правила из списка выше,
        # пойдут через дефолтный outbound клиента (обычно это proxy).

        return base64.b64encode(json.dumps(routing).encode()).decode()
    except Exception:
        return None


# WebView в Телеге жестко режет кастомные схемы (типа v2raytun://).
# Поэтому отдаем простую HTML, которая редиректит на диплинк (обрабатывается внешним Safari/Chrome).

def _build_redirect_html(deeplink: str, action_label: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="refresh" content="1;url={deeplink}">
    <title>Dem1chVPN — {action_label}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'SF Pro', 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0a0a1a 0%, #0d1b2a 50%, #1a0a2e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}
        .container {{
            text-align: center;
            max-width: 400px;
            width: 100%;
        }}
        .shield {{
            width: 64px; height: 64px;
            margin: 0 auto 20px;
            animation: pulse 2s ease-in-out infinite;
        }}
        .shield svg {{
            width: 100%; height: 100%;
            filter: drop-shadow(0 0 20px rgba(0, 212, 255, 0.4));
        }}
        @keyframes pulse {{
            0%, 100% {{ transform: scale(1); opacity: 1; }}
            50% {{ transform: scale(1.05); opacity: 0.8; }}
        }}
        h1 {{
            font-size: 20px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 8px;
        }}
        .subtitle {{
            font-size: 14px;
            color: #8899aa;
            margin-bottom: 32px;
        }}
        .spinner {{
            width: 40px; height: 40px;
            margin: 0 auto 20px;
            border: 3px solid rgba(0, 212, 255, 0.15);
            border-top-color: #00d4ff;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        .status {{
            font-size: 15px;
            color: #ccddee;
            margin-bottom: 24px;
        }}
        .manual-link {{
            display: inline-block;
            padding: 14px 28px;
            background: linear-gradient(135deg, #00d4ff, #0066ff);
            color: #ffffff;
            text-decoration: none;
            border-radius: 12px;
            font-weight: 600;
            font-size: 15px;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
        }}
        .manual-link:active {{
            transform: scale(0.97);
        }}
        .hint {{
            margin-top: 20px;
            font-size: 12px;
            color: #667788;
            line-height: 1.5;
        }}
        .hint code {{
            background: rgba(0, 212, 255, 0.1);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 11px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="shield">
            <svg viewBox="0 0 24 24" fill="none" stroke="#00d4ff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                <path d="M9 12l2 2 4-4" stroke="#00d4ff"/>
            </svg>
        </div>
        <h1>Dem1chVPN</h1>
        <p class="subtitle">{action_label}</p>
        <div class="spinner"></div>
        <p class="status">Открываю V2RayTun...</p>
        <a href="{deeplink}" class="manual-link">
            Открыть вручную
        </a>
        <p class="hint">
            Если приложение не открылось автоматически,<br>
            нажмите кнопку выше или установите
            <a href="https://apps.apple.com/app/v2raytun/id6476628951" style="color: #00d4ff;">V2RayTun</a>
        </p>
    </div>
    <script>
        // JavaScript fallback redirect
        setTimeout(function() {{
            window.location.href = "{deeplink}";
        }}, 800);
    </script>
</body>
</html>"""


@app.get("/redirect/sub/{token}")
async def redirect_subscription(token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    deeplink = f"v2raytun://import/{sub_url}"

    html = _build_redirect_html(deeplink, "Импорт подписки")
    return HTMLResponse(content=html)


@app.get("/redirect/route/{token}")
async def redirect_routing(token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    routing_header = await _build_routing_header()
    if not routing_header:
        raise HTTPException(status_code=404, detail="No routing rules configured")

    deeplink = f"v2raytun://import_route/{routing_header}"

    html = _build_redirect_html(deeplink, "Импорт маршрутов")
    return HTMLResponse(content=html)


@app.get("/redirect/win/sub/{token}")
async def redirect_win_subscription(token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    deeplink = f"dem1chvpn://import/{sub_url}"

    html = _build_redirect_html(deeplink, "Импорт подписки — Windows")
    return HTMLResponse(content=html)


@app.get("/redirect/win/route/{token}")
async def redirect_win_routing(token: str):
    mgr = UserManager()
    user = await mgr.get_user_by_subscription_token(token)
    if not user:
        raise HTTPException(status_code=404, detail="Invalid subscription")

    routing_header = await _build_routing_header()
    if not routing_header:
        raise HTTPException(status_code=404, detail="No routing rules configured")

    deeplink = f"dem1chvpn://import_route/{routing_header}"

    html = _build_redirect_html(deeplink, "Импорт маршрутов — Windows")
    return HTMLResponse(content=html)


from server.subscription.webapp_api import api as webapp_api
app.include_router(webapp_api)


WEBAPP_DIR = Path(__file__).resolve().parent.parent / "webapp" / "dist"
if WEBAPP_DIR.exists():
    app.mount("/webapp", StaticFiles(directory=str(WEBAPP_DIR), html=True), name="webapp")


def main():
    uvicorn.run(
        "server.subscription.app:app",
        host=config.SUB_HOST,
        port=config.SUB_PORT,
        log_level="info",
    )


if __name__ == "__main__":
    main()
