"""
Dem1chVPN — Аутентификация WebApp
"""
import hashlib
import hmac
import json
import time
import urllib.parse
from typing import Optional

from fastapi import Request, HTTPException

import sys
from pathlib import Path


PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.bot.config import config


def validate_init_data(init_data: str) -> Optional[dict]:

    if not init_data:
        return None

    try:
        params = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))


        received_hash = params.pop("hash", "")
        if not received_hash:
            return None


        data_check_parts = sorted(params.items())
        data_check_string = "\n".join(f"{k}={v}" for k, v in data_check_parts)


        secret_key = hmac.new(
            b"WebAppData",
            config.BOT_TOKEN.encode("utf-8"),
            hashlib.sha256,
        ).digest()


        expected_hash = hmac.new(
            secret_key,
            data_check_string.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()


        if not hmac.compare_digest(expected_hash, received_hash):
            return None


        auth_date = int(params.get("auth_date", "0"))
        if time.time() - auth_date > 86400:
            return None


        user_data = params.get("user", "{}")
        try:
            user = json.loads(user_data)
        except (json.JSONDecodeError, TypeError):
            user = {}

        return {
            "user_id": user.get("id"),
            "first_name": user.get("first_name", ""),
            "username": user.get("username", ""),
            "is_admin": user.get("id") in config.ADMIN_IDS if user.get("id") else False,
            "raw_params": params,
        }

    except Exception:
        return None


async def require_admin(request: Request) -> dict:


    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not init_data:
        init_data = request.query_params.get("initData", "")

    if not init_data:

        try:
            body = await request.json()
            init_data = body.get("initData", "")
        except Exception:
            pass

    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")

    result = validate_init_data(init_data)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid initData")

    if not result.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")

    return result


async def require_auth(request: Request) -> dict:

    init_data = request.headers.get("X-Telegram-Init-Data", "")
    if not init_data:
        init_data = request.query_params.get("initData", "")

    if not init_data:
        try:
            body = await request.json()
            init_data = body.get("initData", "")
        except Exception:
            pass

    if not init_data:
        raise HTTPException(status_code=401, detail="Missing initData")

    result = validate_init_data(init_data)
    if result is None:
        raise HTTPException(status_code=401, detail="Invalid initData")

    return result
