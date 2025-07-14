from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from pathlib import Path
import shutil
import uuid
import mimetypes
from datetime import datetime
from typing import List

from ..models.database import get_db
from ..models.user import User
from ..utils.auth import get_current_user
from ..utils.exceptions import validation_error, internal_server_error
from ..utils.logging import get_logger
from ..config.settings import settings
from .schemas import FileUploadResponse, ApiResponse

router = APIRouter()
logger = get_logger(__name__)

# Ensure upload directory exists
UPLOAD_DIR = Path(settings.upload_folder)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if not filename:
        return False
    
    file_ext = Path(filename).suffix.lower()
    return file_ext in settings.allowed_extensions


def get_file_size(file: UploadFile) -> int:
    """Get file size."""
    file.file.seek(0, 2)  # Seek to end
    size = file.file.tell()
    file.file.seek(0)  # Seek back to beginning
    return size


def generate_unique_filename(original_filename: str) -> str:
    """Generate unique filename while preserving extension."""
    file_ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4()}{file_ext}"
    return unique_name


def save_file(file: UploadFile, filename: str) -> Path:
    """Save uploaded file to disk."""
    file_path = UPLOAD_DIR / filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        logger.info(f"File saved: {file_path}")
        return file_path
    
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        raise internal_server_error("Failed to save file")


