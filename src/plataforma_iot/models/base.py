"""Classe base declarativa."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Arrel de la jerarquia declarativa.

    Totes les taules hereten d'ací perquè les seues definicions
    queden registrades en Base.metadata.
    """