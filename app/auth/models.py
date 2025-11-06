"""
User SQLAlchemy Model
Matching Django User model functionality
"""

from sqlalchemy import String, Text, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid

from ..database import Base


class User(Base):
    """User model with DJ platform specific fields"""
    
    __tablename__ = "users"
    
    # Primary fields
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    username: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(254), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Profile fields
    first_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # File path
    
    # DJ-specific fields
    dj_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Account settings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    email_notifications: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Timestamps
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    @property
    def full_name(self) -> str:
        """Return full name or username if names not provided"""
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        return self.username
    
    @property
    def display_name(self) -> str:
        """Return DJ name, full name, or username in that order"""
        return self.dj_name or self.full_name or self.username
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, dj_name={self.dj_name})>"