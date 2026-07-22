import uuid

from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    prefix: str
    key: str


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    organization_id: uuid.UUID

    model_config = {"from_attributes": True}
