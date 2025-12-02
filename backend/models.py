"""
SQLAlchemy ORM models for LifeQuest AI.

Notes:
- UUIDs are stored as strings for easier cross-language handling with Supabase.
- Uses declarative base (SQLAlchemy 1.4+ style).
- Add or adjust relationships/columns as features evolve.
"""

from datetime import datetime
import enum
import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Text,
    DateTime,
    ForeignKey,
    Boolean,
    Enum,
    JSON,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


def gen_uuid() -> str:
    return str(uuid.uuid4())


class DifficultyEnum(enum.Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=gen_uuid)  # UUID as string
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    avatar_url = Column(String(1024), nullable=True)

    # relationships
    goals = relationship("Goal", back_populates="owner", cascade="all, delete-orphan")
    xp_logs = relationship("XPLog", back_populates="user", cascade="all, delete-orphan")

    avatar_url = Column(String, nullable=True)

    def __repr__(self):
        return f"<User id={self.id} email={self.email}>"


class Goal(Base):
    __tablename__ = "goals"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_confirmed = Column(Boolean, default=False, nullable=False)
    ai_plan = Column(JSON, nullable=True)  # cached AI-generated plan (JSON)

    # relationships
    owner = relationship("User", back_populates="goals")
    steps = relationship("Step", back_populates="goal", cascade="all, delete-orphan", order_by="Step.position")

    completed_at = Column(DateTime(timezone=True), nullable=True)
    completion_summary = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Goal id={self.id} title={self.title} user_id={self.user_id}>"


class Step(Base):
    __tablename__ = "steps"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    goal_id = Column(String(36), ForeignKey("goals.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    position = Column(Integer, nullable=False)  # linear order within the goal
    difficulty = Column(Enum(DifficultyEnum), default=DifficultyEnum.medium, nullable=False)
    est_time_minutes = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    substeps = Column(JSON, nullable=True)

    reflection_required = Column(Boolean, default=False, nullable=False)
    reflection_prompt = Column(Text, nullable=True)

    # relationships
    goal = relationship("Goal", back_populates="steps")
    user_steps = relationship("UserStep", back_populates="step", cascade="all, delete-orphan")
    quizzes = relationship("Quiz", back_populates="step", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Step id={self.id} title={self.title} position={self.position}>"


class UserStep(Base):
    __tablename__ = "user_steps"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(String(36), ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    reflection_id = Column(String(36), ForeignKey("reflections.id"), nullable=True)
    evidence_id = Column(String(36), ForeignKey("evidence.id"), nullable=True)
    xp_awarded = Column(Integer, default=0, nullable=False)
    is_locked = Column(Boolean, default=False, nullable=False)  # used to require reflection/quiz before completion

    # relationships
    step = relationship("Step", back_populates="user_steps")
    # Consider adding relationship to User if helpful in queries

    def __repr__(self):
        return f"<UserStep id={self.id} user_id={self.user_id} step_id={self.step_id}>"


class XPLog(Base):
    __tablename__ = "xp_log"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = Column(Integer, nullable=False)
    reason = Column(String(255), nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    user = relationship("User", back_populates="xp_logs")

    def __repr__(self):
        return f"<XPLog id={self.id} user_id={self.user_id} amount={self.amount}>"


class Reflection(Base):
    __tablename__ = "reflections"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(String(36), ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True)
    text = Column(Text, nullable=False)
    sentiment = Column(String(50), nullable=True)  # optional sentiment label
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Reflection id={self.id} user_id={self.user_id} step_id={self.step_id}>"


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(String(36), ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True)
    filename = Column(String(1024), nullable=False)
    url = Column(String(2048), nullable=True)
    meta = Column("metadata", JSON, nullable=True)  # DB column still named "metadata"
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Evidence id={self.id} filename={self.filename}>"


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String(36), primary_key=True, default=gen_uuid)
    step_id = Column(String(36), ForeignKey("steps.id", ondelete="CASCADE"), nullable=False, index=True)
    questions = Column(JSON, nullable=False)  # list of question objects: {q, choices, hashed_answer_id}
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # relationships
    step = relationship("Step", back_populates="quizzes")

    def __repr__(self):
        return f"<Quiz id={self.id} step_id={self.step_id}>"
