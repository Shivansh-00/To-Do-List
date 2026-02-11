from __future__ import annotations

import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.auth import get_password_hash, verify_password, create_access_token
from app.schemas import UserCreate, UserLogin, UserResponse, Token

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/signup", response_model=Token, status_code=status.HTTP_201_CREATED)
@router.post("/signup/", response_model=Token, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def signup(payload: UserCreate, db: Session = Depends(get_db)):
    try:
        # Check existing username
        existing_user = db.query(User).filter(User.username == payload.username).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username already taken",
            )
        # Check existing email
        existing_email = db.query(User).filter(User.email == payload.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered",
            )

        hashed = get_password_hash(payload.password)
        user = User(
            username=payload.username,
            email=payload.email,
            full_name=payload.full_name,
            hashed_password=hashed,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        access_token = create_access_token(data={"sub": user.id})
        user_resp = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        return Token(access_token=access_token, user=user_resp)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Signup error: {traceback.format_exc()}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Account creation failed: {str(exc)}",
        )


@router.post("/login", response_model=Token)
@router.post("/login/", response_model=Token, include_in_schema=False)
async def login(payload: UserLogin, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == payload.username).first()
        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        access_token = create_access_token(data={"sub": user.id})
        user_resp = UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            is_active=user.is_active,
            created_at=user.created_at,
        )
        return Token(access_token=access_token, user=user_resp)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Login error: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(exc)}",
        )


@router.get("/me", response_model=UserResponse)
@router.get("/me/", response_model=UserResponse, include_in_schema=False)
async def get_me(
    db: Session = Depends(get_db),
    token: str = None,
):
    """Get current user info from token passed as query param."""
    from jose import JWTError, jwt
    from app.auth import SECRET_KEY, ALGORITHM

    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        decoded = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = decoded.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        created_at=user.created_at,
    )
