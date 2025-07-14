from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

from ..models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from ..models.user import User, UserRole
from ..models.activity import Activity
from ..models.classification import Classification
from ..utils.logging import get_logger

logger = get_logger(__name__)


class DashboardService:
    """Service for generating dashboard analytics and statistics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_dashboard_stats(self, user: User) -> Dict:
        """Get comprehensive dashboard statistics."""
        logger.info(f"Generating dashboard stats for user: {user.email}")
        
        # Get basic ticket statistics
        total_tickets = self._get_total_tickets(user)
        open_tickets = self._get_open_tickets(user)
        resolved_tickets = self._get_resolved_tickets(user)
        avg_resolution_time = self._get_avg_resolution_time(user)
        
        # Get distribution statistics
        category_distribution = self._get_category_distribution(user)
        priority_distribution = self._get_priority_distribution(user)
        status_distribution = self._get_status_distribution(user)
        
        # Get recent activity
        recent_activity = self._get_recent_activity(user)
        
        # Get performance metrics
        performance_metrics = self._get_performance_metrics(user)
        
        # Get trending data
        trending_data = self._get_trending_data(user)
        
        return {
            "totalTickets": total_tickets,
            "openTickets": open_tickets,
            "resolvedTickets": resolved_tickets,
            "avgResolutionTime": avg_resolution_time,
            "categoryDistribution": category_distribution,
            "priorityDistribution": priority_distribution,
            "statusDistribution": status_distribution,
            "recentActivity": recent_activity,
            "performanceMetrics": performance_metrics,
            "trendingData": trending_data
        }
    
    def _get_total_tickets(self, user: User) -> int:
        """Get total number of tickets based on user role."""
        query = self.db.query(Ticket)
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        # Admin sees all tickets
        
        return query.count()
    
    def _get_open_tickets(self, user: User) -> int:
        """Get number of open tickets."""
        query = self.db.query(Ticket).filter(
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING])
        )
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        return query.count()
    
    def _get_resolved_tickets(self, user: User) -> int:
        """Get number of resolved tickets."""
        query = self.db.query(Ticket).filter(
            Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED])
        )
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        return query.count()
    
    def _get_avg_resolution_time(self, user: User) -> float:
        """Get average resolution time in hours."""
        query = self.db.query(Ticket).filter(
            and_(
                Ticket.resolved_at.isnot(None),
                Ticket.submitted_at.isnot(None)
            )
        )
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        tickets = query.all()
        
        if not tickets:
            return 0.0
        
        total_time = sum(
            (ticket.resolved_at - ticket.submitted_at).total_seconds() / 3600
            for ticket in tickets
        )
        
        return total_time / len(tickets)
    
    def _get_category_distribution(self, user: User) -> List[Dict]:
        """Get ticket distribution by category."""
        query = self.db.query(
            Ticket.category,
            func.count(Ticket.id).label('count')
        )
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        results = query.group_by(Ticket.category).all()
        total = sum(result.count for result in results)
        
        distribution = []
        for result in results:
            distribution.append({
                "category": result.category.value,
                "count": result.count,
                "percentage": (result.count / total * 100) if total > 0 else 0
            })
        
        return distribution
    
    def _get_priority_distribution(self, user: User) -> List[Dict]:
        """Get ticket distribution by priority."""
        query = self.db.query(
            Ticket.priority,
            func.count(Ticket.id).label('count')
        )
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        results = query.group_by(Ticket.priority).all()
        total = sum(result.count for result in results)
        
        distribution = []
        for result in results:
            distribution.append({
                "priority": result.priority.value,
                "count": result.count,
                "percentage": (result.count / total * 100) if total > 0 else 0
            })
        
        return distribution
    
    def _get_status_distribution(self, user: User) -> List[Dict]:
        """Get ticket distribution by status."""
        query = self.db.query(
            Ticket.status,
            func.count(Ticket.id).label('count')
        )
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        results = query.group_by(Ticket.status).all()
        total = sum(result.count for result in results)
        
        distribution = []
        for result in results:
            distribution.append({
                "status": result.status.value,
                "count": result.count,
                "percentage": (result.count / total * 100) if total > 0 else 0
            })
        
        return distribution
    
    def _get_recent_activity(self, user: User, limit: int = 10) -> List[Dict]:
        """Get recent activity."""
        query = self.db.query(Activity).join(Ticket, Activity.ticket_id == Ticket.id)
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        activities = query.order_by(desc(Activity.created_at)).limit(limit).all()
        
        return [activity.to_dict() for activity in activities]
    
    def _get_performance_metrics(self, user: User) -> Dict:
        """Get performance metrics."""
        # Get metrics for the last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        
        query = self.db.query(Ticket).filter(Ticket.submitted_at >= thirty_days_ago)
        
        if user.role == UserRole.USER:
            query = query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            query = query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        tickets = query.all()
        
        if not tickets:
            return {
                "totalTicketsLast30Days": 0,
                "resolvedTicketsLast30Days": 0,
                "avgResponseTime": 0.0,
                "customerSatisfactionAvg": 0.0,
                "overdueTickets": 0
            }
        
        resolved_tickets = [t for t in tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        
        # Calculate average response time (from creation to assignment)
        assigned_tickets = [t for t in tickets if t.assigned_at]
        avg_response_time = 0.0
        if assigned_tickets:
            total_response_time = sum(
                (t.assigned_at - t.submitted_at).total_seconds() / 3600
                for t in assigned_tickets
            )
            avg_response_time = total_response_time / len(assigned_tickets)
        
        # Calculate customer satisfaction
        satisfied_tickets = [t for t in tickets if t.customer_satisfaction]
        customer_satisfaction = 0.0
        if satisfied_tickets:
            customer_satisfaction = sum(t.customer_satisfaction for t in satisfied_tickets) / len(satisfied_tickets)
        
        # Count overdue tickets
        overdue_tickets = sum(1 for t in tickets if t.is_overdue)
        
        return {
            "totalTicketsLast30Days": len(tickets),
            "resolvedTicketsLast30Days": len(resolved_tickets),
            "avgResponseTime": avg_response_time,
            "customerSatisfactionAvg": customer_satisfaction,
            "overdueTickets": overdue_tickets
        }
    
    def _get_trending_data(self, user: User, days: int = 30) -> Dict:
        """Get trending data for the last N days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily ticket counts
        daily_tickets = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            query = self.db.query(Ticket).filter(
                and_(
                    Ticket.submitted_at >= date,
                    Ticket.submitted_at < next_date
                )
            )
            
            if user.role == UserRole.USER:
                query = query.filter(Ticket.submitted_by == user.id)
            elif user.role == UserRole.AGENT:
                query = query.filter(
                    or_(
                        Ticket.submitted_by == user.id,
                        Ticket.assigned_to == user.id
                    )
                )
            
            count = query.count()
            daily_tickets.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
        # Get resolution trends
        daily_resolutions = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            next_date = date + timedelta(days=1)
            
            query = self.db.query(Ticket).filter(
                and_(
                    Ticket.resolved_at >= date,
                    Ticket.resolved_at < next_date
                )
            )
            
            if user.role == UserRole.USER:
                query = query.filter(Ticket.submitted_by == user.id)
            elif user.role == UserRole.AGENT:
                query = query.filter(
                    or_(
                        Ticket.submitted_by == user.id,
                        Ticket.assigned_to == user.id
                    )
                )
            
            count = query.count()
            daily_resolutions.append({
                "date": date.strftime("%Y-%m-%d"),
                "count": count
            })
        
        return {
            "dailyTickets": daily_tickets,
            "dailyResolutions": daily_resolutions
        }
    
    def get_agent_performance(self, agent_id: Optional[str] = None) -> Dict:
        """Get agent performance metrics."""
        logger.info(f"Getting agent performance metrics for agent: {agent_id}")
        
        query = self.db.query(Ticket)
        
        if agent_id:
            query = query.filter(Ticket.assigned_to == agent_id)
        
        tickets = query.all()
        
        if not tickets:
            return {
                "totalAssignedTickets": 0,
                "resolvedTickets": 0,
                "avgResolutionTime": 0.0,
                "customerSatisfactionAvg": 0.0,
                "categoryExpertise": []
            }
        
        resolved_tickets = [t for t in tickets if t.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]]
        
        # Calculate average resolution time
        avg_resolution_time = 0.0
        if resolved_tickets:
            total_time = sum(
                (t.resolved_at - t.submitted_at).total_seconds() / 3600
                for t in resolved_tickets
                if t.resolved_at and t.submitted_at
            )
            avg_resolution_time = total_time / len(resolved_tickets)
        
        # Calculate customer satisfaction
        satisfied_tickets = [t for t in tickets if t.customer_satisfaction]
        customer_satisfaction = 0.0
        if satisfied_tickets:
            customer_satisfaction = sum(t.customer_satisfaction for t in satisfied_tickets) / len(satisfied_tickets)
        
        # Get category expertise
        category_counts = {}
        for ticket in tickets:
            category = ticket.category.value
            if category not in category_counts:
                category_counts[category] = 0
            category_counts[category] += 1
        
        category_expertise = [
            {"category": cat, "count": count}
            for cat, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True)
        ]
        
        return {
            "totalAssignedTickets": len(tickets),
            "resolvedTickets": len(resolved_tickets),
            "avgResolutionTime": avg_resolution_time,
            "customerSatisfactionAvg": customer_satisfaction,
            "categoryExpertise": category_expertise
        }
    
    def get_classification_metrics(self) -> Dict:
        """Get ML classification performance metrics."""
        logger.info("Getting classification metrics")
        
        # Get all classifications
        classifications = self.db.query(Classification).all()
        
        if not classifications:
            return {
                "totalClassifications": 0,
                "avgConfidence": 0.0,
                "accuracyRate": 0.0,
                "modelPerformance": {}
            }
        
        total_classifications = len(classifications)
        
        # Calculate average confidence
        avg_confidence = sum(c.confidence_score for c in classifications) / total_classifications
        
        # Calculate accuracy rate (for validated classifications)
        validated_classifications = [c for c in classifications if c.is_validated]
        accuracy_rate = 0.0
        if validated_classifications:
            correct_classifications = [c for c in validated_classifications if c.is_validated == "correct"]
            accuracy_rate = len(correct_classifications) / len(validated_classifications) * 100
        
        # Get model performance breakdown
        model_performance = {}
        for classification in classifications:
            model = classification.model_name
            if model not in model_performance:
                model_performance[model] = {
                    "total": 0,
                    "avg_confidence": 0.0,
                    "processing_time": 0.0
                }
            
            model_performance[model]["total"] += 1
            model_performance[model]["avg_confidence"] += classification.confidence_score
            if classification.processing_time_ms:
                model_performance[model]["processing_time"] += classification.processing_time_ms
        
        # Calculate averages
        for model, stats in model_performance.items():
            if stats["total"] > 0:
                stats["avg_confidence"] /= stats["total"]
                stats["processing_time"] /= stats["total"]
        
        return {
            "totalClassifications": total_classifications,
            "avgConfidence": avg_confidence,
            "accuracyRate": accuracy_rate,
            "modelPerformance": model_performance
        }
    
    def get_workload_distribution(self) -> Dict:
        """Get workload distribution across agents."""
        logger.info("Getting workload distribution")
        
        # Get all agents
        agents = self.db.query(User).filter(
            User.role.in_([UserRole.AGENT, UserRole.ADMIN])
        ).all()
        
        agent_workloads = []
        for agent in agents:
            # Get open tickets assigned to this agent
            open_tickets = self.db.query(Ticket).filter(
                and_(
                    Ticket.assigned_to == agent.id,
                    Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING])
                )
            ).count()
            
            # Get resolved tickets in the last 30 days
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            resolved_tickets = self.db.query(Ticket).filter(
                and_(
                    Ticket.assigned_to == agent.id,
                    Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED]),
                    Ticket.resolved_at >= thirty_days_ago
                )
            ).count()
            
            agent_workloads.append({
                "agent_id": agent.id,
                "agent_name": agent.name,
                "open_tickets": open_tickets,
                "resolved_tickets_30days": resolved_tickets,
                "workload_score": open_tickets * 2 + resolved_tickets  # Simple scoring
            })
        
        return {
            "agents": agent_workloads,
            "total_agents": len(agents)
        }