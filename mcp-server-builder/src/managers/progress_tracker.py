"""Progress tracking and reporting system for MCP server builder."""

import logging
import time
from typing import Dict, Any, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading


class LogLevel(Enum):
    """Logging verbosity levels."""
    SILENT = 0
    ERROR = 1
    WARNING = 2
    INFO = 3
    DEBUG = 4
    VERBOSE = 5


class ProgressEventType(Enum):
    """Types of progress events."""
    PHASE_START = "phase_start"
    PHASE_PROGRESS = "phase_progress"
    PHASE_COMPLETE = "phase_complete"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    DEBUG = "debug"


@dataclass
class ProgressEvent:
    """Represents a progress event."""
    event_type: ProgressEventType
    project_id: str
    timestamp: datetime
    phase: str
    percentage: float
    message: str
    details: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProgressTracker:
    """Tracks and reports progress for MCP server building operations."""
    
    def __init__(self, 
                 log_level: LogLevel = LogLevel.INFO,
                 enable_real_time: bool = True,
                 log_file: Optional[str] = None):
        """Initialize the progress tracker.
        
        Args:
            log_level: Minimum log level to report
            enable_real_time: Whether to enable real-time progress updates
            log_file: Optional file path for logging output
        """
        self.log_level = log_level
        self.enable_real_time = enable_real_time
        self._events: Dict[str, List[ProgressEvent]] = {}
        self._current_phase: Dict[str, str] = {}
        self._phase_start_times: Dict[str, datetime] = {}
        self._callbacks: List[Callable[[ProgressEvent], None]] = []
        self._lock = threading.Lock()
        
        # Set up logging
        self._setup_logging(log_file)
        
        # Progress phases and their expected durations (for estimation)
        self.phase_weights = {
            "initialization": 5.0,
            "template_preparation": 5.0,
            "directory_creation": 10.0,
            "file_download": 15.0,
            "template_customization": 15.0,
            "dependency_installation": 25.0,
            "build_execution": 20.0,
            "validation": 5.0
        }
    
    def _setup_logging(self, log_file: Optional[str]):
        """Set up logging configuration."""
        # Create logger
        self.logger = logging.getLogger(f"mcp_builder_progress")
        self.logger.setLevel(self._log_level_to_logging_level(self.log_level))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Console handler
        if self.log_level != LogLevel.SILENT:
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
    
    def _log_level_to_logging_level(self, level: LogLevel) -> int:
        """Convert LogLevel to logging module level."""
        mapping = {
            LogLevel.SILENT: logging.CRITICAL + 1,
            LogLevel.ERROR: logging.ERROR,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.INFO: logging.INFO,
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.VERBOSE: logging.DEBUG
        }
        return mapping.get(level, logging.INFO)
    
    def add_callback(self, callback: Callable[[ProgressEvent], None]):
        """Add a callback for progress events.
        
        Args:
            callback: Function to call when progress events occur
        """
        with self._lock:
            self._callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[ProgressEvent], None]):
        """Remove a progress event callback.
        
        Args:
            callback: Callback function to remove
        """
        with self._lock:
            if callback in self._callbacks:
                self._callbacks.remove(callback)
    
    def start_phase(self, project_id: str, phase: str, message: str = ""):
        """Start a new progress phase.
        
        Args:
            project_id: Unique project identifier
            phase: Phase name
            message: Optional descriptive message
        """
        with self._lock:
            self._current_phase[project_id] = phase
            self._phase_start_times[f"{project_id}:{phase}"] = datetime.now()
            
            event = ProgressEvent(
                event_type=ProgressEventType.PHASE_START,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=phase,
                percentage=self._calculate_phase_start_percentage(phase),
                message=message or f"Starting {phase}",
                details={"phase_start": True}
            )
            
            self._add_event(project_id, event)
            self._notify_callbacks(event)
            
            if self.log_level.value >= LogLevel.INFO.value:
                self.logger.info(f"[{project_id}] Starting phase: {phase} - {event.message}")
    
    def update_progress(self, project_id: str, percentage: float, message: str = "", 
                       details: Optional[Dict[str, Any]] = None):
        """Update progress within the current phase.
        
        Args:
            project_id: Unique project identifier
            percentage: Progress percentage (0-100)
            message: Progress message
            details: Optional additional details
        """
        with self._lock:
            current_phase = self._current_phase.get(project_id, "unknown")
            
            event = ProgressEvent(
                event_type=ProgressEventType.PHASE_PROGRESS,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=current_phase,
                percentage=percentage,
                message=message,
                details=details
            )
            
            self._add_event(project_id, event)
            
            if self.enable_real_time:
                self._notify_callbacks(event)
            
            if self.log_level.value >= LogLevel.DEBUG.value:
                self.logger.debug(f"[{project_id}] Progress {percentage:.1f}%: {message}")
    
    def complete_phase(self, project_id: str, message: str = "", 
                      details: Optional[Dict[str, Any]] = None):
        """Complete the current phase.
        
        Args:
            project_id: Unique project identifier
            message: Completion message
            details: Optional additional details
        """
        with self._lock:
            current_phase = self._current_phase.get(project_id, "unknown")
            
            # Calculate phase duration
            start_key = f"{project_id}:{current_phase}"
            duration = None
            if start_key in self._phase_start_times:
                duration = (datetime.now() - self._phase_start_times[start_key]).total_seconds()
                del self._phase_start_times[start_key]
            
            event = ProgressEvent(
                event_type=ProgressEventType.PHASE_COMPLETE,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=current_phase,
                percentage=self._calculate_phase_end_percentage(current_phase),
                message=message or f"Completed {current_phase}",
                details={**(details or {}), "duration_seconds": duration}
            )
            
            self._add_event(project_id, event)
            self._notify_callbacks(event)
            
            if self.log_level.value >= LogLevel.INFO.value:
                duration_str = f" ({duration:.2f}s)" if duration else ""
                self.logger.info(f"[{project_id}] Completed phase: {current_phase}{duration_str} - {event.message}")
    
    def log_error(self, project_id: str, error_message: str, 
                  details: Optional[Dict[str, Any]] = None):
        """Log an error event.
        
        Args:
            project_id: Unique project identifier
            error_message: Error message
            details: Optional additional details
        """
        with self._lock:
            current_phase = self._current_phase.get(project_id, "unknown")
            
            event = ProgressEvent(
                event_type=ProgressEventType.ERROR,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=current_phase,
                percentage=0.0,
                message="Error occurred",
                details=details,
                error=error_message
            )
            
            self._add_event(project_id, event)
            self._notify_callbacks(event)
            
            if self.log_level.value >= LogLevel.ERROR.value:
                self.logger.error(f"[{project_id}] Error in {current_phase}: {error_message}")
    
    def log_warning(self, project_id: str, warning_message: str, 
                   details: Optional[Dict[str, Any]] = None):
        """Log a warning event.
        
        Args:
            project_id: Unique project identifier
            warning_message: Warning message
            details: Optional additional details
        """
        with self._lock:
            current_phase = self._current_phase.get(project_id, "unknown")
            
            event = ProgressEvent(
                event_type=ProgressEventType.WARNING,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=current_phase,
                percentage=0.0,
                message=warning_message,
                details=details
            )
            
            self._add_event(project_id, event)
            self._notify_callbacks(event)
            
            if self.log_level.value >= LogLevel.WARNING.value:
                self.logger.warning(f"[{project_id}] Warning in {current_phase}: {warning_message}")
    
    def log_info(self, project_id: str, info_message: str, 
                details: Optional[Dict[str, Any]] = None):
        """Log an info event.
        
        Args:
            project_id: Unique project identifier
            info_message: Info message
            details: Optional additional details
        """
        with self._lock:
            current_phase = self._current_phase.get(project_id, "unknown")
            
            event = ProgressEvent(
                event_type=ProgressEventType.INFO,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=current_phase,
                percentage=0.0,
                message=info_message,
                details=details
            )
            
            self._add_event(project_id, event)
            
            if self.enable_real_time:
                self._notify_callbacks(event)
            
            if self.log_level.value >= LogLevel.INFO.value:
                self.logger.info(f"[{project_id}] {info_message}")
    
    def log_debug(self, project_id: str, debug_message: str, 
                 details: Optional[Dict[str, Any]] = None):
        """Log a debug event.
        
        Args:
            project_id: Unique project identifier
            debug_message: Debug message
            details: Optional additional details
        """
        with self._lock:
            current_phase = self._current_phase.get(project_id, "unknown")
            
            event = ProgressEvent(
                event_type=ProgressEventType.DEBUG,
                project_id=project_id,
                timestamp=datetime.now(),
                phase=current_phase,
                percentage=0.0,
                message=debug_message,
                details=details
            )
            
            self._add_event(project_id, event)
            
            if self.log_level.value >= LogLevel.DEBUG.value:
                self.logger.debug(f"[{project_id}] {debug_message}")
    
    def get_project_events(self, project_id: str) -> List[ProgressEvent]:
        """Get all events for a specific project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            List of progress events for the project
        """
        with self._lock:
            return self._events.get(project_id, []).copy()
    
    def get_project_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of project progress.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Dictionary with project progress summary
        """
        with self._lock:
            events = self._events.get(project_id, [])
            
            if not events:
                return {"project_id": project_id, "status": "not_found"}
            
            # Find latest progress event
            latest_progress = None
            errors = []
            warnings = []
            phases_completed = []
            
            for event in events:
                if event.event_type == ProgressEventType.PHASE_PROGRESS:
                    if not latest_progress or event.timestamp > latest_progress.timestamp:
                        latest_progress = event
                elif event.event_type == ProgressEventType.ERROR:
                    errors.append(event.error or event.message)
                elif event.event_type == ProgressEventType.WARNING:
                    warnings.append(event.message)
                elif event.event_type == ProgressEventType.PHASE_COMPLETE:
                    phases_completed.append(event.phase)
            
            current_phase = self._current_phase.get(project_id, "unknown")
            current_percentage = latest_progress.percentage if latest_progress else 0.0
            
            return {
                "project_id": project_id,
                "current_phase": current_phase,
                "current_percentage": current_percentage,
                "phases_completed": phases_completed,
                "error_count": len(errors),
                "warning_count": len(warnings),
                "latest_errors": errors[-3:] if errors else [],
                "latest_warnings": warnings[-3:] if warnings else [],
                "start_time": events[0].timestamp.isoformat() if events else None,
                "last_update": events[-1].timestamp.isoformat() if events else None
            }
    
    def _add_event(self, project_id: str, event: ProgressEvent):
        """Add an event to the project's event list."""
        if project_id not in self._events:
            self._events[project_id] = []
        self._events[project_id].append(event)
    
    def _notify_callbacks(self, event: ProgressEvent):
        """Notify all registered callbacks of an event."""
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                # Don't let callback errors break the progress tracking
                self.logger.error(f"Callback error: {str(e)}")
    
    def _calculate_phase_start_percentage(self, phase: str) -> float:
        """Calculate the starting percentage for a phase."""
        completed_weight = 0.0
        total_weight = sum(self.phase_weights.values())
        
        phase_order = list(self.phase_weights.keys())
        if phase in phase_order:
            phase_index = phase_order.index(phase)
            completed_weight = sum(list(self.phase_weights.values())[:phase_index])
        
        return (completed_weight / total_weight) * 100.0
    
    def _calculate_phase_end_percentage(self, phase: str) -> float:
        """Calculate the ending percentage for a phase."""
        completed_weight = 0.0
        total_weight = sum(self.phase_weights.values())
        
        phase_order = list(self.phase_weights.keys())
        if phase in phase_order:
            phase_index = phase_order.index(phase)
            completed_weight = sum(list(self.phase_weights.values())[:phase_index + 1])
        
        return (completed_weight / total_weight) * 100.0
    
    def clear_project_events(self, project_id: str):
        """Clear all events for a specific project.
        
        Args:
            project_id: Unique project identifier
        """
        with self._lock:
            if project_id in self._events:
                del self._events[project_id]
            if project_id in self._current_phase:
                del self._current_phase[project_id]
            
            # Clean up phase start times
            keys_to_remove = [key for key in self._phase_start_times.keys() 
                            if key.startswith(f"{project_id}:")]
            for key in keys_to_remove:
                del self._phase_start_times[key]