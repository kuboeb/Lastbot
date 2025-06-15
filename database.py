import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
from contextlib import asynccontextmanager

import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, DateTime, Boolean, BIGINT, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func

from config import config

# Создаем базовый класс для моделей
Base = declarative_base()

# Создаем движок базы данных
engine = create_async_engine(
    config.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://'),
    echo=False,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True,
    pool_recycle=3600
)

# Создаем фабрику сессий
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Модели базы данных

class BotUser(Base):
    __tablename__ = 'bot_users'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, unique=True, nullable=False)
    username = Column(String(100))
    first_seen = Column(DateTime, default=func.now())
    last_activity = Column(DateTime, default=func.now(), onupdate=func.now())
    source_id = Column(Integer, ForeignKey('traffic_sources.id'))
    has_application = Column(Boolean, default=False)
    is_blocked = Column(Boolean, default=False)
    registration_step = Column(String(50))

class Application(Base):
    __tablename__ = 'applications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, ForeignKey('bot_users.user_id'), unique=True)
    full_name = Column(String(255), nullable=False)
    country = Column(String(100), nullable=False)
    phone = Column(String(50), nullable=False)
    preferred_time = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())
    referrer_id = Column(BIGINT)
    source_id = Column(Integer, ForeignKey('traffic_sources.id'))

class TrafficSource(Base):
    __tablename__ = 'traffic_sources'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    platform = Column(String(50), nullable=False)
    tracking_code = Column(String(100), unique=True, nullable=False)
    link = Column(String(500))
    settings = Column(JSON)
    created_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

class Referral(Base):
    __tablename__ = 'referrals'
    
    id = Column(Integer, primary_key=True)
    referrer_id = Column(BIGINT, nullable=False)
    referred_id = Column(BIGINT, nullable=False)
    created_at = Column(DateTime, default=func.now())
    status = Column(String(20), default='registered')

class UserAction(Base):
    __tablename__ = 'user_actions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BIGINT, nullable=False)
    action = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())

class BotText(Base):
    __tablename__ = 'bot_texts'
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    category = Column(String(50))
    text = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey('admins.id'))

class Admin(Base):
    __tablename__ = 'admins'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())

class Operator(Base):
    __tablename__ = 'operators'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now())

# Менеджер базы данных
class DatabaseManager:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """Создает пул соединений с базой данных"""
        self.pool = await asyncpg.create_pool(
            config.DATABASE_URL,
            min_size=10,
            max_size=20,
            command_timeout=60
        )
    
    async def disconnect(self):
        """Закрывает пул соединений"""
        if self.pool:
            await self.pool.close()
    
    @asynccontextmanager
    async def get_session(self):
        """Контекстный менеджер для работы с сессией"""
        async with async_session() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def create_tables(self):
        """Создает все таблицы в базе данных"""
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

# Создаем экземпляр менеджера БД
db_manager = DatabaseManager()

class TrackingEvent(Base):
    __tablename__ = 'tracking_events'
    
    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey('traffic_sources.id'))
    user_id = Column(BIGINT)
    event_type = Column(String(50))
    created_at = Column(DateTime, default=func.now())

class IntegrationLog(Base):
    __tablename__ = 'integration_logs'
    
    id = Column(Integer, primary_key=True)
    integration_id = Column(Integer)
    application_id = Column(Integer, ForeignKey('applications.id'))
    status = Column(String(20))
    request_data = Column(JSON)
    response_data = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
