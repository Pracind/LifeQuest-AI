from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.db import get_db
from backend import models
from backend.schemas import UserCreate, UserOut, LoginRequest, Token
from backend.security import hash_password, verify_password, create_access_token
from backend.deps import get_current_user

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
