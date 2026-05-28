"""
Dem1chVPN — WebApp REST API
"""
import psutil
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

import sys
from pathlib import Path


PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.bot.config import config
from server.bot.services.user_manager import UserManager
from server.bot.services.xray_config import XrayConfigManager
from server.bot.services.route_manager import RouteManager
from server.bot.utils.formatters import format_uptime
from .auth import require_admin, require_auth, validate_init_data

api = APIRouter(prefix="/api")



@api.post("/auth/check")
async def auth_check(request: Request):

    data = await request.json()
    init_data = data.get("initData", "")

    result = validate_init_data(init_data)
    if result is None:
        return {"valid": False}

    return {
        "is_admin": result.get("is_admin", False),
        "valid": True,
        "user_id": result.get("user_id"),
        "first_name": result.get("first_name", ""),
    }



@api.get("/status", dependencies=[Depends(require_auth)])
async def server_status():

    cpu = psutil.cpu_percent(interval=0.5)
    mem = psutil.virtual_memory()

    try:
        disk = psutil.disk_usage("/")
    except OSError:
        disk = psutil.disk_usage("C:\\")

    boot_time = psutil.boot_time()
    uptime = (datetime.now(timezone.utc) - datetime.fromtimestamp(boot_time, tz=timezone.utc)).total_seconds()

    xray_mgr = XrayConfigManager()
    xray_running = await xray_mgr.is_xray_running()
    xray_version = await xray_mgr.get_xray_version()

    user_mgr = UserManager()
    users = await user_mgr.get_all_users()

    total_up = sum(u.traffic_used_up for u in users)
    total_down = sum(u.traffic_used_down for u in users)

    return {
        "cpu": cpu,
        "ram_used": mem.used,
        "ram_total": mem.total,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "uptime": format_uptime(uptime),
        "xray_running": xray_running,
        "xray_version": xray_version,
        "users_count": len(users),
        "traffic_today_up": total_up,
        "traffic_today_down": total_down,
    }



@api.get("/users", dependencies=[Depends(require_admin)])
async def list_users():
    mgr = UserManager()
    users = await mgr.get_all_users()
    return {
        "users": [
            {
                "id": u.id,
                "name": u.name,
                "active": u.is_active,
                "traffic_up": u.traffic_used_up,
                "traffic_down": u.traffic_used_down,
                "traffic_total": u.traffic_total,
                "traffic_limit": u.traffic_limit,
                "expiry": u.expiry_date.isoformat() if u.expiry_date else None,
                "created": u.created_at.isoformat() if u.created_at else None,
            }
            for u in users
        ]
    }


@api.post("/users/{user_id}/toggle", dependencies=[Depends(require_admin)])
async def toggle_user(user_id: int):

    mgr = UserManager()
    user = await mgr.toggle_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    xray_mgr = XrayConfigManager()
    if user.is_active:
        await xray_mgr.add_client(user.uuid, user.email)
    else:
        await xray_mgr.remove_client(user.email)

    return {"id": user.id, "active": user.is_active, "name": user.name}


@api.get("/users/{user_id}/link", dependencies=[Depends(require_admin)])
async def get_user_link(user_id: int):

    mgr = UserManager()
    user = await mgr.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"

    return {"vless_url": vless_url, "sub_url": sub_url}



@api.get("/routes", dependencies=[Depends(require_admin)])
async def list_routes():
    mgr = RouteManager()
    rules = await mgr.get_rules()
    return {
        "rules": [
            {"id": r.id, "domain": r.domain, "rule_type": r.rule_type, "added_by": r.added_by}
            for r in rules
        ]
    }


@api.post("/routes", dependencies=[Depends(require_admin)])
async def add_route(request: Request):
    data = await request.json()
    domain = data.get("domain", "").strip().lower()
    rule_type = data.get("type", "proxy")

    if not domain:
        raise HTTPException(400, "Domain required")
    if rule_type not in ("proxy", "direct"):
        raise HTTPException(400, "Type must be 'proxy' or 'direct'")

    mgr = RouteManager()
    result = await mgr.add_rule(domain, rule_type, "webapp")
    return {"success": result, "domain": domain, "type": rule_type}


