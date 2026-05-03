"""
Database models for Awaaz.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum


class ComplaintStatus(str, enum.Enum):
    DRAFT = "draft"
    READY = "ready"
    FILED = "filed"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class ComplaintCategory(str, enum.Enum):
    CYBERCRIME = "cybercrime"
    CONSUMER = "consumer"
    MUNICIPAL = "municipal"
    RTI = "rti"
    POLICE = "police"
    RERA = "rera"
    RAILWAYS = "railways"
    TAX = "tax"
    LABOUR = "labour"
    OTHER = "other"


class Complaint(Base):
    __tablename__ = "complaints"

    id = Column(Integer, primary_key=True, index=True)
    tracking_id = Column(String(20), unique=True, index=True)
    
    # User info (simple for MVP — no full auth yet)
    user_name = Column(String(100), nullable=True)
    user_email = Column(String(200), nullable=True)
    user_phone = Column(String(15), nullable=True)
    user_city = Column(String(100), default="Kochi")
    
    # Complaint details
    original_description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    subcategory = Column(String(100), nullable=True)
    
    # AI-generated content
    ai_draft = Column(Text, nullable=True)
    ai_summary = Column(Text, nullable=True)
    authority = Column(String(200), nullable=True)
    authority_portal = Column(String(500), nullable=True)
    filing_guide = Column(Text, nullable=True)
    evidence_checklist = Column(Text, nullable=True)
    legal_rights = Column(Text, nullable=True)
    
    # Status tracking
    status = Column(String(20), default=ComplaintStatus.DRAFT)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    filed_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    evidence = relationship("Evidence", back_populates="complaint")


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(Integer, ForeignKey("complaints.id"))
    file_name = Column(String(255))
    file_type = Column(String(50))
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    complaint = relationship("Complaint", back_populates="evidence")
