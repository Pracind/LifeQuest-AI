from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend import models
from backend.schemas import UserCreate, UserOut, LoginRequest, Token, GoalCreate, GoalOut
from backend.security import hash_password, verify_password, create_access_token
from backend.deps import get_current_user

from typing import List

app = FastAPI(title="LifeQuest AI API")


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
