#!/usr/bin/env python3
"""
Database Connection and Session Management
==========================================
PostgreSQL connection with SQLAlchemy ORM.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import os
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

# Get database URL from environment
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://fantasy_user:fantasy_pass@localhost:5432/fantasy_cricket"
)

# Create engine
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# =============================================================================
# SESSION MANAGEMENT
# =============================================================================

def get_db() -> Session:
    """
    Dependency for FastAPI endpoints.

    Usage:
        @app.get("/players")
        def get_players(db: Session = Depends(get_db)):
            return db.query(Player).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager for scripts and background tasks.

    Usage:
        with get_db_session() as db:
            players = db.query(Player).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()


# =============================================================================
# DATABASE INITIALIZATION
# =============================================================================

def init_db():
    """
    Initialize database schema.
    Creates all tables if they don't exist.
    """
    from database_models import Base

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")


def reset_db():
    """
    Drop and recreate all tables.
    ⚠️  USE WITH CAUTION - DELETES ALL DATA
    """
    from database_models import Base

    logger.warning("⚠️  Dropping all database tables...")
    Base.metadata.drop_all(bind=engine)

    logger.info("Creating fresh database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database reset complete")


def test_connection():
    """
    Test database connection.
    Returns True if connection is successful.
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_or_create(session: Session, model, **kwargs):
    """
    Get existing instance or create new one.

    Usage:
        season = get_or_create(db, Season, year="2026",
                              defaults={"name": "Topklasse 2026"})
    """
    defaults = kwargs.pop('defaults', {})
    instance = session.query(model).filter_by(**kwargs).first()

    if instance:
        return instance, False
    else:
        kwargs.update(defaults)
        instance = model(**kwargs)
        session.add(instance)
        session.flush()
        return instance, True


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    print("\n🔧 Database Connection Test\n")

    # Test connection
    if test_connection():
        print("\n✅ Connection successful!")
        print(f"   Database: {DATABASE_URL.split('@')[1]}")
    else:
        print("\n❌ Connection failed!")
        print(f"   Check DATABASE_URL: {DATABASE_URL}")
        exit(1)

    # Initialize schema
    choice = input("\nInitialize database schema? (y/n): ")
    if choice.lower() == 'y':
        init_db()
        print("\n✅ Database initialized")
