"""
Dem1chVPN — Common Authentication Utilities
Shared admin check function used across handlers and middleware.
"""
from ..config import config


def is_admin(user_id: int) -> bool:
    """Check if user is an admin by Telegram user ID."""
    return user_id in config.ADMIN_IDS
