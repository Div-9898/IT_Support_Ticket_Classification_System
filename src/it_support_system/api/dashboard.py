from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..models.database import get_db
from ..models.user import User
from ..utils.auth import get_current_user, require_agent_or_admin
from ..utils.logging import get_logger
from ..services.dashboard_service import DashboardService
from .schemas import DashboardStats, ApiResponse

router = APIRouter()
logger = get_logger(__name__)


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics for the current user."""
    logger.info(f"Getting dashboard stats for user: {current_user.email}")
    
    dashboard_service = DashboardService(db)
    stats = dashboard_service.get_dashboard_stats(current_user)
    
    return DashboardStats(**stats)


@router.get("/performance/agent")
async def get_agent_performance(
    agent_id: Optional[str] = Query(None),
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get agent performance metrics."""
    logger.info(f"Getting agent performance for agent: {agent_id}")
    
    dashboard_service = DashboardService(db)
    
    # If no agent_id provided, get performance for current user if they're an agent
    if not agent_id:
        if current_user.role.value in ["Agent", "Admin"]:
            agent_id = current_user.id
        else:
            # Return performance for all agents if user is admin
            if current_user.role.value == "Admin":
                agent_id = None
            else:
                return {"error": "Agent ID required"}
    
    performance = dashboard_service.get_agent_performance(agent_id)
    
    return ApiResponse(
        data=performance,
        message="Agent performance retrieved successfully"
    )


