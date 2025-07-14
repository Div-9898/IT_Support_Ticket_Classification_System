# IT Support Ticket Classification System - Backend

This is the complete, production-ready backend for the IT Support Ticket Classification System built with FastAPI, SQLAlchemy, and advanced ML capabilities.

## Features

### Core Features
- **User Management**: Role-based access control (User, Agent, Admin)
- **Ticket Management**: Full CRUD operations with status tracking
- **AI/ML Classification**: Automated ticket categorization using multiple ML models
- **Search & Analytics**: Advanced search with full-text capabilities
- **File Upload**: Secure file handling with processing capabilities
- **Dashboard**: Comprehensive analytics and reporting
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

### Technical Features
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **SQLAlchemy**: Robust ORM with database migrations
- **JWT Authentication**: Secure token-based authentication
- **ML Pipeline**: Multiple ML models (scikit-learn, Transformers, spaCy)
- **Background Tasks**: Asynchronous processing for ML classification
- **Comprehensive Logging**: Structured logging with loguru
- **Error Handling**: Graceful error handling with custom exceptions
- **Rate Limiting**: Built-in request rate limiting
- **CORS Support**: Cross-origin resource sharing configuration
- **File Processing**: Document processing and text extraction

## Project Structure

```
src/it_support_system/
├── api/                    # API endpoints
│   ├── __init__.py
│   ├── auth.py            # Authentication endpoints
│   ├── dashboard.py       # Dashboard analytics
│   ├── schemas.py         # Pydantic schemas
│   ├── search.py          # Search endpoints
│   ├── tickets.py         # Ticket management
│   ├── upload.py          # File upload handling
│   └── users.py           # User management
├── config/                 # Configuration
│   ├── __init__.py
│   └── settings.py        # Application settings
├── models/                 # Database models
│   ├── __init__.py
│   ├── activity.py        # Activity tracking
│   ├── classification.py  # ML classification results
│   ├── database.py        # Database connection
│   ├── ticket.py          # Ticket model
│   └── user.py            # User model
├── services/               # Business logic
│   ├── __init__.py
│   ├── dashboard_service.py  # Dashboard analytics
│   ├── ml_service.py         # ML classification service
│   ├── search_service.py     # Search functionality
│   ├── ticket_service.py     # Ticket business logic
│   └── user_service.py       # User management logic
├── utils/                  # Utilities
│   ├── __init__.py
│   ├── auth.py            # Authentication utilities
│   ├── exceptions.py      # Custom exceptions
│   └── logging.py         # Logging configuration
├── cli.py                 # Command-line interface
└── main.py                # FastAPI application
```

## Installation

### Prerequisites
- Python 3.9-3.11
- PostgreSQL (or SQLite for development)
- Redis (optional, for caching)

### Setup

1. **Create Virtual Environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. **Install Dependencies**
```bash
pip install -r requirements.txt
```

3. **Environment Configuration**
Create `.env` file in the project root:
```bash
# Application
APP_NAME="IT Support Ticket Classification System"
APP_VERSION="1.0.0"
DEBUG=true
ENVIRONMENT=development

# Database
DATABASE_URL=sqlite:///./it_support_tickets.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/it_support_db

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# ML Configuration
ML_MODEL_PATH=./models/
HUGGINGFACE_MODEL_NAME=distilbert-base-uncased
USE_GPU=true
CUDA_VISIBLE_DEVICES=0

# File Upload
UPLOAD_FOLDER=./uploads/
MAX_CONTENT_LENGTH=16777216  # 16MB

# CORS
CORS_ORIGINS=["http://localhost:3000", "http://localhost:8080"]

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/app.log
```

4. **Initialize Database**
```bash
python -m it_support_system.cli init-db
```

5. **Create Admin User**
```bash
python -m it_support_system.cli create-admin
```

6. **Create Sample Data (Optional)**
```bash
python -m it_support_system.cli create-sample-data --count 20
```

## Running the Application

### Development Server
```bash
python -m it_support_system.cli run-server --reload
```

### Production Server
```bash
uvicorn it_support_system.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Docker
```bash
# Build image
docker build -t it-support-backend .

# Run container
docker run -p 8000:8000 -e DATABASE_URL=sqlite:///./data/tickets.db it-support-backend
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/register` - User registration
- `GET /api/v1/auth/me` - Get current user info
- `POST /api/v1/auth/logout` - User logout
- `POST /api/v1/auth/refresh` - Refresh token

### Tickets
- `GET /api/v1/tickets` - List tickets (with pagination & filters)
- `POST /api/v1/tickets` - Create new ticket
- `GET /api/v1/tickets/{id}` - Get ticket details
- `PUT /api/v1/tickets/{id}` - Update ticket
- `DELETE /api/v1/tickets/{id}` - Delete ticket
- `POST /api/v1/tickets/{id}/classify` - Classify ticket
- `POST /api/v1/tickets/{id}/assign` - Assign ticket
- `POST /api/v1/tickets/{id}/resolve` - Resolve ticket
- `POST /api/v1/tickets/{id}/close` - Close ticket

### Users
- `GET /api/v1/users` - List users
- `POST /api/v1/users` - Create user (admin only)
- `GET /api/v1/users/{id}` - Get user details
- `PUT /api/v1/users/{id}` - Update user
- `DELETE /api/v1/users/{id}` - Delete user

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/performance/agent` - Agent performance metrics
- `GET /api/v1/dashboard/classification/metrics` - ML classification metrics
- `GET /api/v1/dashboard/workload/distribution` - Workload distribution