@api.delete("/routes/{domain}", dependencies=[Depends(require_admin)])
async def delete_route(domain: str):
    mgr = RouteManager()
    result = await mgr.delete_rule(domain)
    return {"success": result}



@api.get("/settings", dependencies=[Depends(require_admin)])
async def get_settings():

    warp_enabled = False
    adguard_enabled = False
    mtproto_enabled = False

    try:
        from server.bot.services.warp_manager import WarpManager
        warp_enabled = WarpManager().is_enabled()
    except Exception:
        pass

    try:
        from server.bot.services.adguard_api import AdGuardAPI
        adguard_enabled = await AdGuardAPI().is_container_running()
    except Exception:
        pass

    try:
        from server.bot.services.mtproto_manager import MTProtoManager
        mtproto_enabled = await MTProtoManager().is_running()
    except Exception:
        pass

    return {
        "warp_enabled": warp_enabled,
        "adguard_enabled": adguard_enabled,
        "mtproto_enabled": mtproto_enabled,
        "server_ip": config.SERVER_IP,
        "reality_sni": config.REALITY_SNI,
    }


@api.post("/settings/{feature}/toggle", dependencies=[Depends(require_admin)])
async def toggle_feature(feature: str):
    if feature == "warp":
        from server.bot.services.warp_manager import WarpManager
        mgr = WarpManager()
        try:
            new_state = await mgr.toggle()

            actual = mgr.is_enabled()
            return {"enabled": actual}
        except Exception as e:
            raise HTTPException(500, f"WARP toggle failed: {e}")
    elif feature == "adguard":
        from server.bot.services.adguard_api import AdGuardAPI
        api_client = AdGuardAPI()
        try:
            running = await api_client.is_container_running()
            if running:

                success = await api_client.stop_container()
                if not success:
                    raise HTTPException(500, "Не удалось остановить AdGuard — проверьте Docker")
                return {"enabled": False}
            else:

                success = await api_client.start_container()
                if not success:
                    raise HTTPException(500, "Не удалось запустить AdGuard — проверьте Docker")
                return {"enabled": True}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"AdGuard toggle failed: {e}")
    elif feature == "mtproto":
        from server.bot.services.mtproto_manager import MTProtoManager
        mgr = MTProtoManager()
        try:
            running = await mgr.is_running()
            if running:
                success = await mgr.stop()
                if not success:
                    raise HTTPException(500, "Не удалось остановить MTProto — проверьте Docker")
                return {"enabled": False}
            else:
                success = await mgr.start()
                if not success:
                    raise HTTPException(500, "Не удалось запустить MTProto — проверьте Docker")

                import asyncio
                await asyncio.sleep(2)
                actual = await mgr.is_running()
                return {"enabled": actual}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"MTProto toggle failed: {e}")

    raise HTTPException(400, "Unknown feature")



@api.post("/xray/restart", dependencies=[Depends(require_admin)])
async def restart_xray():
    mgr = XrayConfigManager()
    await mgr.reload_xray()
    running = await mgr.is_xray_running()
    return {"success": running}


@api.post("/geo/update", dependencies=[Depends(require_admin)])
async def update_geo():
    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "sudo", "bash", "/opt/dem1chvpn/cron/update_geodata.sh",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=120)
    return {"success": True}


@api.post("/backup", dependencies=[Depends(require_admin)])
async def create_backup():

    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "bash", "/opt/dem1chvpn/cron/backup.sh",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=30)
    return {"success": True, "message": "Backup created. Check /opt/dem1chvpn/backups/"}



from server.bot.services.ticket_manager import TicketManager


async def _get_auth_user(request: Request) -> dict:

    return await require_auth(request)


async def _require_vpn_user(request: Request) -> dict:

    auth = await require_auth(request)
    user_id = auth.get("user_id")
    if not user_id:
        raise HTTPException(401, "User ID not found")
    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(user_id)
    if not user:
        raise HTTPException(403, "Only VPN users can create tickets")
    auth["vpn_user"] = user
    return auth


async def _send_bot_message(chat_id: int, text: str):

    import aiohttp
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    async with aiohttp.ClientSession() as session:
        await session.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        })


