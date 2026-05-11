import pytest
from fastapi import HTTPException, status
from app.controllers.user_controller import create_user, authenticate_user, get_all_users, update_user_role
from app.schemas.user_schema import UserCreate

@pytest.mark.usefixtures("db_session")
class TestUserController:
    def test_create_success(self, db_session, fake_user_data):
        u = create_user(UserCreate(**fake_user_data), db_session)
        assert u.role == "guest"

    def test_create_duplicate(self, db_session, fake_user_data):
        create_user(UserCreate(**fake_user_data), db_session)
        with pytest.raises(HTTPException) as exc:
            create_user(UserCreate(**fake_user_data), db_session)
        assert "уже существует" in exc.value.detail

    def test_auth_success(self, db_session, fake_user_data):
        create_user(UserCreate(**fake_user_data), db_session)
        tokens = authenticate_user(fake_user_data["username"], fake_user_data["password"], db_session)
        assert "access_token" in tokens

    def test_auth_wrong_pass(self, db_session, fake_user_data):
        create_user(UserCreate(**fake_user_data), db_session)
        with pytest.raises(HTTPException) as exc:
            authenticate_user(fake_user_data["username"], "WrongPass1!", db_session)
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all(self, db_session, fake_user_data):
        create_user(UserCreate(**fake_user_data), db_session)
        assert len(get_all_users(db_session)) >= 1

    def test_update_role_success(self, db_session, fake_user_data):
        u = create_user(UserCreate(**fake_user_data), db_session)
        upd = update_user_role(u.id, "dispatcher", db_session)
        assert upd.role == "dispatcher"

    def test_update_role_invalid(self, db_session, fake_user_data):
        u = create_user(UserCreate(**fake_user_data), db_session)
        with pytest.raises(HTTPException) as exc:
            update_user_role(u.id, "super_admin", db_session)
        assert "Недопустимая роль" in exc.value.detail

    def test_update_role_not_found(self, db_session, max_user_id):
        with pytest.raises(HTTPException) as exc:
            update_user_role(max_user_id, "admin", db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND