from sqlalchemy import Column, String, DateTime, Enum, Text, ForeignKey, Integer, JSON, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
import uuid

from .database import Base


class TicketCategory(enum.Enum):
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    SECURITY = "Security"
    ACCESS = "Access"
    EMAIL = "Email"
    OTHER = "Other"


class TicketPriority(enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class TicketStatus(enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    RESOLVED = "Resolved"
    CLOSED = "Closed"


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(Enum(TicketCategory), nullable=False)
    priority = Column(Enum(TicketPriority), nullable=False, default=TicketPriority.MEDIUM)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.OPEN)
    
    # User relationships
    submitted_by = Column(String, ForeignKey("users.id"), nullable=False)
    assigned_to = Column(String, ForeignKey("users.id"), nullable=True)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Additional fields
    tags = Column(JSON, nullable=True, default=list)
    resolution_notes = Column(Text, nullable=True)
    estimated_resolution_time = Column(Integer, nullable=True)  # in minutes
    actual_resolution_time = Column(Integer, nullable=True)  # in minutes
    customer_satisfaction = Column(Integer, nullable=True)  # 1-5 scale
    attachments = Column(JSON, nullable=True, default=list)
    
    # AI/ML fields
    is_classified = Column(Boolean, default=False)
    classification_confidence = Column(String(10), nullable=True)  # stored as percentage string
    auto_assigned = Column(Boolean, default=False)
    
    # Relationships
    submitter = relationship("User", foreign_keys=[submitted_by], back_populates="submitted_tickets")
    assignee = relationship("User", foreign_keys=[assigned_to], back_populates="assigned_tickets")
    classification = relationship("Classification", back_populates="ticket", uselist=False)
    activities = relationship("Activity", back_populates="ticket", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ticket {self.id}: {self.title[:50]}>"

    @property
    def is_overdue(self) -> bool:
        """Check if ticket is overdue based on priority and creation time."""
        if self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return False
        
        now = datetime.utcnow()
        hours_since_creation = (now - self.submitted_at.replace(tzinfo=None)).total_seconds() / 3600
        
        priority_thresholds = {
            TicketPriority.URGENT: 2,    # 2 hours
            TicketPriority.HIGH: 8,      # 8 hours
            TicketPriority.MEDIUM: 24,   # 24 hours
            TicketPriority.LOW: 72,      # 72 hours
        }
        
        return hours_since_creation > priority_thresholds.get(self.priority, 24)

    @property
    def time_to_resolution(self) -> int:
        """Calculate time to resolution in minutes."""
        if self.resolved_at and self.submitted_at:
            return int((self.resolved_at - self.submitted_at).total_seconds() / 60)
        return 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "priority": self.priority.value,
            "status": self.status.value,
            "submittedBy": self.submitted_by,
            "assignedTo": self.assigned_to,
            "submittedAt": self.submitted_at.isoformat() if self.submitted_at else None,
            "assignedAt": self.assigned_at.isoformat() if self.assigned_at else None,
            "resolvedAt": self.resolved_at.isoformat() if self.resolved_at else None,
            "closedAt": self.closed_at.isoformat() if self.closed_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
            "tags": self.tags or [],
            "resolutionNotes": self.resolution_notes,
            "estimatedResolutionTime": self.estimated_resolution_time,
            "actualResolutionTime": self.actual_resolution_time,
            "customerSatisfaction": self.customer_satisfaction,
            "attachments": self.attachments or [],
            "isClassified": self.is_classified,
            "classificationConfidence": self.classification_confidence,
            "autoAssigned": self.auto_assigned,
            "isOverdue": self.is_overdue,
            "timeToResolution": self.time_to_resolution,
            "classification": self.classification.to_dict() if self.classification else None,
        }