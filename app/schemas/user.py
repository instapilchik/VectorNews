from pydantic import BaseModel, Field
from typing import Optional


class UserCreateRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    display_name: Optional[str] = Field(None, max_length=255)
    password: str = Field(..., min_length=6, max_length=255)
    role: str = Field(default="user", pattern="^(user|admin)$")


class UserUpdateRequest(BaseModel):
    display_name: Optional[str] = Field(None, max_length=255)
    password: Optional[str] = Field(None, min_length=6, max_length=255)
    role: Optional[str] = Field(None, pattern="^(user|admin)$")
    is_active: Optional[bool] = None
