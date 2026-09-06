from pydantic import BaseModel
import uuid

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: str | None = None

class UserAuthResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    company_id: uuid.UUID
