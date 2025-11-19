import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from backend.main import app
from backend.db import get_db
from backend import models
from backend.deps import get_current_user

# -----------------------------
# Test database setup
# -----------------------------

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# StaticPool + :memory: => same in-memory DB for all sessions
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    """Create all tables once for the test session."""
    models.Base.metadata.create_all(bind=engine)
    yield
    models.Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Session:
    """Provide a fresh DB session per test."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


# -----------------------------
# Dependency overrides
# -----------------------------

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def make_test_user_goal_step(db: Session):
    """Seed a user, goal, and step for testing."""
    user = models.User(
        email="test@example.com",
        password_hash="fake-hash",
        display_name="Test User",
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    goal = models.Goal(
        user_id=user.id,
        title="Test Goal",
        description="Testing reflection endpoint",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)

    step = models.Step(
        goal_id=goal.id,
        title="Test Step",
        description="Step for reflection testing",
        position=1,
        difficulty=models.DifficultyEnum.easy,
        est_time_minutes=30,
        substeps=[],  # important now that steps have substeps
    )
    db.add(step)
    db.commit()
    db.refresh(step)

    return user, goal, step


# -----------------------------
# Actual test
# -----------------------------

def test_reflection_creates_and_awards_xp(db_session: Session):
    # Seed user, goal, step in the test DB
    user, goal, step = make_test_user_goal_step(db_session)

    # Now that we have a real user, override get_current_user
    def _override_current_user():
        return user

    app.dependency_overrides[get_current_user] = _override_current_user

    # 1) First POST: create reflection
    payload = {"text": "This is my first reflection on this step."}
    url = f"/goals/{goal.id}/steps/{step.id}/reflect"

    response = client.post(url, json=payload)
    assert response.status_code == 201, response.text

    data = response.json()
    assert data["text"] == payload["text"]
    assert data["step_id"] == step.id
    assert data["user_id"] == user.id

    # 2) Check that exactly one reflection exists in DB
    reflection_in_db = (
        db_session.query(models.Reflection)
        .filter(
            models.Reflection.user_id == user.id,
            models.Reflection.step_id == step.id,
        )
        .first()
    )
    assert reflection_in_db is not None
    assert reflection_in_db.text == payload["text"]

    # 3) Check XP was awarded (one XPLog row with correct amount)
    xp_logs = (
        db_session.query(models.XPLog)
        .filter(models.XPLog.user_id == user.id)
        .all()
    )
    assert len(xp_logs) == 1

    xp_entry = xp_logs[0]
    # Easy difficulty → base 10 + reflection bonus 5 = 15
    assert xp_entry.amount == 15
    assert xp_entry.reason == "reflection"
    assert xp_entry.meta.get("goal_id") == goal.id
    assert xp_entry.meta.get("step_id") == step.id

    # 4) Second POST: update reflection (should NOT award extra XP)
    payload2 = {"text": "Updated reflection after thinking more."}
    response2 = client.post(url, json=payload2)
    assert response2.status_code == 201, response2.text

    data2 = response2.json()
    assert data2["text"] == payload2["text"]

    # Reflection text should be updated in DB
    db_session.expire_all()

    reflection_in_db2 = (
        db_session.query(models.Reflection)
        .filter(
            models.Reflection.user_id == user.id,
            models.Reflection.step_id == step.id,
        )
        .first()
    )
    assert reflection_in_db2 is not None
    assert reflection_in_db2.text == payload2["text"]

    # XP logs should still be exactly 1 (no extra XP for editing)
    xp_logs_after = (
        db_session.query(models.XPLog)
        .filter(models.XPLog.user_id == user.id)
        .all()
    )
    assert len(xp_logs_after) == 1
    assert xp_logs_after[0].id == xp_entry.id