@api.get("/tickets/my")
async def get_my_tickets(request: Request):

    auth = await _require_vpn_user(request)
    user_id = auth["user_id"]
    ticket_mgr = TicketManager()
    tickets = await ticket_mgr.get_user_tickets(user_id)
    return {
        "tickets": [
            {
                "id": t.id,
                "message": t.message,
                "reply": t.reply,
                "is_resolved": t.is_resolved,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            }
            for t in tickets
        ]
    }


@api.post("/tickets")
async def create_ticket(request: Request):

    auth = await _require_vpn_user(request)
    data = await request.json()
    message = data.get("message", "").strip()

    if not message or len(message) < 5:
        raise HTTPException(400, "Message must be at least 5 characters")

    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.create_ticket(
        user_telegram_id=auth["user_id"],
        user_name=auth.get("first_name", "User"),
        message=message[:2000],
    )


    for admin_id in config.ADMIN_IDS:
        try:
            await _send_bot_message(
                admin_id,
                f"🎫 <b>Новый тикет #{ticket.id}</b>\n\n"
                f"👤 От: <b>{auth.get('first_name', 'User')}</b>\n"
                f"📝 {message[:500]}",
            )
        except Exception:
            pass

    return {
        "id": ticket.id,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
    }


@api.get("/tickets", dependencies=[Depends(require_admin)])
async def list_all_tickets(status: str = "all"):

    ticket_mgr = TicketManager()

    if status == "open":
        tickets = await ticket_mgr.get_open_tickets()
    elif status == "closed":
        tickets = await ticket_mgr.get_closed_tickets()
    else:
        tickets = await ticket_mgr.get_all_tickets()

    return {
        "tickets": [
            {
                "id": t.id,
                "user_telegram_id": t.user_telegram_id,
                "user_name": t.user_name,
                "message": t.message,
                "reply": t.reply,
                "is_resolved": t.is_resolved,
                "created_at": t.created_at.isoformat() if t.created_at else None,
                "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            }
            for t in tickets
        ]
    }


@api.post("/tickets/{ticket_id}/reply", dependencies=[Depends(require_admin)])
async def reply_to_ticket(ticket_id: int, request: Request):

    data = await request.json()
    reply_text = data.get("reply", "").strip()

    if not reply_text:
        raise HTTPException(400, "Reply text required")

    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.resolve_ticket(ticket_id, reply_text)

    if not ticket:
        raise HTTPException(404, "Ticket not found")


    try:
        await _send_bot_message(
            ticket.user_telegram_id,
            f"💬 <b>Ответ на ваш тикет #{ticket_id}</b>\n\n"
            f"{reply_text}\n\n"
            f"<i>— Администратор Dem1chVPN</i>",
        )
    except Exception:
        pass

    return {"success": True, "id": ticket_id}


@api.post("/tickets/{ticket_id}/close", dependencies=[Depends(require_admin)])
async def close_ticket(ticket_id: int):

    ticket_mgr = TicketManager()
    ticket = await ticket_mgr.resolve_ticket(ticket_id)

    if not ticket:
        raise HTTPException(404, "Ticket not found")

    return {"success": True, "id": ticket_id}



@api.get("/my/links", dependencies=[Depends(require_auth)])
async def my_links(request: Request):


    init_data = request.headers.get("X-Telegram-Init-Data", "")
    result = validate_init_data(init_data)
    if not result:
        raise HTTPException(401, "Invalid auth")

    tg_id = result.get("user_id")
    if not tg_id:
        raise HTTPException(401, "No user ID")

    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(tg_id)
    if not user:
        return {
            "has_account": False,
            "sub_url": None,
            "vless_url": None,
            "sub_deeplink": None,
            "route_deeplink": None,
            "sub_redirect_url": None,
            "route_redirect_url": None,
            "win_sub_deeplink": None,
            "win_route_deeplink": None,
            "win_sub_redirect_url": None,
            "win_route_redirect_url": None,
        }

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    sub_deeplink = f"v2raytun://import/{sub_url}"
    win_sub_deeplink = f"dem1chvpn://import/{sub_url}"


    from server.subscription.app import _build_routing_header
    routing_b64 = await _build_routing_header()
    route_deeplink = f"v2raytun://import_route/{routing_b64}" if routing_b64 else None
    win_route_deeplink = f"dem1chvpn://import_route/{routing_b64}" if routing_b64 else None


    sub_redirect_url = f"{config.sub_base_url}/redirect/sub/{user.subscription_token}"
    route_redirect_url = f"{config.sub_base_url}/redirect/route/{user.subscription_token}" if routing_b64 else None
    win_sub_redirect_url = f"{config.sub_base_url}/redirect/win/sub/{user.subscription_token}"
    win_route_redirect_url = f"{config.sub_base_url}/redirect/win/route/{user.subscription_token}" if routing_b64 else None

    return {
        "has_account": True,
        "name": user.name,
        "sub_url": sub_url,
        "vless_url": vless_url,
        "sub_deeplink": sub_deeplink,
        "route_deeplink": route_deeplink,
        "sub_redirect_url": sub_redirect_url,
        "route_redirect_url": route_redirect_url,
        "win_sub_deeplink": win_sub_deeplink,
        "win_route_deeplink": win_route_deeplink,
        "win_sub_redirect_url": win_sub_redirect_url,
        "win_route_redirect_url": win_route_redirect_url,
    }



@api.get("/my/account")
async def my_account(request: Request):

    init_data = request.headers.get("X-Telegram-Init-Data", "")
    result = validate_init_data(init_data)
    if not result:
        raise HTTPException(401, "Invalid auth")

    tg_id = result.get("user_id")
    if not tg_id:
        raise HTTPException(401, "No user ID")

    is_admin = result.get("is_admin", False)

    mgr = UserManager()
    user = await mgr.get_user_by_telegram_id(tg_id)
    if not user:
        return {
            "has_account": False,
            "is_admin": is_admin,
        }

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"
    sub_deeplink = f"v2raytun://import/{sub_url}"
    win_sub_deeplink = f"dem1chvpn://import/{sub_url}"


    route_deeplink = None
    win_route_deeplink = None
    try:
        from server.subscription.app import _build_routing_header
        routing_b64 = await _build_routing_header()
        route_deeplink = f"v2raytun://import_route/{routing_b64}" if routing_b64 else None
        win_route_deeplink = f"dem1chvpn://import_route/{routing_b64}" if routing_b64 else None
    except Exception:
        pass


    traffic_percent = 0
    if user.traffic_limit and user.traffic_limit > 0:
        traffic_percent = min(round(user.traffic_total / user.traffic_limit * 100, 1), 100)


    sub_redirect_url = f"{config.sub_base_url}/redirect/sub/{user.subscription_token}"
    route_redirect_url = f"{config.sub_base_url}/redirect/route/{user.subscription_token}" if route_deeplink else None
    win_sub_redirect_url = f"{config.sub_base_url}/redirect/win/sub/{user.subscription_token}"
    win_route_redirect_url = f"{config.sub_base_url}/redirect/win/route/{user.subscription_token}" if route_deeplink else None

    return {
        "has_account": True,
        "is_admin": is_admin,
        "name": user.name,
        "active": user.is_active,
        "expired": user.is_expired,
        "traffic_up": user.traffic_used_up,
        "traffic_down": user.traffic_used_down,
        "traffic_total": user.traffic_total,
        "traffic_limit": user.traffic_limit,
        "traffic_percent": traffic_percent,
        "expiry": user.expiry_date.isoformat() if user.expiry_date else None,
        "created": user.created_at.isoformat() if user.created_at else None,
        "sub_url": sub_url,
        "vless_url": vless_url,
        "sub_deeplink": sub_deeplink,
        "route_deeplink": route_deeplink,
        "sub_redirect_url": sub_redirect_url,
        "route_redirect_url": route_redirect_url,
        "win_sub_deeplink": win_sub_deeplink,
        "win_route_deeplink": win_route_deeplink,
        "win_sub_redirect_url": win_sub_redirect_url,
        "win_route_redirect_url": win_route_redirect_url,
    }
