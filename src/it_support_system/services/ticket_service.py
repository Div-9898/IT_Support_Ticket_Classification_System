from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime

from ..models.ticket import Ticket, TicketStatus, TicketPriority
from ..models.user import User, UserRole
from ..models.activity import Activity, ActivityType
from ..models.classification import Classification
from ..utils.logging import get_logger

logger = get_logger(__name__)


class TicketService:
    """Service layer for ticket operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def auto_assign_ticket(self, ticket: Ticket) -> Optional[User]:
        """
        Auto-assign ticket to the best available agent.
        """
        logger.info(f"Auto-assigning ticket: {ticket.id}")
        
        # Get all active agents
        agents = self.db.query(User).filter(
            User.role.in_([UserRole.AGENT, UserRole.ADMIN]),
            User.is_active == True
        ).all()
        
        if not agents:
            logger.warning("No agents available for auto-assignment")
            return None
        
        # Calculate workload for each agent
        agent_workloads = []
        for agent in agents:
            # Count open tickets assigned to this agent
            open_tickets = self.db.query(Ticket).filter(
                Ticket.assigned_to == agent.id,
                Ticket.status.in_([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.PENDING])
            ).count()
            
            # Calculate expertise score based on category
            expertise_score = self._calculate_expertise_score(agent, ticket.category)
            
            agent_workloads.append({
                'agent': agent,
                'open_tickets': open_tickets,
                'expertise_score': expertise_score,
                'assignment_score': expertise_score - (open_tickets * 0.5)  # Prefer less busy agents
            })
        
        # Sort by assignment score (higher is better)
        agent_workloads.sort(key=lambda x: x['assignment_score'], reverse=True)
        
        # Assign to best agent
        best_agent = agent_workloads[0]['agent']
        
        # Update ticket
        ticket.assigned_to = best_agent.id
        ticket.assigned_at = datetime.utcnow()
        ticket.auto_assigned = True
        
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS
        
        self.db.commit()
        
        # Create activity
        activity = Activity(
            ticket_id=ticket.id,
            user_id=best_agent.id,
            activity_type=ActivityType.ASSIGNED,
            description=f"Ticket auto-assigned to {best_agent.name}",
            metadata="auto_assignment"
        )
        
        self.db.add(activity)
        self.db.commit()
        
        logger.info(f"Ticket {ticket.id} auto-assigned to {best_agent.name}")
        
        return best_agent
    
    def _calculate_expertise_score(self, agent: User, category) -> float:
        """
        Calculate agent expertise score for a category.
        """
        # Get resolved tickets by this agent in this category
        resolved_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_to == agent.id,
            Ticket.category == category,
            Ticket.status.in_([TicketStatus.RESOLVED, TicketStatus.CLOSED])
        ).count()
        
        # Get total tickets by this agent in this category
        total_tickets = self.db.query(Ticket).filter(
            Ticket.assigned_to == agent.id,
            Ticket.category == category
        ).count()
        
        if total_tickets == 0:
            return 1.0  # Neutral score for new agents
        
        # Calculate success rate
        success_rate = resolved_tickets / total_tickets
        
        # Weight by experience (more tickets = more experience)
        experience_weight = min(total_tickets / 10, 1.0)  # Cap at 10 tickets
        
        return (success_rate * 0.7) + (experience_weight * 0.3)
    
    def escalate_ticket(self, ticket: Ticket, reason: str = "Auto-escalation") -> bool:
        """
        Escalate ticket to higher priority or different agent.
        """
        logger.info(f"Escalating ticket: {ticket.id}")
        
        # Increase priority
        if ticket.priority == TicketPriority.LOW:
            ticket.priority = TicketPriority.MEDIUM
        elif ticket.priority == TicketPriority.MEDIUM:
            ticket.priority = TicketPriority.HIGH
        elif ticket.priority == TicketPriority.HIGH:
            ticket.priority = TicketPriority.URGENT
        else:
            logger.warning(f"Ticket {ticket.id} already at highest priority")
            return False
        
        # Create activity
        activity = Activity(
            ticket_id=ticket.id,
            user_id="system",
            activity_type=ActivityType.PRIORITY_CHANGED,
            description=f"Ticket escalated: {reason}",
            old_value=ticket.priority.value,
            new_value=ticket.priority.value
        )
        
        self.db.add(activity)
        self.db.commit()
        
        logger.info(f"Ticket {ticket.id} escalated to {ticket.priority.value}")
        
        return True
    
    def check_sla_compliance(self, ticket: Ticket) -> Dict:
        """
        Check SLA compliance for a ticket.
        """
        # SLA thresholds based on priority (in hours)
        sla_thresholds = {
            TicketPriority.URGENT: 2,
            TicketPriority.HIGH: 8,
            TicketPriority.MEDIUM: 24,
            TicketPriority.LOW: 72
        }
        
        threshold = sla_thresholds.get(ticket.priority, 24)
        
        # Calculate time since submission
        time_since_submission = (datetime.utcnow() - ticket.submitted_at).total_seconds() / 3600
        
        # Calculate response time (time to assignment)
        response_time = None
        if ticket.assigned_at:
            response_time = (ticket.assigned_at - ticket.submitted_at).total_seconds() / 3600
        
        # Calculate resolution time
        resolution_time = None
        if ticket.resolved_at:
            resolution_time = (ticket.resolved_at - ticket.submitted_at).total_seconds() / 3600
        
        # Determine compliance status
        is_overdue = time_since_submission > threshold and ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]
        is_resolved_within_sla = resolution_time is not None and resolution_time <= threshold
        
        return {
            'sla_threshold_hours': threshold,
            'time_since_submission': time_since_submission,
            'response_time': response_time,
            'resolution_time': resolution_time,
            'is_overdue': is_overdue,
            'is_resolved_within_sla': is_resolved_within_sla,
            'remaining_time': max(0, threshold - time_since_submission) if not is_overdue else 0
        }
    
    def suggest_resolution(self, ticket: Ticket) -> List[str]:
        """
        Suggest resolution steps based on ticket content and classification.
        """
        logger.info(f"Generating resolution suggestions for ticket: {ticket.id}")
        
        suggestions = []
        
        # Get classification suggestions
        if ticket.classification:
            suggestions.extend(ticket.classification.suggested_actions or [])
        
        # Add category-specific suggestions
        category_suggestions = {
            'Hardware': [
                'Check hardware connections',
                'Run hardware diagnostics',
                'Update device drivers',
                'Check warranty status'
            ],
            'Software': [
                'Restart the application',
                'Check for software updates',
                'Verify system requirements',
                'Clear application cache'
            ],
            'Network': [
                'Test network connectivity',
                'Check network settings',
                'Restart network equipment',
                'Contact network administrator'
            ],
            'Security': [
                'Run antivirus scan',
                'Check security settings',
                'Update security software',
                'Review access permissions'
            ],
            'Access': [
                'Verify user credentials',
                'Check account status',
                'Reset password',
                'Review access rights'
            ],
            'Email': [
                'Check email settings',
                'Verify SMTP configuration',
                'Clear email cache',
                'Test with different client'
            ]
        }
        
        category_specific = category_suggestions.get(ticket.category.value, [])
        suggestions.extend(category_specific)
        
        # Add priority-specific suggestions
        if ticket.priority == TicketPriority.URGENT:
            suggestions.insert(0, 'Escalate to senior technician immediately')
            suggestions.insert(1, 'Contact user directly for more details')
        
        # Remove duplicates while preserving order
        unique_suggestions = []
        seen = set()
        for suggestion in suggestions:
            if suggestion not in seen:
                unique_suggestions.append(suggestion)
                seen.add(suggestion)
        
        return unique_suggestions[:10]  # Return top 10 suggestions
    
    def get_similar_tickets(self, ticket: Ticket, limit: int = 5) -> List[Ticket]:
        """
        Find similar tickets based on content and category.
        """
        logger.info(f"Finding similar tickets for: {ticket.id}")
        
        # Start with tickets in the same category
        similar_query = self.db.query(Ticket).filter(
            Ticket.id != ticket.id,
            Ticket.category == ticket.category
        )
        
        # Add text similarity check (simple keyword matching)
        ticket_keywords = set(ticket.title.lower().split() + ticket.description.lower().split())
        
        similar_tickets = []
        for candidate in similar_query.all():
            candidate_keywords = set(candidate.title.lower().split() + candidate.description.lower().split())
            
            # Calculate similarity score
            common_keywords = ticket_keywords.intersection(candidate_keywords)
            similarity_score = len(common_keywords) / len(ticket_keywords.union(candidate_keywords))
            
            if similarity_score > 0.2:  # Threshold for similarity
                similar_tickets.append((candidate, similarity_score))
        
        # Sort by similarity score
        similar_tickets.sort(key=lambda x: x[1], reverse=True)
        
        # Return top matches
        return [ticket for ticket, score in similar_tickets[:limit]]
    
    def calculate_satisfaction_score(self, ticket: Ticket) -> Optional[float]:
        """
        Calculate estimated satisfaction score based on ticket metrics.
        """
        if ticket.customer_satisfaction:
            return float(ticket.customer_satisfaction)
        
        # Estimate based on resolution time and SLA compliance
        sla_info = self.check_sla_compliance(ticket)
        
        if ticket.status not in [TicketStatus.RESOLVED, TicketStatus.CLOSED]:
            return None
        
        # Base score
        score = 3.0  # Neutral
        
        # Adjust based on SLA compliance
        if sla_info['is_resolved_within_sla']:
            score += 1.0
        else:
            score -= 1.0
        
        # Adjust based on resolution time
        if sla_info['resolution_time']:
            threshold = sla_info['sla_threshold_hours']
            if sla_info['resolution_time'] < threshold * 0.5:
                score += 0.5  # Very fast resolution
            elif sla_info['resolution_time'] > threshold * 1.5:
                score -= 0.5  # Very slow resolution
        
        # Adjust based on priority
        if ticket.priority == TicketPriority.URGENT:
            score -= 0.2  # Urgent tickets are inherently less satisfying
        elif ticket.priority == TicketPriority.LOW:
            score += 0.2  # Low priority tickets are more forgiving
        
        # Clamp to valid range
        return max(1.0, min(5.0, score))
    
    def update_ticket_metrics(self, ticket: Ticket):
        """
        Update calculated metrics for a ticket.
        """
        # Update resolution time
        if ticket.resolved_at and ticket.submitted_at:
            ticket.actual_resolution_time = int(
                (ticket.resolved_at - ticket.submitted_at).total_seconds() / 60
            )
        
        # Update estimated satisfaction if not provided
        if not ticket.customer_satisfaction:
            estimated_satisfaction = self.calculate_satisfaction_score(ticket)
            if estimated_satisfaction:
                ticket.customer_satisfaction = int(estimated_satisfaction)
        
        self.db.commit()
    
    def get_ticket_analytics(self, ticket: Ticket) -> Dict:
        """
        Get comprehensive analytics for a ticket.
        """
        analytics = {
            'ticket_id': ticket.id,
            'age_hours': (datetime.utcnow() - ticket.submitted_at).total_seconds() / 3600,
            'sla_compliance': self.check_sla_compliance(ticket),
            'similar_tickets_count': len(self.get_similar_tickets(ticket)),
            'activity_count': len(ticket.activities),
            'has_classification': ticket.is_classified,
            'auto_assigned': ticket.auto_assigned,
            'estimated_satisfaction': self.calculate_satisfaction_score(ticket)
        }
        
        # Add classification analytics
        if ticket.classification:
            analytics['classification'] = {
                'confidence': ticket.classification.confidence_score,
                'model': ticket.classification.model_name,
                'processing_time': ticket.classification.processing_time_ms,
                'validated': ticket.classification.is_validated
            }
        
        return analytics