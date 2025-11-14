"""
Insert demo seed data for development/testing.
Run once after create_db.py has successfully created tables.
"""

from backend.db import SessionLocal
from backend.models import User, Goal, Step, DifficultyEnum
from datetime import datetime
import bcrypt


def seed():
    db = SessionLocal()

    print("Seeding demo data...")

    # Check if demo user already exists
    existing = db.query(User).filter(User.email == "demo@lifequest.test").first()
    if existing:
        print("⚠️ Demo user already exists. Skipping insert.")
        db.close()
        return

    # Create password hash for demo password: demo123
    password = "demo123"
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Create sample user
    user = User(
        email="demo@lifequest.test",
        password_hash=password_hash,
        display_name="Demo User",
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Create sample goal
    goal = Goal(
        user_id=user.id,
        title="Learn Guitar",
        description="Practice guitar daily to play a full song in 30 days",
        created_at=datetime.utcnow(),
        is_confirmed=True,
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    # Create steps
    step1 = Step(
        goal_id=goal.id,
        title="Buy a guitar",
        description="Purchase an acoustic guitar from a local store",
        position=1,
        difficulty=DifficultyEnum.easy,
        est_time_minutes=30,
    )

    step2 = Step(
        goal_id=goal.id,
        title="Learn basic chords",
        description="Practice C, G, D chords for 30 minutes",
        position=2,
        difficulty=DifficultyEnum.medium,
        est_time_minutes=60,
    )

    db.add(step1)
    db.add(step2)
    db.commit()

    print("🎉 Demo seed inserted successfully!")
    db.close()


if __name__ == "__main__":
    seed()
