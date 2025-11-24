from datetime import datetime
from typing import Optional, List
from enum import Enum

from pydantic import BaseModel, EmailStr, ConfigDict


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

    substeps: List[str] = []  
    is_started: bool = False
    is_completed: bool = False
    has_reflection: bool = False

    reflection_required: bool = False
    reflection_prompt: Optional[str] = None
    reflection_text: Optional[str] = None

    started_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        from_attributes = True
    



class GoalOut(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    created_at: datetime
    is_confirmed: bool
    completed_at: datetime | None = None 
    completion_summary: str | None = None
    steps: List[StepOut] = []

    class Config:
        orm_mode = True

class GeneratedStep(BaseModel):
    title: str
    description: Optional[str] = None
    position: int
    difficulty: Difficulty
    est_time_minutes: Optional[int] = None
    substeps: List[str] = []   

    reflection_required: bool = False
    reflection_prompt: Optional[str] = None

    class Config:
        orm_mode = True


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


class ReflectionCreate(BaseModel):
    text: str


class ReflectionOut(BaseModel):
    id: str
    user_id: str
    step_id: str
    text: str
    sentiment: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class UserProgress(BaseModel):
    total_xp: int
    level: int
    current_level_xp: int
    next_level_xp: int

    class Config:
        orm_mode = True

class XPSummary(BaseModel):
    total_xp: int
    level: int
    current_level_xp: int
    next_level_xp: int
    progress_to_next: float


class GoalCompletionSummary(BaseModel):
    goal_id: str
    summary_text: str