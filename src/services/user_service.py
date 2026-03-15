from datetime import UTC

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logger import logger
from src.core.security import get_password_hash, verify_password
from src.models.user import User
from src.schemas.user import UserCreate


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    logger.debug(f"search user by email {email}")

    result = await session.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if user:
        logger.debug(f"User found {user.id}")
    else:
        logger.debug(f"User not found {email}")
    return user


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    logger.debug(f"search user by id {user_id}")

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user:
        logger.debug(f"User found {user.id}")
    else:
        logger.debug(f"User not found {user_id}")
    return user


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    logger.info(f"Creating user with email {payload.email}")
    test_user = await get_user_by_email(session, payload.email)
    if test_user:
        logger.warning(f"User with email exists {payload.email}")
        raise ValueError("Пользователь с такой почтой уже есть")
    hashed_password = get_password_hash(payload.password)
    logger.debug(f"get hash password {hashed_password[:10]}")

    user = User(
        username=payload.username,
        email=payload.email,
        password_hash=hashed_password,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.info(f"User with id {user.id} and email {user.email} create")
    return user


async def authenticate_user(
    session: AsyncSession, email: str, password: str
) -> User | None:
    logger.debug(f"Auth user {email}")
    user = await get_user_by_email(session, email)
    if not user:
        logger.warning(f"Auth failed, user not found {email}")
        return None
    is_valid_password = verify_password(password, user.password_hash)
    if not is_valid_password:
        logger.warning(f"Auth failed, wrong password {email}")
        return None

    if not user.is_active:
        logger.warning(
            "Auth failed, User os not active"
        )  ##не забыть потом админку допилить
        return None

    logger.info(f"Sessecc User Auth {email}")
    return user


async def update_last_login(session: AsyncSession, user: User) -> None:
    from datetime import datetime

    now_naive = datetime.now(UTC).replace(tzinfo=None)
    user.last_login_at = now_naive
    await session.commit()
    logger.debug(f"update last login for user {user.id}")
