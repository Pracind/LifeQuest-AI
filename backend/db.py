"""
Database connection setup for LifeQuest AI.

- Loads DATABASE_URL from environment (.env)
- Creates a SQLAlchemy engine and SessionLocal factory
- Exposes get_db() for FastAPI dependency injection
"""

import os
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Load environment variables from .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set. "
        "Make sure you have a .env file with DATABASE_URL defined."
    )

# Create the SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # checks connections before using them
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a DB session and closes it after the request.
    
    Usage in FastAPI routes:
    
    from fastapi import Depends
    from .db import get_db
    from . import models
    
    @router.get("/goals")
    def list_goals(db: Session = Depends(get_db)):
        return db.query(models.Goal).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
