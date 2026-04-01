"""
Dem1chVPN — User Manager Service
CRUD operations for VPN users + auto-limit enforcement.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select

from ..database import async_session, User, AuditLog, TrafficLog

logger = logging.getLogger("dem1chvpn.user_manager")


class UserManager:
    """Manages VPN users in the database. Singleton — UserManager() always returns the same instance."""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    async def create_user(
        self,
        name: str,
        traffic_limit: Optional[int] = None,
        expiry_days: Optional[int] = None,
        telegram_id: Optional[int] = None,
    ) -> Optional[User]:
        """Create a new user."""
        import uuid as uuid_module
        async with async_session() as session:
            user_uuid = str(uuid_module.uuid4())
            # Use UUID prefix in email to guarantee uniqueness
            email_base = name.lower().replace(' ', '_').replace('@', '')[:20]
            email = f"{email_base}_{user_uuid[:8]}@dem1chvpn"

            user = User(
                name=name,
                uuid=user_uuid,
                email=email,
                traffic_limit=traffic_limit,
                telegram_id=telegram_id,
            )
            if expiry_days:
                user.expiry_date = datetime.now(timezone.utc) + timedelta(days=expiry_days)

            try:
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
            except Exception as e:
                await session.rollback()
                logger.error(f"Error creating user: {e}")
                return None

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by DB id."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            return result.scalar_one_or_none()

    async def get_user_by_uuid(self, uuid: str) -> Optional[User]:
        """Get user by Xray UUID."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.uuid == uuid))
            return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email tag."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            return result.scalar_one_or_none()

    async def get_user_by_telegram_id(self, tg_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == tg_id)
            )
            return result.scalar_one_or_none()

    async def get_user_by_subscription_token(self, token: str) -> Optional[User]:
        """Get user by subscription token."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.subscription_token == token)
            )
            return result.scalar_one_or_none()

    async def get_all_users(self) -> list[User]:
        """Get all users."""
        async with async_session() as session:
            result = await session.execute(
                select(User).order_by(User.created_at.desc())
            )
            return list(result.scalars().all())

    async def link_telegram(self, user_id: int, telegram_id: int) -> Optional[User]:
        """Link a Telegram account to a VPN user."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.telegram_id = telegram_id
                await session.commit()
                await session.refresh(user)
            return user

    async def get_active_users(self) -> list[User]:
        """Get all active users."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.is_active == True).order_by(User.name)
            )
            return list(result.scalars().all())

    async def get_users_page(self, page: int = 0, per_page: int = 8) -> tuple[list[User], int]:
        """Get paginated users. Returns (users, total_count)."""
        async with async_session() as session:
            from sqlalchemy import func
            total = (await session.execute(select(func.count(User.id)))).scalar()
            result = await session.execute(
                select(User)
                .order_by(User.created_at.desc())
                .offset(page * per_page)
                .limit(per_page)
            )
            return list(result.scalars().all()), total

    async def toggle_user(self, user_id: int) -> Optional[User]:
        """Toggle user active status."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_active = not user.is_active
                await session.commit()
                await session.refresh(user)
            return user

    async def set_user_active(self, user_id: int, active: bool) -> Optional[User]:
        """Explicitly set user active status (for auto-block)."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.is_active = active
                await session.commit()
                await session.refresh(user)
            return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete user by id."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                await session.delete(user)
                await session.commit()
                return True
            return False

    async def update_traffic(self, email: str, upload: int, download: int) -> Optional[User]:
        """Set user traffic counters to absolute values (overwrites, not increments)."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user.traffic_used_up = upload
                user.traffic_used_down = download
                await session.commit()
                await session.refresh(user)
            return user

    async def reset_traffic(self, user_id: int) -> Optional[User]:
        """Reset user traffic counters."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.traffic_used_up = 0
                user.traffic_used_down = 0
                await session.commit()
                await session.refresh(user)
            return user

    async def count_users(self) -> int:
        """Count total users."""
        async with async_session() as session:
            from sqlalchemy import func
            result = await session.execute(select(func.count(User.id)))
            return result.scalar()

    async def add_traffic(self, user_id: int, upload: int = 0, download: int = 0) -> Optional[User]:
        """Increment user traffic counters (additive, not absolute)."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.traffic_used_up += upload
                user.traffic_used_down += download
                await session.commit()
                await session.refresh(user)
            return user

    async def get_expired_active_users(self) -> list[User]:
        """Get users whose accounts are expired but still active."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.expiry_date != None,
                    User.expiry_date < datetime.now(timezone.utc),
                )
            )
            return list(result.scalars().all())

    async def get_traffic_exceeded_users(self) -> list[User]:
        """Get active users who exceeded their traffic limit."""
        async with async_session() as session:
            # SQLAlchemy can't compute traffic_total in SQL easily,
            # so we fetch all limited users and check in Python.
            result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.traffic_limit != None,
                )
            )
            users = list(result.scalars().all())
            return [u for u in users if u.traffic_total >= u.traffic_limit]

    # ── Audit Logging ──

    async def log_action(
        self,
        action: str,
        admin_id: Optional[int] = None,
        target_user_id: Optional[int] = None,
        details: Optional[str] = None,
    ):
        """Log an admin/system action to audit log."""
        async with async_session() as session:
            entry = AuditLog(
                action=action,
                admin_id=admin_id,
                target_user_id=target_user_id,
                details=details,
            )
            session.add(entry)
            await session.commit()

    # ── Online Status (#1) ──

    async def update_last_seen(self, email: str):
        """Update last_seen_at for a user (called from traffic_sync)."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            if user:
                user.last_seen_at = datetime.now(timezone.utc)
                await session.commit()

    async def get_online_users(self, threshold_seconds: int = 120) -> list[User]:
        """Get users who had traffic within the last N seconds."""
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=threshold_seconds)
        async with async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.last_seen_at != None,
                    User.last_seen_at >= cutoff,
                )
            )
            return list(result.scalars().all())

    # ── Extend / Reset (#2) ──

    async def extend_user(self, user_id: int, days: int) -> Optional[User]:
        """Extend user expiry by N days (from now or from current expiry)."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                base = user.expiry_date if user.expiry_date and user.expiry_date > datetime.now(timezone.utc) else datetime.now(timezone.utc)
                user.expiry_date = base + timedelta(days=days)
                # Only reactivate if was blocked specifically by expiry
                # (i.e. the user was inactive AND had an expired date)
                if not user.is_active and user.expiry_date and not user.is_traffic_exceeded:
                    user.is_active = True
                await session.commit()
                await session.refresh(user)
            return user

    async def set_traffic_limit(self, user_id: int, limit_bytes: Optional[int]) -> Optional[User]:
        """Change user traffic limit."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.traffic_limit = limit_bytes
                user.warning_sent = False  # Reset warning flag
                await session.commit()
                await session.refresh(user)
            return user

    # ── 80% Warning (#3) ──

    async def set_warning_sent(self, user_id: int, sent: bool = True):
        """Mark that 80% warning was sent to user."""
        async with async_session() as session:
            result = await session.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()
            if user:
                user.warning_sent = sent
                await session.commit()

    async def get_warning_candidates(self) -> list[User]:
        """Get active users at >=80% traffic who haven't been warned yet."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(
                    User.is_active == True,
                    User.traffic_limit != None,
                    User.warning_sent == False,
                )
            )
            users = list(result.scalars().all())
            return [u for u in users if u.traffic_limit and u.traffic_total >= u.traffic_limit * 0.8]

    # ── Monthly Reset (#6) ──

    async def reset_all_traffic_limited(self) -> int:
        """Reset traffic for all users with a limit. Returns count reset."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.traffic_limit != None)
            )
            users = list(result.scalars().all())
            count = 0
            for user in users:
                user.traffic_used_up = 0
                user.traffic_used_down = 0
                user.warning_sent = False
                count += 1
            await session.commit()
            return count

    async def reactivate_traffic_blocked(self) -> list[User]:
        """Reactivate users that were auto-blocked by traffic limit."""
        async with async_session() as session:
            # Find users blocked by traffic with a limit
            result = await session.execute(
                select(User).where(
                    User.is_active == False,
                    User.traffic_limit != None,
                )
            )
            users = list(result.scalars().all())
            reactivated = []
            for user in users:
                # Only reactivate if traffic is now under limit (after reset)
                if user.traffic_total < (user.traffic_limit or 0):
                    user.is_active = True
                    reactivated.append(user)
            await session.commit()
            return reactivated

    async def reset_and_reactivate_traffic(self) -> tuple[int, list[User]]:
        """Reset traffic and reactivate blocked users in a single transaction.
        Eliminates race condition between separate reset + reactivate calls.
        Returns: (reset_count, reactivated_users)
        """
        async with async_session() as session:
            # Step 1: Reset traffic for all limited users
            result = await session.execute(
                select(User).where(User.traffic_limit != None)
            )
            limited_users = list(result.scalars().all())
            reset_count = 0
            for user in limited_users:
                user.traffic_used_up = 0
                user.traffic_used_down = 0
                user.warning_sent = False
                reset_count += 1

            # Step 2: Reactivate users blocked by traffic (now within same session)
            result = await session.execute(
                select(User).where(
                    User.is_active == False,
                    User.traffic_limit != None,
                )
            )
            blocked_users = list(result.scalars().all())
            reactivated = []
            for user in blocked_users:
                # After reset above, traffic_total is 0 → always under limit
                if user.traffic_total < (user.traffic_limit or 0):
                    user.is_active = True
                    reactivated.append(user)

            await session.commit()
            return reset_count, reactivated

    # ── Traffic Snapshots (#8) ──

    async def save_traffic_snapshot(self, user_id: int, upload: int, download: int):
        """Save a traffic snapshot to TrafficLog."""
        async with async_session() as session:
            log = TrafficLog(user_id=user_id, upload=upload, download=download)
            session.add(log)
            await session.commit()

    async def get_traffic_history(self, user_id: int, hours: int = 24) -> list:
        """Get traffic snapshots for a user within the last N hours."""
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        async with async_session() as session:
            result = await session.execute(
                select(TrafficLog)
                .where(TrafficLog.user_id == user_id, TrafficLog.recorded_at >= cutoff)
                .order_by(TrafficLog.recorded_at.asc())
            )
            return list(result.scalars().all())

    # ── Broadcast (#7) ──

    async def get_users_with_telegram(self) -> list[User]:
        """Get all users with linked Telegram ID (for broadcast)."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id != None)
            )
            return list(result.scalars().all())

