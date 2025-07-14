from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# User schemas  
class UserRole(str, Enum):
    USER = "User"
    AGENT = "Agent" 
    ADMIN = "Admin"

class UserBase(BaseModel):
    email: EmailStr
    name: str
    role: UserRole = UserRole.USER
    department: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    department: Optional[str] = None
    phone: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None

class UserResponse(UserBase):
    id: str
    is_active: bool
    avatar_url: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}

# Ticket schemas
class TicketCategory(str, Enum):
    HARDWARE = "Hardware"
    SOFTWARE = "Software"
    NETWORK = "Network"
    SECURITY = "Security"
    ACCESS = "Access"
    EMAIL = "Email"
    OTHER = "Other"

class TicketPriority(str, Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"

class TicketStatus(str, Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    PENDING = "Pending"
    RESOLVED = "Resolved"
    CLOSED = "Closed"

class TicketBase(BaseModel):
    title: str
    description: str
    category: TicketCategory
    priority: TicketPriority = TicketPriority.MEDIUM

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if len(v.strip()) < 5:
            raise ValueError('Title must be at least 5 characters long')
        return v.strip()

    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Description must be at least 10 characters long')
        return v.strip()

class TicketCreate(TicketBase):
    tags: Optional[List[str]] = []
    attachments: Optional[List[str]] = []

class TicketUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None
    tags: Optional[List[str]] = None
    resolution_notes: Optional[str] = None
    customer_satisfaction: Optional[int] = None

    @field_validator('customer_satisfaction')
    @classmethod
    def validate_satisfaction(cls, v):
        if v is not None and (v < 1 or v > 5):
            raise ValueError('Customer satisfaction must be between 1 and 5')
        return v

class ClassificationResponse(BaseModel):
    id: str
    ticketId: str
    category: str
    confidence: float
    modelName: str
    modelVersion: str
    suggestedActions: List[str]
    keywordsIdentified: List[str]
    sentimentScore: Optional[float] = None
    urgencyScore: Optional[float] = None
    estimatedResolutionTime: Optional[float] = None
    processingTimeMs: Optional[float] = None
    createdAt: Optional[datetime] = None

    model_config = {"from_attributes": True}

class TicketResponse(TicketBase):
    id: str
    status: TicketStatus
    submittedBy: str
    assignedTo: Optional[str] = None
    submittedAt: Optional[datetime] = None
    assignedAt: Optional[datetime] = None
    resolvedAt: Optional[datetime] = None
    closedAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    tags: List[str]
    resolutionNotes: Optional[str] = None
    estimatedResolutionTime: Optional[int] = None
    actualResolutionTime: Optional[int] = None
    customerSatisfaction: Optional[int] = None
    attachments: List[str]
    isClassified: bool
    classificationConfidence: Optional[str] = None
    autoAssigned: bool
    isOverdue: bool
    timeToResolution: int
    classification: Optional[ClassificationResponse] = None

    model_config = {"from_attributes": True}

# Activity schemas
class ActivityResponse(BaseModel):
    id: str
    ticketId: str
    userId: str
    action: str
    description: str
    oldValue: Optional[str] = None
    newValue: Optional[str] = None
    user: Optional[str] = None
    timestamp: Optional[datetime] = None

    model_config = {"from_attributes": True}

# Dashboard schemas
class CategoryStats(BaseModel):
    category: str
    count: int
    percentage: float

class PriorityStats(BaseModel):
    priority: str
    count: int
    percentage: float

class DashboardStats(BaseModel):
    totalTickets: int
    openTickets: int
    resolvedTickets: int
    avgResolutionTime: float
    categoryDistribution: List[CategoryStats]
    priorityDistribution: List[PriorityStats]
    recentActivity: List[ActivityResponse]

# Generic response schemas
class ApiResponse(BaseModel):
    data: Any
    message: str = "Success"
    success: bool = True

class PaginatedResponse(BaseModel):
    data: List[Any]
    total: int
    page: int
    limit: int
    hasMore: bool

class ErrorResponse(BaseModel):
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = datetime.utcnow()

# Authentication schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    token: str
    user: UserResponse
    token_type: str = "bearer"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

# Filter schemas
class TicketFilters(BaseModel):
    category: Optional[TicketCategory] = None
    priority: Optional[TicketPriority] = None
    status: Optional[TicketStatus] = None
    assigned_to: Optional[str] = None
    submitted_by: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None

# File upload schemas
class FileUploadResponse(BaseModel):
    url: str
    filename: str
    size: int
    content_type: str
    upload_timestamp: datetime

# Classification validation schemas
class ClassificationValidation(BaseModel):
    is_correct: bool
    feedback: Optional[str] = None
    correct_category: Optional[TicketCategory] = None