#!/usr/bin/env python3
"""
CLI entry point for the IT Support Ticket Classification System.
"""

import click
import asyncio
from pathlib import Path
from sqlalchemy.orm import Session

from .config.settings import settings
from .models.database import SessionLocal, create_tables, drop_tables
from .models.user import User, UserRole
from .models.ticket import Ticket, TicketCategory, TicketPriority, TicketStatus
from .services.ml_service import MLService
from .utils.auth import auth_service
from .utils.logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


@click.group()
def cli():
    """IT Support Ticket Classification System CLI"""
    pass


@cli.command()
def init_db():
    """Initialize the database with tables."""
    click.echo("Initializing database...")
    
    try:
        create_tables()
        click.echo("✓ Database tables created successfully")
    except Exception as e:
        click.echo(f"✗ Error creating database tables: {e}")
        raise


@cli.command()
@click.option('--confirm', is_flag=True, help='Confirm deletion')
def drop_db(confirm):
    """Drop all database tables."""
    if not confirm:
        click.echo("This will delete all data. Use --confirm to proceed.")
        return
    
    click.echo("Dropping database tables...")
    
    try:
        drop_tables()
        click.echo("✓ Database tables dropped successfully")
    except Exception as e:
        click.echo(f"✗ Error dropping database tables: {e}")
        raise


