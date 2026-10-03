from plataforma_iot.api.schemas.base import OutSchema

class TokenOut(OutSchema):
    """Token d'accés"""

    access_token: str
    token_type: str = "bearer"