from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
import uuid

from .database import Base


class ActivityType(enum.Enum):
    CREATED = "created"
    UPDATED = "updated"
    ASSIGNED = "assigned"
    UNASSIGNED = "unassigned"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    CATEGORY_CHANGED = "category_changed"
    CLASSIFIED = "classified"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"
    COMMENT_ADDED = "comment_added"
    ATTACHMENT_ADDED = "attachment_added"
    ATTACHMENT_REMOVED = "attachment_removed"


class Activity(Base):
    __tablename__ = "activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    
    # Activity details
    activity_type = Column(Enum(ActivityType), nullable=False)
    description = Column(Text, nullable=False)
    
    # Change tracking
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    
    # Additional metadata
    extra_data = Column(Text, nullable=True)  # JSON string for additional data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="activities")
    user = relationship("User", back_populates="activities")

    def __repr__(self):
        return f"<Activity {self.id}: {self.activity_type.value} on {self.ticket_id}>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticketId": self.ticket_id,
            "userId": self.user_id,
            "action": self.activity_type.value,
            "description": self.description,
            "oldValue": self.old_value,
            "newValue": self.new_value,
            "metadata": self.extra_data,
            "user": self.user.name if self.user else None,
            "timestamp": self.created_at.isoformat() if self.created_at else None,
        }