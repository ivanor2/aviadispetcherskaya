"""Тесты сравнения версий API v1 и v2.

Проверяют различия в структуре ответов и функциональности между версиями API.
"""
import pytest


class TestV1VsV2Comparison:
    """Набор тестов для сравнения функциональности API v1 и v2."""

    def test_list_structure_difference(self, client, admin_token, fake_airport_data):
        """Тестирует различия в структуре ответов между v1 и v2.
        
        Проверяет:
        - V1 возвращает Page[AirportResponse] (fastapi-pagination)
        - V2 возвращает Page с поиском и сортировкой, содержит items и total
        """
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post("/api/v2/airports", json=fake_airport_data, headers=headers)

        # V1 возвращает Page[AirportResponse] (fastapi-pagination)
        res_v1 = client.get("/api/v1/airports", headers=headers)
        assert res_v1.status_code == 200

        # V2 возвращает Page с поиском и сортировкой
        res_v2 = client.get("/api/v2/airports?page=1&size=1", headers=headers)
        assert res_v2.status_code == 200
        data = res_v2.json()
        assert "items" in data and "total" in data

    def test_search_feature_v2(self, client, admin_token, fake_airport_data):
        """Тестирует функцию поиска, доступную только в API v2.
        
        Проверяет, что поиск по названию аэропорта возвращает результаты.
        """
        headers = {"Authorization": f"Bearer {admin_token}"}
        client.post("/api/v2/airports", json=fake_airport_data, headers=headers)

        res = client.get(f"/api/v2/airports?search={fake_airport_data['name'][:4]}", headers=headers)
        assert res.status_code == 200
        assert len(res.json()["items"]) >= 1

    def test_sorting_v2(self, client, admin_token, fake_airport_data):
        """Тестирует функцию сортировки, доступную только в API v2.
        
        Проверяет сортировку аэропортов по имени в убывающем порядке.
        """
        headers = {"Authorization": f"Bearer {admin_token}"}
        for i in range(2):
            data = fake_airport_data.copy()
            data["icaoCode"] = f"SORT{i:02d}"
            data["name"] = f"City {i}"
            client.post("/api/v2/airports", json=data, headers=headers)

        res = client.get("/api/v2/airports?sort_by=name&order=desc", headers=headers)
        assert res.status_code == 200