# tests/api/controllers/test_user_controller.py
"""
Тесты для контроллера пользователей (UserController).

Проверяет:
- Создание пользователя (успешно и дубликат)
- Аутентификацию пользователя (правильный/неправильный пароль)
- Получение списка всех пользователей
- Обновление роли пользователя (успешно, недопустимая роль, не найден)
"""
import pytest
from fastapi import HTTPException, status
from app.controllers.user_controller import create_user, authenticate_user, get_all_users, update_user_role
from app.schemas.user_schema import UserCreate


@pytest.mark.usefixtures("db_session")
class TestUserController:
    """Набор тестов для функциональности контроллера пользователей."""

    def test_create_success(self, db_session, fake_user_data):
        """
        Тестирует успешное создание пользователя.
        
        Проверяет, что новый пользователь создаётся с ролью "guest" по умолчанию.
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Роль созданного пользователя равна "guest".
        """
        u = create_user(UserCreate(**fake_user_data), db_session)
        assert u.role == "guest"

    def test_create_duplicate(self, db_session, fake_user_data):
        """
        Тестирует создание пользователя с дублирующимся именем (ошибка 400).
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Вызывается HTTPException с сообщением о существовании пользователя.
        """
        create_user(UserCreate(**fake_user_data), db_session)
        with pytest.raises(HTTPException) as exc:
            create_user(UserCreate(**fake_user_data), db_session)
        assert "уже существует" in exc.value.detail

    def test_auth_success(self, db_session, fake_user_data):
        """
        Тестирует успешную аутентификацию пользователя.
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Ответ содержит access_token.
        """
        create_user(UserCreate(**fake_user_data), db_session)
        tokens = authenticate_user(fake_user_data["username"], fake_user_data["password"], db_session)
        assert "access_token" in tokens

    def test_auth_wrong_pass(self, db_session, fake_user_data):
        """
        Тестирует аутентификацию с неправильным паролем (ошибка 401).
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Вызывается HTTPException со статусом 401 UNAUTHORIZED.
        """
        create_user(UserCreate(**fake_user_data), db_session)
        with pytest.raises(HTTPException) as exc:
            authenticate_user(fake_user_data["username"], "WrongPass1!", db_session)
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_all(self, db_session, fake_user_data):
        """
        Тестирует получение списка всех пользователей.
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Список содержит как минимум одного пользователя.
        """
        create_user(UserCreate(**fake_user_data), db_session)
        assert len(get_all_users(db_session)) >= 1

    def test_update_role_success(self, db_session, fake_user_data):
        """
        Тестирует успешное обновление роли пользователя.
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Роль пользователя изменена на "dispatcher".
        """
        u = create_user(UserCreate(**fake_user_data), db_session)
        upd = update_user_role(u.id, "dispatcher", db_session)
        assert upd.role == "dispatcher"

    def test_update_role_invalid(self, db_session, fake_user_data):
        """
        Тестирует обновление роли на недопустимое значение (ошибка 400).
        
        Args:
            db_session: Сессия базы данных.
            fake_user_data: Фикстура с данными пользователя.
            
        Asserts:
            - Вызывается HTTPException с сообщением о недопустимой роли.
        """
        u = create_user(UserCreate(**fake_user_data), db_session)
        with pytest.raises(HTTPException) as exc:
            update_user_role(u.id, "super_admin", db_session)
        assert "Недопустимая роль" in exc.value.detail

    def test_update_role_not_found(self, db_session, max_user_id):
        """
        Тестирует обновление роли несуществующего пользователя (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            max_user_id: Следующий доступный ID (несуществующий).
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            update_user_role(max_user_id, "admin", db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND