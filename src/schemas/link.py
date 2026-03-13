from datetime import UTC, datetime

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)


class LinkCreate(BaseModel):
    original_url: AnyHttpUrl = Field(
        ..., max_length=2048, description="Ссылка должна начинаться с https://"
    )
    custom_alias: str | None = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9\-_ ]+$"
    )
    expires_at: datetime | None = Field(None, description="Время жизни ссылки")

    @field_validator("expires_at")
    @classmethod
    def check_future_date(cls, v: datetime | None) -> datetime | None:
        if v and v <= datetime.now(UTC):
            raise ValueError("время должно быть в будущем ")
        return v


class LinkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    short_code: str
    custom_alias: str | None
    original_url: str
    created_at: datetime
    expires_at: datetime | None
    is_active: bool
    clicks_count: int
    user_id: int | None = None


class LinkUpdate(BaseModel):
    is_active: bool | None = None
    expires_at: datetime | None = None
    custom_alias: str | None = Field(
        None, min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9\-_ ]+$"
    )


class LinkRedirect(BaseModel):
    message: str = "Redirecting ..."
    original_url: str
