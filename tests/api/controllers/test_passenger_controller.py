import pytest
from fastapi import HTTPException, status
from app.controllers.passenger_controller import (
    create_passenger, get_all_passengers, get_passenger_by_id,
    find_passenger_by_passport, find_passengers_by_name,
    delete_passenger, update_passenger
)
from app.schemas.passenger_schema import PassengerCreate, PassengerUpdate

@pytest.mark.usefixtures("db_session")
class TestPassengerController:
    def test_create_success(self, db_session, fake_passenger_data):
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        assert p.passport_number == fake_passenger_data["passportNumber"]

    def test_create_duplicate(self, db_session, fake_passenger_data):
        create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        with pytest.raises(HTTPException) as exc:
            create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        assert "уже зарегистрирован" in exc.value.detail

    def test_get_all(self, db_session, fake_passenger_data):
        create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        assert len(get_all_passengers(db_session)) == 1

    def test_get_by_id_success(self, db_session, fake_passenger_data):
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        assert get_passenger_by_id(p.id, db_session).id == p.id

    def test_get_by_id_not_found(self, db_session, max_passenger_id):
        with pytest.raises(HTTPException) as exc:
            get_passenger_by_id(max_passenger_id, db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_find_by_passport(self, db_session, fake_passenger_data):
        create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        res = find_passenger_by_passport(fake_passenger_data["passportNumber"], db_session)
        assert res.passport_number == fake_passenger_data["passportNumber"]

    def test_find_by_passport_not_found(self, db_session):
        with pytest.raises(HTTPException) as exc:
            find_passenger_by_passport("0000-000000", db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND

    def test_find_by_name(self, db_session, fake_passenger_data):
        fake_passenger_data["fullName"] = "Иванов Иван"
        create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        assert len(find_passengers_by_name("Иванов", db_session)) == 1

    def test_update_success(self, db_session, fake_passenger_data):
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        upd = update_passenger(p.id, PassengerUpdate(fullName="New Name"), db_session)
        assert upd.full_name == "New Name"

    def test_update_not_found(self, db_session, max_passenger_id):
        assert update_passenger(max_passenger_id, PassengerUpdate(fullName="X"), db_session) is None

    def test_delete_success(self, db_session, fake_passenger_data):
        p = create_passenger(PassengerCreate(**fake_passenger_data), db_session)
        delete_passenger(p.id, db_session)
        with pytest.raises(HTTPException):
            get_passenger_by_id(p.id, db_session)

    def test_delete_not_found(self, db_session, max_passenger_id):
        with pytest.raises(HTTPException) as exc:
            delete_passenger(max_passenger_id, db_session)
        assert exc.value.status_code == status.HTTP_404_NOT_FOUND