from src.core.security import (
    create_access_token,
    decode_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing() -> None:
    password = "TestPassword123!"

    hashed = get_password_hash(password)
    assert isinstance(hashed, str)
    assert len(hashed) == 60

    assert verify_password(password, hashed) is True

    assert verify_password("wrong_password", hashed) is False

    hashed2 = get_password_hash(password)
    assert hashed != hashed2

    assert verify_password(password, hashed2) is True


def test_jwt_token() -> None:
    user_data = {"sub": "123", "username": "test_user"}
    token = create_access_token(user_data)

    assert isinstance(token, str)
    assert len(token) > 0

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "123"
    assert payload["username"] == "test_user"
    assert "exp" in payload
    assert "iat" in payload

    invalid = decode_access_token("invalid.token.here")
    assert invalid is None
