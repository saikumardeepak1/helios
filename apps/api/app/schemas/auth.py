import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [{"email": "you@example.com", "password": "hunter2"}]
        }
    )


class RefreshRequest(BaseModel):
    refresh_token: str = Field(description="A refresh token previously issued by /v1/auth/login.")


class TokenResponse(BaseModel):
    access_token: str = Field(description="Short-lived token for Authorization headers.")
    refresh_token: str = Field(description="Longer-lived token used to obtain a new access token.")
    token_type: str = "bearer"


class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    prefix: str = Field(description="Non-secret prefix of the key, safe to display in a UI.")
    key: str = Field(
        description="The full API key. Shown only in this response — Helios stores just a "
        "salted hash, so it can't be recovered later."
    )


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)
