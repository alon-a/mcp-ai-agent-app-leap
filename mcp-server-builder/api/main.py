"""FastAPI wrapper for MCP Server Builder.

This module provides a REST API interface for the MCP Server Builder,
enabling web applications to create and manage MCP server projects.
"""

import os
import uuid
import asyncio
from typing import Dict, Any, Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .models import (
    CreateProjectRequest, ProjectResponse, ProjectStatusResponse,
    ProjectListResponse, ProjectDetailsResponse, ProgressUpdate,
    ValidationRequest, ValidationResponse, ErrorResponse
)
from .services import ProjectService
from .websocket_manager import EnhancedWebSocketManager
from .config import settings


# Global instances
project_service: Optional[ProjectService] = None
websocket_manager: Optional[EnhancedWebSocketManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global project_service, websocket_manager
    
    # Initialize services
    websocket_manager = EnhancedWebSocketManager(
        ping_interval=30,
        connection_timeout=300
    )
    project_service = ProjectService(websocket_manager)
    
    yield
    
    # Cleanup
    if websocket_manager:
        await websocket_manager.cleanup()


# Create FastAPI application
app = FastAPI(
    title="MCP Server Builder API",
    description="REST API for creating and managing MCP server projects",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-server-builder-api"}


@app.get("/api/v1/websocket/stats")
async def websocket_stats():
    """Get WebSocket connection statistics."""
    if websocket_manager:
        return websocket_manager.get_connection_stats()
    return {"error": "WebSocket manager not initialized"}


@app.post("/api/v1/projects", response_model=ProjectResponse)
async def create_project(
    request: CreateProjectRequest,
    background_tasks: BackgroundTasks
) -> ProjectResponse:
    """Create a new MCP server project.
    
    Args:
        request: Project creation request
        background_tasks: FastAPI background tasks
        
    Returns:
        ProjectResponse with project ID and initial status
    """
    try:
        project_id = str(uuid.uuid4())
        
        # Start project creation in background
        background_tasks.add_task(
            project_service.create_project_async,
            project_id,
            request
        )
        
        return ProjectResponse(
            project_id=project_id,
            status="initiated",
            message="Project creation started"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initiate project creation: {str(e)}"
        )


@app.get("/api/v1/projects/{project_id}/status", response_model=ProjectStatusResponse)
async def get_project_status(project_id: str) -> ProjectStatusResponse:
    """Get the current status of a project.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        ProjectStatusResponse with current status and progress
    """
    try:
        status_info = project_service.get_project_status(project_id)
        if not status_info:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        return ProjectStatusResponse(**status_info)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project status: {str(e)}"
        )


@app.get("/api/v1/projects/{project_id}/details", response_model=ProjectDetailsResponse)
async def get_project_details(project_id: str) -> ProjectDetailsResponse:
    """Get detailed information about a project.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        ProjectDetailsResponse with comprehensive project information
    """
    try:
        details = project_service.get_project_details(project_id)
        if not details:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        return ProjectDetailsResponse(**details)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project details: {str(e)}"
        )


@app.get("/api/v1/projects", response_model=ProjectListResponse)
async def list_projects(
    status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
) -> ProjectListResponse:
    """List all tracked projects with optional filtering and pagination.
    
    Args:
        status: Optional status filter (created, downloading, building, completed, failed)
        limit: Maximum number of projects to return (default: 100)
        offset: Number of projects to skip (default: 0)
    
    Returns:
        ProjectListResponse with list of project summaries
    """
    try:
        projects = project_service.list_projects(
            status_filter=status,
            limit=limit,
            offset=offset
        )
        return ProjectListResponse(projects=projects)
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list projects: {str(e)}"
        )


