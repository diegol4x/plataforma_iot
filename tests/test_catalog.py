"""Proves del catàleg d'unitats i magnituds."""

import pytest

from plataforma_iot.models.catalog import Unit


@pytest.fixture
def units(session) -> None:
    session.add_all(
        [
            Unit(name="Hectopascal", symbol="hPa"),
            Unit(name="Pascal", symbol="Pa"),
        ]
    )
    session.flush()


def _create(client, admin_auth, **extra) -> dict:
    body = {"code": "pressure", "name": "Pressió", "unit_symbol": "hPa"} | extra
    return client.post("/sensor_types", json=body, headers=admin_auth).json()


def test_the_unit_can_be_corrected(client, admin_auth, units):
    """El cas real: es mesurava en Pa però el catàleg deia hPa."""
    created = _create(client, admin_auth)

    response = client.patch(
        f"/sensor_types/{created['id']}", json={"unit_symbol": "Pa"}, headers=admin_auth
    )

    assert response.status_code == 200
    assert response.json()["unit"] == "Pa"


def test_an_unknown_unit_is_rejected(client, admin_auth, units):
    created = _create(client, admin_auth)

    response = client.patch(
        f"/sensor_types/{created['id']}", json={"unit_symbol": "psi"}, headers=admin_auth
    )

    assert response.status_code == 422


def test_the_range_is_checked_against_the_stored_value(client, admin_auth, units):
    """Enviant sols el màxim, es compara amb el mínim que ja tenia."""
    created = _create(client, admin_auth, range_min=300.0, range_max=1100.0)

    response = client.patch(
        f"/sensor_types/{created['id']}", json={"range_max": 100.0}, headers=admin_auth
    )

    assert response.status_code == 422


def test_a_viewer_cannot_edit_the_catalogue(client, viewer_auth, admin_auth, units):
    created = _create(client, admin_auth)

    response = client.patch(
        f"/sensor_types/{created['id']}", json={"name": "Meu"}, headers=viewer_auth
    )

    assert response.status_code == 403