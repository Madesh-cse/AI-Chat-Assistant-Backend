from fastapi import APIRouter, Depends, HTTPException, status # type: ignore
from sqlalchemy import select # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.database import get_db
from app.models.user import User

from app.Schemas.auth import ( RegisterRequest, LoginRequest, TokenResponse)

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# ==================================================
# REGISTER
# ==================================================

@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db),
):
    email = data.email.lower().strip()

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    user = User(
        name=data.name.strip(),
        email=email,
        password_hash=hash_password(data.password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


# ==================================================
# LOGIN
# ==================================================

@router.post(
    "/login",
    response_model=TokenResponse,
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db),
):
    email = data.email.lower().strip()

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    valid_password = verify_password(
        data.password,
        user.password_hash,
    )

    if not valid_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }