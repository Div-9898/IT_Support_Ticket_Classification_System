from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional

from ..models.database import get_db
from ..models.user import User, UserRole
from ..utils.auth import get_current_user, require_admin, require_agent_or_admin, auth_service
from ..utils.exceptions import not_found_error, forbidden_error, conflict_error
from ..utils.logging import get_logger
from .schemas import UserCreate, UserUpdate, UserResponse, PaginatedResponse, ApiResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("/", response_model=PaginatedResponse)
async def get_users(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    role: Optional[UserRole] = None,
    department: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get users with pagination and filtering."""
    logger.info(f"Getting users for user: {current_user.email}")
    
    # Build query
    query = db.query(User)
    
    # Apply filters
    if role:
        query = query.filter(User.role == role)
    
    if department:
        query = query.filter(User.department == department)
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                User.name.ilike(search_term),
                User.email.ilike(search_term),
                User.department.ilike(search_term)
            )
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.order_by(User.name).offset((page - 1) * limit).limit(limit).all()
    
    # Convert to response format
    user_responses = [UserResponse.from_orm(user) for user in users]
    
    return PaginatedResponse(
        data=user_responses,
        total=total,
        page=page,
        limit=limit,
        hasMore=total > page * limit
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return UserResponse.from_orm(current_user)


@router.put("/me", response_model=UserResponse)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user profile."""
    logger.info(f"Updating profile for user: {current_user.email}")
    
    # Update allowed fields
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(current_user, field):
            setattr(current_user, field, value)
    
    db.commit()
    
    logger.info(f"Profile updated for user: {current_user.email}")
    
    return UserResponse.from_orm(current_user)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get a specific user."""
    logger.info(f"Getting user: {user_id}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    return UserResponse.from_orm(user)


@router.post("/", response_model=UserResponse)
async def create_user(
    user_create: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    logger.info(f"Creating user: {user_create.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        logger.warning(f"User already exists: {user_create.email}")
        raise conflict_error("User with this email already exists")
    
    # Create user
    hashed_password = auth_service.get_password_hash(user_create.password)
    db_user = User(
        email=user_create.email,
        name=user_create.name,
        hashed_password=hashed_password,
        role=user_create.role,
        department=user_create.department,
        phone=user_create.phone,
        bio=user_create.bio,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User created successfully: {db_user.email}")
    
    return UserResponse.from_orm(db_user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Update a user (admin only)."""
    logger.info(f"Updating user: {user_id}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Update fields
    update_data = user_update.dict(exclude_unset=True)
    
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    
    logger.info(f"User updated successfully: {user_id}")
    
    return UserResponse.from_orm(user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Delete a user (admin only)."""
    logger.info(f"Deleting user: {user_id}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Cannot delete self
    if user.id == current_user.id:
        logger.warning(f"User attempted to delete themselves: {user_id}")
        raise forbidden_error("Cannot delete yourself")
    
    # Cannot delete the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(User.role == UserRole.ADMIN).count()
        if admin_count <= 1:
            logger.warning(f"Attempt to delete last admin: {user_id}")
            raise forbidden_error("Cannot delete the last admin")
    
    # Soft delete - just deactivate
    user.is_active = False
    db.commit()
    
    logger.info(f"User deactivated successfully: {user_id}")
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Activate a user (admin only)."""
    logger.info(f"Activating user: {user_id}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Activate user
    user.is_active = True
    db.commit()
    
    logger.info(f"User activated successfully: {user_id}")
    
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Deactivate a user (admin only)."""
    logger.info(f"Deactivating user: {user_id}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Cannot deactivate self
    if user.id == current_user.id:
        logger.warning(f"User attempted to deactivate themselves: {user_id}")
        raise forbidden_error("Cannot deactivate yourself")
    
    # Cannot deactivate the last admin
    if user.role == UserRole.ADMIN:
        admin_count = db.query(User).filter(
            and_(User.role == UserRole.ADMIN, User.is_active == True)
        ).count()
        if admin_count <= 1:
            logger.warning(f"Attempt to deactivate last admin: {user_id}")
            raise forbidden_error("Cannot deactivate the last admin")
    
    # Deactivate user
    user.is_active = False
    db.commit()
    
    logger.info(f"User deactivated successfully: {user_id}")
    
    return {"message": "User deactivated successfully"}


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: str,
    new_password: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Reset user password (admin only)."""
    logger.info(f"Resetting password for user: {user_id}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Reset password
    user.hashed_password = auth_service.get_password_hash(new_password)
    db.commit()
    
    logger.info(f"Password reset successfully for user: {user_id}")
    
    return {"message": "Password reset successfully"}


@router.post("/{user_id}/change-role")
async def change_user_role(
    user_id: str,
    new_role: UserRole,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Change user role (admin only)."""
    logger.info(f"Changing role for user: {user_id} to {new_role}")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Cannot change role of the last admin
    if user.role == UserRole.ADMIN and new_role != UserRole.ADMIN:
        admin_count = db.query(User).filter(
            and_(User.role == UserRole.ADMIN, User.is_active == True)
        ).count()
        if admin_count <= 1:
            logger.warning(f"Attempt to change role of last admin: {user_id}")
            raise forbidden_error("Cannot change role of the last admin")
    
    # Change role
    old_role = user.role
    user.role = new_role
    db.commit()
    
    logger.info(f"Role changed successfully for user: {user_id} from {old_role} to {new_role}")
    
    return {"message": f"Role changed from {old_role.value} to {new_role.value}"}


@router.get("/stats/summary")
async def get_user_stats(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get user statistics."""
    logger.info("Getting user statistics")
    
    # Get user counts by role
    role_stats = {}
    for role in UserRole:
        count = db.query(User).filter(
            and_(User.role == role, User.is_active == True)
        ).count()
        role_stats[role.value] = count
    
    # Get total users
    total_users = db.query(User).filter(User.is_active == True).count()
    inactive_users = db.query(User).filter(User.is_active == False).count()
    
    # Get department distribution
    department_stats = {}
    departments = db.query(User.department).filter(
        and_(User.department.isnot(None), User.is_active == True)
    ).distinct().all()
    
    for dept in departments:
        if dept[0]:  # Skip None values
            count = db.query(User).filter(
                and_(User.department == dept[0], User.is_active == True)
            ).count()
            department_stats[dept[0]] = count
    
    return {
        "total_users": total_users,
        "inactive_users": inactive_users,
        "role_distribution": role_stats,
        "department_distribution": department_stats
    }


@router.get("/{user_id}/activity-summary")
async def get_user_activity_summary(
    user_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user activity summary."""
    logger.info(f"Getting activity summary for user: {user_id}")
    
    # Check permission
    if current_user.id != user_id and current_user.role.value not in ["Agent", "Admin"]:
        logger.warning(f"Access denied to user activity {user_id} for user {current_user.email}")
        raise forbidden_error("Access denied")
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User not found: {user_id}")
        raise not_found_error("User not found")
    
    # Get ticket counts
    from ..models.ticket import Ticket, TicketStatus
    
    submitted_tickets = db.query(Ticket).filter(Ticket.submitted_by == user_id).count()
    assigned_tickets = db.query(Ticket).filter(Ticket.assigned_to == user_id).count()
    resolved_tickets = db.query(Ticket).filter(
        and_(Ticket.assigned_to == user_id, Ticket.status == TicketStatus.RESOLVED)
    ).count()
    
    # Get recent activity
    from ..models.activity import Activity
    recent_activities = db.query(Activity).filter(
        Activity.user_id == user_id
    ).order_by(desc(Activity.created_at)).limit(10).all()
    
    return {
        "user_id": user_id,
        "submitted_tickets": submitted_tickets,
        "assigned_tickets": assigned_tickets,
        "resolved_tickets": resolved_tickets,
        "recent_activities": [activity.to_dict() for activity in recent_activities]
    }


@router.get("/agents/available")
async def get_available_agents(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get available agents for ticket assignment."""
    logger.info("Getting available agents")
    
    # Get all active agents and admins
    agents = db.query(User).filter(
        and_(
            User.role.in_([UserRole.AGENT, UserRole.ADMIN]),
            User.is_active == True
        )
    ).order_by(User.name).all()
    
    # Get workload for each agent
    from ..models.ticket import Ticket, TicketStatus
    
    agent_workloads = []
    for agent in agents:
        open_tickets = db.query(Ticket).filter(
            and_(
                Ticket.assigned_to == agent.id,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING])
            )
        ).count()
        
        agent_workloads.append({
            "id": agent.id,
            "name": agent.name,
            "email": agent.email,
            "role": agent.role.value,
            "department": agent.department,
            "open_tickets": open_tickets
        })
    
    # Sort by workload (agents with fewer tickets first)
    agent_workloads.sort(key=lambda x: x["open_tickets"])
    
    return agent_workloads