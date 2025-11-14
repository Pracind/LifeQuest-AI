from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: Optional[str] = None


class UserOut(BaseModel):
    id: str
    email: EmailStr
    display_name: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class GoalCreate(BaseModel):
    title: str
    description: Optional[str] = None


class Difficulty(str, Enum):
    easy = "easy"
    medium = "medium"
    hard = "hard"


class StepOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    position: int
    difficulty: Difficulty
    est_time_minutes: Optional[int] = None

    class Config:
        orm_mode = True


class GoalOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    is_confirmed: bool
    steps: List[StepOut] = []

    class Config:
        orm_mode = True

class GeneratedStep(BaseModel):
    title: str
    description: Optional[str] = None
    position: int
    difficulty: Difficulty
    est_time_minutes: Optional[int] = None


class GeneratePlanResponse(BaseModel):
    goal_id: str
    steps: List[GeneratedStep]


class ConfirmPlanResponse(BaseModel):
    goal_id: str
    steps: List[StepOut]


class ErrorResponse(BaseModel):
    error: str
    message: str
    code: int
    path: Optional[str] = None


