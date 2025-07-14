from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from ..models.database import get_db
from ..models.user import User, UserRole
from ..models.ticket import TicketCategory, TicketPriority, TicketStatus
from ..utils.auth import get_current_user
from ..utils.logging import get_logger
from ..services.search_service import SearchService
from .schemas import ApiResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("/tickets")
async def search_tickets(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    status: Optional[TicketStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search tickets with full-text search and filters."""
    logger.info(f"Searching tickets with query: '{q}' for user: {current_user.email}")
    
    search_service = SearchService(db)
    results = search_service.search_tickets(
        query=q,
        user=current_user,
        category=category,
        priority=priority,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=limit
    )
    
    return ApiResponse(
        data=results,
        message=f"Found {len(results)} tickets matching search criteria"
    )


@router.get("/users")
async def search_users(
    q: str = Query(..., min_length=1, description="Search query"),
    role: Optional[UserRole] = None,
    department: Optional[str] = None,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search users (agents and admins only)."""
    logger.info(f"Searching users with query: '{q}' for user: {current_user.email}")
    
    search_service = SearchService(db)
    results = search_service.search_users(
        query=q,
        requesting_user=current_user,
        role=role,
        department=department,
        limit=limit
    )
    
    return ApiResponse(
        data=results,
        message=f"Found {len(results)} users matching search criteria"
    )


@router.get("/suggestions")
async def get_search_suggestions(
    q: str = Query(..., min_length=2, description="Partial search query"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get search suggestions based on partial query."""
    logger.info(f"Getting search suggestions for query: '{q}'")
    
    search_service = SearchService(db)
    suggestions = search_service.get_search_suggestions(q, current_user)
    
    return ApiResponse(
        data=suggestions,
        message=f"Generated {len(suggestions)} search suggestions"
    )


@router.get("/popular")
async def get_popular_searches(
    limit: int = Query(10, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get popular search terms."""
    logger.info("Getting popular search terms")
    
    search_service = SearchService(db)
    popular_terms = search_service.get_popular_searches(current_user, limit)
    
    return ApiResponse(
        data=popular_terms,
        message=f"Retrieved {len(popular_terms)} popular search terms"
    )


@router.post("/advanced")
async def advanced_search(
    title: Optional[str] = None,
    description: Optional[str] = None,
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    status: Optional[TicketStatus] = None,
    submitted_by: Optional[str] = None,
    assigned_to: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    has_classification: Optional[bool] = None,
    classification_confidence_min: Optional[float] = Query(None, ge=0.0, le=1.0),
    customer_satisfaction_min: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Advanced search with multiple criteria."""
    logger.info(f"Performing advanced search for user: {current_user.email}")
    
    search_service = SearchService(db)
    results = search_service.advanced_search(
        user=current_user,
        title=title,
        description=description,
        category=category,
        priority=priority,
        status=status,
        submitted_by=submitted_by,
        assigned_to=assigned_to,
        date_from=date_from,
        date_to=date_to,
        has_classification=has_classification,
        classification_confidence_min=classification_confidence_min,
        customer_satisfaction_min=customer_satisfaction_min,
        limit=limit
    )
    
    return ApiResponse(
        data=results,
        message=f"Advanced search returned {len(results)} results"
    )


@router.get("/filters/options")
async def get_filter_options(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available filter options for search."""
    logger.info("Getting filter options")
    
    # Get available categories
    categories = [{"value": cat.value, "label": cat.value} for cat in TicketCategory]
    
    # Get available priorities
    priorities = [{"value": pri.value, "label": pri.value} for pri in TicketPriority]
    
    # Get available statuses
    statuses = [{"value": stat.value, "label": stat.value} for stat in TicketStatus]
    
    # Get available users for assignment (agents and admins only)
    users = []
    if current_user.role in [UserRole.AGENT, UserRole.ADMIN]:
        from ..models.user import User as UserModel
        user_list = db.query(UserModel).filter(
            UserModel.role.in_([UserRole.AGENT, UserRole.ADMIN])
        ).filter(UserModel.is_active == True).all()
        
        users = [
            {"value": user.id, "label": f"{user.name} ({user.email})"}
            for user in user_list
        ]
    
    # Get available departments
    departments = db.query(User.department).filter(
        User.department.isnot(None)
    ).distinct().all()
    
    department_options = [
        {"value": dept[0], "label": dept[0]}
        for dept in departments if dept[0]
    ]
    
    return ApiResponse(
        data={
            "categories": categories,
            "priorities": priorities,
            "statuses": statuses,
            "users": users,
            "departments": department_options
        },
        message="Filter options retrieved successfully"
    )


@router.get("/history")
async def get_search_history(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's search history (placeholder - would need separate table)."""
    logger.info(f"Getting search history for user: {current_user.email}")
    
    # This would typically be stored in a separate search_history table
    # For now, return empty history
    return ApiResponse(
        data=[],
        message="Search history retrieved successfully"
    )


@router.delete("/history")
async def clear_search_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Clear user's search history."""
    logger.info(f"Clearing search history for user: {current_user.email}")
    
    # This would typically clear entries from a search_history table
    # For now, just return success
    return ApiResponse(
        data={"cleared": True},
        message="Search history cleared successfully"
    )


@router.get("/export")
async def export_search_results(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[TicketCategory] = None,
    priority: Optional[TicketPriority] = None,
    status: Optional[TicketStatus] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    format: str = Query("csv", regex="^(csv|xlsx|json)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export search results to various formats."""
    logger.info(f"Exporting search results for query: '{q}' in format: {format}")
    
    search_service = SearchService(db)
    results = search_service.search_tickets(
        query=q,
        user=current_user,
        category=category,
        priority=priority,
        status=status,
        date_from=date_from,
        date_to=date_to,
        limit=1000  # Higher limit for export
    )
    
    # For now, just return the results as JSON
    # In a real implementation, you would generate the actual file
    return ApiResponse(
        data={
            "results": results,
            "format": format,
            "total_count": len(results),
            "export_url": f"/api/v1/search/download/{format}?q={q}"  # Placeholder
        },
        message=f"Search results prepared for export in {format} format"
    )