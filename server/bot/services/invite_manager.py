"""
Dem1chVPN — Invite Manager Service
"""
from typing import Optional
from sqlalchemy import select
from ..database import async_session, Invite


class InviteManager:

    async def create_invite(
        self, name: str, traffic_limit: Optional[int] = None,
        days_valid: Optional[int] = None, created_by: Optional[int] = None,
    ) -> Invite:
        async with async_session() as session:
            invite = Invite(
                name=name, traffic_limit=traffic_limit,
                days_valid=days_valid, created_by=created_by,
            )
            session.add(invite)
            await session.commit()
            await session.refresh(invite)
            return invite

    async def get_invite(self, code: str) -> Optional[Invite]:
        async with async_session() as session:
            result = await session.execute(
                select(Invite).where(Invite.code == code)
            )
            return result.scalar_one_or_none()

    async def use_invite(self, code: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Invite).where(Invite.code == code)
            )
            invite = result.scalar_one_or_none()
            if invite:
                invite.times_used += 1
                if invite.times_used >= invite.max_uses:
                    invite.is_active = False
                await session.commit()
                return True
            return False

    async def get_all_invites(self) -> list[Invite]:
        async with async_session() as session:
            result = await session.execute(
                select(Invite).order_by(Invite.created_at.desc())
            )
            return list(result.scalars().all())

    async def revoke_invite(self, code: str) -> bool:
        async with async_session() as session:
            result = await session.execute(
                select(Invite).where(Invite.code == code)
            )
            invite = result.scalar_one_or_none()
            if invite:
                invite.is_active = False
                await session.commit()
                return True
            return False
