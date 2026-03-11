"""
Database Session Management for Cyber Incident Response AI

Provides database engine, session factory, and connection management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator
import logging
import os

from .models import Base

logger = logging.getLogger(__name__)

# Global engine and session factory
_engine = None
_SessionLocal = None


def init_database(database_url: str = None, echo: bool = False):
    """
    Initialize database engine and create tables.
    
    Args:
        database_url: SQLAlchemy database URL (default: sqlite:///./cyber_ir.db)
        echo: Whether to echo SQL statements
    """
    global _engine, _SessionLocal
    
    if database_url is None:
        database_url = os.getenv('DATABASE_URL', 'sqlite:///./cyber_ir.db')
    
    logger.info(f"Initializing database: {database_url}")
    
    # Create engine
    if database_url.startswith('sqlite'):
        # SQLite-specific configuration
        _engine = create_engine(
            database_url,
            echo=echo,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
    else:
        # PostgreSQL or other databases
        _engine = create_engine(
            database_url,
            echo=echo,
            pool_size=10,
            max_overflow=20
        )
    
    # Create session factory
    _SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=_engine
    )
    
    # Create all tables
    Base.metadata.create_all(bind=_engine)
    logger.info("Database tables created successfully")


def get_engine():
    """Get database engine."""
    if _engine is None:
        init_database()
    return _engine


def get_session_factory():
    """Get session factory."""
    if _SessionLocal is None:
        init_database()
    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    
    Usage:
        with get_db_session() as session:
            session.query(Alert).all()
    """
    SessionLocal = get_session_factory()
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {str(e)}")
        raise
    finally:
        session.close()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency for FastAPI endpoints.
    
    Usage:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def reset_database():
    """Drop all tables and recreate them. USE WITH CAUTION!"""
    logger.warning("Resetting database - all data will be lost!")
    engine = get_engine()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    logger.info("Database reset complete")


def close_database():
    """Close database connections."""
    global _engine, _SessionLocal
    if _engine:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
        logger.info("Database connections closed")
