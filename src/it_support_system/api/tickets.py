from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional
from datetime import datetime

from ..models.database import get_db
from ..models.user import User
from ..models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from ..models.classification import Classification
from ..models.activity import Activity, ActivityType
from ..utils.auth import get_current_user, can_access_ticket, can_modify_ticket, can_resolve_ticket
from ..utils.exceptions import not_found_error, forbidden_error, validation_error
from ..utils.logging import get_logger
from ..services.ml_service import MLService
from .schemas import (
    TicketCreate, TicketUpdate, TicketResponse, TicketFilters,
    PaginatedResponse, ApiResponse, ClassificationValidation
)

router = APIRouter()
logger = get_logger(__name__)

# ML service will be imported from main
from .. import main

async def classify_ticket_background(ticket_id: str, db: Session):
    """Background task to classify a ticket."""
    try:
        # Get ticket
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            logger.error(f"Ticket not found for classification: {ticket_id}")
            return
        
        # Classify ticket
        classification_result = await main.ml_service.classify_ticket(ticket.title, ticket.description)
        
        # Create classification record
        classification = Classification(
            ticket_id=ticket_id,
            predicted_category=classification_result['predicted_category'],
            confidence_score=classification_result['confidence_score'],
            model_name=classification_result['model_name'],
            model_version=classification_result['model_version'],
            suggested_actions=classification_result['suggested_actions'],
            keywords_identified=classification_result['keywords_identified'],
            sentiment_score=classification_result.get('sentiment_score'),
            urgency_score=classification_result.get('urgency_score'),
            estimated_resolution_time=classification_result.get('estimated_resolution_time'),
            processing_time_ms=classification_result.get('processing_time_ms'),
            preprocessing_applied=classification_result.get('preprocessing_applied', [])
        )
        
        db.add(classification)
        
        # Update ticket
        ticket.is_classified = True
        ticket.classification_confidence = f"{classification_result['confidence_score']:.1%}"
        
        # Create activity
        activity = Activity(
            ticket_id=ticket_id,
            user_id="system",  # System user
            activity_type=ActivityType.CLASSIFIED,
            description=f"Ticket automatically classified as {classification_result['predicted_category']} with {classification_result['confidence_score']:.1%} confidence"
        )
        
        db.add(activity)
        db.commit()
        
        logger.info(f"Ticket {ticket_id} classified successfully")
        
    except Exception as e:
        logger.error(f"Failed to classify ticket {ticket_id}: {e}")
        db.rollback()


