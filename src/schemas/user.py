from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_]+$",
        description="Только латинские буквы, цифры и подчеркивание",
    )
    email: EmailStr
    password: str = Field(
        ..., min_length=8, max_length=128, description="Минимум 8 символов"
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    email: str
    created_at: datetime
    is_active: bool
    last_login_at: datetime | None = None


class UserUpdate(BaseModel):
    username: str | None = Field(
        None,
        min_length=3,
        max_length=50,
        pattern="^[a-zA-Z0-9_]+$",
        description="Только латинские буквы, цифры и подчеркивание",
    )
    email: EmailStr | None = None


##TODO
# можно добавить обновленеи пароля и отправку на почту
# но как будет время и желание
# так же сделать класс для валидации пароля и тд по желанию потом
