from fastapi import FastAPI, Depends, HTTPException, status, Response
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from groq import Groq
import os

from backend.db import get_db
from backend import models
from backend.security import hash_password, verify_password, create_access_token
from backend.deps import get_current_user
from backend.ai import generate_plan_for_goal, generate_completion_summary_for_goal
from datetime import datetime, timezone

from fastapi.middleware.cors import CORSMiddleware
from backend.logging_config import logger

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

from backend.schemas import (
    UserCreate,
    UserOut,
    LoginRequest,
    Token,
    GoalCreate,
    GoalOut,
    GeneratedStep,
    GeneratePlanResponse,
    ConfirmPlanResponse,
    ErrorResponse,
    ReflectionCreate,   
    ReflectionOut,     
    UserProgress,
    StepOut,
    XPSummary,
    GoalCompletionSummary,
    UserUpdate,
    PasswordChange,
)

origins = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "http://ec2-13-62-226-79.eu-north-1.compute.amazonaws.com",
    "http://ec2-13-62-226-79.eu-north-1.compute.amazonaws.com:80",
]



MAX_LEVEL = 60


def _build_level_requirements() -> list[int]:
    """
    Build XP requirements for each level-up:

    index 0: XP needed from level 1 -> 2
    index 1: XP needed from level 2 -> 3
    ...
    index 58: XP needed from level 59 -> 60

    Rule:
    - Level 1 -> 2: 100 XP
    - Each next level: previous * 1.10, then rounded to the nearest 10.
      e.g. 100, 110, 121 (~120), 133 (~130), 146.3 (~150), ...
    """
    requirements: list[int] = []
    for lvl in range(1, MAX_LEVEL):  # up to 59 (since 59->60 is last)
        if lvl == 1:
            needed = 100.0
        else:
            needed = requirements[-1] * 1.10  # +10% from previous

        # round to nearest 10
        rounded = int(round(needed / 10.0) * 10)

        if rounded < 10:
            rounded = 10

        requirements.append(rounded)

    return requirements


# XP needed to go from level N -> N+1
LEVEL_XP_REQUIREMENTS: list[int] = _build_level_requirements()
XP_TO_REACH_MAX = sum(LEVEL_XP_REQUIREMENTS)


def compute_level_from_xp(total_xp: int) -> tuple[int, int, int, float]:
    """
    Convert total XP into:
    - level (1-based)
    - current_level_xp (XP into *current* level)
    - next_level_xp (XP needed to go from current level -> next)
    - progress_to_next (0.0–1.0)

    Uses LEVEL_XP_REQUIREMENTS with +10% per level, rounded to nearest 10.
    Max level is MAX_LEVEL; once reached, the bar stays full.
    """
    if total_xp < 0:
        total_xp = 0

    # If we've hit or exceeded the XP for max level, clamp there
    if total_xp >= XP_TO_REACH_MAX:
        return MAX_LEVEL, 0, 0, 1.0

    level = 1
    remaining = total_xp

    # Walk through level requirements
    for idx, needed in enumerate(LEVEL_XP_REQUIREMENTS, start=1):
        # needed is XP to go from level idx -> idx+1
        if remaining >= needed and level < MAX_LEVEL:
            remaining -= needed
            level += 1
        else:
            break

    if level >= MAX_LEVEL:
        return MAX_LEVEL, 0, 0, 1.0

    current_level_xp = remaining
    next_level_xp = LEVEL_XP_REQUIREMENTS[level - 1]  # index by (level-1)

    progress_to_next = (
        current_level_xp / next_level_xp if next_level_xp else 0.0
    )

    return level, current_level_xp, next_level_xp, progress_to_next


def award_xp(
    db: Session,
    user_id: str,
    amount: int,
    reason: str,
    meta: dict | None = None,
) -> models.XPLog:
    """
    Create an XPLog entry for the user.
    Later we can use this table to compute total XP, levels, badges, etc.
    """
    xp_log = models.XPLog(
        user_id=user_id,
        amount=amount,
        reason=reason,
        meta=meta or {},
    )
    db.add(xp_log)
    return xp_log


