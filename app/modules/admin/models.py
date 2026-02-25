from datetime import datetime
from typing import Optional
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String, Boolean, JSON, Integer, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    security_level = Column(String(20), nullable=False, default="standard")
    mfa_required = Column(Boolean, nullable=False, default=True)
    ip_whitelist = Column(JSON, nullable=False, default=list)
    time_restrictions = Column(JSON, nullable=False, default=dict)
    emergency_contacts = Column(JSON, nullable=False, default=list)
    is_setup_complete = Column(Boolean, nullable=False, default=False)
    setup_completed_at = Column(DateTime)
    security_policy_accepted = Column(Boolean, nullable=False, default=False)
    security_policy_version = Column(String(20), nullable=False, default="1.0")
    last_security_review = Column(DateTime)
    security_health_score = Column(Integer, nullable=False, default=50)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="admin")

    def __repr__(self):
        return f"<Admin(id={self.id}, user_id={self.user_id}, security_level={self.security_level})>"
