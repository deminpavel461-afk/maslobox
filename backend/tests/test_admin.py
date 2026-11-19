from __future__ import annotations


def _create_booking(client, phone="89123334455", point_id=None):
    payload = {
        "name": "Админ Тест",
        "phone": phone,
        "car_model": "Skoda Octavia",
        "consent": True,
    }
    if point_id is not None:
        payload["point_id"] = point_id
    response = client.post("/api/v1/bookings", json=payload)
    assert response.status_code == 201, response.text
    return response.json()["id"]


def test_admin_requires_auth(client):
    response = client.get("/api/v1/admin/bookings")
    assert response.status_code == 401


def test_admin_list_and_filter(client):
    points = {p["slug"]: p for p in client.get("/api/v1/points").json()}
    _create_booking(client, phone="89120000001", point_id=points["north"]["id"])
    _create_booking(client, phone="89120000002", point_id=points["center"]["id"])

    headers = {"Authorization": "Bearer test-admin-token"}
    response = client.get("/api/v1/admin/bookings", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] >= 2

    filtered = client.get(
        "/api/v1/admin/bookings",
        headers=headers,
        params={"point_id": points["north"]["id"], "q": "000001"},
    )
    assert filtered.status_code == 200
    items = filtered.json()["items"]
    assert len(items) == 1
    assert items[0]["phone"] == "+79120000001"


def test_point_admin_sees_only_own(client):
    points = {p["slug"]: p for p in client.get("/api/v1/points").json()}
    _create_booking(client, phone="89120000011", point_id=points["north"]["id"])
    _create_booking(client, phone="89120000012", point_id=points["south"]["id"])

    response = client.get(
        "/api/v1/admin/bookings",
        headers={"X-Admin-Token": "north-token"},
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(item["point_id"] == points["north"]["id"] for item in items)


def test_admin_status_transition(client):
    booking_id = _create_booking(client, phone="89120000021")
    headers = {"Authorization": "Bearer test-admin-token"}

    confirmed = client.patch(
        f"/api/v1/admin/bookings/{booking_id}",
        headers=headers,
        json={"status": "confirmed", "admin_comment": "Перезвонили"},
    )
    assert confirmed.status_code == 200
    assert confirmed.json()["status"] == "confirmed"
    assert confirmed.json()["admin_comment"] == "Перезвонили"

    done = client.patch(
        f"/api/v1/admin/bookings/{booking_id}",
        headers=headers,
        json={"status": "done"},
    )
    assert done.status_code == 200
    assert done.json()["status"] == "done"

    invalid = client.patch(
        f"/api/v1/admin/bookings/{booking_id}",
        headers=headers,
        json={"status": "new"},
    )
    assert invalid.status_code == 422