app = FastAPI(title="LifeQuest AI API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.warning(
        "HTTPException | status=%s | path=%s | detail=%s",
        exc.status_code,
        request.url.path,
        exc.detail,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error="http_error",
            message=str(exc.detail),
            code=exc.status_code,
            path=request.url.path,
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(
        "UnhandledException | path=%s | error=%r",
        request.url.path,
        exc,
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="internal_server_error",
            message="An unexpected error occurred.",
            code=500,
            path=request.url.path,
        ).model_dump(),
    )


@app.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user:
    - Validates email format via Pydantic
    - Rejects if email already exists
    - Hashes password with bcrypt
    - Returns user data (no password)
    """
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user = models.User(
        email=payload.email,
        password_hash=hash_password(payload.password),
        display_name=payload.display_name,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@app.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT:
    - Looks up user by email
    - Verifies password with bcrypt
    - Returns access_token if valid
    """
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Use user.id as subject
    access_token = create_access_token(data={"sub": user.id})

    return Token(access_token=access_token)


@app.get("/me", response_model=UserOut)
def read_me(current_user: models.User = Depends(get_current_user)):
    """
    Return the currently authenticated user.
    Requires Authorization: Bearer <token>
    """
    return current_user


@app.get("/user/progress", response_model=UserProgress)
def get_user_progress(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return total XP and derived level info for the current user.
    Uses xp_log table as the source of truth.
    """

    total_xp = (
        db.query(func.coalesce(func.sum(models.XPLog.amount), 0))
        .filter(models.XPLog.user_id == current_user.id)
        .scalar()
    ) or 0

    level, current_level_xp, next_level_xp, _ = compute_level_from_xp(total_xp)

    return UserProgress(
        total_xp=total_xp,
        level=level,
        current_level_xp=current_level_xp,
        next_level_xp=next_level_xp,
    )


@app.post("/goals", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
def create_goal(
    payload: GoalCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create a new goal for the current authenticated user.
    Returns the created goal (including its id).
    """
    goal = models.Goal(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
    )

    db.add(goal)
    db.commit()
    db.refresh(goal)

    return goal


@app.get("/goals", response_model=List[GoalOut])
def list_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    List all goals for the current authenticated user.
    Most recent first.
    """
    goals = (
        db.query(models.Goal)
        .options(
            joinedload(models.Goal.steps).joinedload(models.Step.user_steps)
        )
        .filter(
            models.Goal.user_id == current_user.id,
            models.Goal.is_confirmed == True,
            models.Goal.completed_at.is_(None),
        )
        .order_by(models.Goal.created_at.desc())
        .all()
    )

    for g in goals:
        for s in g.steps:
            if s.substeps is None:
                s.substeps = []

            user_step = next(
                (us for us in s.user_steps if us.user_id == current_user.id),
                None,
            )

            s.is_started = bool(user_step and user_step.started_at)
            s.is_completed = bool(user_step and user_step.completed_at)
            
    return goals


@app.get("/goals/completed", response_model=List[GoalOut])
def get_completed_goals(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goals = (
        db.query(models.Goal)
        .filter(
            models.Goal.user_id == current_user.id,
            models.Goal.completed_at.isnot(None),
        )
        .order_by(models.Goal.completed_at.desc())
        .all()
    )

    for g in goals:
        for s in g.steps:
            if s.substeps is None:
                s.substeps = []

    return goals



@app.get("/goals/{goal_id}", response_model=GoalOut)
def get_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return a single goal with all steps for the current user.

    - Loads steps via relationship
    - Ensures substeps is always a list
    - Attaches user-specific flags on each step:
      - is_started
      - is_completed
      - has_reflection
      - reflection_text
    """
    goal = (
        db.query(models.Goal)
        .options(
            joinedload(models.Goal.steps).joinedload(models.Step.user_steps)
        )
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    for step in goal.steps:
        # Ensure substeps is always a list
        if step.substeps is None:
            step.substeps = []

        # Find the UserStep row for this user, if any
        user_step = next(
            (us for us in step.user_steps if us.user_id == current_user.id),
            None,
        )

        # Attach user-specific flags directly to the ORM object
        step.is_started = bool(user_step and user_step.started_at)
        step.is_completed = bool(user_step and user_step.completed_at)

        step.started_at = user_step.started_at if user_step else None
        step.completed_at = user_step.completed_at if user_step else None

        # Reflection info
        reflection = (
            db.query(models.Reflection)
            .filter(
                models.Reflection.user_id == current_user.id,
                models.Reflection.step_id == step.id,
            )
            .first()
        )

        step.has_reflection = reflection is not None
        # This is what StepCard wants to see after refresh
        step.reflection_text = reflection.text if reflection else None

        # reflection_required and reflection_prompt are real Step columns,
        # so they are already present on `step` and will be picked up by Pydantic.

    # Thanks to orm_mode / from_attributes, returning the ORM object is fine
    return goal


@app.post("/goals/{goal_id}/generate", response_model=GeneratePlanResponse)
def generate_goal_plan(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    AI generator for a goal's linear steps.
    - Verifies goal belongs to current user
    - Calls AI module to generate a plan
    - Stores it in goal.ai_plan (JSON)
    - Returns the generated steps (not yet saved as Step rows)
    """
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    

    # ⭐ If cached AI plan exists, return it immediately
    if goal.ai_plan and "steps" in goal.ai_plan:
        logger.info("AI: returning cached plan for goal %s", goal.id)
        return GeneratePlanResponse(
            goal_id=goal.id,
            steps=[GeneratedStep.model_validate(s) for s in goal.ai_plan["steps"]]
        )

    # Use AI module (Groq / OpenAI / HF / mock)
    steps = generate_plan_for_goal(goal.title, goal.description)

    goal.ai_plan = {"steps": [step.model_dump() for step in steps]}
    db.commit()
    db.refresh(goal)

    return GeneratePlanResponse(goal_id=goal.id, steps=steps)


@app.post("/goals/{goal_id}/confirm", response_model=ConfirmPlanResponse)
def confirm_goal_plan(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Confirm the AI-generated plan for a goal:
    - Reads goal.ai_plan["steps"]
    - Clears existing steps for that goal (if any)
    - Creates Step rows in the DB
    - Marks goal as confirmed
    """
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    if not goal.ai_plan or "steps" not in goal.ai_plan:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No generated plan to confirm. Call /goals/{id}/generate first.",
        )

    plan_steps = goal.ai_plan["steps"]

    # 🔹 Clear existing steps for this goal to avoid duplicates on re-confirm
    db.query(models.Step).filter(
        models.Step.goal_id == goal.id
    ).delete(synchronize_session=False)

    created_steps: list[models.Step] = []

    for step_data in plan_steps:
        difficulty_value = step_data.get("difficulty", "medium")

        step = models.Step(
            goal_id=goal.id,
            title=step_data.get("title", ""),
            description=step_data.get("description"),
            position=step_data.get("position", 1),
            difficulty=models.DifficultyEnum(difficulty_value),
            est_time_minutes=step_data.get("est_time_minutes"),
            substeps=step_data.get("substeps") or [],
            reflection_required=bool(step_data.get("reflection_required", False)),
            reflection_prompt=step_data.get("reflection_prompt"),
        )
        db.add(step)
        created_steps.append(step)

    goal.is_confirmed = True
    db.commit()

    # 🔹 Reload created steps from DB in order
    steps_db = (
        db.query(models.Step)
        .filter(models.Step.goal_id == goal.id)
        .order_by(models.Step.position.asc())
        .all()
    )

    # Map to StepOut for the response
    step_out_list: list[StepOut] = []
    for step in steps_db:
        difficulty_value = (
            step.difficulty.value
            if isinstance(step.difficulty, models.DifficultyEnum)
            else step.difficulty
        )

        step_out_list.append(
            StepOut(
                id=step.id,
                title=step.title,
                description=step.description,
                position=step.position,
                difficulty=difficulty_value,
                est_time_minutes=step.est_time_minutes,
                substeps=step.substeps or [],
                is_started=False,
                is_completed=False,
                has_reflection=False,
                reflection_required=bool(getattr(step, "reflection_required", False)),
                reflection_prompt=getattr(step, "reflection_prompt", None),
                reflection_text=None,
            )
        )

    return ConfirmPlanResponse(
        goal_id=goal.id,
        steps=step_out_list,
    )


@app.post("/goals/{goal_id}/regenerate", response_model=GeneratePlanResponse)
def regenerate_goal_plan(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Regenerate an alternate AI plan for an existing goal.

    - Always calls the AI provider (ignores any existing cached ai_plan)
    - Overwrites goal.ai_plan with the new steps
    - Does NOT modify existing Step rows (those are only changed on /confirm)
    """
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    # Force a fresh AI generation (no cache)
    steps = generate_plan_for_goal(goal.title, goal.description)

    goal.ai_plan = {"steps": [s.model_dump() for s in steps]}
    db.commit()
    db.refresh(goal)

    return GeneratePlanResponse(goal_id=goal.id, steps=steps)


@app.post(
    "/goals/{goal_id}/steps/{step_id}/reflect",
    response_model=ReflectionOut,
    status_code=status.HTTP_201_CREATED,
)
def create_or_update_reflection(
    goal_id: str,
    step_id: str,
    payload: ReflectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Create or update the user's reflection for a specific step.

    - Ensures the goal belongs to the current user
    - Ensures the step belongs to that goal
    - Upserts a Reflection row (user_id + step_id)
    - On first creation → award base XP for reflection
    """

    # 1) Ensure goal belongs to user
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    # 2) Ensure step belongs to that goal
    step = (
        db.query(models.Step)
        .filter(
            models.Step.id == step_id,
            models.Step.goal_id == goal.id,
        )
        .first()
    )
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )

    # 3) Look up existing reflection (to decide XP)
    reflection = (
        db.query(models.Reflection)
        .filter(
            models.Reflection.user_id == current_user.id,
            models.Reflection.step_id == step_id,
        )
        .first()
    )

    is_new = reflection is None

    if reflection:
        # Update existing
        reflection.text = payload.text
    else:
        # Create new
        reflection = models.Reflection(
            user_id=current_user.id,
            step_id=step_id,
            text=payload.text,
        )
        db.add(reflection)

    # 4) If this is a NEW reflection → award base XP
    if is_new:
        reflection_xp = 5

        diff = step.difficulty  # still useful for logging/meta

        award_xp(
            db=db,
            user_id=current_user.id,
            amount=reflection_xp,
            reason="reflection",
            meta={
                "goal_id": goal_id,
                "step_id": step_id,
                "difficulty": diff.value if hasattr(diff, "value") else str(diff),
                "reflection_bonus": reflection_xp,
            },
        )

        logger.info(
            "XP awarded | user=%s | goal=%s | step=%s | amount=%s (reflection only)",
            current_user.id,
            goal_id,
            step_id,
            reflection_xp,
        )


    db.commit()
    db.refresh(reflection)

    logger.info(
        "Reflection saved | user=%s | goal=%s | step=%s | reflection_id=%s | new=%s",
        current_user.id,
        goal_id,
        step_id,
        reflection.id,
        is_new,
    )

    return reflection


@app.get("/xp/logs")
def get_xp_logs(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    logs = (
        db.query(models.XPLog)
        .filter(models.XPLog.user_id == current_user.id)
        .order_by(models.XPLog.created_at.desc())
        .limit(50)
        .all()
    )
    return logs


@app.post("/goals/{goal_id}/steps/{step_id}/start")
def start_step(
    goal_id: str,
    step_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # make sure goal belongs to user
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    step = (
        db.query(models.Step)
        .filter(
            models.Step.id == step_id,
            models.Step.goal_id == goal.id,
        )
        .first()
    )
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    
    prev_step = (
        db.query(models.Step)
        .filter(
            models.Step.goal_id == goal.id,
            models.Step.position < step.position,
        )
        .order_by(models.Step.position.desc())
        .first()
    )

    if prev_step:
        prev_user_step = (
            db.query(models.UserStep)
            .filter(
                models.UserStep.user_id == current_user.id,
                models.UserStep.step_id == prev_step.id,
            )
            .first()
        )
        if not prev_user_step or prev_user_step.completed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You need to complete earlier steps before starting this one.",
            )

    user_step = (
        db.query(models.UserStep)
        .filter(
            models.UserStep.user_id == current_user.id,
            models.UserStep.step_id == step.id,
        )
        .first()
    )

    if not user_step:
        user_step = models.UserStep(
            user_id=current_user.id,
            step_id=step.id,
            started_at = datetime.now(timezone.utc),
            xp_awarded=0,
        )
        db.add(user_step)
    elif user_step.started_at is None:
        user_step.started_at = datetime.utcnow()

    db.commit()
    db.refresh(user_step)

    return {
        "goal_id": goal.id,
        "step_id": step.id,
        "status": "in_progress",
        "started_at": user_step.started_at,
        "completed_at": user_step.completed_at,
    }


@app.post(
    "/goals/{goal_id}/steps/{step_id}/complete",
    status_code=status.HTTP_200_OK,
)
def complete_step(
    goal_id: str,
    step_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Mark a step as completed for the current user and award base XP
    (once per step).

    XP formula:
    - easy   -> 10 XP
    - medium -> 20 XP
    - hard   -> 40 XP
    """
    # 1) Make sure goal belongs to user
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    # 2) Make sure step belongs to goal
    step = (
        db.query(models.Step)
        .filter(
            models.Step.id == step_id,
            models.Step.goal_id == goal.id,
        )
        .first()
    )
    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Step not found",
        )
    
    prev_step = (
        db.query(models.Step)
        .filter(
            models.Step.goal_id == goal.id,
            models.Step.position < step.position,
        )
        .order_by(models.Step.position.desc())
        .first()
    )

    if prev_step:
        prev_user_step = (
            db.query(models.UserStep)
            .filter(
                models.UserStep.user_id == current_user.id,
                models.UserStep.step_id == prev_step.id,
            )
            .first()
        )
        if not prev_user_step or prev_user_step.completed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You need to complete earlier steps before completing this one.",
            )

    # 3) Get or create UserStep (progress row)
    user_step = (
        db.query(models.UserStep)
        .filter(
            models.UserStep.user_id == current_user.id,
            models.UserStep.step_id == step.id,
        )
        .first()
    )

    now_utc = datetime.now(timezone.utc)

    if not user_step:
        user_step = models.UserStep(
            user_id=current_user.id,
            step_id=step.id,
            started_at=now_utc,
            completed_at=now_utc,
            xp_awarded=0,
        )
        db.add(user_step)
        db.flush()
    else:
        if user_step.completed_at is None:
            user_step.completed_at = now_utc

    # 4) Check if we already gave completion XP for this step
    existing_completion_xp = (
        db.query(models.XPLog)
        .filter(
            models.XPLog.user_id == current_user.id,
            models.XPLog.reason == "step_complete",
            models.XPLog.meta["step_id"].as_string() == step.id,
        )
        .first()
    )

    xp_awarded = 0

    if not existing_completion_xp:
        # Base XP by difficulty
        if step.difficulty == models.DifficultyEnum.easy:
            base_xp = 10
        elif step.difficulty == models.DifficultyEnum.medium:
            base_xp = 20
        elif step.difficulty == models.DifficultyEnum.hard:
            base_xp = 40
        else:
            base_xp = 10

        xp_log = models.XPLog(
            user_id=current_user.id,
            amount=base_xp,
            reason="step_complete",
            meta={
                "goal_id": goal.id,
                "step_id": step.id,
                "difficulty": step.difficulty.value,
                "source": "completion",
            },
        )
        db.add(xp_log)

        user_step.xp_awarded = (user_step.xp_awarded or 0) + base_xp
        xp_awarded = base_xp

    db.commit()
    db.refresh(user_step)

    return {
        "status": "completed",
        "xp_awarded": xp_awarded,
        "step_id": step.id,
        "goal_id": goal.id,
    }


@app.get("/xp/summary", response_model=XPSummary)
def get_xp_summary(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Return total XP, level, and progress for the sidebar header.
    """
    total_xp = (
        db.query(func.coalesce(func.sum(models.XPLog.amount), 0))
        .filter(models.XPLog.user_id == current_user.id)
        .scalar()
    )

    level, current_level_xp, next_level_xp, progress_to_next = compute_level_from_xp(
        int(total_xp or 0)
    )

    return XPSummary(
        total_xp=int(total_xp or 0),
        level=level,
        current_level_xp=current_level_xp,
        next_level_xp=next_level_xp,
        progress_to_next=progress_to_next,
    )


@app.delete("/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """
    Permanently delete a goal and all its steps / XP / reflections for this user.
    """
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )

    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )

    db.delete(goal)
    db.commit()

    # 204: no content
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.post("/goals/{goal_id}/finish")
def finish_goal(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    # 1) Make sure goal belongs to user
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    # 2) Count how many steps exist for this goal
    total_steps = (
        db.query(models.Step)
        .filter(models.Step.goal_id == goal.id)
        .count()
    )

    # 3) Count how many of those steps this user has completed
    completed_steps = (
        db.query(models.UserStep)
        .join(models.Step, models.Step.id == models.UserStep.step_id)
        .filter(
            models.Step.goal_id == goal.id,
            models.UserStep.user_id == current_user.id,
            models.UserStep.completed_at.isnot(None),
        )
        .count()
    )

    # If there are steps, require all to be completed
    if total_steps > 0 and completed_steps < total_steps:
        raise HTTPException(
            status_code=400,
            detail="Goal cannot be finished until all steps are completed",
        )

    # 4) Total XP earned on this goal (steps + reflections, etc.)
    total_goal_xp = (
        db.query(func.coalesce(func.sum(models.XPLog.amount), 0))
        .filter(models.XPLog.user_id == current_user.id)
        .filter(models.XPLog.meta["goal_id"].as_string() == goal.id)
        .scalar()
    )

    # 5% bonus, rounded to nearest 10
    bonus = round((total_goal_xp * 0.05) / 10) * 10

    if bonus > 0:
        award_xp(
            db=db,
            user_id=current_user.id,
            amount=bonus,
            reason="goal_complete",
            meta={"goal_id": goal.id, "bonus_percent": 5},
        )

    # 5) Load steps + reflections for summary
    steps = (
        db.query(models.Step)
        .filter(models.Step.goal_id == goal.id)
        .order_by(models.Step.position.asc())
        .all()
    )

    reflections = (
        db.query(models.Reflection)
        .filter(
            models.Reflection.user_id == current_user.id,
            models.Reflection.step_id.in_([s.id for s in steps]),
        )
        .order_by(models.Reflection.created_at.asc())
        .all()
    )

    # 6) Generate and store AI summary
    summary = generate_completion_summary_for_goal(goal, steps, reflections)
    goal.completion_summary = summary
    goal.completed_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(goal)

    return {
        "goal_id": goal.id,
        "bonus_xp": int(bonus),
        "completed_at": goal.completed_at,
        "summary_text": summary,
    }



@app.get(
    "/goals/{goal_id}/completion-summary",
    response_model=GoalCompletionSummary,
)
def get_goal_completion_summary(
    goal_id: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    goal = (
        db.query(models.Goal)
        .filter(
            models.Goal.id == goal_id,
            models.Goal.user_id == current_user.id,
        )
        .first()
    )
    if not goal:
        raise HTTPException(status_code=404, detail="Goal not found")

    if not goal.completed_at:
        raise HTTPException(
            status_code=400,
            detail="Quest is not finished yet.",
        )

    # If we already have a stored summary, just return it
    if goal.completion_summary:
        return GoalCompletionSummary(
            goal_id=goal.id,
            summary_text=goal.completion_summary,
        )

    # Otherwise, generate once (for old quests), store, and return
    steps = (
        db.query(models.Step)
        .filter(models.Step.goal_id == goal.id)
        .order_by(models.Step.position.asc())
        .all()
    )

    reflections = (
        db.query(models.Reflection)
        .filter(
            models.Reflection.user_id == current_user.id,
            models.Reflection.step_id.in_([s.id for s in steps]),
        )
        .order_by(models.Reflection.created_at.asc())
        .all()
    )

    summary = generate_completion_summary_for_goal(goal, steps, reflections)
    goal.completion_summary = summary

    db.commit()
    db.refresh(goal)

    return GoalCompletionSummary(
        goal_id=goal.id,
        summary_text=summary,
    )



@app.patch("/me", response_model=UserOut)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Update display name and avatar URL."""
    if payload.display_name is not None:
        current_user.display_name = payload.display_name.strip() or None

    if payload.avatar_url is not None:
        current_user.avatar_url = payload.avatar_url.strip() or None

    db.commit()
    db.refresh(current_user)
    return current_user


@app.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_my_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Change password after verifying current one."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")

    current_user.password_hash = hash_password(payload.new_password)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)





