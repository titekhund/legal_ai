"""
Application configuration management using pydantic-settings
"""
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # LLM API Keys
    gemini_api_key: str = Field(..., description="Google Gemini API key (required)")
    claude_api_key: Optional[str] = Field(None, description="Anthropic Claude API key (optional fallback)")

    # Environment
    environment: str = Field("dev", description="Environment: dev, staging, or prod")

    # Logging
    log_level: str = Field("INFO", description="Logging level")

    # CORS
    cors_origins: str = Field(
        "http://localhost:3000,http://localhost:8000",
        description="Comma-separated list of allowed CORS origins"
    )

    # Tax Code
    tax_code_path: str = Field(
        "data/tax_code/tax_code.pdf",
        description="Path to tax code PDF file"
    )

    # Conversation Settings
    max_conversation_history: int = Field(
        50,
        description="Maximum number of messages to keep in conversation history"
    )

    # Rate Limiting
    rate_limit_requests: int = Field(
        60,
        description="Maximum number of requests allowed per window"
    )
    rate_limit_window: int = Field(
        60,
        description="Rate limit time window in seconds"
    )

    # API Server Settings
    api_host: str = Field("0.0.0.0", description="API server host")
    api_port: int = Field(8000, description="API server port")

    # Database (optional for future use)
    database_url: Optional[str] = Field(None, description="Database connection URL")

    # Vector Database (optional for future use)
    vector_db_type: Optional[str] = Field(None, description="Vector database type (pinecone/weaviate/chroma)")
    pinecone_api_key: Optional[str] = Field(None, description="Pinecone API key")
    pinecone_environment: Optional[str] = Field(None, description="Pinecone environment")
    pinecone_index_name: Optional[str] = Field(None, description="Pinecone index name")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment value"""
        allowed = ["dev", "staging", "prod"]
        if v.lower() not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got {v}")
        return v.lower()

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level"""
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in allowed:
            raise ValueError(f"Log level must be one of {allowed}, got {v}")
        return v_upper

    @field_validator("max_conversation_history")
    @classmethod
    def validate_max_conversation_history(cls, v: int) -> int:
        """Validate conversation history limit"""
        if v < 1:
            raise ValueError("max_conversation_history must be at least 1")
        if v > 1000:
            raise ValueError("max_conversation_history cannot exceed 1000")
        return v

    @field_validator("rate_limit_requests")
    @classmethod
    def validate_rate_limit_requests(cls, v: int) -> int:
        """Validate rate limit requests"""
        if v < 1:
            raise ValueError("rate_limit_requests must be at least 1")
        return v

    @field_validator("rate_limit_window")
    @classmethod
    def validate_rate_limit_window(cls, v: int) -> int:
        """Validate rate limit window"""
        if v < 1:
            raise ValueError("rate_limit_window must be at least 1 second")
        return v

    def get_cors_origins_list(self) -> list[str]:
        """Parse CORS origins from comma-separated string"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    def is_development(self) -> bool:
        """Check if running in development mode"""
        return self.environment == "dev"

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.environment == "prod"


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance

    Uses lru_cache to ensure settings are loaded only once
    and reused across the application.
    """
    return Settings()
