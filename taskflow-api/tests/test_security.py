import time
from datetime import timedelta

from jose import jwt

from app.core.config import settings
from app.core.security import (
    ALGORITHM,
    create_access_token,
    get_password_hash,
    verify_password,
)


def test_password_hash_and_verify():
    password = "secret123"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_access_token_contains_sub_and_valid_exp():
    token = create_access_token({"sub": "user@example.com"})
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == "user@example.com"
    assert "exp" in decoded
    now = int(time.time())
    exp = int(decoded["exp"])
    max_delta = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60 + 60
    assert 0 < exp - now <= max_delta


def test_create_access_token_custom_expiry_short_window():
    token = create_access_token({"sub": "a@b.com"}, expires_delta=timedelta(seconds=5))
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    now = int(time.time())
    exp = int(decoded["exp"])
    assert 0 < exp - now <= 5 + 2
