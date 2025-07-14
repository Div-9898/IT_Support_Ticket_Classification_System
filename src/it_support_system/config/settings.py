"""
Configuration settings for the IT Support Ticket Classification System.

This module handles loading and validation of environment variables using pydantic.
"""

import os
from typing import List, Optional
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application Configuration
    app_name: str = Field(default="IT Support Ticket Classification System", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")

    # Server Configuration
    host: str = Field(default="localhost", env="HOST")
    port: int = Field(default=8000, env="PORT")
    workers: int = Field(default=4, env="WORKERS")
    reload: bool = Field(default=False, env="RELOAD")

    # Database Configuration
    database_url: str = Field(default="sqlite:///./it_support_tickets.db", env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")

    # Machine Learning Configuration
    ml_model_path: str = Field(default="./models/", env="ML_MODEL_PATH")
    huggingface_model_name: str = Field(default="distilbert-base-uncased", env="HUGGINGFACE_MODEL_NAME")
    max_sequence_length: int = Field(default=512, env="MAX_SEQUENCE_LENGTH")
    batch_size: int = Field(default=32, env="BATCH_SIZE")
    learning_rate: float = Field(default=2e-5, env="LEARNING_RATE")
    epochs: int = Field(default=3, env="EPOCHS")

    # CUDA Configuration
    cuda_visible_devices: str = Field(default="0", env="CUDA_VISIBLE_DEVICES")
    use_gpu: bool = Field(default=True, env="USE_GPU")
    mixed_precision: bool = Field(default=True, env="MIXED_PRECISION")

    # Security Configuration
    secret_key: str = Field(default="change-this-secret-key", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    algorithm: str = Field(default="HS256", env="ALGORITHM")

    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    log_file: str = Field(default="./logs/app.log", env="LOG_FILE")
    enable_file_logging: bool = Field(default=True, env="ENABLE_FILE_LOGGING")

    # API Configuration
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    enable_docs: bool = Field(default=True, env="ENABLE_DOCS")
    docs_url: str = Field(default="/docs", env="DOCS_URL")
    redoc_url: str = Field(default="/redoc", env="REDOC_URL")

    # Feature Flags
    enable_async_processing: bool = Field(default=True, env="ENABLE_ASYNC_PROCESSING")
    enable_caching: bool = Field(default=True, env="ENABLE_CACHING")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_rate_limiting: bool = Field(default=True, env="ENABLE_RATE_LIMITING")

    # External Services
    smtp_host: str = Field(default="smtp.gmail.com", env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")

    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")

    # Data Processing
    data_preprocessing_batch_size: int = Field(default=1000, env="DATA_PREPROCESSING_BATCH_SIZE")
    text_preprocessing_workers: int = Field(default=4, env="TEXT_PREPROCESSING_WORKERS")
    feature_extraction_workers: int = Field(default=2, env="FEATURE_EXTRACTION_WORKERS")

    # Model Training
    train_test_split: float = Field(default=0.8, env="TRAIN_TEST_SPLIT")
    validation_split: float = Field(default=0.1, env="VALIDATION_SPLIT")
    random_seed: int = Field(default=42, env="RANDOM_SEED")
    model_save_interval: int = Field(default=1000, env="MODEL_SAVE_INTERVAL")
    early_stopping_patience: int = Field(default=5, env="EARLY_STOPPING_PATIENCE")

    # Cache Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")
    cache_prefix: str = Field(default="it_support_", env="CACHE_PREFIX")

    # File Storage
    upload_folder: str = Field(default="./uploads/", env="UPLOAD_FOLDER")
    max_content_length: int = Field(default=16777216, env="MAX_CONTENT_LENGTH")  # 16MB
    allowed_extensions: List[str] = Field(
        default=[".txt", ".csv", ".json", ".xlsx"],
        env="ALLOWED_EXTENSIONS"
    )

    @field_validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_environments = ["development", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of {valid_environments}")
        return v.lower()

    @field_validator("train_test_split", "validation_split")
    def validate_split_ratios(cls, v):
        """Validate split ratios are between 0 and 1."""
        if not 0 < v < 1:
            raise ValueError("Split ratios must be between 0 and 1")
        return v

    @field_validator("ml_model_path", "upload_folder", "log_file")
    def ensure_directories_exist(cls, v):
        """Ensure directories exist for file paths."""
        path = Path(v)
        if path.suffix:  # It's a file path
            path.parent.mkdir(parents=True, exist_ok=True)
        else:  # It's a directory path
            path.mkdir(parents=True, exist_ok=True)
        return v

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


# Global settings instance
settings = get_settings()
