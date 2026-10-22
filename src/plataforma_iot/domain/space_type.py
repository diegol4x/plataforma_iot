"""Tipus d'espai, segons les subclasses de BOT:Zone (W3C)"""

from enum import StrEnum

class SpaceType(StrEnum):
    """Classificació d'un espai"""

    SITE="site"
    BUILDING="building"
    STOREY="storey"
    SPACE="space"