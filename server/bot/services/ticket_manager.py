"""
Dem1chVPN — Ticket Manager Service
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select

from ..database import async_session, Ticket

logger = logging.getLogger("dem1chvpn.ticket_manager")


class TicketManager:
    """Manages support tickets."""

    async def create_ticket(
        self,
        user_telegram_id: int,
        user_name: str,
        message: str,
    ) -> Optional[Ticket]:
        """Create a new support ticket."""
        async with async_session() as session:
            ticket = Ticket(
                user_telegram_id=user_telegram_id,
                user_name=user_name,
                message=message,
            )
            session.add(ticket)
            await session.commit()
            await session.refresh(ticket)
            return ticket

    async def get_open_tickets(self) -> list[Ticket]:
        """Get all unresolved tickets, newest first."""
        async with async_session() as session:
            result = await session.execute(
                select(Ticket)
                .where(Ticket.is_resolved == False)
                .order_by(Ticket.created_at.desc())
            )
            return list(result.scalars().all())

    async def get_ticket(self, ticket_id: int) -> Optional[Ticket]:
        """Get a ticket by ID."""
        async with async_session() as session:
            result = await session.execute(
                select(Ticket).where(Ticket.id == ticket_id)
            )
            return result.scalar_one_or_none()

    async def resolve_ticket(
        self,
        ticket_id: int,
        reply_text: Optional[str] = None,
    ) -> Optional[Ticket]:
        """Resolve a ticket and optionally add a reply."""
        async with async_session() as session:
            result = await session.execute(
                select(Ticket).where(Ticket.id == ticket_id)
            )
            ticket = result.scalar_one_or_none()
            if ticket:
                ticket.is_resolved = True
                ticket.resolved_at = datetime.now(timezone.utc)
                if reply_text:
                    ticket.reply = reply_text
                await session.commit()
                await session.refresh(ticket)
            return ticket

    async def count_open_tickets(self) -> int:
        """Count unresolved tickets."""
        from sqlalchemy import func
        async with async_session() as session:
            result = await session.execute(
                select(func.count(Ticket.id)).where(Ticket.is_resolved == False)
            )
            return result.scalar() or 0

    async def get_user_tickets(self, telegram_id: int) -> list[Ticket]:
        """Get all tickets for a specific user (by TG ID)."""
        async with async_session() as session:
            result = await session.execute(
                select(Ticket)
                .where(Ticket.user_telegram_id == telegram_id)
                .order_by(Ticket.created_at.desc())
            )
            return list(result.scalars().all())

    async def get_closed_tickets(self) -> list[Ticket]:
        """Get all resolved tickets."""
        async with async_session() as session:
            result = await session.execute(
                select(Ticket)
                .where(Ticket.is_resolved == True)
                .order_by(Ticket.created_at.desc())
            )
            return list(result.scalars().all())

    async def get_all_tickets(self) -> list[Ticket]:
        """Get all tickets (open + closed)."""
        async with async_session() as session:
            result = await session.execute(
                select(Ticket).order_by(Ticket.created_at.desc())
            )
            return list(result.scalars().all())
