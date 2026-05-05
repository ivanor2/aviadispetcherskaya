# tests/api/test_security.py
import pytest
from fastapi import HTTPException, status
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    get_current_user, admin_required, dispatcher_or_higher
)
from app.models.user import User


def test_hash_and_verify_password():
    password = "MySecureP@ss123"
    hashed = hash_password(password)

    assert hashed != password  # Пароль захеширован
    assert verify_password(password, hashed)  # Проверка проходит
    assert not verify_password("WrongPassword", hashed)  # Неправильный пароль не проходит


def test_create_and_decode_access_token():
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data)

    assert token is not None
    username = decode_token(token, expected_type="access")
    assert username == "testuser"


def test_decode_wrong_token_type():
    access_token = create_access_token({"sub": "user"})

    # Пытаемся декодировать access-токен как refresh
    with pytest.raises(HTTPException) as exc:
        decode_token(access_token, expected_type="refresh")
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_decode_expired_token():
    from datetime import timedelta
    # Создаём токен с истёкшим сроком
    token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-1))

    result = decode_token(token)
    assert result is None  # Истёкший токен не декодируется


def test_decode_invalid_token():
    result = decode_token("invalid.token.here")
    assert result is None


def test_get_current_user_invalid_token(db_session):
    from fastapi import Depends

    with pytest.raises(HTTPException) as exc:
        get_current_user(token="invalid_token", session=db_session)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin_required_non_admin(db_session):
    user = User(username="guest_user", password=hash_password("pass"), role="guest")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})

    with pytest.raises(HTTPException) as exc:
        admin_required(user=get_current_user(token=token, session=db_session))
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_dispatcher_or_higher_guest_denied(db_session):
    user = User(username="guest", password=hash_password("pass"), role="guest")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})

    with pytest.raises(HTTPException) as exc:
        dispatcher_or_higher(user=get_current_user(token=token, session=db_session))
    assert exc.value.status_code == status.HTTP_403_FORBIDDEN


def test_dispatcher_or_higher_dispatcher_allowed(db_session):
    user = User(username="dispatch", password=hash_password("pass"), role="dispatcher")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({"sub": user.username})
    result = dispatcher_or_higher(user=get_current_user(token=token, session=db_session))

    assert result.role == "dispatcher"