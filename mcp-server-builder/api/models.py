"""Pydantic models for API request/response validation."""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class CreateProjectRequest(BaseModel):
    """Request model for creating a new project."""
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    template: str = Field(..., description="Template identifier")
    output_directory: Optional[str] = Field(None, description="Output directory path")
    custom_settings: Dict[str, Any] = Field(default_factory=dict, description="Custom template settings")
    environment_variables: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    additional_dependencies: List[str] = Field(default_factory=list, description="Additional dependencies")
    
    @validator('name')
    def validate_name(cls, v):
        """Validate project name."""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Project name must contain only alphanumeric characters, hyphens, and underscores')
        return v


class ProjectResponse(BaseModel):
    """Response model for project creation."""
    project_id: str = Field(..., description="Unique project identifier")
    status: str = Field(..., description="Current project status")
    message: str = Field(..., description="Status message")


class ProjectStatusResponse(BaseModel):
    """Response model for project status."""
    project_id: str = Field(..., description="Unique project identifier")
    status: str = Field(..., description="Current project status")
    current_phase: str = Field(..., description="Current build phase")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    errors: List[str] = Field(default_factory=list, description="List of errors")


class ProjectSummary(BaseModel):
    """Summary information for a project."""
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    status: str = Field(..., description="Current project status")
    template_id: str = Field(..., description="Template identifier used")
    created_at: datetime = Field(..., description="Project creation timestamp")


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""
    projects: List[ProjectSummary] = Field(..., description="List of project summaries")


class ProjectDetailsResponse(BaseModel):
    """Response model for detailed project information."""
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    template_id: str = Field(..., description="Template identifier used")
    status: str = Field(..., description="Current project status")
    current_phase: str = Field(..., description="Current build phase")
    progress_percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    created_at: datetime = Field(..., description="Project creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    output_directory: str = Field(..., description="Output directory path")
    errors: List[str] = Field(default_factory=list, description="List of errors")
    created_files: List[str] = Field(default_factory=list, description="List of created files")


class ProgressUpdate(BaseModel):
    """Model for progress update messages."""
    project_id: str = Field(..., description="Unique project identifier")
    event_type: str = Field(..., description="Type of progress event")
    phase: str = Field(..., description="Current build phase")
    percentage: float = Field(..., ge=0, le=100, description="Progress percentage")
    message: str = Field(..., description="Progress message")
    timestamp: datetime = Field(..., description="Event timestamp")
    error: Optional[str] = Field(None, description="Error message if any")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional event details")


class ValidationRequest(BaseModel):
    """Request model for project validation."""
    validation_type: str = Field(
        default="comprehensive",
        description="Type of validation to run",
        regex="^(startup|protocol|functionality|comprehensive)$"
    )
    custom_tests: List[str] = Field(
        default_factory=list,
        description="List of custom test scenarios to run"
    )


class ValidationResponse(BaseModel):
    """Response model for validation results."""
    project_id: str = Field(..., description="Unique project identifier")
    validation_type: str = Field(..., description="Type of validation performed")
    success: bool = Field(..., description="Overall validation success")
    results: Dict[str, Any] = Field(..., description="Detailed validation results")
    errors: List[str] = Field(default_factory=list, description="List of validation errors")
    warnings: List[str] = Field(default_factory=list, description="List of validation warnings")
    execution_time: float = Field(..., description="Validation execution time in seconds")
    timestamp: datetime = Field(..., description="Validation timestamp")


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(..., description="Service health status")
    service: str = Field(..., description="Service name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")