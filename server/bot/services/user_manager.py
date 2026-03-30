"""
XShield — User Manager Service
CRUD operations for VPN users.
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy import select

from ..database import async_session, User

logger = logging.getLogger("xshield.user_manager")


class UserManager:
    """Manages VPN users in the database."""

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
            email = f"{email_base}_{user_uuid[:8]}@xshield"

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

    async def get_active_users(self) -> list[User]:
        """Get all active users."""
        async with async_session() as session:
            result = await session.execute(
                select(User).where(User.is_active == True).order_by(User.name)
            )
            return list(result.scalars().all())

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
