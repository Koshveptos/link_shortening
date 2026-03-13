from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.click_events import ClickEvent
    from src.models.user import User


class Link(Base):
    __tablename__ = "links"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    short_code: Mapped[str] = mapped_column(String(12), index=True, unique=True)
    custom_alias: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True
    )
    original_url: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True, nullable=False
    )

    expires_at: Mapped[datetime | None] = mapped_column(index=True, nullable=True)
    last_clicked_at: Mapped[datetime | None] = mapped_column(index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    clicks_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    owner: Mapped[Optional["User"]] = relationship(back_populates="links")

    click_events: Mapped[list["ClickEvent"]] = relationship(
        back_populates="link", cascade="all, delete-orphan", lazy="selectin"
    )
    __table_args__ = (
        Index("ix_links_active_expiration", "is_active", "expires_at"),
        Index("ix_links_user_active", "user_id", "is_active"),
    )

    def record_click(self) -> None:
        self.clicks_count += 1
        self.last_clicked_at = datetime.now(UTC)

    def __repr__(self) -> str:
        return f"Link(id={self.id}, short={self.short_code!r}, url={self.original_url[:40]!r}...)"
