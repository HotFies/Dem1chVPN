"""
XShield — WebApp REST API
REST endpoints for the Telegram Mini App.
All admin endpoints require Telegram initData validation.
"""
import psutil
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse

import sys
from pathlib import Path

# Ensure project root is in path for imports
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


# ── Auth ──

@api.post("/auth/check")
async def auth_check(request: Request):
    """Verify Telegram Mini App initData."""
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


# ── Server Status ──

@api.get("/status", dependencies=[Depends(require_auth)])
async def server_status():
    """Get server status for dashboard."""
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


# ── Users ──

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
    """Toggle user active status."""
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
    """Get VLESS link for a user."""
    mgr = UserManager()
    user = await mgr.get_user(user_id)
    if not user:
        raise HTTPException(404, "User not found")

    xray_mgr = XrayConfigManager()
    vless_url = xray_mgr.generate_vless_url(user.uuid, user.name)
    sub_url = f"{config.sub_base_url}/sub/{user.subscription_token}"

    return {"vless_url": vless_url, "sub_url": sub_url}


# ── Routes ──

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


# ── Settings ──

@api.get("/settings", dependencies=[Depends(require_admin)])
async def get_settings():
    return {
        "warp_enabled": config.WARP_ENABLED,
        "adguard_enabled": config.ADGUARD_ENABLED,
        "mtproto_enabled": config.MTPROTO_ENABLED,
        "server_ip": config.SERVER_IP,
        "reality_sni": config.REALITY_SNI,
    }


@api.post("/settings/{feature}/toggle", dependencies=[Depends(require_admin)])
async def toggle_feature(feature: str):
    if feature == "warp":
        from server.bot.services.warp_manager import WarpManager
        mgr = WarpManager()
        new_state = await mgr.toggle()
        return {"enabled": new_state}
    elif feature == "adguard":
        from server.bot.services.adguard_api import AdGuardAPI
        api_client = AdGuardAPI()
        status = await api_client.get_status()
        new_state = not status.get("protection_enabled", False)
        await api_client.toggle_protection(new_state)
        return {"enabled": new_state}
    elif feature == "mtproto":
        from server.bot.services.mtproto_manager import MTProtoManager
        mgr = MTProtoManager()
        if await mgr.is_running():
            await mgr.stop()
            return {"enabled": False}
        else:
            await mgr.start()
            return {"enabled": True}

    raise HTTPException(400, "Unknown feature")


# ── Actions ──

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
        "bash", "/opt/xshield/cron/update_geodata.sh",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=120)
    return {"success": True}


@api.post("/backup", dependencies=[Depends(require_admin)])
async def create_backup():
    """Create and return backup info."""
    import asyncio
    proc = await asyncio.create_subprocess_exec(
        "bash", "/opt/xshield/cron/backup.sh",
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.wait_for(proc.communicate(), timeout=30)
    return {"success": True, "message": "Backup created. Check /opt/xshield/backups/"}
