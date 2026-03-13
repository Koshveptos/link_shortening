from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.links import Link


class ClickEvent(Base):
    __tablename__ = "click_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    link_id: Mapped[int] = mapped_column(
        ForeignKey("links.id", ondelete="CASCADE"), index=True
    )

    ip_address: Mapped[str | None] = mapped_column(
        String(45), index=True, nullable=True
    )  # для айти 4-6
    country_code: Mapped[str | None] = mapped_column(String(2), nullable=True)
    device_type: Mapped[str | None] = mapped_column(
        String(100), index=True, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True, nullable=False
    )

    link: Mapped["Link"] = relationship(back_populates="click_events")

    __table_args__ = (
        Index("ix_clicks_link_created", "link_id", "created_at"),
        Index("ix_clicks_country_created", "country_code", "created_at"),
        Index("ix_clicks_device_created", "device_type", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ClickEvent id={self.id} link_id={self.link_id}>"
