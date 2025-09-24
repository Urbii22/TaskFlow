from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    # sub = subject (p. ej., email del usuario)
    sub: str


