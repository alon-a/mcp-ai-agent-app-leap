"""Service layer for the FastAPI wrapper."""

import asyncio
import json
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
from pathlib import Path

from fastapi import WebSocket

import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from .models import CreateProjectRequest, ValidationRequest, ProgressUpdate
from .websocket_manager import EnhancedWebSocketManager
from .progress_integration import ProgressIntegration
from .validation_service import ValidationService
from managers.project_manager import ProjectManagerImpl
from managers.progress_tracker import LogLevel, ProgressEvent
from managers.validation_engine import MCPValidationEngine


# Use the enhanced WebSocket manager as an alias for backward compatibility
WebSocketManager = EnhancedWebSocketManager


class LegacyWebSocketManager:
    """Manages WebSocket connections for real-time progress updates."""
    
    def __init__(self):
        # Map project_id -> set of websockets
        self.connections: Dict[str, Set[WebSocket]] = {}
        
    async def connect(self, websocket: WebSocket, project_id: str):
        """Accept a WebSocket connection for a project."""
        await websocket.accept()
        
        if project_id not in self.connections:
            self.connections[project_id] = set()
        
        self.connections[project_id].add(websocket)
        
        # Send initial connection confirmation
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "project_id": project_id,
            "timestamp": datetime.now().isoformat()
        }))
    
    def disconnect(self, websocket: WebSocket, project_id: str):
        """Remove a WebSocket connection."""
        if project_id in self.connections:
            self.connections[project_id].discard(websocket)
            
            # Clean up empty project connection sets
            if not self.connections[project_id]:
                del self.connections[project_id]
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a project."""
        if project_id not in self.connections:
            return
        
        # Create a copy of the set to avoid modification during iteration
        connections = self.connections[project_id].copy()
        
        for websocket in connections:
            try:
                await websocket.send_text(json.dumps(message))
            except Exception:
                # Remove failed connections
                self.disconnect(websocket, project_id)
    
    async def cleanup(self):
        """Clean up all connections."""
        for project_id in list(self.connections.keys()):
            connections = self.connections[project_id].copy()
            for websocket in connections:
                try:
                    await websocket.close()
                except Exception:
                    pass
        
        self.connections.clear()


class ProjectService:
    """Service for managing MCP server projects."""
    
    def __init__(self, websocket_manager: EnhancedWebSocketManager):
        self.websocket_manager = websocket_manager
        self.validation_engine = MCPValidationEngine()
        self.validation_service = ValidationService()
        
        # Initialize progress integration
        self.progress_integration = ProgressIntegration(websocket_manager)
        
        # Initialize project manager with progress callback
        self.project_manager = ProjectManagerImpl(
            progress_callback=self._handle_progress_update,
            error_callback=self._handle_error_update,
            log_level=LogLevel.INFO
        )
        
        # Register progress event callback with the project manager
        self.project_manager.add_progress_callback(
            self.progress_integration.create_progress_callback()
        )
    
    async def create_project_async(self, project_id: str, request: CreateProjectRequest):
        """Create a project asynchronously in a background task."""
        try:
            # Prepare configuration
            config = {
                'output_directory': request.output_directory or str(Path.cwd()),
                'custom_settings': request.custom_settings,
                'environment_variables': request.environment_variables,
                'additional_dependencies': request.additional_dependencies
            }
            
            # Send initial progress update
            await self._send_progress_update(project_id, {
                "type": "project_started",
                "project_id": project_id,
                "phase": "initialization",
                "percentage": 0.0,
                "message": "Project creation started",
                "timestamp": datetime.now().isoformat()
            })
            
            # Run project creation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self.project_manager.create_project,
                request.name,
                request.template,
                config
            )
            
            # Send completion update
            if result.success:
                await self._send_progress_update(project_id, {
                    "type": "project_completed",
                    "project_id": project_id,
                    "phase": "completed",
                    "percentage": 100.0,
                    "message": "Project creation completed successfully",
                    "timestamp": datetime.now().isoformat(),
                    "project_path": result.project_path,
                    "created_files": result.created_files
                })
            else:
                await self._send_progress_update(project_id, {
                    "type": "project_failed",
                    "project_id": project_id,
                    "phase": "failed",
                    "percentage": 0.0,
                    "message": "Project creation failed",
                    "timestamp": datetime.now().isoformat(),
                    "errors": result.errors
                })
            
        except Exception as e:
            # Send error update
            await self._send_progress_update(project_id, {
                "type": "project_error",
                "project_id": project_id,
                "phase": "error",
                "percentage": 0.0,
                "message": f"Project creation failed with error: {str(e)}",
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            })
    
    def get_project_status(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the current status of a project."""
        details = self.project_manager.get_project_details(project_id)
        if not details:
            return None
        
        return {
            "project_id": project_id,
            "status": details["status"],
            "current_phase": details["current_phase"],
            "progress_percentage": details["progress_percentage"],
            "created_at": datetime.fromisoformat(details["created_at"]),
            "updated_at": datetime.fromisoformat(details["updated_at"]),
            "errors": details["errors"]
        }
    
    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a project."""
        details = self.project_manager.get_project_details(project_id)
        if not details:
            return None
        
        return {
            "project_id": project_id,
            "name": details["name"],
            "template_id": details["template_id"],
            "status": details["status"],
            "current_phase": details["current_phase"],
            "progress_percentage": details["progress_percentage"],
            "created_at": datetime.fromisoformat(details["created_at"]),
            "updated_at": datetime.fromisoformat(details["updated_at"]),
            "output_directory": details["output_directory"],
            "errors": details["errors"],
            "created_files": details["created_files"]
        }
    
    def list_projects(self, status_filter: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """List all tracked projects with optional filtering and pagination."""
        projects = self.project_manager.list_projects()
        
        # Apply status filter
        if status_filter:
            projects = [p for p in projects if p["status"] == status_filter]
        
        # Apply pagination
        projects = projects[offset:offset + limit]
        
        return [
            {
                "project_id": project["project_id"],
                "name": project["name"],
                "status": project["status"],
                "template_id": project["template_id"],
                "created_at": datetime.fromisoformat(project["created_at"])
            }
            for project in projects
        ]
    
    def cancel_project(self, project_id: str, force: bool = False) -> bool:
        """Cancel and cleanup a project."""
        # Clean up progress state
        self.progress_integration.cleanup_project_state(project_id)
        
        # Cancel the project
        return self.project_manager.cleanup_project(project_id)
    
    def pause_project(self, project_id: str) -> bool:
        """Pause a running project."""
        # Note: This would require extending the ProjectManager interface
        # For now, return False as pause/resume is not implemented in the base system
        return False
    
    def resume_project(self, project_id: str) -> bool:
        """Resume a paused project."""
        # Note: This would require extending the ProjectManager interface
        # For now, return False as pause/resume is not implemented in the base system
        return False
    
    def get_project_logs(self, project_id: str, level: str = "info", limit: int = 100, offset: int = 0) -> Optional[List[Dict[str, Any]]]:
        """Get project logs."""
        # Get progress events which contain log information
        events = self.project_manager.get_project_events(project_id)
        if not events:
            return None
        
        # Filter by log level
        level_map = {"debug": 0, "info": 1, "warning": 2, "error": 3}
        min_level = level_map.get(level.lower(), 1)
        
        logs = []
        for event in events:
            event_level = 1  # Default to info
            if event.error:
                event_level = 3  # Error
            elif "warning" in event.message.lower():
                event_level = 2  # Warning
            
            if event_level >= min_level:
                logs.append({
                    "timestamp": event.timestamp.isoformat(),
                    "level": ["debug", "info", "warning", "error"][event_level],
                    "phase": event.phase,
                    "message": event.message,
                    "details": event.details,
                    "error": event.error
                })
        
        # Apply pagination
        return logs[offset:offset + limit]
    
    def list_project_files(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """List files created by a project."""
        details = self.project_manager.get_project_details(project_id)
        if not details:
            return None
        
        files = []
        for file_path in details.get("created_files", []):
            try:
                file_stat = Path(file_path).stat()
                files.append({
                    "path": file_path,
                    "size": file_stat.st_size,
                    "modified": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "is_directory": Path(file_path).is_dir()
                })
            except Exception:
                # File might not exist anymore
                files.append({
                    "path": file_path,
                    "size": 0,
                    "modified": None,
                    "is_directory": False,
                    "error": "File not accessible"
                })
        
        return files
    
    async def create_project_archive(self, project_id: str) -> Optional[str]:
        """Create a ZIP archive of project files."""
        details = self.project_manager.get_project_details(project_id)
        if not details or details["status"] != "completed":
            return None
        
        import zipfile
        import tempfile
        
        # Create temporary ZIP file
        temp_dir = Path(tempfile.gettempdir())
        zip_path = temp_dir / f"project_{project_id}.zip"
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                project_path = Path(details["output_directory"]) / details["name"]
                
                if project_path.exists():
                    for file_path in project_path.rglob("*"):
                        if file_path.is_file():
                            # Add file to ZIP with relative path
                            arcname = file_path.relative_to(project_path)
                            zipf.write(file_path, arcname)
            
            return str(zip_path)
            
        except Exception as e:
            self.logger.error(f"Failed to create project archive: {e}")
            return None
    
    def get_validation_history(self, project_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get validation history for a project."""
        details = self.project_manager.get_project_details(project_id)
        if not details:
            return None
        
        return self.validation_service.get_validation_history(project_id)
    
    async def run_custom_test_scenarios(self, project_id: str, scenarios: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Run custom test scenarios on a project."""
        details = self.project_manager.get_project_details(project_id)
        if not details or details["status"] not in ["completed", "failed"]:
            return None
        
        project_path = Path(details["output_directory"]) / details["name"]
        if not project_path.exists():
            return None
        
        try:
            results = await self.validation_service.run_custom_test_scenarios(str(project_path), scenarios)
            results["project_id"] = project_id
            return results
            
        except Exception as e:
            return {
                "project_id": project_id,
                "scenarios_run": len(scenarios),
                "results": [],
                "overall_success": False,
                "execution_time": 0.0,
                "timestamp": datetime.now(),
                "error": str(e)
            }
    
    async def _run_single_test_scenario(self, project_path: Path, scenario: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Run a single test scenario."""
        scenario_name = scenario.get("name", f"Scenario {index + 1}")
        scenario_type = scenario.get("type", "custom")
        
        try:
            # Placeholder implementation - would run actual tests based on scenario type
            if scenario_type == "startup":
                success = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.validation_engine.validate_server_startup,
                    str(project_path)
                )
            elif scenario_type == "protocol":
                success = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.validation_engine.validate_mcp_protocol,
                    str(project_path)
                )
            else:
                # Custom scenario - placeholder implementation
                success = True
            
            return {
                "name": scenario_name,
                "type": scenario_type,
                "success": success,
                "details": scenario.get("details", {}),
                "execution_time": 1.0,  # Placeholder
                "errors": [] if success else ["Test failed"],
                "warnings": []
            }
            
        except Exception as e:
            return {
                "name": scenario_name,
                "type": scenario_type,
                "success": False,
                "details": scenario.get("details", {}),
                "execution_time": 0.0,
                "errors": [str(e)],
                "warnings": []
            }
    
    def list_validation_templates(self) -> List[Dict[str, Any]]:
        """List available validation templates."""
        return self.validation_service.get_validation_templates()
    
    async def validate_project(self, project_id: str, request: ValidationRequest) -> Optional[Dict[str, Any]]:
        """Run validation tests on a project."""
        details = self.project_manager.get_project_details(project_id)
        if not details:
            return None
        
        # Check if project is in a state that can be validated
        if details["status"] not in ["completed", "failed"]:
            return None
        
        project_path = Path(details["output_directory"]) / details["name"]
        if not project_path.exists():
            return None
        
        try:
            start_time = datetime.now()
            
            # Send validation start update
            await self._send_progress_update(project_id, {
                "type": "validation_started",
                "project_id": project_id,
                "phase": "validation",
                "percentage": 0.0,
                "message": f"Starting {request.validation_type} validation",
                "timestamp": start_time.isoformat()
            })
            
            # Run validation using the validation service
            validation_results = await self.validation_service.run_validation(
                str(project_path),
                request.validation_type,
                request.custom_tests if hasattr(request, 'custom_tests') else None
            )
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Extract success from validation results
            success = validation_results.get("success", False)
            
            # Send validation complete update
            await self._send_progress_update(project_id, {
                "type": "validation_completed",
                "project_id": project_id,
                "phase": "validation_complete",
                "percentage": 100.0,
                "message": f"Validation completed - {'Success' if success else 'Failed'}",
                "timestamp": end_time.isoformat(),
                "validation_results": validation_results
            })
            
            return {
                "project_id": project_id,
                "validation_type": request.validation_type,
                "success": success,
                "results": validation_results.get("results", {}),
                "errors": validation_results.get("errors", []),
                "warnings": validation_results.get("warnings", []),
                "execution_time": execution_time,
                "timestamp": end_time
            }
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Send validation error update
            await self._send_progress_update(project_id, {
                "type": "validation_error",
                "project_id": project_id,
                "phase": "validation_error",
                "percentage": 0.0,
                "message": f"Validation failed with error: {str(e)}",
                "timestamp": end_time.isoformat(),
                "error": str(e)
            })
            
            return {
                "project_id": project_id,
                "validation_type": request.validation_type,
                "success": False,
                "results": {},
                "errors": [str(e)],
                "warnings": [],
                "execution_time": execution_time,
                "timestamp": end_time
            }
    
    def _handle_progress_update(self, project_id: str, percentage: float, phase: str):
        """Handle progress updates from the project manager."""
        asyncio.create_task(self._send_progress_update(project_id, {
            "type": "progress_update",
            "project_id": project_id,
            "phase": phase,
            "percentage": percentage,
            "message": f"Phase: {phase} - {percentage:.1f}% complete",
            "timestamp": datetime.now().isoformat()
        }))
    
    def _handle_error_update(self, project_id: str, error_message: str):
        """Handle error updates from the project manager."""
        asyncio.create_task(self._send_progress_update(project_id, {
            "type": "error_update",
            "project_id": project_id,
            "phase": "error",
            "percentage": 0.0,
            "message": error_message,
            "timestamp": datetime.now().isoformat(),
            "error": error_message
        }))
    
    def _handle_progress_event(self, event: ProgressEvent):
        """Handle progress events from the progress tracker."""
        asyncio.create_task(self._send_progress_event(event))
    
    async def _send_progress_event(self, event: ProgressEvent):
        """Send a progress event via WebSocket."""
        update = {
            "type": event.event_type.value,
            "project_id": event.project_id,
            "phase": event.phase,
            "percentage": event.percentage,
            "message": event.message,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details,
            "error": event.error
        }
        
        await self.websocket_manager.broadcast_to_project(event.project_id, update)
    
    async def _send_progress_update(self, project_id: str, update: Dict[str, Any]):
        """Send a progress update via WebSocket."""
        await self.websocket_manager.broadcast_to_project(project_id, update)