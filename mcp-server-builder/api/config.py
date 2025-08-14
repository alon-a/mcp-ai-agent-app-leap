"""Configuration settings for the FastAPI application."""

import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # API Configuration
    api_title: str = "MCP Server Builder API"
    api_description: str = "REST API for creating and managing MCP server projects"
    api_version: str = "1.0.0"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False
    log_level: str = "info"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Project Configuration
    default_output_directory: str = "/tmp/mcp_projects"
    max_concurrent_projects: int = 10
    project_timeout_minutes: int = 30
    
    # Logging Configuration
    log_file: str = None
    enable_real_time_logging: bool = True
    
    class Config:
        env_prefix = "MCP_API_"
        env_file = ".env"


# Global settings instance
settings = Settings()