@router.get("/classification/metrics")
async def get_classification_metrics(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get ML classification performance metrics."""
    logger.info("Getting classification metrics")
    
    dashboard_service = DashboardService(db)
    metrics = dashboard_service.get_classification_metrics()
    
    return ApiResponse(
        data=metrics,
        message="Classification metrics retrieved successfully"
    )


@router.get("/workload/distribution")
async def get_workload_distribution(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get workload distribution across agents."""
    logger.info("Getting workload distribution")
    
    dashboard_service = DashboardService(db)
    distribution = dashboard_service.get_workload_distribution()
    
    return ApiResponse(
        data=distribution,
        message="Workload distribution retrieved successfully"
    )


@router.get("/analytics/trends")
async def get_analytics_trends(
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics trends for the specified number of days."""
    logger.info(f"Getting analytics trends for {days} days")
    
    dashboard_service = DashboardService(db)
    trends = dashboard_service._get_trending_data(current_user, days)
    
    return ApiResponse(
        data=trends,
        message="Analytics trends retrieved successfully"
    )


@router.get("/analytics/category-performance")
async def get_category_performance(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get performance metrics by ticket category."""
    logger.info("Getting category performance analytics")
    
    dashboard_service = DashboardService(db)
    
    # Get category distribution
    category_dist = dashboard_service._get_category_distribution(current_user)
    
    # Get additional metrics for each category
    from ..models.ticket import Ticket, TicketCategory, TicketStatus
    from sqlalchemy import func, and_
    
    category_performance = []
    
    for category in TicketCategory:
        # Get tickets for this category
        category_tickets = db.query(Ticket).filter(Ticket.category == category)
        
        if current_user.role.value == "User":
            category_tickets = category_tickets.filter(Ticket.submitted_by == current_user.id)
        elif current_user.role.value == "Agent":
            from sqlalchemy import or_
            category_tickets = category_tickets.filter(
                or_(
                    Ticket.submitted_by == current_user.id,
                    Ticket.assigned_to == current_user.id
                )
            )
        
        tickets = category_tickets.all()
        
        if tickets:
            # Calculate metrics
            total_tickets = len(tickets)
            resolved_tickets = len([t for t in tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]])
            
            # Average resolution time
            resolved_with_time = [t for t in tickets if t.resolved_at and t.submitted_at]
            avg_resolution_time = 0.0
            if resolved_with_time:
                total_time = sum(
                    (t.resolved_at - t.submitted_at).total_seconds() / 3600
                    for t in resolved_with_time
                )
                avg_resolution_time = total_time / len(resolved_with_time)
            
            # Customer satisfaction
            satisfied_tickets = [t for t in tickets if t.customer_satisfaction]
            avg_satisfaction = 0.0
            if satisfied_tickets:
                avg_satisfaction = sum(t.customer_satisfaction for t in satisfied_tickets) / len(satisfied_tickets)
            
            category_performance.append({
                "category": category.value,
                "total_tickets": total_tickets,
                "resolved_tickets": resolved_tickets,
                "resolution_rate": (resolved_tickets / total_tickets * 100) if total_tickets > 0 else 0,
                "avg_resolution_time": avg_resolution_time,
                "avg_satisfaction": avg_satisfaction
            })
    
    return ApiResponse(
        data={"category_performance": category_performance},
        message="Category performance retrieved successfully"
    )


@router.get("/analytics/priority-analysis")
async def get_priority_analysis(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get analysis of ticket priorities and handling."""
    logger.info("Getting priority analysis")
    
    from ..models.ticket import Ticket, TicketPriority, TicketStatus
    from sqlalchemy import func, and_
    from datetime import datetime, timedelta
    
    priority_analysis = []
    
    for priority in TicketPriority:
        # Get tickets for this priority
        priority_tickets = db.query(Ticket).filter(Ticket.priority == priority)
        
        if current_user.role.value == "User":
            priority_tickets = priority_tickets.filter(Ticket.submitted_by == current_user.id)
        elif current_user.role.value == "Agent":
            from sqlalchemy import or_
            priority_tickets = priority_tickets.filter(
                or_(
                    Ticket.submitted_by == current_user.id,
                    Ticket.assigned_to == current_user.id
                )
            )
        
        tickets = priority_tickets.all()
        
        if tickets:
            total_tickets = len(tickets)
            overdue_tickets = len([t for t in tickets if t.is_overdue])
            
            # SLA compliance (based on priority)
            sla_thresholds = {
                TicketPriority.URGENT: 2,    # 2 hours
                TicketPriority.HIGH: 8,      # 8 hours
                TicketPriority.MEDIUM: 24,   # 24 hours
                TicketPriority.LOW: 72,      # 72 hours
            }
            
            sla_threshold = sla_thresholds.get(priority, 24)
            sla_compliant = 0
            
            for ticket in tickets:
                if ticket.resolved_at and ticket.submitted_at:
                    resolution_time = (ticket.resolved_at - ticket.submitted_at).total_seconds() / 3600
                    if resolution_time <= sla_threshold:
                        sla_compliant += 1
            
            priority_analysis.append({
                "priority": priority.value,
                "total_tickets": total_tickets,
                "overdue_tickets": overdue_tickets,
                "sla_threshold_hours": sla_threshold,
                "sla_compliant": sla_compliant,
                "sla_compliance_rate": (sla_compliant / total_tickets * 100) if total_tickets > 0 else 0
            })
    
    return ApiResponse(
        data={"priority_analysis": priority_analysis},
        message="Priority analysis retrieved successfully"
    )


@router.get("/analytics/time-analysis")
async def get_time_analysis(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get time-based analysis of ticket handling."""
    logger.info("Getting time analysis")
    
    from ..models.ticket import Ticket, TicketStatus
    from datetime import datetime, timedelta
    import calendar
    
    # Get tickets from the last 12 months
    twelve_months_ago = datetime.utcnow() - timedelta(days=365)
    
    tickets_query = db.query(Ticket).filter(Ticket.submitted_at >= twelve_months_ago)
    
    if current_user.role.value == "User":
        tickets_query = tickets_query.filter(Ticket.submitted_by == current_user.id)
    elif current_user.role.value == "Agent":
        from sqlalchemy import or_
        tickets_query = tickets_query.filter(
            or_(
                Ticket.submitted_by == current_user.id,
                Ticket.assigned_to == current_user.id
            )
        )
    
    tickets = tickets_query.all()
    
    # Monthly analysis
    monthly_data = {}
    for i in range(12):
        month_start = datetime.utcnow() - timedelta(days=30 * (i + 1))
        month_end = datetime.utcnow() - timedelta(days=30 * i)
        
        month_tickets = [t for t in tickets if month_start <= t.submitted_at <= month_end]
        month_resolved = [t for t in month_tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        
        monthly_data[month_start.strftime("%Y-%m")] = {
            "submitted": len(month_tickets),
            "resolved": len(month_resolved),
            "backlog": len(month_tickets) - len(month_resolved)
        }
    
    # Weekly analysis (last 8 weeks)
    weekly_data = {}
    for i in range(8):
        week_start = datetime.utcnow() - timedelta(days=7 * (i + 1))
        week_end = datetime.utcnow() - timedelta(days=7 * i)
        
        week_tickets = [t for t in tickets if week_start <= t.submitted_at <= week_end]
        week_resolved = [t for t in week_tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        
        weekly_data[week_start.strftime("%Y-W%U")] = {
            "submitted": len(week_tickets),
            "resolved": len(week_resolved)
        }
    
    # Daily analysis (last 30 days)
    daily_data = {}
    for i in range(30):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)
        
        day_tickets = [t for t in tickets if day_start <= t.submitted_at < day_end]
        day_resolved = [t for t in day_tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        
        daily_data[day.strftime("%Y-%m-%d")] = {
            "submitted": len(day_tickets),
            "resolved": len(day_resolved)
        }
    
    return ApiResponse(
        data={
            "monthly_data": monthly_data,
            "weekly_data": weekly_data,
            "daily_data": daily_data
        },
        message="Time analysis retrieved successfully"
    )


@router.get("/analytics/user-engagement")
async def get_user_engagement(
    current_user: User = Depends(require_agent_or_admin),
    db: Session = Depends(get_db)
):
    """Get user engagement analytics."""
    logger.info("Getting user engagement analytics")
    
    from ..models.ticket import Ticket
    from ..models.user import User, UserRole
    from ..models.activity import Activity
    from sqlalchemy import func, desc
    from datetime import datetime, timedelta
    
    # Get active users (submitted tickets in last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    active_users = db.query(User).join(Ticket, User.id == Ticket.submitted_by).filter(
        Ticket.submitted_at >= thirty_days_ago
    ).distinct().all()
    
    # Get user engagement metrics
    user_engagement = []
    for user in active_users:
        user_tickets = db.query(Ticket).filter(
            and_(
                Ticket.submitted_by == user.id,
                Ticket.submitted_at >= thirty_days_ago
            )
        ).count()
        
        user_activities = db.query(Activity).filter(
            and_(
                Activity.user_id == user.id,
                Activity.created_at >= thirty_days_ago
            )
        ).count()
        
        user_engagement.append({
            "user_id": user.id,
            "user_name": user.name,
            "user_role": user.role.value,
            "tickets_submitted": user_tickets,
            "activities": user_activities,
            "engagement_score": user_tickets * 2 + user_activities  # Simple scoring
        })
    
    # Sort by engagement score
    user_engagement.sort(key=lambda x: x["engagement_score"], reverse=True)
    
    # Get department engagement
    department_engagement = {}
    for user in active_users:
        dept = user.department or "Unknown"
        if dept not in department_engagement:
            department_engagement[dept] = {
                "users": 0,
                "tickets": 0,
                "activities": 0
            }
        
        department_engagement[dept]["users"] += 1
        department_engagement[dept]["tickets"] += db.query(Ticket).filter(
            and_(
                Ticket.submitted_by == user.id,
                Ticket.submitted_at >= thirty_days_ago
            )
        ).count()
        department_engagement[dept]["activities"] += db.query(Activity).filter(
            and_(
                Activity.user_id == user.id,
                Activity.created_at >= thirty_days_ago
            )
        ).count()
    
    return ApiResponse(
        data={
            "active_users_count": len(active_users),
            "user_engagement": user_engagement[:20],  # Top 20 users
            "department_engagement": department_engagement
        },
        message="User engagement analytics retrieved successfully"
    )