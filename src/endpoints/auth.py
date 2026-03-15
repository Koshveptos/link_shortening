from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logger import logger
from src.core.security import create_access_token
from src.db.session import get_session
from src.endpoints.deps import get_current_active_user
from src.models.user import User
from src.schemas.auth import Token
from src.schemas.user import UserCreate, UserLogin, UserOut
from src.services.user_service import authenticate_user, create_user, update_last_login

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate, db: AsyncSession = Depends(get_session)
) -> UserOut:
    try:
        user = await create_user(db, payload)
        logger.info(f" User registered: {user.email}")
        return user
    except ValueError as e:
        logger.warning(f"Registration failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=Token)
async def login(payload: UserLogin, db: AsyncSession = Depends(get_session)) -> Token:
    user = await authenticate_user(db, payload.email, payload.password)

    if not user:
        logger.warning(f"Login failed: {payload.email}")
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    await update_last_login(db, user)

    logger.info(f" User logged in: {user.email}")
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_active_user)) -> UserOut:
    return current_user