@cli.command()
@click.option('--email', prompt=True, help='Admin email')
@click.option('--name', prompt=True, help='Admin name')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='Admin password')
@click.option('--department', default='IT', help='Department')
def create_admin(email, name, password, department):
    """Create an admin user."""
    click.echo("Creating admin user...")
    
    db = SessionLocal()
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            click.echo(f"✗ User with email {email} already exists")
            return
        
        # Create admin user
        hashed_password = auth_service.get_password_hash(password)
        admin_user = User(
            email=email,
            name=name,
            hashed_password=hashed_password,
            role=UserRole.ADMIN,
            department=department,
            is_active=True
        )
        
        db.add(admin_user)
        db.commit()
        
        click.echo(f"✓ Admin user created successfully: {email}")
        
    except Exception as e:
        click.echo(f"✗ Error creating admin user: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@cli.command()
@click.option('--count', default=10, help='Number of sample tickets to create')
def create_sample_data(count):
    """Create sample data for testing."""
    click.echo(f"Creating {count} sample tickets...")
    
    db = SessionLocal()
    try:
        # Create sample users if they don't exist
        users = []
        
        # Create sample user
        sample_user = db.query(User).filter(User.email == 'user@example.com').first()
        if not sample_user:
            sample_user = User(
                email='user@example.com',
                name='Sample User',
                hashed_password=auth_service.get_password_hash('password123'),
                role=UserRole.USER,
                department='Sales',
                is_active=True
            )
            db.add(sample_user)
        users.append(sample_user)
        
        # Create sample agent
        sample_agent = db.query(User).filter(User.email == 'agent@example.com').first()
        if not sample_agent:
            sample_agent = User(
                email='agent@example.com',
                name='Sample Agent',
                hashed_password=auth_service.get_password_hash('password123'),
                role=UserRole.AGENT,
                department='IT',
                is_active=True
            )
            db.add(sample_agent)
        users.append(sample_agent)
        
        db.commit()
        
        # Sample ticket data
        sample_tickets = [
            {
                'title': 'Computer won\'t start',
                'description': 'My computer is not turning on when I press the power button. The LED lights are not showing.',
                'category': TicketCategory.HARDWARE,
                'priority': TicketPriority.HIGH
            },
            {
                'title': 'Email not working',
                'description': 'I cannot send or receive emails. Getting error message "Connection failed".',
                'category': TicketCategory.EMAIL,
                'priority': TicketPriority.MEDIUM
            },
            {
                'title': 'Password reset needed',
                'description': 'I forgot my password and need to reset it to access the system.',
                'category': TicketCategory.ACCESS,
                'priority': TicketPriority.LOW
            },
            {
                'title': 'Network connection issues',
                'description': 'Internet is very slow and keeps disconnecting frequently.',
                'category': TicketCategory.NETWORK,
                'priority': TicketPriority.MEDIUM
            },
            {
                'title': 'Software installation help',
                'description': 'Need help installing the new CRM software on my workstation.',
                'category': TicketCategory.SOFTWARE,
                'priority': TicketPriority.LOW
            },
            {
                'title': 'Security alert - suspicious activity',
                'description': 'Received suspicious emails and think my account might be compromised.',
                'category': TicketCategory.SECURITY,
                'priority': TicketPriority.URGENT
            },
            {
                'title': 'Printer not working',
                'description': 'Office printer is showing error message and won\'t print documents.',
                'category': TicketCategory.HARDWARE,
                'priority': TicketPriority.MEDIUM
            },
            {
                'title': 'Application crashes frequently',
                'description': 'The accounting software keeps crashing when I try to generate reports.',
                'category': TicketCategory.SOFTWARE,
                'priority': TicketPriority.HIGH
            },
            {
                'title': 'VPN connection problems',
                'description': 'Cannot connect to VPN from home office. Keep getting timeout errors.',
                'category': TicketCategory.NETWORK,
                'priority': TicketPriority.MEDIUM
            },
            {
                'title': 'File server access denied',
                'description': 'Getting "Access Denied" error when trying to access shared folders.',
                'category': TicketCategory.ACCESS,
                'priority': TicketPriority.HIGH
            }
        ]
        
        # Create tickets
        import random
        from datetime import datetime, timedelta
        
        for i in range(min(count, len(sample_tickets))):
            ticket_data = sample_tickets[i]
            
            # Random submission time within last 30 days
            submission_time = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            
            ticket = Ticket(
                title=ticket_data['title'],
                description=ticket_data['description'],
                category=ticket_data['category'],
                priority=ticket_data['priority'],
                status=random.choice([TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.RESOLVED]),
                submitted_by=random.choice(users).id,
                submitted_at=submission_time,
                tags=['sample', 'test'],
                attachments=[]
            )
            
            # Randomly assign some tickets
            if random.random() > 0.3:  # 70% chance of assignment
                ticket.assigned_to = sample_agent.id
                ticket.assigned_at = submission_time + timedelta(hours=random.randint(1, 12))
            
            # Randomly resolve some tickets
            if ticket.status == TicketStatus.RESOLVED:
                ticket.resolved_at = submission_time + timedelta(hours=random.randint(2, 48))
                ticket.resolution_notes = "Sample resolution - issue fixed"
                ticket.customer_satisfaction = random.randint(3, 5)
            
            db.add(ticket)
        
        db.commit()
        
        click.echo(f"✓ Created {min(count, len(sample_tickets))} sample tickets")
        
    except Exception as e:
        click.echo(f"✗ Error creating sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


@cli.command()
def train_ml_models():
    """Train machine learning models."""
    click.echo("Training ML models...")
    
    async def train_models():
        try:
            # Initialize ML service
            ml_service = MLService()
            await ml_service.initialize()
            
            # Get training data from database
            db = SessionLocal()
            tickets = db.query(Ticket).all()
            
            if not tickets:
                click.echo("No tickets found in database. Create sample data first.")
                return
            
            # Prepare training data
            training_data = []
            for ticket in tickets:
                training_data.append({
                    'title': ticket.title,
                    'description': ticket.description,
                    'category': ticket.category.value
                })
            
            # Train models
            await ml_service.train_models(training_data)
            
            click.echo("✓ ML models trained successfully")
            
        except Exception as e:
            click.echo(f"✗ Error training ML models: {e}")
            raise
        finally:
            db.close()
            await ml_service.cleanup()
    
    asyncio.run(train_models())


@cli.command()
@click.option('--host', default=settings.host, help='Host to bind to')
@click.option('--port', default=settings.port, help='Port to bind to')
@click.option('--reload', is_flag=True, help='Enable auto-reload')
def run_server(host, port, reload):
    """Run the FastAPI server."""
    click.echo(f"Starting server on {host}:{port}")
    
    import uvicorn
    
    uvicorn.run(
        "it_support_system.main:app",
        host=host,
        port=port,
        reload=reload,
        log_level=settings.log_level.lower()
    )


@cli.command()
def check_config():
    """Check configuration settings."""
    click.echo("Configuration Settings:")
    click.echo(f"  App Name: {settings.app_name}")
    click.echo(f"  Version: {settings.app_version}")
    click.echo(f"  Environment: {settings.environment}")
    click.echo(f"  Debug: {settings.debug}")
    click.echo(f"  Database URL: {settings.database_url}")
    click.echo(f"  Host: {settings.host}")
    click.echo(f"  Port: {settings.port}")
    click.echo(f"  Log Level: {settings.log_level}")
    click.echo(f"  ML Model Path: {settings.ml_model_path}")
    click.echo(f"  HuggingFace Model: {settings.huggingface_model_name}")
    click.echo(f"  Use GPU: {settings.use_gpu}")
    click.echo(f"  Upload Folder: {settings.upload_folder}")
    click.echo(f"  Max Content Length: {settings.max_content_length}")
    click.echo(f"  CORS Origins: {settings.cors_origins}")


@cli.command()
def show_routes():
    """Show available API routes."""
    click.echo("Available API Routes:")
    
    routes = [
        ("POST", "/api/v1/auth/login", "User login"),
        ("POST", "/api/v1/auth/register", "User registration"),
        ("GET", "/api/v1/auth/me", "Get current user"),
        ("GET", "/api/v1/tickets", "Get tickets"),
        ("POST", "/api/v1/tickets", "Create ticket"),
        ("GET", "/api/v1/tickets/{id}", "Get ticket details"),
        ("PUT", "/api/v1/tickets/{id}", "Update ticket"),
        ("DELETE", "/api/v1/tickets/{id}", "Delete ticket"),
        ("POST", "/api/v1/tickets/{id}/classify", "Classify ticket"),
        ("GET", "/api/v1/users", "Get users"),
        ("POST", "/api/v1/users", "Create user"),
        ("GET", "/api/v1/users/{id}", "Get user details"),
        ("GET", "/api/v1/dashboard/stats", "Get dashboard statistics"),
        ("GET", "/api/v1/search/tickets", "Search tickets"),
        ("GET", "/api/v1/search/users", "Search users"),
        ("POST", "/api/v1/upload", "Upload file"),
        ("GET", "/health", "Health check"),
        ("GET", "/docs", "API documentation"),
    ]
    
    for method, path, description in routes:
        click.echo(f"  {method:<6} {path:<40} {description}")


@cli.command()
def test_ml_service():
    """Test the ML service."""
    click.echo("Testing ML service...")
    
    async def test_ml():
        try:
            ml_service = MLService()
            await ml_service.initialize()
            
            # Test classification
            result = await ml_service.classify_ticket(
                "Computer won't start",
                "My computer is not turning on when I press the power button"
            )
            
            click.echo("✓ ML service test successful")
            click.echo(f"  Predicted category: {result['predicted_category']}")
            click.echo(f"  Confidence: {result['confidence_score']:.2f}")
            click.echo(f"  Model: {result['model_name']}")
            
        except Exception as e:
            click.echo(f"✗ ML service test failed: {e}")
            raise
        finally:
            await ml_service.cleanup()
    
    asyncio.run(test_ml())


@cli.command()
def backup_db():
    """Backup database to JSON file."""
    click.echo("Creating database backup...")
    
    db = SessionLocal()
    try:
        import json
        from datetime import datetime
        
        # Get all data
        users = db.query(User).all()
        tickets = db.query(Ticket).all()
        
        # Create backup data
        backup_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'users': [user.to_dict() for user in users],
            'tickets': [ticket.to_dict() for ticket in tickets]
        }
        
        # Save to file
        backup_file = Path(f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2, default=str)
        
        click.echo(f"✓ Database backup created: {backup_file}")
        
    except Exception as e:
        click.echo(f"✗ Error creating backup: {e}")
        raise
    finally:
        db.close()


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()