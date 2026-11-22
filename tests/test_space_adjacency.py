"""Proves de l'adjacència entre espais."""

import pytest
from sqlalchemy import select

from plataforma_iot.models.project import Project
from plataforma_iot.models.space import Space, space_adjacency
from plataforma_iot.models.user import User
from plataforma_iot.models.workgroup import Workgroup


@pytest.fixture
def rooms(session, project) -> dict:
    """Dues sales del mateix projecte i una tercera d'un altre."""
    first = Space(name="Sala 101", type="space", project_id=project.id)
    second = Space(name="Sala 102", type="space", project_id=project.id)
    session.add_all([first, second])
    session.flush()

    other_project = Project(
        name="Un altre estudi",
        workgroup_id=project.workgroup_id,
        owner_id=project.owner_id,
    )
    session.add(other_project)
    session.flush()

    alien = Space(name="Zona A", type="space", project_id=other_project.id)
    session.add(alien)
    session.flush()

    return {"first": first.id, "second": second.id, "alien": alien.id}


def _pairs(session) -> list[tuple[int, int]]:
    return [
        (row.a_id, row.b_id) for row in session.execute(select(space_adjacency))
    ]


def test_declares_an_adjacency(client, admin_auth, session, rooms):
    response = client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['second']}", headers=admin_auth
    )

    assert response.status_code == 204
    assert _pairs(session) == [(rooms["first"], rooms["second"])]


def test_the_order_of_the_ids_does_not_matter(client, admin_auth, session, rooms):
    """El parell es guarda sempre amb el menor primer, vinga com vinga."""
    client.put(
        f"/spaces/{rooms['second']}/adjacent/{rooms['first']}", headers=admin_auth
    )

    assert _pairs(session) == [(rooms["first"], rooms["second"])]


def test_declaring_it_twice_changes_nothing(client, admin_auth, session, rooms):
    path = f"/spaces/{rooms['first']}/adjacent/{rooms['second']}"
    client.put(path, headers=admin_auth)

    assert client.put(path, headers=admin_auth).status_code == 204
    assert len(_pairs(session)) == 1


def test_it_is_symmetric(client, admin_auth, rooms):
    """Si A és adjacent a B, B ho és a A: una sola fila, les dues consultes."""
    client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['second']}", headers=admin_auth
    )

    from_first = client.get(f"/spaces/{rooms['first']}/adjacent", headers=admin_auth)
    from_second = client.get(f"/spaces/{rooms['second']}/adjacent", headers=admin_auth)

    assert [s["name"] for s in from_first.json()] == ["Sala 102"]
    assert [s["name"] for s in from_second.json()] == ["Sala 101"]


def test_a_space_cannot_be_adjacent_to_itself(client, admin_auth, rooms):
    response = client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['first']}", headers=admin_auth
    )

    assert response.status_code == 422


def test_rejects_spaces_of_different_projects(client, admin_auth, rooms):
    """Invariant d'aplicació: l'adjacència viu dins d'un projecte."""
    response = client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['alien']}", headers=admin_auth
    )

    assert response.status_code == 422


def test_removes_an_adjacency(client, admin_auth, session, rooms):
    path = f"/spaces/{rooms['first']}/adjacent/{rooms['second']}"
    client.put(path, headers=admin_auth)

    assert client.delete(path, headers=admin_auth).status_code == 204
    assert _pairs(session) == []


def test_removing_one_that_did_not_exist_is_not_an_error(client, admin_auth, rooms):
    response = client.delete(
        f"/spaces/{rooms['first']}/adjacent/{rooms['second']}", headers=admin_auth
    )

    assert response.status_code == 204


def test_removing_it_from_the_other_side_works(client, admin_auth, session, rooms):
    client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['second']}", headers=admin_auth
    )

    client.delete(
        f"/spaces/{rooms['second']}/adjacent/{rooms['first']}", headers=admin_auth
    )

    assert _pairs(session) == []


def test_deleting_a_space_takes_its_adjacencies(client, admin_auth, session, rooms):
    """CASCADE: una adjacència a un espai que ja no existix no vol dir res."""
    client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['second']}", headers=admin_auth
    )

    client.delete(f"/spaces/{rooms['second']}", headers=admin_auth)

    assert _pairs(session) == []


def test_an_unknown_space_gives_404(client, admin_auth, rooms):
    response = client.put(
        f"/spaces/{rooms['first']}/adjacent/9999", headers=admin_auth
    )

    assert response.status_code == 404


def test_a_viewer_without_groups_cannot_see_them(client, viewer_auth, rooms):
    response = client.get(f"/spaces/{rooms['first']}/adjacent", headers=viewer_auth)

    assert response.status_code == 404

def test_the_listing_brings_the_neighbours(client, admin_auth, rooms):
    """Els veïns ixen en les dues direccions encara que el parell es guarde
    una sola volta."""
    client.put(
        f"/spaces/{rooms['first']}/adjacent/{rooms['second']}", headers=admin_auth
    )

    spaces = {s["id"]: s for s in client.get("/spaces", headers=admin_auth).json()}

    assert spaces[rooms["first"]]["adjacent_ids"] == [rooms["second"]]
    assert spaces[rooms["second"]]["adjacent_ids"] == [rooms["first"]]