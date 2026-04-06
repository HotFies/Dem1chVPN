"""
Dem1chVPN Bot — Database Models & Engine
"""
import uuid as uuid_lib
import secrets
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, BigInteger, Float, Text,
    ForeignKey, create_engine, event,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship

from .config import config

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid_lib.uuid4()))
    email = Column(String(200), unique=True, nullable=False)
    telegram_id = Column(BigInteger, nullable=True)
    subscription_token = Column(String(64), unique=True, nullable=False,
                                default=lambda: secrets.token_urlsafe(32))

    traffic_limit = Column(BigInteger, nullable=True)
    traffic_used_up = Column(BigInteger, default=0)
    traffic_used_down = Column(BigInteger, default=0)
    expiry_date = Column(DateTime, nullable=True)

    is_active = Column(Boolean, default=True)
    warning_sent = Column(Boolean, default=False)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    traffic_logs = relationship("TrafficLog", back_populates="user", cascade="all, delete-orphan")

    @property
    def traffic_total(self) -> int:
        return self.traffic_used_up + self.traffic_used_down

    @property
    def is_expired(self) -> bool:
        if self.expiry_date is None:
            return False
        return datetime.now(timezone.utc) > self.expiry_date

    @property
    def is_traffic_exceeded(self) -> bool:
        if self.traffic_limit is None:
            return False
        return self.traffic_total >= self.traffic_limit

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', active={self.is_active})>"


class RouteRule(Base):
    __tablename__ = "route_rules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    domain = Column(String(255), unique=True, nullable=False)
    rule_type = Column(String(10), nullable=False)
    added_by = Column(String(50), default="admin")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<RouteRule(domain='{self.domain}', type='{self.rule_type}')>"


class Invite(Base):
    __tablename__ = "invites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(32), unique=True, nullable=False,
                  default=lambda: secrets.token_urlsafe(8))
    name = Column(String(100), nullable=False)
    traffic_limit = Column(BigInteger, nullable=True)
    days_valid = Column(Integer, nullable=True)
    max_uses = Column(Integer, default=1)
    times_used = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    @property
    def is_exhausted(self) -> bool:
        return self.times_used >= self.max_uses

    def __repr__(self):
        return f"<Invite(code='{self.code}', name='{self.name}', used={self.times_used}/{self.max_uses})>"


class TrafficLog(Base):
    __tablename__ = "traffic_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    upload = Column(BigInteger, default=0)
    download = Column(BigInteger, default=0)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="traffic_logs")


class ServerConfig(Base):
    __tablename__ = "server_config"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<ServerConfig(key='{self.key}')>"


class BackupRecord(Base):
    __tablename__ = "backup_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)
    size = Column(BigInteger, default=0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    action = Column(String(100), nullable=False)
    admin_id = Column(BigInteger, nullable=True)
    target_user_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<AuditLog(action='{self.action}', admin={self.admin_id})>"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_telegram_id = Column(BigInteger, nullable=False)
    user_name = Column(String(200), nullable=True)
    message = Column(Text, nullable=False)
    reply = Column(Text, nullable=True)
    is_resolved = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<Ticket(id={self.id}, user={self.user_name}, resolved={self.is_resolved})>"


def get_db_url() -> str:
    return f"sqlite+aiosqlite:///{config.DB_PATH}"


engine = create_async_engine(
    get_db_url(),
    echo=False,
    future=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def init_db():
    db_dir = Path(config.DB_PATH).parent
    db_dir.mkdir(parents=True, exist_ok=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

