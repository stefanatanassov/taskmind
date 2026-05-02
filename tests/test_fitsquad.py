from __future__ import annotations


def test_fitsquad_pages_and_package_api(client):
    home = client.get("/fitsquad/")
    assert home.status_code == 200
    assert "FitSquad" in home.text
    assert "Current packages" in home.text

    packages = client.get("/fitsquad/api/packages")
    assert packages.status_code == 200
    body = packages.json()
    assert len(body) >= 2
    assert body[0]["remaining_spots"] > 0


def test_fitsquad_reservation_and_admin_update(client):
    packages = client.get("/fitsquad/api/packages").json()
    package = packages[0]

    create_response = client.post(
        f"/fitsquad/api/packages/{package['slug']}/reservations",
        json={
            "client_name": "Stefan Atanassov",
            "email": "stefan@example.com",
            "phone": "+359888123456",
            "participants": 2,
            "payment_option": "deposit",
        },
    )
    assert create_response.status_code == 200
    reservation = create_response.json()
    assert reservation["payment_status"] == "deposit_paid"
    assert reservation["reservation_status"] == "pending"

    confirmation = client.get(f"/fitsquad/reservations/{reservation['reservation_code']}")
    assert confirmation.status_code == 200
    assert reservation["reservation_code"] in confirmation.text
    assert "Automatic emails generated" in confirmation.text

    admin = client.get("/fitsquad/api/admin/reservations")
    assert admin.status_code == 200
    admin_rows = admin.json()
    assert len(admin_rows) == 1

    update = client.post(
        f"/fitsquad/api/admin/reservations/{reservation['id']}",
        json={"reservation_status": "confirmed"},
    )
    assert update.status_code == 200
    assert update.json()["reservation_status"] == "confirmed"


def test_fitsquad_prevents_overbooking(client):
    packages = client.get("/fitsquad/api/packages").json()
    package = packages[1]

    first = client.post(
        f"/fitsquad/api/packages/{package['slug']}/reservations",
        json={
            "client_name": "First Booker",
            "email": "first@example.com",
            "phone": "+359888111111",
            "participants": package["capacity"],
            "payment_option": "full",
        },
    )
    assert first.status_code == 200

    second = client.post(
        f"/fitsquad/api/packages/{package['slug']}/reservations",
        json={
            "client_name": "Second Booker",
            "email": "second@example.com",
            "phone": "+359888222222",
            "participants": 1,
            "payment_option": "deposit",
        },
    )
    assert second.status_code == 400
    assert "spots remain" in second.json()["detail"]