@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket_create: TicketCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new ticket."""
    logger.info(f"Creating new ticket: {ticket_create.title}")
    
    # Create ticket
    db_ticket = Ticket(
        title=ticket_create.title,
        description=ticket_create.description,
        category=ticket_create.category,
        priority=ticket_create.priority,
        submitted_by=current_user.id,
        tags=ticket_create.tags or [],
        attachments=ticket_create.attachments or []
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    
    # Create activity
    activity = Activity(
        ticket_id=db_ticket.id,
        user_id=current_user.id,
        activity_type=ActivityType.CREATED,
        description=f"Ticket created by {current_user.name}"
    )
    
    db.add(activity)
    db.commit()
    
    # Schedule classification
    if main.ml_service and main.ml_service.is_ready():
        background_tasks.add_task(classify_ticket_background, db_ticket.id, db)
    
    logger.info(f"Ticket created successfully: {db_ticket.id}")
    
    return TicketResponse.from_orm(db_ticket)


@router.get("/", response_model=PaginatedResponse)
async def get_tickets(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    filters: TicketFilters = Depends(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tickets with pagination and filtering."""
    logger.info(f"Getting tickets for user: {current_user.email}")
    
    # Build query
    query = db.query(Ticket)
    
    # Apply user-based filtering
    if current_user.role.value == "User":
        # Users can only see their own tickets
        query = query.filter(Ticket.submitted_by == current_user.id)
    
    # Apply filters
    if filters.category:
        query = query.filter(Ticket.category == filters.category)
    
    if filters.priority:
        query = query.filter(Ticket.priority == filters.priority)
    
    if filters.status:
        query = query.filter(Ticket.status == filters.status)
    
    if filters.assigned_to:
        query = query.filter(Ticket.assigned_to == filters.assigned_to)
    
    if filters.submitted_by:
        query = query.filter(Ticket.submitted_by == filters.submitted_by)
    
    if filters.date_from:
        query = query.filter(Ticket.submitted_at >= filters.date_from)
    
    if filters.date_to:
        query = query.filter(Ticket.submitted_at <= filters.date_to)
    
    if filters.search:
        search_term = f"%{filters.search}%"
        query = query.filter(
            or_(
                Ticket.title.ilike(search_term),
                Ticket.description.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    tickets = query.order_by(desc(Ticket.submitted_at)).offset((page - 1) * limit).limit(limit).all()
    
    # Convert to response format
    ticket_responses = []
    for ticket in tickets:
        ticket_dict = ticket.to_dict()
        ticket_responses.append(ticket_dict)
    
    return PaginatedResponse(
        data=ticket_responses,
        total=total,
        page=page,
        limit=limit,
        hasMore=total > page * limit
    )


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific ticket."""
    logger.info(f"Getting ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check access permission
    if not can_access_ticket(current_user, ticket):
        logger.warning(f"Access denied to ticket {ticket_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    return TicketResponse.from_orm(ticket)


@router.put("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: str,
    ticket_update: TicketUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a ticket."""
    logger.info(f"Updating ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check modify permission
    if not can_modify_ticket(current_user, ticket):
        logger.warning(f"Modify denied for ticket {ticket_id} by user {current_user.email}")
        raise forbidden_error("Modification not allowed")
    
    # Store old values for activity tracking
    old_values = {}
    changes = []
    
    # Update fields
    update_data = ticket_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(ticket, field):
            old_value = getattr(ticket, field)
            if old_value != value:
                old_values[field] = old_value
                setattr(ticket, field, value)
                changes.append(field)
    
    # Handle status changes
    if 'status' in changes:
        if ticket.status == TicketStatus.RESOLVED:
            ticket.resolved_at = datetime.utcnow()
        elif ticket.status == TicketStatus.CLOSED:
            ticket.closed_at = datetime.utcnow()
    
    # Handle assignment changes
    if 'assigned_to' in changes:
        ticket.assigned_at = datetime.utcnow() if ticket.assigned_to else None
    
    db.commit()
    
    # Create activities for changes
    for field in changes:
        activity_type = ActivityType.UPDATED
        if field == 'status':
            activity_type = ActivityType.STATUS_CHANGED
        elif field == 'priority':
            activity_type = ActivityType.PRIORITY_CHANGED
        elif field == 'assigned_to':
            activity_type = ActivityType.ASSIGNED if ticket.assigned_to else ActivityType.UNASSIGNED
        
        activity = Activity(
            ticket_id=ticket_id,
            user_id=current_user.id,
            activity_type=activity_type,
            description=f"{field.replace('_', ' ').title()} changed from {old_values.get(field)} to {update_data[field]}",
            old_value=str(old_values.get(field)),
            new_value=str(update_data[field])
        )
        
        db.add(activity)
    
    db.commit()
    
    logger.info(f"Ticket updated successfully: {ticket_id}")
    
    return TicketResponse.from_orm(ticket)


@router.delete("/{ticket_id}")
async def delete_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a ticket."""
    logger.info(f"Deleting ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Only admins can delete tickets
    if current_user.role.value != "Admin":
        logger.warning(f"Delete denied for ticket {ticket_id} by user {current_user.email}")
        raise forbidden_error("Only admins can delete tickets")
    
    # Delete ticket (activities will be cascade deleted)
    db.delete(ticket)
    db.commit()
    
    logger.info(f"Ticket deleted successfully: {ticket_id}")
    
    return {"message": "Ticket deleted successfully"}


@router.post("/{ticket_id}/classify", response_model=ApiResponse)
async def classify_ticket(
    ticket_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Manually trigger ticket classification."""
    logger.info(f"Manual classification requested for ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check access permission
    if not can_access_ticket(current_user, ticket):
        logger.warning(f"Access denied to ticket {ticket_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    # Check if ML service is ready
    if not main.ml_service or not main.ml_service.is_ready():
        logger.warning("ML service not ready")
        raise HTTPException(
            status_code=503,
            detail="ML classification service is not available"
        )
    
    # Schedule classification
    background_tasks.add_task(classify_ticket_background, ticket_id, db)
    
    return ApiResponse(
        data={"ticket_id": ticket_id},
        message="Classification queued successfully"
    )


@router.get("/{ticket_id}/activities", response_model=List[dict])
async def get_ticket_activities(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get activities for a ticket."""
    logger.info(f"Getting activities for ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check access permission
    if not can_access_ticket(current_user, ticket):
        logger.warning(f"Access denied to ticket {ticket_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    # Get activities
    activities = db.query(Activity).filter(Activity.ticket_id == ticket_id).order_by(desc(Activity.created_at)).all()
    
    return [activity.to_dict() for activity in activities]


@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assignee_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign a ticket to a user."""
    logger.info(f"Assigning ticket {ticket_id} to user {assignee_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check if user can assign tickets
    if current_user.role.value not in ["Agent", "Admin"]:
        logger.warning(f"Assign denied for ticket {ticket_id} by user {current_user.email}")
        raise forbidden_error("Only agents and admins can assign tickets")
    
    # Get assignee
    assignee = db.query(User).filter(User.id == assignee_id).first()
    if not assignee:
        logger.warning(f"Assignee not found: {assignee_id}")
        raise not_found_error("Assignee not found")
    
    # Check if assignee is an agent or admin
    if assignee.role.value not in ["Agent", "Admin"]:
        logger.warning(f"Invalid assignee role: {assignee.role.value}")
        raise validation_error("Can only assign to agents or admins")
    
    # Update ticket
    old_assignee = ticket.assigned_to
    ticket.assigned_to = assignee_id
    ticket.assigned_at = datetime.utcnow()
    
    # Update status if needed
    if ticket.status == TicketStatus.OPEN:
        ticket.status = TicketStatus.IN_PROGRESS
    
    db.commit()
    
    # Create activity
    activity = Activity(
        ticket_id=ticket_id,
        user_id=current_user.id,
        activity_type=ActivityType.ASSIGNED,
        description=f"Ticket assigned to {assignee.name}",
        old_value=old_assignee,
        new_value=assignee_id
    )
    
    db.add(activity)
    db.commit()
    
    logger.info(f"Ticket {ticket_id} assigned to {assignee.name}")
    
    return {"message": f"Ticket assigned to {assignee.name}"}


@router.post("/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution_notes: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Resolve a ticket."""
    logger.info(f"Resolving ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check resolve permission
    if not can_resolve_ticket(current_user, ticket):
        logger.warning(f"Resolve denied for ticket {ticket_id} by user {current_user.email}")
        raise forbidden_error("Cannot resolve this ticket")
    
    # Update ticket
    ticket.status = TicketStatus.RESOLVED
    ticket.resolved_at = datetime.utcnow()
    ticket.resolution_notes = resolution_notes
    
    # Calculate resolution time
    if ticket.submitted_at:
        ticket.actual_resolution_time = int((ticket.resolved_at - ticket.submitted_at).total_seconds() / 60)
    
    db.commit()
    
    # Create activity
    activity = Activity(
        ticket_id=ticket_id,
        user_id=current_user.id,
        activity_type=ActivityType.RESOLVED,
        description=f"Ticket resolved by {current_user.name}",
        new_value=resolution_notes
    )
    
    db.add(activity)
    db.commit()
    
    logger.info(f"Ticket resolved successfully: {ticket_id}")
    
    return {"message": "Ticket resolved successfully"}


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Close a ticket."""
    logger.info(f"Closing ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Only resolved tickets can be closed
    if ticket.status != TicketStatus.RESOLVED:
        logger.warning(f"Cannot close non-resolved ticket: {ticket_id}")
        raise validation_error("Only resolved tickets can be closed")
    
    # Check permission
    if not can_access_ticket(current_user, ticket):
        logger.warning(f"Access denied to ticket {ticket_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    # Update ticket
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.utcnow()
    
    db.commit()
    
    # Create activity
    activity = Activity(
        ticket_id=ticket_id,
        user_id=current_user.id,
        activity_type=ActivityType.CLOSED,
        description=f"Ticket closed by {current_user.name}"
    )
    
    db.add(activity)
    db.commit()
    
    logger.info(f"Ticket closed successfully: {ticket_id}")
    
    return {"message": "Ticket closed successfully"}


@router.post("/{ticket_id}/reopen")
async def reopen_ticket(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reopen a ticket."""
    logger.info(f"Reopening ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check permission
    if not can_access_ticket(current_user, ticket):
        logger.warning(f"Access denied to ticket {ticket_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    # Update ticket
    old_status = ticket.status
    ticket.status = TicketStatus.OPEN
    ticket.resolved_at = None
    ticket.closed_at = None
    
    db.commit()
    
    # Create activity
    activity = Activity(
        ticket_id=ticket_id,
        user_id=current_user.id,
        activity_type=ActivityType.REOPENED,
        description=f"Ticket reopened by {current_user.name}",
        old_value=old_status.value,
        new_value=TicketStatus.OPEN.value
    )
    
    db.add(activity)
    db.commit()
    
    logger.info(f"Ticket reopened successfully: {ticket_id}")
    
    return {"message": "Ticket reopened successfully"}


@router.post("/{ticket_id}/validate-classification")
async def validate_classification(
    ticket_id: str,
    validation: ClassificationValidation,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate or correct a classification."""
    logger.info(f"Validating classification for ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check permission (only agents and admins can validate)
    if current_user.role.value not in ["Agent", "Admin"]:
        logger.warning(f"Validation denied for ticket {ticket_id} by user {current_user.email}")
        raise forbidden_error("Only agents and admins can validate classifications")
    
    # Get classification
    classification = db.query(Classification).filter(Classification.ticket_id == ticket_id).first()
    if not classification:
        logger.warning(f"Classification not found for ticket: {ticket_id}")
        raise not_found_error("Classification not found")
    
    # Update classification
    classification.is_validated = "correct" if validation.is_correct else "incorrect"
    classification.validation_feedback = validation.feedback
    classification.validated_by = current_user.id
    classification.validated_at = datetime.utcnow()
    
    # If incorrect and correct category provided, update
    if not validation.is_correct and validation.correct_category:
        classification.is_validated = "partial"
        # Could also update the ticket category here
    
    db.commit()
    
    logger.info(f"Classification validated for ticket: {ticket_id}")
    
    return {"message": "Classification validation saved"}


@router.get("/{ticket_id}/classification", response_model=dict)
async def get_ticket_classification(
    ticket_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get classification details for a ticket."""
    logger.info(f"Getting classification for ticket: {ticket_id}")
    
    # Get ticket
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        logger.warning(f"Ticket not found: {ticket_id}")
        raise not_found_error("Ticket not found")
    
    # Check access permission
    if not can_access_ticket(current_user, ticket):
        logger.warning(f"Access denied to ticket {ticket_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    # Get classification
    classification = db.query(Classification).filter(Classification.ticket_id == ticket_id).first()
    if not classification:
        logger.warning(f"Classification not found for ticket: {ticket_id}")
        raise not_found_error("Classification not found")
    
    return classification.to_dict()


from pydantic import BaseModel

class TextClassificationRequest(BaseModel):
    title: str
    description: str

@router.post("/classify-text")
async def classify_text(
    request: TextClassificationRequest,
    current_user: User = Depends(get_current_user),
):
    """Classify text directly without creating a ticket."""
    logger.info(f"Text classification requested by user: {current_user.email}")
    
    # Check if ML service is ready
    if not main.ml_service or not main.ml_service.is_ready():
        logger.warning("ML service not ready")
        raise HTTPException(
            status_code=503,
            detail="ML classification service is not available"
        )
    
    try:
        # Classify the text
        classification_result = await main.ml_service.classify_ticket(request.title, request.description)
        
        logger.info(f"Text classified successfully for user: {current_user.email}")
        
        return classification_result
        
    except Exception as e:
        logger.error(f"Text classification failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )