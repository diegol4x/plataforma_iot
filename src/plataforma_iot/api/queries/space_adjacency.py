"""Consultes sobre l'adjacència d'espais."""

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from plataforma_iot.models.space import Space, space_adjacency


def neighbours(session: Session, space_id: int) -> list[Space]:
    """Espais adjacents a un altre.

    El parell es guarda una sola volta amb a_id < b_id, així que cal mirar les
    dues columnes. Amb els índexs de la taula el cost és menyspreable.
    """
    ids = select(space_adjacency.c.b_id).where(space_adjacency.c.a_id == space_id)
    reverse = select(space_adjacency.c.a_id).where(space_adjacency.c.b_id == space_id)

    return list(
        session.scalars(
            select(Space).where(Space.id.in_(ids.union(reverse))).order_by(Space.name)
        )
    )


def ordered_pair(first: int, second: int) -> tuple[int, int]:
    """El parell en l'ordre que exigix la restricció de la taula."""
    return (first, second) if first < second else (second, first)