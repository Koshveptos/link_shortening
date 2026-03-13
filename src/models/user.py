from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import Base

if TYPE_CHECKING:
    from src.models.links import Link


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), index=True, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(default=True, index=True)
    last_login_at: Mapped[datetime | None] = mapped_column(nullable=True)
    links: Mapped[list["Link"]] = relationship(
        back_populates="owner",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="Link.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"User with id {self.id}  and username {self.username}"
