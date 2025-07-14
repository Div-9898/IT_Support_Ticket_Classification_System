from sqlalchemy import Column, String, DateTime, Float, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from .database import Base


class Classification(Base):
    __tablename__ = "classifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    ticket_id = Column(String, ForeignKey("tickets.id"), nullable=False, unique=True)
    
    # Classification results
    predicted_category = Column(String(50), nullable=False)
    confidence_score = Column(Float, nullable=False)
    
    # Model information
    model_name = Column(String(100), nullable=False)
    model_version = Column(String(50), nullable=False)
    
    # Suggested actions and metadata
    suggested_actions = Column(JSON, nullable=True, default=list)
    keywords_identified = Column(JSON, nullable=True, default=list)
    sentiment_score = Column(Float, nullable=True)
    urgency_score = Column(Float, nullable=True)
    
    # Estimated resolution time in minutes
    estimated_resolution_time = Column(Float, nullable=True)
    
    # Processing metadata
    processing_time_ms = Column(Float, nullable=True)
    preprocessing_applied = Column(JSON, nullable=True, default=list)
    
    # Validation and feedback
    is_validated = Column(String(10), nullable=True)  # 'correct', 'incorrect', 'partial'
    validation_feedback = Column(Text, nullable=True)
    validated_by = Column(String, ForeignKey("users.id"), nullable=True)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="classification")
    validator = relationship("User", foreign_keys=[validated_by])

    def __repr__(self):
        return f"<Classification {self.id}: {self.predicted_category} ({self.confidence_score:.2f})>"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "ticketId": self.ticket_id,
            "category": self.predicted_category,
            "confidence": self.confidence_score,
            "modelName": self.model_name,
            "modelVersion": self.model_version,
            "suggestedActions": self.suggested_actions or [],
            "keywordsIdentified": self.keywords_identified or [],
            "sentimentScore": self.sentiment_score,
            "urgencyScore": self.urgency_score,
            "estimatedResolutionTime": self.estimated_resolution_time,
            "processingTimeMs": self.processing_time_ms,
            "preprocessingApplied": self.preprocessing_applied or [],
            "isValidated": self.is_validated,
            "validationFeedback": self.validation_feedback,
            "validatedBy": self.validated_by,
            "validatedAt": self.validated_at.isoformat() if self.validated_at else None,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }