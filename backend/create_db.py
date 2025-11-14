"""
Initialize the database schema for LifeQuest AI.

- Imports SQLAlchemy Base from models.py
- Uses the engine from db.py (which connects to Supabase)
- Calls Base.metadata.create_all(engine) to create tables

Run this once (or whenever models change) to sync tables in dev.
"""

from backend.models import Base
from backend.db import engine


def init_db() -> None:
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Done.")


if __name__ == "__main__":
    init_db()
