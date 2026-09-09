"""Models de dades de la plataforma.

Aquest mòdul importa totes les taules perquè queden registrades en
`Base.metadata`. Si un model no s'importa no apareix en les
migracions generades per Alembic. 
"""

from plataforma_iot.models.base import Base

__all__ = ["Base"]