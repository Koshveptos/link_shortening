from datetime import UTC, datetime, timedelta
from typing import Any, cast

import bcrypt
from jose import JWTError, jwt

from src.core.config import settings
from src.core.logger import logger


def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    hashed_str = hashed.decode("utf-8")
    logger.debug(f"Password hashed: {hashed_str[:10]}...")
    return cast(str, hashed_str)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    hashed_bytes = hashed_password.encode("utf-8")
    is_valid = bcrypt.checkpw(password_bytes, hashed_bytes)
    logger.debug(f"Верификация пароля: {is_valid}")
    return cast(bool, bcrypt.checkpw(password_bytes, hashed_bytes))


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(UTC),
        }
    )
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    logger.debug(f"Created JWT token for user: {data.get('sub')}")
    return cast(str, encoded_jwt)


def decode_access_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        logger.debug(f"Decoded JWT token: {payload.get('sub')}")
        return cast(dict[str, Any] | None, payload)
    except JWTError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None
