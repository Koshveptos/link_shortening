from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ClickEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    link_id: int
    clicked_at: datetime
    ip_address: str | None = None
    country_code: str | None = None
    device_type: str | None = None


class LinkStats(BaseModel):
    total_clicks: int = Field(..., ge=0)
    unique_ips: int = Field(..., ge=0)
    last_clecked_at: datetime | None = None
    clicks_by_country: dict[str, int] = Field(default_factory=dict)
    clicks_by_devise: dict[str, int] = Field(default_factory=dict)
    clicks_last_7_days: dict[str, int] = Field(default_factory=dict)
