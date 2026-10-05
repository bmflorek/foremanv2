from pydantic import BaseModel, ConfigDict, Field
from models.common import new_id, now_iso


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=new_id)
    email: str
    name: str
    picture: str = ""
    created_at: str = Field(default_factory=now_iso)


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetVerify(BaseModel):
    email: str
    otp: str
    new_password: str
