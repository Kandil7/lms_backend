from __future__ import annotations
from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, Integer, Text, JSON
from sqlalchemy import Uuid
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.modules.courses.models.course import Course


class Instructor(Base):
    __tablename__ = "instructors"

    id = Column(Uuid(as_uuid=True), primary_key=True)
    user_id = Column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    bio = Column(Text, nullable=False)
    expertise = Column(JSON, nullable=False, default=list)
    teaching_experience_years = Column(Integer, nullable=False, default=0)
    education_level = Column(String(100), nullable=False)
    institution = Column(String(255), nullable=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_status = Column(String(50), nullable=False, default="pending")
    verification_notes = Column(Text)
    verification_document_url = Column(String(1000))
    verification_expires_at = Column(DateTime)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="instructor")

    def __repr__(self):
        return f"<Instructor(id={self.id}, user_id={self.user_id}, is_verified={self.is_verified})>"