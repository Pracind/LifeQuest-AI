from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.requests import Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List
from backend.db import get_db
from backend import models
from backend.security import hash_password, verify_password, create_access_token
from backend.deps import get_current_user

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
    Difficulty,
    ConfirmPlanResponse,
    ErrorResponse,
)


app = FastAPI(title="LifeQuest AI API")


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
    return goals


@app.get("/goals/{goal_id}", response_model=GoalOut)
def get_goal(
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
    Mock AI generator for a goal's linear steps.
    - Verifies goal belongs to current user
    - Creates a fake linear plan
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

    # --- MOCK "AI" PLAN (static, but uses goal title) ---
    base_title = goal.title

    fake_steps: list[GeneratedStep] = [
        GeneratedStep(
            title=f"Define your why for '{base_title}'",
            description=f"Write down why {base_title.lower()} matters to you and what success looks like.",
            position=1,
            difficulty=Difficulty.easy,
            est_time_minutes=15,
        ),
        GeneratedStep(
            title=f"Break '{base_title}' into milestones",
            description="Create 3–5 concrete checkpoints you can track weekly.",
            position=2,
            difficulty=Difficulty.medium,
            est_time_minutes=30,
        ),
        GeneratedStep(
            title="Set up your environment",
            description="Prepare tools, calendar blocks, and remove obvious distractions.",
            position=3,
            difficulty=Difficulty.medium,
            est_time_minutes=45,
        ),
        GeneratedStep(
            title="Do the first deep work session",
            description="Focus solely on this goal for at least 60 minutes.",
            position=4,
            difficulty=Difficulty.hard,
            est_time_minutes=60,
        ),
        GeneratedStep(
            title="Reflect and adjust your plan",
            description="Review what worked, what didn’t, and tweak your schedule.",
            position=5,
            difficulty=Difficulty.easy,
            est_time_minutes=20,
        ),
    ]

    # Store in goal.ai_plan for later confirmation
    goal.ai_plan = {
        "steps": [step.model_dump() for step in fake_steps]
    }
    db.commit()
    db.refresh(goal)

    return GeneratePlanResponse(goal_id=goal.id, steps=fake_steps)


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




