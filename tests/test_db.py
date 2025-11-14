from sqlalchemy import text
from backend.db import SessionLocal
from backend.models import User


def test_db_connection_and_demo_user():
    """
    Basic sanity test:
    - We can open a DB session
    - The demo user from seed_demo.py exists
    """
    db = SessionLocal()
    try:
        # Simple query to ensure connection works
        result = db.execute(text("SELECT 1")).scalar_one()
        assert result == 1

        # Check demo user
        demo_user = db.query(User).filter(User.email == "demo@lifequest.test").first()
        assert demo_user is not None, "Demo user not found. Did you run seed_demo.py?"
        assert demo_user.email == "demo@lifequest.test"
    finally:
        db.close()
