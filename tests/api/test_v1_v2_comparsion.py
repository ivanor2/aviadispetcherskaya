import pytest
from fastapi import status


def test_list_pagination_v1_vs_v2(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    # Создаем тестовые данные
    for i in range(15):
        client.post("/api/v1/airports", json={"icaoCode": f"TEST{i:02d}", "name": f"Airport {i}"}, headers=headers)

    v1_res = client.get("/api/v1/airports", headers=headers)
    v2_res = client.get("/api/v2/airports?page=1&size=5", headers=headers)

    # V1 возвращает плоский список (или первую страницу без metadata)
    assert v1_res.status_code == 200
    assert isinstance(v1_res.json(), list)

    # V2 возвращает пагинированный объект
    assert v2_res.status_code == 200
    data = v2_res.json()
    assert "items" in data and "total" in data
    assert len(data["items"]) == 5
    assert data["total"] == 15


def test_search_feature_v2(client, admin_token):
    headers = {"Authorization": f"Bearer {admin_token}"}
    client.post("/api/v2/airports", json={"icaoCode": "SVO1", "name": "Sheremetyevo"}, headers=headers)

    res = client.get("/api/v2/airports?search=Sher", headers=headers)
    assert res.status_code == 200
    assert len(res.json()["items"]) == 1