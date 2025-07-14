from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from datetime import timedelta

from ..models.database import get_db
from ..models.user import User
from ..models.user import UserRole as DBUserRole
from ..utils.auth import auth_service, get_current_user
from ..utils.exceptions import unauthorized_error, conflict_error
from ..utils.logging import get_logger
from .schemas import LoginRequest, LoginResponse, UserCreate, UserResponse, TokenResponse

router = APIRouter()
logger = get_logger(__name__)
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return access token.
    """
    logger.info(f"Login attempt for user: {login_request.email}")
    
    # Authenticate user
    user = auth_service.authenticate_user(db, login_request.email, login_request.password)
    if not user:
        logger.warning(f"Failed login attempt for user: {login_request.email}")
        raise unauthorized_error("Invalid email or password")
    
    # Create access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": user.id, "email": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    logger.info(f"Successful login for user: {user.email}")
    
    return LoginResponse(
        token=access_token,
        user=UserResponse.model_validate(user)
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    Logout user (client should remove token).
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Successfully logged out"}


@router.post("/register", response_model=UserResponse)
async def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    """
    logger.info(f"Registration attempt for user: {user_create.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_create.email).first()
    if existing_user:
        logger.warning(f"Registration failed - user already exists: {user_create.email}")
        raise conflict_error("User with this email already exists")
    
    # Create new user
    hashed_password = auth_service.get_password_hash(user_create.password)
    
    # Map role value to database enum - handle both string and enum
    role_value = user_create.role.value if hasattr(user_create.role, 'value') else str(user_create.role)
    logger.info(f"Converting role: {role_value} (type: {type(user_create.role)})")
    
    if role_value == "User":
        db_role = DBUserRole.USER
    elif role_value == "Agent": 
        db_role = DBUserRole.AGENT
    elif role_value == "Admin":
        db_role = DBUserRole.ADMIN
    else:
        db_role = DBUserRole.USER  # Default to USER
    
    db_user = User(
        email=user_create.email,
        name=user_create.name,
        hashed_password=hashed_password,
        role=db_role,
        department=user_create.department,
        phone=user_create.phone,
        bio=user_create.bio,
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"User registered successfully: {db_user.email}")
    
    return UserResponse.model_validate(db_user)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information.
    """
    return UserResponse.model_validate(current_user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token.
    """
    logger.info(f"Token refresh for user: {current_user.email}")
    
    # Create new access token
    access_token_expires = timedelta(minutes=auth_service.access_token_expire_minutes)
    access_token = auth_service.create_access_token(
        data={"sub": current_user.id, "email": current_user.email, "role": current_user.role.value},
        expires_delta=access_token_expires
    )
    
    return TokenResponse(
        access_token=access_token,
        expires_in=auth_service.access_token_expire_minutes * 60
    )


@router.post("/change-password")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change user password.
    """
    logger.info(f"Password change request for user: {current_user.email}")
    
    # Verify current password
    if not auth_service.verify_password(current_password, current_user.hashed_password):
        logger.warning(f"Invalid current password for user: {current_user.email}")
        raise unauthorized_error("Invalid current password")
    
    # Update password
    current_user.hashed_password = auth_service.get_password_hash(new_password)
    db.commit()
    
    logger.info(f"Password changed successfully for user: {current_user.email}")
    
    return {"message": "Password changed successfully"}


@router.post("/forgot-password")
async def forgot_password(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Initiate password reset process.
    """
    logger.info(f"Password reset request for email: {email}")
    
    # Check if user exists
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Don't reveal if user exists or not
        logger.warning(f"Password reset request for non-existent user: {email}")
        return {"message": "If the email exists, password reset instructions have been sent"}
    
    # TODO: Implement email sending logic
    # For now, just log the request
    logger.info(f"Password reset requested for user: {user.email}")
    
    return {"message": "If the email exists, password reset instructions have been sent"}


@router.post("/reset-password")
async def reset_password(
    token: str,
    new_password: str,
    db: Session = Depends(get_db)
):
    """
    Reset password using token.
    """
    # TODO: Implement token verification and password reset
    # For now, return not implemented
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password reset functionality not yet implemented"
    )


@router.get("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    """
    Validate if token is still valid.
    """
    return {
        "valid": True,
        "user": UserResponse.model_validate(current_user)
    }