@router.post("/", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a single file."""
    logger.info(f"File upload request from user: {current_user.email}")
    
    # Validate file
    if not file.filename:
        raise validation_error("No file selected")
    
    if not is_allowed_file(file.filename):
        raise validation_error(
            f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
        )
    
    # Check file size
    file_size = get_file_size(file)
    if file_size > settings.max_content_length:
        raise validation_error(
            f"File too large. Maximum size: {settings.max_content_length / 1024 / 1024:.1f} MB"
        )
    
    if file_size == 0:
        raise validation_error("Empty file not allowed")
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Save file
    file_path = save_file(file, unique_filename)
    
    # Get content type
    content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
    
    # Create response
    file_url = f"/api/v1/upload/files/{unique_filename}"
    
    logger.info(f"File uploaded successfully: {file.filename} -> {unique_filename}")
    
    return FileUploadResponse(
        url=file_url,
        filename=file.filename,
        size=file_size,
        content_type=content_type,
        upload_timestamp=datetime.utcnow()
    )


@router.post("/multiple", response_model=List[FileUploadResponse])
async def upload_multiple_files(
    files: List[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload multiple files."""
    logger.info(f"Multiple file upload request from user: {current_user.email}")
    
    if len(files) > 10:  # Limit to 10 files
        raise validation_error("Maximum 10 files allowed per upload")
    
    uploaded_files = []
    
    for file in files:
        try:
            # Validate file
            if not file.filename:
                logger.warning(f"Skipping file with no filename")
                continue
            
            if not is_allowed_file(file.filename):
                logger.warning(f"Skipping file with invalid extension: {file.filename}")
                continue
            
            # Check file size
            file_size = get_file_size(file)
            if file_size > settings.max_content_length:
                logger.warning(f"Skipping file too large: {file.filename}")
                continue
            
            if file_size == 0:
                logger.warning(f"Skipping empty file: {file.filename}")
                continue
            
            # Generate unique filename
            unique_filename = generate_unique_filename(file.filename)
            
            # Save file
            file_path = save_file(file, unique_filename)
            
            # Get content type
            content_type = file.content_type or mimetypes.guess_type(file.filename)[0] or "application/octet-stream"
            
            # Create response
            file_url = f"/api/v1/upload/files/{unique_filename}"
            
            uploaded_files.append(FileUploadResponse(
                url=file_url,
                filename=file.filename,
                size=file_size,
                content_type=content_type,
                upload_timestamp=datetime.utcnow()
            ))
            
            logger.info(f"File uploaded successfully: {file.filename} -> {unique_filename}")
            
        except Exception as e:
            logger.error(f"Failed to upload file {file.filename}: {e}")
            # Continue with other files
    
    return uploaded_files


@router.get("/files/{filename}")
async def get_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Get/download a uploaded file."""
    logger.info(f"File download request: {filename} by user: {current_user.email}")
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Security check: ensure file is within upload directory
    try:
        file_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get content type
    content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
    
    # Return file
    from fastapi.responses import FileResponse
    return FileResponse(
        path=str(file_path),
        media_type=content_type,
        filename=filename
    )


@router.delete("/files/{filename}")
async def delete_file(
    filename: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an uploaded file."""
    logger.info(f"File deletion request: {filename} by user: {current_user.email}")
    
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Security check: ensure file is within upload directory
    try:
        file_path.resolve().relative_to(UPLOAD_DIR.resolve())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        file_path.unlink()
        logger.info(f"File deleted successfully: {filename}")
        
        return ApiResponse(
            data={"filename": filename},
            message="File deleted successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to delete file {filename}: {e}")
        raise internal_server_error("Failed to delete file")


@router.get("/info")
async def get_upload_info(
    current_user: User = Depends(get_current_user)
):
    """Get upload configuration and limits."""
    return ApiResponse(
        data={
            "max_file_size": settings.max_content_length,
            "max_file_size_mb": settings.max_content_length / 1024 / 1024,
            "allowed_extensions": settings.allowed_extensions,
            "max_files_per_upload": 10,
            "upload_folder": str(UPLOAD_DIR)
        },
        message="Upload configuration retrieved successfully"
    )


@router.get("/validate")
async def validate_file_info(
    filename: str,
    size: int,
    current_user: User = Depends(get_current_user)
):
    """Validate file before upload."""
    logger.info(f"File validation request: {filename} ({size} bytes)")
    
    errors = []
    
    # Check filename
    if not filename:
        errors.append("Filename is required")
    elif not is_allowed_file(filename):
        errors.append(f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}")
    
    # Check size
    if size <= 0:
        errors.append("File size must be greater than 0")
    elif size > settings.max_content_length:
        errors.append(f"File too large. Maximum size: {settings.max_content_length / 1024 / 1024:.1f} MB")
    
    is_valid = len(errors) == 0
    
    return ApiResponse(
        data={
            "valid": is_valid,
            "errors": errors,
            "filename": filename,
            "size": size,
            "size_mb": size / 1024 / 1024
        },
        message="File validation completed"
    )


@router.post("/process-document")
async def process_document(
    file: UploadFile = File(...),
    extract_text: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process uploaded document and extract text/metadata."""
    logger.info(f"Document processing request from user: {current_user.email}")
    
    # Validate file
    if not file.filename:
        raise validation_error("No file selected")
    
    if not is_allowed_file(file.filename):
        raise validation_error(
            f"File type not allowed. Allowed types: {', '.join(settings.allowed_extensions)}"
        )
    
    # Check file size
    file_size = get_file_size(file)
    if file_size > settings.max_content_length:
        raise validation_error(
            f"File too large. Maximum size: {settings.max_content_length / 1024 / 1024:.1f} MB"
        )
    
    # Generate unique filename
    unique_filename = generate_unique_filename(file.filename)
    
    # Save file
    file_path = save_file(file, unique_filename)
    
    # Process document
    try:
        processing_result = {
            "filename": file.filename,
            "size": file_size,
            "content_type": file.content_type,
            "file_url": f"/api/v1/upload/files/{unique_filename}",
            "processed_at": datetime.utcnow().isoformat()
        }
        
        # Extract text based on file type
        if extract_text:
            text_content = ""
            
            if file.content_type == "text/plain":
                # Read plain text
                with open(file_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
            
            elif file.content_type == "application/json":
                # Read JSON
                import json
                with open(file_path, 'r', encoding='utf-8') as f:
                    json_data = json.load(f)
                    text_content = json.dumps(json_data, indent=2)
            
            elif file.content_type in ["text/csv", "application/csv"]:
                # Read CSV
                import csv
                with open(file_path, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    text_content = '\n'.join([','.join(row) for row in csv_reader])
            
            # Add more document types as needed (PDF, DOCX, etc.)
            
            processing_result["text_content"] = text_content
            processing_result["text_length"] = len(text_content)
            processing_result["word_count"] = len(text_content.split()) if text_content else 0
        
        logger.info(f"Document processed successfully: {file.filename}")
        
        return ApiResponse(
            data=processing_result,
            message="Document processed successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to process document {file.filename}: {e}")
        # Clean up file
        if file_path.exists():
            file_path.unlink()
        raise internal_server_error("Failed to process document")


@router.get("/stats")
async def get_upload_stats(
    current_user: User = Depends(get_current_user)
):
    """Get upload statistics."""
    logger.info("Getting upload statistics")
    
    try:
        # Get directory stats
        total_files = len(list(UPLOAD_DIR.glob("*")))
        total_size = sum(f.stat().st_size for f in UPLOAD_DIR.glob("*") if f.is_file())
        
        # Get file type distribution
        file_types = {}
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return ApiResponse(
            data={
                "total_files": total_files,
                "total_size": total_size,
                "total_size_mb": total_size / 1024 / 1024,
                "file_type_distribution": file_types,
                "upload_directory": str(UPLOAD_DIR)
            },
            message="Upload statistics retrieved successfully"
        )
    
    except Exception as e:
        logger.error(f"Failed to get upload stats: {e}")
        raise internal_server_error("Failed to get upload statistics")