@app.delete("/api/v1/projects/{project_id}")
async def cancel_project(project_id: str, force: bool = False) -> JSONResponse:
    """Cancel and cleanup a project.
    
    Args:
        project_id: Unique project identifier
        force: Force cancellation even if project is in progress
        
    Returns:
        JSON response with cancellation status
    """
    try:
        success = project_service.cancel_project(project_id, force=force)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or cannot be cancelled"
            )
        
        return JSONResponse(
            content={"message": f"Project {project_id} cancelled successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel project: {str(e)}"
        )


@app.post("/api/v1/projects/{project_id}/pause")
async def pause_project(project_id: str) -> JSONResponse:
    """Pause a running project.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        JSON response with pause status
    """
    try:
        success = project_service.pause_project(project_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or cannot be paused"
            )
        
        return JSONResponse(
            content={"message": f"Project {project_id} paused successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to pause project: {str(e)}"
        )


@app.post("/api/v1/projects/{project_id}/resume")
async def resume_project(project_id: str) -> JSONResponse:
    """Resume a paused project.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        JSON response with resume status
    """
    try:
        success = project_service.resume_project(project_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or cannot be resumed"
            )
        
        return JSONResponse(
            content={"message": f"Project {project_id} resumed successfully"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resume project: {str(e)}"
        )


@app.get("/api/v1/projects/{project_id}/logs")
async def get_project_logs(
    project_id: str,
    level: str = "info",
    limit: int = 100,
    offset: int = 0
) -> JSONResponse:
    """Get project logs.
    
    Args:
        project_id: Unique project identifier
        level: Log level filter (debug, info, warning, error)
        limit: Maximum number of log entries to return
        offset: Number of log entries to skip
        
    Returns:
        JSON response with project logs
    """
    try:
        logs = project_service.get_project_logs(
            project_id,
            level=level,
            limit=limit,
            offset=offset
        )
        
        if logs is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        return JSONResponse(content={"logs": logs})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get project logs: {str(e)}"
        )


@app.get("/api/v1/projects/{project_id}/files")
async def list_project_files(project_id: str) -> JSONResponse:
    """List files created by a project.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        JSON response with list of project files
    """
    try:
        files = project_service.list_project_files(project_id)
        if files is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        return JSONResponse(content={"files": files})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list project files: {str(e)}"
        )


@app.get("/api/v1/projects/{project_id}/download")
async def download_project(project_id: str):
    """Download project files as a ZIP archive.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        ZIP file download response
    """
    try:
        zip_file = await project_service.create_project_archive(project_id)
        if not zip_file:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or not ready for download"
            )
        
        from fastapi.responses import FileResponse
        return FileResponse(
            zip_file,
            media_type="application/zip",
            filename=f"project_{project_id}.zip"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download project: {str(e)}"
        )


@app.post("/api/v1/projects/{project_id}/validate", response_model=ValidationResponse)
async def validate_project(
    project_id: str,
    request: ValidationRequest
) -> ValidationResponse:
    """Run validation tests on a project.
    
    Args:
        project_id: Unique project identifier
        request: Validation request parameters
        
    Returns:
        ValidationResponse with validation results
    """
    try:
        result = await project_service.validate_project(project_id, request)
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or not ready for validation"
            )
        
        return ValidationResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate project: {str(e)}"
        )


@app.get("/api/v1/projects/{project_id}/validation-history")
async def get_validation_history(project_id: str) -> JSONResponse:
    """Get validation history for a project.
    
    Args:
        project_id: Unique project identifier
        
    Returns:
        JSON response with validation history
    """
    try:
        history = project_service.get_validation_history(project_id)
        if history is None:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found"
            )
        
        return JSONResponse(content={"validation_history": history})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get validation history: {str(e)}"
        )


@app.post("/api/v1/projects/{project_id}/test-scenarios")
async def run_custom_test_scenarios(
    project_id: str,
    scenarios: List[Dict[str, Any]]
) -> JSONResponse:
    """Run custom test scenarios on a project.
    
    Args:
        project_id: Unique project identifier
        scenarios: List of custom test scenarios
        
    Returns:
        JSON response with test results
    """
    try:
        results = await project_service.run_custom_test_scenarios(project_id, scenarios)
        if not results:
            raise HTTPException(
                status_code=404,
                detail=f"Project {project_id} not found or not ready for testing"
            )
        
        return JSONResponse(content={"test_results": results})
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to run custom test scenarios: {str(e)}"
        )


@app.get("/api/v1/validation/templates")
async def list_validation_templates() -> JSONResponse:
    """List available validation templates and test scenarios.
    
    Returns:
        JSON response with available validation templates
    """
    try:
        templates = project_service.list_validation_templates()
        return JSONResponse(content={"templates": templates})
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list validation templates: {str(e)}"
        )


@app.websocket("/api/v1/projects/{project_id}/progress")
async def websocket_progress(websocket: WebSocket, project_id: str, user_id: Optional[str] = None):
    """WebSocket endpoint for real-time progress updates.
    
    Args:
        websocket: WebSocket connection
        project_id: Unique project identifier
        user_id: Optional user identifier for session isolation
    """
    connection_id = None
    
    try:
        connection_id = await websocket_manager.connect(websocket, project_id, user_id)
        
        while True:
            # Handle incoming messages from client
            data = await websocket.receive_text()
            await websocket_manager.handle_client_message(connection_id, data)
            
    except WebSocketDisconnect:
        if connection_id:
            await websocket_manager.disconnect(connection_id, "client_disconnect")
    except Exception as e:
        if connection_id:
            await websocket_manager.disconnect(connection_id, f"error: {str(e)}")
        else:
            try:
                await websocket.close(code=1011, reason=f"Connection error: {str(e)}")
            except:
                pass


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            message=str(exc),
            details={"type": type(exc).__name__}
        ).dict()
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    )