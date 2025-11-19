from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List
from backend.db import get_db
from backend import models
from backend.security import hash_password, verify_password, create_access_token
from backend.deps import get_current_user
from backend.ai import generate_plan_for_goal

from fastapi.middleware.cors import CORSMiddleware
from backend.logging_config import logger

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
)

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


def compute_level_from_xp(total_xp: int) -> tuple[int, int, int]:
    """
    Very simple leveling system:
    - Level 1 starts at 0 XP
    - Every 100 XP → +1 level
    Returns (level, current_level_xp, next_level_xp).
    """
    xp_per_level = 100

    if total_xp < 0:
        total_xp = 0

    level = (total_xp // xp_per_level) + 1
    current_level_xp = total_xp % xp_per_level
    next_level_xp = xp_per_level

    return level, current_level_xp, next_level_xp

app = FastAPI(title="LifeQuest AI API")

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

    level, current_level_xp, next_level_xp = compute_level_from_xp(total_xp)

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
        .filter(models.Goal.user_id == current_user.id)
        .order_by(models.Goal.created_at.desc())
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
    goal = (
        db.query(models.Goal)
        .options(joinedload(models.Goal.steps))   # <-- add this
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

    # Clear existing steps for this goal to avoid duplicates on re-confirm
    db.query(models.Step).filter(models.Step.goal_id == goal.id).delete(synchronize_session=False)

    created_steps: list[models.Step] = []

    for step_data in plan_steps:
        # step_data is a dict from GeneratedStep.model_dump()
        difficulty_value = step_data.get("difficulty", "medium")
        step = models.Step(
            goal_id=goal.id,
            title=step_data.get("title", ""),
            description=step_data.get("description"),
            position=step_data.get("position", 1),
            difficulty=models.DifficultyEnum(difficulty_value),
            est_time_minutes=step_data.get("est_time_minutes"),
            substeps=step_data.get("substeps") or [],
        )
        db.add(step)
        created_steps.append(step)

    goal.is_confirmed = True
    db.commit()

    # Reload created steps from DB in order
    steps_db = (
        db.query(models.Step)
        .filter(models.Step.goal_id == goal.id)
        .order_by(models.Step.position.asc())
        .all()
    )

    return {"goal_id": goal.id, "steps": steps_db}


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
        # XP formula (from your spec):
        # Easy = 10 XP
        # Medium = 20 XP
        # Hard = 40 XP
        # Reflection bonus = +5 XP

        diff = step.difficulty  # this is a DifficultyEnum
        if diff == models.DifficultyEnum.easy:
            base_xp = 10
        elif diff == models.DifficultyEnum.medium:
            base_xp = 20
        elif diff == models.DifficultyEnum.hard:
            base_xp = 40
        else:
            base_xp = 10

        total_xp = base_xp + 5  # reflection bonus

        award_xp(
            db=db,
            user_id=current_user.id,
            amount=total_xp,
            reason="reflection",
            meta={
                "goal_id": goal_id,
                "step_id": step_id,
                "difficulty": diff.value if hasattr(diff, "value") else str(diff),
                "base_xp": base_xp,
                "reflection_bonus": 5,
            },
        )

        logger.info(
            "XP awarded | user=%s | goal=%s | step=%s | amount=%s",
            current_user.id,
            goal_id,
            step_id,
            total_xp,
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
   