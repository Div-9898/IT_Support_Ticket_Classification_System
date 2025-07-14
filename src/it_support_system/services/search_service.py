from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Dict, Optional
import re
from datetime import datetime

from ..models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from ..models.user import User, UserRole
from ..models.classification import Classification
from ..utils.logging import get_logger

logger = get_logger(__name__)


class SearchService:
    """Service for searching tickets and users."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def search_tickets(
        self, 
        query: str, 
        user: User, 
        category: Optional[TicketCategory] = None,
        priority: Optional[TicketPriority] = None,
        status: Optional[TicketStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search tickets with full-text search and filters.
        """
        logger.info(f"Searching tickets with query: '{query}' for user: {user.email}")
        
        # Start with base query
        ticket_query = self.db.query(Ticket)
        
        # Apply user-based filtering
        if user.role == UserRole.USER:
            ticket_query = ticket_query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            ticket_query = ticket_query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        # Admin sees all tickets
        
        # Apply search query
        if query:
            search_terms = self._parse_search_query(query)
            search_conditions = self._build_search_conditions(search_terms)
            ticket_query = ticket_query.filter(search_conditions)
        
        # Apply filters
        if category:
            ticket_query = ticket_query.filter(Ticket.category == category)
        
        if priority:
            ticket_query = ticket_query.filter(Ticket.priority == priority)
        
        if status:
            ticket_query = ticket_query.filter(Ticket.status == status)
        
        if date_from:
            ticket_query = ticket_query.filter(Ticket.submitted_at >= date_from)
        
        if date_to:
            ticket_query = ticket_query.filter(Ticket.submitted_at <= date_to)
        
        # Execute query with relevance scoring
        tickets = ticket_query.order_by(desc(Ticket.submitted_at)).limit(limit).all()
        
        # Convert to dict and add relevance scores
        results = []
        for ticket in tickets:
            ticket_dict = ticket.to_dict()
            
            # Calculate relevance score
            relevance_score = self._calculate_relevance_score(ticket, query) if query else 1.0
            ticket_dict['relevance_score'] = relevance_score
            
            # Add search highlights
            if query:
                ticket_dict['highlights'] = self._generate_highlights(ticket, query)
            
            results.append(ticket_dict)
        
        # Sort by relevance if query was provided
        if query:
            results.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"Found {len(results)} tickets matching search criteria")
        return results
    
    def _parse_search_query(self, query: str) -> List[str]:
        """Parse search query into terms."""
        # Remove special characters and split
        query = re.sub(r'[^\w\s-]', ' ', query)
        terms = [term.strip().lower() for term in query.split() if len(term.strip()) > 2]
        return terms
    
    def _build_search_conditions(self, terms: List[str]):
        """Build SQL conditions for search terms."""
        conditions = []
        
        for term in terms:
            term_pattern = f"%{term}%"
            term_condition = or_(
                Ticket.title.ilike(term_pattern),
                Ticket.description.ilike(term_pattern),
                Ticket.resolution_notes.ilike(term_pattern)
            )
            conditions.append(term_condition)
        
        # All terms must match (AND logic)
        if conditions:
            return and_(*conditions)
        
        return True  # No conditions
    
    def _calculate_relevance_score(self, ticket: Ticket, query: str) -> float:
        """Calculate relevance score for a ticket."""
        score = 0.0
        query_lower = query.lower()
        
        # Title matches (highest weight)
        if query_lower in ticket.title.lower():
            score += 10.0
            # Exact match bonus
            if query_lower == ticket.title.lower():
                score += 5.0
        
        # Description matches
        description_lower = ticket.description.lower()
        description_matches = description_lower.count(query_lower)
        score += description_matches * 2.0
        
        # Resolution notes matches
        if ticket.resolution_notes:
            resolution_matches = ticket.resolution_notes.lower().count(query_lower)
            score += resolution_matches * 1.5
        
        # Recent tickets get slight boost
        age_days = (datetime.utcnow() - ticket.submitted_at).days
        if age_days < 30:
            score += 1.0
        elif age_days < 90:
            score += 0.5
        
        # Priority boost
        priority_scores = {
            TicketPriority.URGENT: 2.0,
            TicketPriority.HIGH: 1.5,
            TicketPriority.MEDIUM: 1.0,
            TicketPriority.LOW: 0.5
        }
        score += priority_scores.get(ticket.priority, 1.0)
        
        return score
    
    def _generate_highlights(self, ticket: Ticket, query: str) -> Dict[str, str]:
        """Generate search highlights."""
        highlights = {}
        query_lower = query.lower()
        
        # Highlight in title
        if query_lower in ticket.title.lower():
            highlights['title'] = self._highlight_text(ticket.title, query)
        
        # Highlight in description
        if query_lower in ticket.description.lower():
            highlights['description'] = self._highlight_text(ticket.description, query, max_length=200)
        
        # Highlight in resolution notes
        if ticket.resolution_notes and query_lower in ticket.resolution_notes.lower():
            highlights['resolution_notes'] = self._highlight_text(ticket.resolution_notes, query, max_length=200)
        
        return highlights
    
    def _highlight_text(self, text: str, query: str, max_length: int = 100) -> str:
        """Highlight query terms in text."""
        if not text or not query:
            return text
        
        # Find the position of the query in the text
        query_lower = query.lower()
        text_lower = text.lower()
        
        pos = text_lower.find(query_lower)
        if pos == -1:
            return text[:max_length] + "..." if len(text) > max_length else text
        
        # Extract context around the match
        start = max(0, pos - 50)
        end = min(len(text), pos + len(query) + 50)
        
        if start > 0:
            # Find word boundary
            while start > 0 and text[start] != ' ':
                start -= 1
            start += 1
        
        if end < len(text):
            # Find word boundary
            while end < len(text) and text[end] != ' ':
                end += 1
        
        excerpt = text[start:end]
        
        # Add ellipsis if truncated
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(text):
            excerpt = excerpt + "..."
        
        # Highlight the query term
        highlighted = re.sub(
            re.escape(query), 
            f"<mark>{query}</mark>", 
            excerpt, 
            flags=re.IGNORECASE
        )
        
        return highlighted
    
    def search_users(
        self, 
        query: str, 
        requesting_user: User,
        role: Optional[UserRole] = None,
        department: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search users.
        """
        logger.info(f"Searching users with query: '{query}' for user: {requesting_user.email}")
        
        # Only agents and admins can search users
        if requesting_user.role == UserRole.USER:
            logger.warning(f"User {requesting_user.email} attempted to search users")
            return []
        
        # Start with base query
        user_query = self.db.query(User).filter(User.is_active == True)
        
        # Apply search query
        if query:
            search_pattern = f"%{query}%"
            user_query = user_query.filter(
                or_(
                    User.name.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.department.ilike(search_pattern)
                )
            )
        
        # Apply filters
        if role:
            user_query = user_query.filter(User.role == role)
        
        if department:
            user_query = user_query.filter(User.department.ilike(f"%{department}%"))
        
        # Execute query
        users = user_query.order_by(User.name).limit(limit).all()
        
        # Convert to dict
        results = []
        for user in users:
            user_dict = user.to_dict()
            
            # Remove sensitive information
            user_dict.pop('hashed_password', None)
            
            # Add search highlights
            if query:
                user_dict['highlights'] = self._generate_user_highlights(user, query)
            
            results.append(user_dict)
        
        logger.info(f"Found {len(results)} users matching search criteria")
        return results
    
    def _generate_user_highlights(self, user: User, query: str) -> Dict[str, str]:
        """Generate search highlights for user."""
        highlights = {}
        query_lower = query.lower()
        
        # Highlight in name
        if query_lower in user.name.lower():
            highlights['name'] = self._highlight_text(user.name, query)
        
        # Highlight in email
        if query_lower in user.email.lower():
            highlights['email'] = self._highlight_text(user.email, query)
        
        # Highlight in department
        if user.department and query_lower in user.department.lower():
            highlights['department'] = self._highlight_text(user.department, query)
        
        return highlights
    
    def get_search_suggestions(self, query: str, user: User) -> List[str]:
        """
        Get search suggestions based on partial query.
        """
        logger.info(f"Getting search suggestions for query: '{query}'")
        
        if len(query) < 2:
            return []
        
        suggestions = []
        
        # Get ticket title suggestions
        title_query = self.db.query(Ticket.title).filter(
            Ticket.title.ilike(f"%{query}%")
        )
        
        # Apply user-based filtering
        if user.role == UserRole.USER:
            title_query = title_query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            title_query = title_query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        titles = title_query.distinct().limit(5).all()
        suggestions.extend([title[0] for title in titles])
        
        # Get category suggestions
        categories = [cat.value for cat in TicketCategory if query.lower() in cat.value.lower()]
        suggestions.extend(categories)
        
        # Get priority suggestions
        priorities = [pri.value for pri in TicketPriority if query.lower() in pri.value.lower()]
        suggestions.extend(priorities)
        
        # Get status suggestions
        statuses = [stat.value for stat in TicketStatus if query.lower() in stat.value.lower()]
        suggestions.extend(statuses)
        
        # Remove duplicates and limit
        suggestions = list(set(suggestions))[:10]
        
        logger.info(f"Generated {len(suggestions)} search suggestions")
        return suggestions
    
    def get_popular_searches(self, user: User, limit: int = 10) -> List[Dict]:
        """
        Get popular search terms (this would typically be tracked in a separate table).
        """
        # For now, return some common search terms based on ticket content
        logger.info("Getting popular search terms")
        
        # Get most common words in ticket titles
        title_query = self.db.query(Ticket.title)
        
        # Apply user-based filtering
        if user.role == UserRole.USER:
            title_query = title_query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            title_query = title_query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        titles = title_query.all()
        
        # Extract common words
        word_counts = {}
        for title in titles:
            words = re.findall(r'\b\w{4,}\b', title[0].lower())
            for word in words:
                if word not in ['ticket', 'issue', 'problem', 'help', 'support']:
                    word_counts[word] = word_counts.get(word, 0) + 1
        
        # Sort by frequency
        popular_terms = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [{"term": term, "count": count} for term, count in popular_terms]
    
    def advanced_search(
        self, 
        user: User,
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
        classification_confidence_min: Optional[float] = None,
        customer_satisfaction_min: Optional[int] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Advanced search with multiple criteria.
        """
        logger.info(f"Performing advanced search for user: {user.email}")
        
        # Start with base query
        ticket_query = self.db.query(Ticket)
        
        # Apply user-based filtering
        if user.role == UserRole.USER:
            ticket_query = ticket_query.filter(Ticket.submitted_by == user.id)
        elif user.role == UserRole.AGENT:
            ticket_query = ticket_query.filter(
                or_(
                    Ticket.submitted_by == user.id,
                    Ticket.assigned_to == user.id
                )
            )
        
        # Apply search criteria
        if title:
            ticket_query = ticket_query.filter(Ticket.title.ilike(f"%{title}%"))
        
        if description:
            ticket_query = ticket_query.filter(Ticket.description.ilike(f"%{description}%"))
        
        if category:
            ticket_query = ticket_query.filter(Ticket.category == category)
        
        if priority:
            ticket_query = ticket_query.filter(Ticket.priority == priority)
        
        if status:
            ticket_query = ticket_query.filter(Ticket.status == status)
        
        if submitted_by:
            ticket_query = ticket_query.filter(Ticket.submitted_by == submitted_by)
        
        if assigned_to:
            ticket_query = ticket_query.filter(Ticket.assigned_to == assigned_to)
        
        if date_from:
            ticket_query = ticket_query.filter(Ticket.submitted_at >= date_from)
        
        if date_to:
            ticket_query = ticket_query.filter(Ticket.submitted_at <= date_to)
        
        if has_classification is not None:
            if has_classification:
                ticket_query = ticket_query.filter(Ticket.is_classified == True)
            else:
                ticket_query = ticket_query.filter(Ticket.is_classified == False)
        
        if classification_confidence_min is not None:
            ticket_query = ticket_query.join(Classification).filter(
                Classification.confidence_score >= classification_confidence_min
            )
        
        if customer_satisfaction_min is not None:
            ticket_query = ticket_query.filter(
                and_(
                    Ticket.customer_satisfaction.isnot(None),
                    Ticket.customer_satisfaction >= customer_satisfaction_min
                )
            )
        
        # Execute query
        tickets = ticket_query.order_by(desc(Ticket.submitted_at)).limit(limit).all()
        
        # Convert to dict
        results = [ticket.to_dict() for ticket in tickets]
        
        logger.info(f"Advanced search returned {len(results)} results")
        return results