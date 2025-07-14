from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime, timedelta

from ..models.user import User, UserRole
from ..models.ticket import Ticket, TicketStatus
from ..models.activity import Activity
from ..utils.logging import get_logger
from ..utils.auth import auth_service

logger = get_logger(__name__)


class UserService:
    """Service layer for user operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: Dict) -> User:
        """
        Create a new user with proper validation.
        """
        logger.info(f"Creating user: {user_data.get('email')}")
        
        # Check if user already exists
        existing_user = self.db.query(User).filter(
            User.email == user_data['email']
        ).first()
        
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Hash password
        hashed_password = auth_service.get_password_hash(user_data['password'])
        
        # Create user
        user = User(
            email=user_data['email'],
            name=user_data['name'],
            hashed_password=hashed_password,
            role=user_data.get('role', UserRole.USER),
            department=user_data.get('department'),
            phone=user_data.get('phone'),
            bio=user_data.get('bio')
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        logger.info(f"User created successfully: {user.email}")
        return user
    
    def get_user_dashboard_data(self, user: User) -> Dict:
        """
        Get dashboard data specific to a user.
        """
        logger.info(f"Getting dashboard data for user: {user.email}")
        
        dashboard_data = {
            'user_info': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'role': user.role.value,
                'department': user.department,
                'last_login': user.last_login
            }
        }
        
        if user.role == UserRole.USER:
            dashboard_data.update(self._get_user_dashboard_data(user))
        elif user.role == UserRole.AGENT:
            dashboard_data.update(self._get_agent_dashboard_data(user))
        elif user.role == UserRole.ADMIN:
            dashboard_data.update(self._get_admin_dashboard_data(user))
        
        return dashboard_data
    
    def _get_user_dashboard_data(self, user: User) -> Dict:
        """Get dashboard data for regular users."""
        # Get user's tickets
        user_tickets = self.db.query(Ticket).filter(
            Ticket.submitted_by == user.id
        ).all()
        
        # Calculate metrics
        total_tickets = len(user_tickets)
        open_tickets = len([t for t in user_tickets if t.status in [
            TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING
        ]])
        resolved_tickets = len([t for t in user_tickets if t.status in [
            TicketStatus.RESOLVED, TicketStatus.CLOSED
        ]])
        
        # Get recent tickets
        recent_tickets = sorted(user_tickets, key=lambda x: x.submitted_at, reverse=True)[:5]
        
        # Calculate average resolution time
        resolved_with_time = [t for t in user_tickets if t.resolved_at and t.submitted_at]
        avg_resolution_time = 0.0
        if resolved_with_time:
            total_time = sum(
                (t.resolved_at - t.submitted_at).total_seconds() / 3600
                for t in resolved_with_time
            )
            avg_resolution_time = total_time / len(resolved_with_time)
        
        return {
            'tickets': {
                'total': total_tickets,
                'open': open_tickets,
                'resolved': resolved_tickets,
                'recent': [t.to_dict() for t in recent_tickets]
            },
            'metrics': {
                'avg_resolution_time': avg_resolution_time,
                'satisfaction_avg': self._calculate_user_satisfaction(user_tickets)
            }
        }
    
    def _get_agent_dashboard_data(self, user: User) -> Dict:
        """Get dashboard data for agents."""
        # Get assigned tickets
        assigned_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_to == user.id
        ).all()
        
        # Get submitted tickets
        submitted_tickets = self.db.query(Ticket).filter(
            Ticket.submitted_by == user.id
        ).all()
        
        # Calculate metrics
        total_assigned = len(assigned_tickets)
        open_assigned = len([t for t in assigned_tickets if t.status in [
            TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING
        ]])
        resolved_assigned = len([t for t in assigned_tickets if t.status in [
            TicketStatus.RESOLVED, TicketStatus.CLOSED
        ]])
        
        # Get workload for today
        today = datetime.utcnow().date()
        today_tickets = [t for t in assigned_tickets if t.submitted_at.date() == today]
        
        # Calculate performance metrics
        performance = self._calculate_agent_performance(user, assigned_tickets)
        
        return {
            'assigned_tickets': {
                'total': total_assigned,
                'open': open_assigned,
                'resolved': resolved_assigned,
                'today': len(today_tickets)
            },
            'submitted_tickets': {
                'total': len(submitted_tickets)
            },
            'performance': performance,
            'workload': {
                'current_load': open_assigned,
                'workload_level': self._calculate_workload_level(open_assigned)
            }
        }
    
    def _get_admin_dashboard_data(self, user: User) -> Dict:
        """Get dashboard data for admins."""
        # Get system-wide metrics
        all_tickets = self.db.query(Ticket).all()
        all_users = self.db.query(User).filter(User.is_active == True).all()
        
        # Calculate system metrics
        total_tickets = len(all_tickets)
        open_tickets = len([t for t in all_tickets if t.status in [
            TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING
        ]])
        resolved_tickets = len([t for t in all_tickets if t.status in [
            TicketStatus.RESOLVED, TicketStatus.CLOSED
        ]])
        
        # Get user distribution
        user_distribution = {}
        for role in UserRole:
            user_distribution[role.value] = len([u for u in all_users if u.role == role])
        
        # Get recent activity
        recent_activity = self.db.query(Activity).order_by(
            Activity.created_at.desc()
        ).limit(10).all()
        
        # Calculate system health
        system_health = self._calculate_system_health(all_tickets, all_users)
        
        return {
            'system_metrics': {
                'total_tickets': total_tickets,
                'open_tickets': open_tickets,
                'resolved_tickets': resolved_tickets,
                'total_users': len(all_users),
                'user_distribution': user_distribution
            },
            'recent_activity': [a.to_dict() for a in recent_activity],
            'system_health': system_health
        }
    
    def _calculate_user_satisfaction(self, tickets: List[Ticket]) -> float:
        """Calculate average satisfaction for user's tickets."""
        satisfied_tickets = [t for t in tickets if t.customer_satisfaction]
        if not satisfied_tickets:
            return 0.0
        
        return sum(t.customer_satisfaction for t in satisfied_tickets) / len(satisfied_tickets)
    
    def _calculate_agent_performance(self, agent: User, tickets: List[Ticket]) -> Dict:
        """Calculate performance metrics for an agent."""
        if not tickets:
            return {
                'resolution_rate': 0.0,
                'avg_resolution_time': 0.0,
                'customer_satisfaction': 0.0,
                'sla_compliance': 0.0
            }
        
        resolved_tickets = [t for t in tickets if t.status in [
            TicketStatus.RESOLVED, TicketStatus.CLOSED
        ]]
        
        # Resolution rate
        resolution_rate = len(resolved_tickets) / len(tickets) * 100
        
        # Average resolution time
        resolved_with_time = [t for t in resolved_tickets if t.resolved_at and t.submitted_at]
        avg_resolution_time = 0.0
        if resolved_with_time:
            total_time = sum(
                (t.resolved_at - t.submitted_at).total_seconds() / 3600
                for t in resolved_with_time
            )
            avg_resolution_time = total_time / len(resolved_with_time)
        
        # Customer satisfaction
        satisfied_tickets = [t for t in tickets if t.customer_satisfaction]
        customer_satisfaction = 0.0
        if satisfied_tickets:
            customer_satisfaction = sum(t.customer_satisfaction for t in satisfied_tickets) / len(satisfied_tickets)
        
        # SLA compliance
        sla_compliant = 0
        for ticket in resolved_tickets:
            if ticket.resolved_at and ticket.submitted_at:
                # Simple SLA check - resolved within priority threshold
                priority_thresholds = {
                    'Urgent': 2,
                    'High': 8,
                    'Medium': 24,
                    'Low': 72
                }
                threshold = priority_thresholds.get(ticket.priority.value, 24)
                resolution_time = (ticket.resolved_at - ticket.submitted_at).total_seconds() / 3600
                
                if resolution_time <= threshold:
                    sla_compliant += 1
        
        sla_compliance = (sla_compliant / len(resolved_tickets) * 100) if resolved_tickets else 0.0
        
        return {
            'resolution_rate': resolution_rate,
            'avg_resolution_time': avg_resolution_time,
            'customer_satisfaction': customer_satisfaction,
            'sla_compliance': sla_compliance
        }
    
    def _calculate_workload_level(self, open_tickets: int) -> str:
        """Calculate workload level based on open tickets."""
        if open_tickets == 0:
            return 'none'
        elif open_tickets <= 5:
            return 'low'
        elif open_tickets <= 15:
            return 'medium'
        elif open_tickets <= 25:
            return 'high'
        else:
            return 'overloaded'
    
    def _calculate_system_health(self, tickets: List[Ticket], users: List[User]) -> Dict:
        """Calculate overall system health metrics."""
        if not tickets:
            return {
                'status': 'healthy',
                'score': 100,
                'indicators': []
            }
        
        indicators = []
        score = 100
        
        # Check ticket backlog
        open_tickets = len([t for t in tickets if t.status in [
            TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING
        ]])
        
        if open_tickets > 50:
            indicators.append('High ticket backlog')
            score -= 20
        elif open_tickets > 20:
            indicators.append('Moderate ticket backlog')
            score -= 10
        
        # Check overdue tickets
        overdue_tickets = len([t for t in tickets if t.is_overdue])
        if overdue_tickets > 10:
            indicators.append('Many overdue tickets')
            score -= 15
        elif overdue_tickets > 5:
            indicators.append('Some overdue tickets')
            score -= 5
        
        # Check agent availability
        agents = [u for u in users if u.role in [UserRole.AGENT, UserRole.ADMIN]]
        if len(agents) < 3:
            indicators.append('Low agent availability')
            score -= 10
        
        # Check recent activity
        recent_activity = self.db.query(Activity).filter(
            Activity.created_at >= datetime.utcnow() - timedelta(hours=24)
        ).count()
        
        if recent_activity < 5:
            indicators.append('Low system activity')
            score -= 5
        
        # Determine overall status
        if score >= 90:
            status = 'healthy'
        elif score >= 70:
            status = 'warning'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'score': max(0, score),
            'indicators': indicators
        }
    
    def get_user_activity_summary(self, user: User, days: int = 30) -> Dict:
        """Get user activity summary for the last N days."""
        logger.info(f"Getting activity summary for user: {user.email}")
        
        # Get date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get activities
        activities = self.db.query(Activity).filter(
            Activity.user_id == user.id,
            Activity.created_at >= start_date
        ).all()
        
        # Get tickets
        if user.role == UserRole.USER:
            tickets = self.db.query(Ticket).filter(
                Ticket.submitted_by == user.id,
                Ticket.submitted_at >= start_date
            ).all()
        elif user.role == UserRole.AGENT:
            tickets = self.db.query(Ticket).filter(
                Ticket.assigned_to == user.id,
                Ticket.submitted_at >= start_date
            ).all()
        else:  # Admin
            tickets = self.db.query(Ticket).filter(
                Ticket.submitted_at >= start_date
            ).all()
        
        # Calculate metrics
        activity_count = len(activities)
        ticket_count = len(tickets)
        
        # Activity type distribution
        activity_types = {}
        for activity in activities:
            activity_type = activity.activity_type.value
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        # Daily activity
        daily_activity = {}
        for i in range(days):
            date = start_date + timedelta(days=i)
            date_str = date.strftime('%Y-%m-%d')
            
            day_activities = [a for a in activities if a.created_at.date() == date.date()]
            daily_activity[date_str] = len(day_activities)
        
        return {
            'period_days': days,
            'activity_count': activity_count,
            'ticket_count': ticket_count,
            'activity_types': activity_types,
            'daily_activity': daily_activity,
            'avg_daily_activity': activity_count / days if days > 0 else 0
        }
    
    def recommend_agent_for_ticket(self, ticket: Ticket) -> Optional[User]:
        """
        Recommend the best agent for a ticket based on expertise and workload.
        """
        logger.info(f"Recommending agent for ticket: {ticket.id}")
        
        # Get all active agents
        agents = self.db.query(User).filter(
            User.role.in_([UserRole.AGENT, UserRole.ADMIN]),
            User.is_active == True
        ).all()
        
        if not agents:
            return None
        
        # Score each agent
        agent_scores = []
        for agent in agents:
            score = self._calculate_agent_score(agent, ticket)
            agent_scores.append((agent, score))
        
        # Sort by score (higher is better)
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        return agent_scores[0][0] if agent_scores else None
    
    def _calculate_agent_score(self, agent: User, ticket: Ticket) -> float:
        """Calculate agent score for ticket assignment."""
        score = 0.0
        
        # Expertise score (based on past performance in this category)
        category_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_to == agent.id,
            Ticket.category == ticket.category
        ).all()
        
        if category_tickets:
            resolved_count = len([t for t in category_tickets if t.status in [
                TicketStatus.RESOLVED, TicketStatus.CLOSED
            ]])
            expertise_score = resolved_count / len(category_tickets)
            score += expertise_score * 40  # 40% weight
        else:
            score += 20  # Neutral score for new category
        
        # Workload score (prefer less busy agents)
        open_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_to == agent.id,
            Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING])
        ).count()
        
        workload_score = max(0, 30 - open_tickets)  # Decrease score for more tickets
        score += workload_score * 30  # 30% weight
        
        # Response time score (prefer agents with faster response times)
        recent_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_to == agent.id,
            Ticket.assigned_at >= datetime.utcnow() - timedelta(days=30)
        ).all()
        
        if recent_tickets:
            response_times = []
            for t in recent_tickets:
                if t.assigned_at and t.submitted_at:
                    response_time = (t.assigned_at - t.submitted_at).total_seconds() / 3600
                    response_times.append(response_time)
            
            if response_times:
                avg_response_time = sum(response_times) / len(response_times)
                response_score = max(0, 10 - avg_response_time)  # Prefer faster response
                score += response_score * 20  # 20% weight
        
        # Availability score (prefer agents who are not overloaded)
        if open_tickets < 5:
            score += 10  # Bonus for low workload
        elif open_tickets > 20:
            score -= 10  # Penalty for high workload
        
        return score
    
    def get_team_performance(self, department: Optional[str] = None) -> Dict:
        """Get team performance metrics."""
        logger.info(f"Getting team performance for department: {department}")
        
        # Get agents (optionally filtered by department)
        agents_query = self.db.query(User).filter(
            User.role.in_([UserRole.AGENT, UserRole.ADMIN]),
            User.is_active == True
        )
        
        if department:
            agents_query = agents_query.filter(User.department == department)
        
        agents = agents_query.all()
        
        # Calculate team metrics
        team_metrics = {
            'total_agents': len(agents),
            'agent_performance': [],
            'team_averages': {
                'resolution_rate': 0.0,
                'avg_resolution_time': 0.0,
                'customer_satisfaction': 0.0,
                'sla_compliance': 0.0
            }
        }
        
        total_resolution_rate = 0.0
        total_resolution_time = 0.0
        total_satisfaction = 0.0
        total_sla_compliance = 0.0
        
        for agent in agents:
            # Get agent's tickets
            agent_tickets = self.db.query(Ticket).filter(
                Ticket.assigned_to == agent.id
            ).all()
            
            # Calculate performance
            performance = self._calculate_agent_performance(agent, agent_tickets)
            
            agent_data = {
                'agent_id': agent.id,
                'agent_name': agent.name,
                'department': agent.department,
                'performance': performance,
                'current_workload': self.db.query(Ticket).filter(
                    Ticket.assigned_to == agent.id,
                    Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING])
                ).count()
            }
            
            team_metrics['agent_performance'].append(agent_data)
            
            # Add to totals for averages
            total_resolution_rate += performance['resolution_rate']
            total_resolution_time += performance['avg_resolution_time']
            total_satisfaction += performance['customer_satisfaction']
            total_sla_compliance += performance['sla_compliance']
        
        # Calculate team averages
        if agents:
            team_metrics['team_averages'] = {
                'resolution_rate': total_resolution_rate / len(agents),
                'avg_resolution_time': total_resolution_time / len(agents),
                'customer_satisfaction': total_satisfaction / len(agents),
                'sla_compliance': total_sla_compliance / len(agents)
            }
        
        return team_metrics