"""
Dem1chVPN — Invite Manager Service
"""
from typing import Optional
from sqlalchemy import select, update
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
        # Атомарный захват слота: инкремент проходит только пока есть свободные использования.
        # Два параллельных перехода по одноразовой ссылке: один получит rowcount=1, второй — 0.
        async with async_session() as session:
            result = await session.execute(
                update(Invite)
                .where(
                    Invite.code == code,
                    Invite.is_active == True,  # noqa: E712
                    Invite.times_used < Invite.max_uses,
                )
                .values(times_used=Invite.times_used + 1)
            )
            if result.rowcount == 0:
                await session.rollback()
                return False
            await session.execute(
                update(Invite)
                .where(Invite.code == code, Invite.times_used >= Invite.max_uses)
                .values(is_active=False)
            )
            await session.commit()
            return True

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