### Search
- `GET /api/v1/search/tickets` - Search tickets
- `GET /api/v1/search/users` - Search users
- `GET /api/v1/search/suggestions` - Get search suggestions
- `POST /api/v1/search/advanced` - Advanced search

### File Upload
- `POST /api/v1/upload` - Upload file
- `POST /api/v1/upload/multiple` - Upload multiple files
- `GET /api/v1/upload/files/{filename}` - Download file
- `DELETE /api/v1/upload/files/{filename}` - Delete file

### Health & Monitoring
- `GET /health` - Health check
- `GET /` - API information
- `GET /docs` - Swagger documentation
- `GET /redoc` - ReDoc documentation

## ML Classification

The system includes a sophisticated ML pipeline with multiple models:

### Supported Models
- **Traditional ML**: Naive Bayes, Random Forest, SVM with TF-IDF
- **Transformers**: BERT-based models via HuggingFace
- **spaCy**: Advanced NLP preprocessing
- **Ensemble**: Combines multiple model predictions

### Categories
- Hardware
- Software
- Network
- Security
- Access
- Email
- Other

### Features
- Automatic text preprocessing
- Confidence scoring
- Suggested actions
- Sentiment analysis
- Urgency detection
- Processing time tracking
- Model performance metrics

### Training Models
```bash
python -m it_support_system.cli train-ml-models
```

## Configuration

### Environment Variables
All configuration is handled through environment variables defined in `settings.py`:

- **Application Settings**: Name, version, debug mode
- **Database**: Connection URL, echo settings
- **Security**: JWT secret, token expiration
- **ML**: Model paths, GPU settings, batch sizes
- **File Upload**: Upload folder, size limits, allowed extensions
- **Logging**: Level, file output, format
- **CORS**: Allowed origins for cross-origin requests

### Database Configuration
Supports multiple database backends:
- **SQLite**: For development and testing
- **PostgreSQL**: Recommended for production
- **MySQL**: Alternative production database

### ML Configuration
- **CPU/GPU**: Automatic detection with fallback
- **Model Selection**: Configurable model selection
- **Batch Processing**: Optimized for performance
- **Caching**: Model caching for faster inference

## Database Schema

### Users Table
- User authentication and profile information
- Role-based access control
- Department and contact information
- Activity tracking

### Tickets Table
- Comprehensive ticket information
- Status and priority tracking
- Assignment and resolution tracking
- Classification results
- Customer satisfaction scores

### Classifications Table
- ML model predictions
- Confidence scores
- Processing metadata
- Validation feedback

### Activities Table
- Complete audit trail
- Action tracking
- Change history
- User attribution

## Security Features

### Authentication
- JWT token-based authentication
- Password hashing with bcrypt
- Token refresh mechanism
- Session management

### Authorization
- Role-based access control
- Resource-level permissions
- Action-specific authorization
- Admin-only operations

### Data Protection
- Input validation with Pydantic
- SQL injection prevention
- XSS protection
- File upload security
- Path traversal protection

## Performance Optimization

### Database
- Connection pooling
- Query optimization
- Lazy loading
- Pagination

### ML Pipeline
- Model caching
- Batch processing
- GPU acceleration
- Async processing

### API
- Response compression
- Caching headers
- Rate limiting
- Background tasks

## Monitoring & Logging

### Logging
- Structured logging with loguru
- Request/response logging
- Error tracking
- Performance monitoring

### Health Checks
- Database connectivity
- ML service status
- Resource utilization
- System health indicators

### Metrics
- Request metrics
- Response times
- Error rates
- ML model performance

## Testing

### Unit Tests
```bash
pytest tests/unit/
```

### Integration Tests
```bash
pytest tests/integration/
```

### End-to-End Tests
```bash
pytest tests/e2e/
```

### Coverage Report
```bash
pytest --cov=src --cov-report=html
```

## Deployment

### Docker Deployment
```bash
docker-compose up -d
```

### Kubernetes
```bash
kubectl apply -f k8s/
```

### Environment-Specific Configurations
- Development: Debug mode, SQLite, verbose logging
- Staging: Similar to production, test data
- Production: PostgreSQL, optimized settings, monitoring

## API Documentation

### Interactive Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### API Schema
- OpenAPI 3.0 specification
- Automatic schema generation
- Request/response examples
- Error code documentation

## CLI Commands

The system includes a comprehensive CLI for administration:

```bash
# Database operations
python -m it_support_system.cli init-db
python -m it_support_system.cli drop-db --confirm
python -m it_support_system.cli backup-db

# User management
python -m it_support_system.cli create-admin
python -m it_support_system.cli create-sample-data

# ML operations
python -m it_support_system.cli train-ml-models
python -m it_support_system.cli test-ml-service

# Server operations
python -m it_support_system.cli run-server
python -m it_support_system.cli check-config
```

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL in environment
   - Verify database server is running
   - Check connection permissions

2. **ML Model Loading Issues**
   - Ensure CUDA is properly installed for GPU
   - Check model file permissions
   - Verify sufficient memory

3. **File Upload Problems**
   - Check upload folder permissions
   - Verify file size limits
   - Check allowed file extensions

4. **Authentication Issues**
   - Verify JWT secret key
   - Check token expiration settings
   - Validate user credentials

### Performance Issues
- Enable database query logging
- Check ML model performance metrics
- Monitor memory usage
- Review API response times

## Contributing

1. Fork the repository
2. Create a feature branch
3. Write tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For technical support or questions:
- Check the documentation
- Review the API endpoints
- Use the CLI help commands
- Check the logs for error details

---

This backend provides a complete, production-ready foundation for the IT Support Ticket Classification System with enterprise-grade features, security, and scalability.