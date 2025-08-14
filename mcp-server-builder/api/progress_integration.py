"""Integration layer for MCP Server Builder progress tracking with WebSocket broadcasting."""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from .websocket_manager import EnhancedWebSocketManager
from managers.progress_tracker import ProgressEvent, ProgressEventType, LogLevel


class ProgressIntegration:
    """Integrates MCP Server Builder progress tracking with WebSocket broadcasting."""
    
    def __init__(self, websocket_manager: EnhancedWebSocketManager):
        self.websocket_manager = websocket_manager
        self.logger = logging.getLogger(__name__)
        
        # Track project progress state
        self.project_states: Dict[str, Dict[str, Any]] = {}
        
        # Phase mapping for better user experience
        self.phase_display_names = {
            "initialization": "Initializing Project",
            "template_preparation": "Preparing Template",
            "directory_creation": "Creating Directory Structure",
            "file_download": "Downloading Template Files",
            "template_customization": "Customizing Template",
            "dependency_installation": "Installing Dependencies",
            "build_execution": "Building Project",
            "validation": "Validating Server",
            "completed": "Project Completed",
            "failed": "Project Failed"
        }
        
        # Progress weights for better percentage calculation
        self.phase_weights = {
            "initialization": 5.0,
            "template_preparation": 10.0,
            "directory_creation": 5.0,
            "file_download": 20.0,
            "template_customization": 15.0,
            "dependency_installation": 25.0,
            "build_execution": 15.0,
            "validation": 5.0
        }
    
    def create_progress_callback(self) -> Callable[[ProgressEvent], None]:
        """Create a progress callback function for the project manager."""
        def progress_callback(event: ProgressEvent):
            """Handle progress events from the MCP Server Builder."""
            asyncio.create_task(self._handle_progress_event(event))
        
        return progress_callback
    
    async def _handle_progress_event(self, event: ProgressEvent):
        """Handle a progress event and broadcast it via WebSocket."""
        try:
            project_id = event.project_id
            
            # Update project state
            if project_id not in self.project_states:
                self.project_states[project_id] = {
                    "current_phase": "initialization",
                    "overall_progress": 0.0,
                    "phase_progress": 0.0,
                    "started_at": datetime.now(),
                    "last_update": datetime.now(),
                    "completed_phases": [],
                    "errors": [],
                    "warnings": []
                }
            
            state = self.project_states[project_id]
            state["last_update"] = datetime.now()
            
            # Process different event types
            if event.event_type == ProgressEventType.PHASE_START:
                await self._handle_phase_start(event, state)
            elif event.event_type == ProgressEventType.PHASE_PROGRESS:
                await self._handle_phase_progress(event, state)
            elif event.event_type == ProgressEventType.PHASE_COMPLETE:
                await self._handle_phase_complete(event, state)
            elif event.event_type == ProgressEventType.ERROR:
                await self._handle_error(event, state)
            elif event.event_type == ProgressEventType.WARNING:
                await self._handle_warning(event, state)
            elif event.event_type == ProgressEventType.INFO:
                await self._handle_info(event, state)
            
            # Broadcast the processed event
            await self._broadcast_progress_update(event, state)
            
        except Exception as e:
            self.logger.error(f"Error handling progress event: {e}")
    
    async def _handle_phase_start(self, event: ProgressEvent, state: Dict[str, Any]):
        """Handle phase start event."""
        state["current_phase"] = event.phase
        state["phase_progress"] = 0.0
        
        # Calculate overall progress based on completed phases
        overall_progress = self._calculate_overall_progress(state)
        state["overall_progress"] = overall_progress
        
        self.logger.info(f"Phase started: {event.phase} for project {event.project_id}")
    
    async def _handle_phase_progress(self, event: ProgressEvent, state: Dict[str, Any]):
        """Handle phase progress event."""
        state["phase_progress"] = event.percentage
        
        # Update overall progress
        overall_progress = self._calculate_overall_progress(state)
        state["overall_progress"] = overall_progress
    
    async def _handle_phase_complete(self, event: ProgressEvent, state: Dict[str, Any]):
        """Handle phase complete event."""
        if event.phase not in state["completed_phases"]:
            state["completed_phases"].append(event.phase)
        
        state["phase_progress"] = 100.0
        
        # Update overall progress
        overall_progress = self._calculate_overall_progress(state)
        state["overall_progress"] = overall_progress
        
        self.logger.info(f"Phase completed: {event.phase} for project {event.project_id}")
    
    async def _handle_error(self, event: ProgressEvent, state: Dict[str, Any]):
        """Handle error event."""
        error_info = {
            "message": event.error or event.message,
            "phase": event.phase,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details
        }
        
        state["errors"].append(error_info)
        self.logger.error(f"Error in project {event.project_id}: {error_info['message']}")
    
    async def _handle_warning(self, event: ProgressEvent, state: Dict[str, Any]):
        """Handle warning event."""
        warning_info = {
            "message": event.message,
            "phase": event.phase,
            "timestamp": event.timestamp.isoformat(),
            "details": event.details
        }
        
        state["warnings"].append(warning_info)
        self.logger.warning(f"Warning in project {event.project_id}: {warning_info['message']}")
    
    async def _handle_info(self, event: ProgressEvent, state: Dict[str, Any]):
        """Handle info event."""
        self.logger.info(f"Info for project {event.project_id}: {event.message}")
    
    def _calculate_overall_progress(self, state: Dict[str, Any]) -> float:
        """Calculate overall progress based on completed phases and current phase progress."""
        total_weight = sum(self.phase_weights.values())
        completed_weight = 0.0
        
        # Add weight for completed phases
        for phase in state["completed_phases"]:
            if phase in self.phase_weights:
                completed_weight += self.phase_weights[phase]
        
        # Add partial weight for current phase
        current_phase = state["current_phase"]
        if current_phase in self.phase_weights:
            phase_weight = self.phase_weights[current_phase]
            phase_progress = state["phase_progress"] / 100.0
            completed_weight += phase_weight * phase_progress
        
        return min(100.0, (completed_weight / total_weight) * 100.0)
    
    async def _broadcast_progress_update(self, event: ProgressEvent, state: Dict[str, Any]):
        """Broadcast progress update via WebSocket."""
        # Create enhanced progress message
        message = {
            "type": "progress_update",
            "event_type": event.event_type.value,
            "project_id": event.project_id,
            "timestamp": event.timestamp.isoformat(),
            
            # Phase information
            "phase": {
                "name": event.phase,
                "display_name": self.phase_display_names.get(event.phase, event.phase.title()),
                "progress": state["phase_progress"]
            },
            
            # Overall progress
            "overall_progress": state["overall_progress"],
            
            # Message and details
            "message": event.message,
            "details": event.details,
            
            # Error information
            "error": event.error,
            
            # Project state summary
            "project_state": {
                "started_at": state["started_at"].isoformat(),
                "last_update": state["last_update"].isoformat(),
                "completed_phases": state["completed_phases"],
                "error_count": len(state["errors"]),
                "warning_count": len(state["warnings"])
            }
        }
        
        # Add estimated time remaining
        if state["overall_progress"] > 0:
            elapsed_time = (state["last_update"] - state["started_at"]).total_seconds()
            if state["overall_progress"] < 100:
                estimated_total_time = elapsed_time / (state["overall_progress"] / 100.0)
                estimated_remaining = max(0, estimated_total_time - elapsed_time)
                message["estimated_time_remaining"] = estimated_remaining
        
        # Broadcast to all connections for this project
        await self.websocket_manager.broadcast_to_project(event.project_id, message)
    
    def get_project_state(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get the current state of a project."""
        return self.project_states.get(project_id)
    
    def cleanup_project_state(self, project_id: str):
        """Clean up state for a completed or cancelled project."""
        if project_id in self.project_states:
            del self.project_states[project_id]
    
    def get_all_project_states(self) -> Dict[str, Dict[str, Any]]:
        """Get states for all tracked projects."""
        return self.project_states.copy()