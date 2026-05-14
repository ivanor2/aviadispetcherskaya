# tests/api/controllers/test_airline_controller.py
"""
Тесты для контроллера авиакомпаний (AirlineController).

Проверяет CRUD операции:
- Создание авиакомпании (успешно и дубликат)
- Получение авиакомпании по коду (существующей и несуществующей)
- Обновление авиакомпании
- Удаление авиакомпании
- Получение списка всех авиакомпаний
"""
import pytest
from fastapi import HTTPException, status
from app.controllers.airline_controller import (
    create_airline, get_airline_by_code, get_all_airlines, update_airline, delete_airline
)
from app.schemas.airline_schema import AirlineCreate


@pytest.mark.usefixtures("db_session")
class TestAirlineController:
    """Набор тестов для функциональности контроллера авиакомпаний."""

    def test_create_success(self, db_session, fake_airline_data):
        """
        Тестирует успешное создание авиакомпании.
        
        Args:
            db_session: Сессия базы данных.
            fake_airline_data: Фикстура с данными авиакомпании.
            
        Asserts:
            - Код созданной авиакомпании совпадает с входными данными.
        """
        al = create_airline(AirlineCreate(**fake_airline_data), db_session)
        assert al.code == fake_airline_data["code"]

    def test_create_duplicate(self, db_session, fake_airline_data):
        """
        Тестирует создание дубликата авиакомпании (ошибка 400).
        
        Проверяет, что попытка создать авиакомпанию с уже существующим кодом
        вызывает HTTPException со статусом 400 BAD REQUEST.
        
        Args:
            db_session: Сессия базы данных.
            fake_airline_data: Фикстура с данными авиакомпании.
        """
        create_airline(AirlineCreate(**fake_airline_data), db_session)
        with pytest.raises(HTTPException) as exc:
            create_airline(AirlineCreate(**fake_airline_data), db_session)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_get_success(self, db_session, fake_airline_data):
        """
        Тестирует успешное получение авиакомпании по коду.
        
        Args:
            db_session: Сессия базы данных.
            fake_airline_data: Фикстура с данными авиакомпании.
            
        Asserts:
            - Название найденной авиакомпании совпадает с входными данными.
        """
        create_airline(AirlineCreate(**fake_airline_data), db_session)
        al = get_airline_by_code(fake_airline_data["code"], db_session)
        assert al.name == fake_airline_data["name"]

    def test_get_not_found(self, db_session):
        """
        Тестирует получение несуществующей авиакомпании (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            get_airline_by_code("ZZZ", db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_list_empty(self, db_session):
        """
        Тестирует получение списка авиакомпаний при пустой базе.
        
        Args:
            db_session: Сессия базы данных.
            
        Asserts:
            - Возвращается пустой список.
        """
        assert get_all_airlines(db_session) == []

    def test_update_success(self, db_session, fake_airline_data):
        """
        Тестирует успешное обновление авиакомпании.
        
        Args:
            db_session: Сессия базы данных.
            fake_airline_data: Фикстура с данными авиакомпании.
            
        Asserts:
            - Название авиакомпании изменено на новое.
        """
        create_airline(AirlineCreate(**fake_airline_data), db_session)
        upd = update_airline(fake_airline_data["code"], AirlineCreate(code=fake_airline_data["code"], name="New"), db_session)
        assert upd.name == "New"

    def test_update_not_found(self, db_session, fake_airline_data):
        """
        Тестирует обновление несуществующей авиакомпании.
        
        Args:
            db_session: Сессия базы данных.
            fake_airline_data: Фикстура с данными авиакомпании.
            
        Asserts:
            - Вызывается HTTPException.
        """
        with pytest.raises(HTTPException):
            update_airline("XXX", AirlineCreate(code="XXX", name="Test"), db_session)

    def test_delete_success(self, db_session, fake_airline_data):
        """
        Тестирует успешное удаление авиакомпании.
        
        После удаления проверяет, что попытка получить удалённую авиакомпанию
        вызывает исключение.
        
        Args:
            db_session: Сессия базы данных.
            fake_airline_data: Фикстура с данными авиакомпании.
        """
        create_airline(AirlineCreate(**fake_airline_data), db_session)
        delete_airline(fake_airline_data["code"], db_session)
        with pytest.raises(HTTPException):
            get_airline_by_code(fake_airline_data["code"], db_session)

    def test_delete_not_found(self, db_session):
        """
        Тестирует удаление несуществующей авиакомпании (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            delete_airline("NNN", db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND