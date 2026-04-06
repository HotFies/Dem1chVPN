"""
Dem1chVPN — Formatters
"""
from datetime import datetime, timezone
from typing import Optional


def format_traffic(bytes_val: Optional[int]) -> str:

    if bytes_val is None:
        return "♾️"
    if bytes_val == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    val = float(bytes_val)
    for unit in units:
        if abs(val) < 1024.0:
            return f"{val:.1f} {unit}"
        val /= 1024.0
    return f"{val:.1f} PB"


def format_user_info(user) -> str:

    status = "🟢 Активен" if user.is_active else "🔴 Заблокирован"
    if user.is_expired:
        status = "⏰ Истёк"
    if user.is_traffic_exceeded:
        status = "📊 Лимит трафика"


    online = "⚪ Офлайн"
    if user.is_active and user.last_seen_at:
        from datetime import timedelta
        delta = datetime.now(timezone.utc) - user.last_seen_at
        if delta < timedelta(seconds=120):
            online = "🟢 Онлайн"
        elif delta < timedelta(hours=1):
            minutes = int(delta.total_seconds() // 60)
            online = f"🕐 {minutes} мин назад"

    traffic_up = format_traffic(user.traffic_used_up)
    traffic_down = format_traffic(user.traffic_used_down)
    traffic_total = format_traffic(user.traffic_total)
    traffic_limit = format_traffic(user.traffic_limit) if user.traffic_limit else "♾️"

    expiry = "♾️ Бессрочно"
    if user.expiry_date:
        remaining = user.expiry_date - datetime.now(timezone.utc)
        if remaining.days > 0:
            expiry = f"{remaining.days}д осталось"
        else:
            expiry = "⏰ Истёк"

    created = user.created_at.strftime("%d.%m.%Y") if user.created_at else "—"

    return (
        f"📋 Статус: {status}\n"
        f"🌐 Сеть: {online}\n"
        f"📊 Трафик: {traffic_total} / {traffic_limit}\n"
        f"  ↑ Upload: {traffic_up}\n"
        f"  ↓ Download: {traffic_down}\n"
        f"⏰ Срок: {expiry}\n"
        f"📅 Создан: {created}"
    )


def format_uptime(seconds: float) -> str:

    days = int(seconds // 86400)
    hours = int((seconds % 86400) // 3600)
    minutes = int((seconds % 3600) // 60)

    parts = []
    if days > 0:
        parts.append(f"{days}д")
    if hours > 0:
        parts.append(f"{hours}ч")
    parts.append(f"{minutes}м")

    return " ".join(parts)


def progress_bar(current: float, total: float, length: int = 8) -> str:

    if total == 0:
        return "░" * length
    ratio = min(current / total, 1.0)
    filled = int(length * ratio)
    return "█" * filled + "░" * (length - filled)


def format_bytes_speed(bps: float) -> str:

    if bps < 1024:
        return f"{bps:.0f} B/s"
    elif bps < 1024 * 1024:
        return f"{bps / 1024:.1f} KB/s"
    elif bps < 1024 * 1024 * 1024:
        return f"{bps / (1024 * 1024):.1f} MB/s"
    else:
        return f"{bps / (1024 * 1024 * 1024):.2f} GB/s"
