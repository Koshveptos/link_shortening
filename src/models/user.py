import time
from typing import List, Optional

from sqlalchemy import Float, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from src.models.base import Base

    
class User(Base):
    __tablename__ = 'users'
    id:Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email:Mapped[str] = mapped_column(String(255),unique=True, index=True, nullable=False)
    password_hash:Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True, nullable=False)
    is_active:Mapped[bool] = mapped_column(default=True, index=True)
    last_login_at:Mapped[Optional[datetime]] = mapped_column(nullable=True)
    links:Mapped[List["Link"]] = relationship(
        back_populates='owner', 
        cascade='all, delete-orphan',
        lazy = 'selectin',
        order_by="Link.created_at.desc()"
    )
    def __repr__(self):
        return f'User with id {self.id}  and username {self.username}'

