# tests/api/controllers/test_airport_controller.py
"""
Тесты для контроллера аэропортов (AirportController).

Проверяет CRUD операции:
- Создание аэропорта (успешно и дубликат ICAO-кода)
- Получение аэропорта по ID и ICAO-коду
- Обновление аэропорта
- Удаление аэропорта
- Получение списка всех аэропортов
"""
import pytest
from fastapi import HTTPException, status
from app.controllers.airport_controller import (
    create_airport, get_airport_by_id, get_airport_by_icao,
    update_airport, delete_airport, get_all_airports
)
from app.schemas.airport_schema import AirportCreate, AirportUpdate
from tests.conftest import fake  # ✅ Фикс NameError


@pytest.mark.usefixtures("db_session")
class TestAirportController:
    """Набор тестов для функциональности контроллера аэропортов."""

    def test_get_all_airports_empty(self, db_session):
        """
        Тестирует получение списка аэропортов при пустой базе.
        
        Args:
            db_session: Сессия базы данных.
            
        Asserts:
            - Возвращается пустой список.
        """
        assert get_all_airports(db_session) == []

    def test_get_all_airports_with_faker_data(self, db_session, fake_airport_data):
        """
        Тестирует получение списка аэропортов с данными.
        
        Создаёт один аэропорт и проверяет, что список содержит один элемент.
        
        Args:
            db_session: Сессия базы данных.
            fake_airport_data: Фикстура с данными аэропорта.
        """
        create_airport(AirportCreate(**fake_airport_data), db_session)
        assert len(get_all_airports(db_session)) == 1

    def test_get_airport_by_id_success(self, db_session, fake_airport_data):
        """
        Тестирует успешное получение аэропорта по ID.
        
        Args:
            db_session: Сессия базы данных.
            fake_airport_data: Фикстура с данными аэропорта.
            
        Asserts:
            - ID найденного аэропорта совпадает с искомым.
        """
        ap = create_airport(AirportCreate(**fake_airport_data), db_session)
        assert get_airport_by_id(ap.id, db_session).id == ap.id

    def test_get_airport_by_id_not_found(self, db_session, max_airport_id):
        """
        Тестирует получение несуществующего аэропорта по ID (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            max_airport_id: Следующий доступный ID (несуществующий).
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            get_airport_by_id(max_airport_id, db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_get_airport_by_icao_not_found(self, db_session):
        """
        Тестирует получение аэропорта по несуществующему ICAO-коду (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            get_airport_by_icao("XXXX", db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_create_airport_success(self, db_session, fake_airport_data):
        """
        Тестирует успешное создание аэропорта.
        
        Args:
            db_session: Сессия базы данных.
            fake_airport_data: Фикстура с данными аэропорта.
            
        Asserts:
            - ICAO-код созданного аэропорта совпадает с входными данными.
        """
        ap = create_airport(AirportCreate(**fake_airport_data), db_session)
        assert ap.icao_code == fake_airport_data["icaoCode"]

    def test_create_airport_duplicate_icao(self, db_session, fake_airport_data):
        """
        Тестирует создание аэропорта с дублирующимся ICAO-кодом (ошибка 400).
        
        Args:
            db_session: Сессия базы данных.
            fake_airport_data: Фикстура с данными аэропорта.
            
        Asserts:
            - Вызывается HTTPException со статусом 400 BAD REQUEST.
        """
        create_airport(AirportCreate(**fake_airport_data), db_session)
        with pytest.raises(HTTPException) as exc:
            create_airport(AirportCreate(**fake_airport_data), db_session)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_update_airport_success(self, db_session, fake_airport_data):
        """
        Тестирует успешное обновление аэропорта.
        
        Args:
            db_session: Сессия базы данных.
            fake_airport_data: Фикстура с данными аэропорта.
            
        Asserts:
            - Название аэропорта содержит новое значение.
        """
        ap = create_airport(AirportCreate(**fake_airport_data), db_session)
        updated = update_airport(ap.id, AirportUpdate(name="Updated " + fake.city()), db_session)
        assert "Updated" in updated.name

    def test_update_airport_not_found(self, db_session, max_airport_id):
        """
        Тестирует обновление несуществующего аэропорта (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            max_airport_id: Следующий доступный ID (несуществующий).
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            update_airport(max_airport_id, AirportUpdate(name="X"), db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_delete_airport_success(self, db_session, fake_airport_data):
        """
        Тестирует успешное удаление аэропорта.
        
        После удаления проверяет, что попытка получить удалённый аэропорт
        вызывает исключение.
        
        Args:
            db_session: Сессия базы данных.
            fake_airport_data: Фикстура с данными аэропорта.
        """
        ap = create_airport(AirportCreate(**fake_airport_data), db_session)
        delete_airport(ap.id, db_session)
        with pytest.raises(HTTPException):
            get_airport_by_id(ap.id, db_session)

    def test_delete_airport_not_found(self, db_session, max_airport_id):
        """
        Тестирует удаление несуществующего аэропорта (ошибка 404).
        
        Args:
            db_session: Сессия базы данных.
            max_airport_id: Следующий доступный ID (несуществующий).
            
        Asserts:
            - Вызывается HTTPException со статусом 404 NOT FOUND.
        """
        with pytest.raises(HTTPException) as exc:
            delete_airport(max_airport_id, db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND