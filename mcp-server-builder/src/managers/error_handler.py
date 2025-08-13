"""Centralized error handling and recovery coordination for MCP server builder."""

import os
import shutil
import traceback
from typing import Dict, Any, List, Optional, Callable, Union
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
import threading


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"           # Warning-level issues that don't stop execution
    MEDIUM = "medium"     # Errors that can be recovered from
    HIGH = "high"         # Critical errors that stop current operation
    CRITICAL = "critical" # Fatal errors that require complete rollback


class ErrorCategory(Enum):
    """Categories of errors that can occur."""
    TEMPLATE = "template"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    DEPENDENCY = "dependency"
    BUILD = "build"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


class RecoveryAction(Enum):
    """Types of recovery actions."""
    RETRY = "retry"
    SKIP = "skip"
    ROLLBACK = "rollback"
    ABORT = "abort"
    MANUAL = "manual"


@dataclass
class ErrorInfo:
    """Information about an error that occurred."""
    error_id: str
    project_id: str
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    phase: str
    traceback_info: Optional[str] = None
    suggested_actions: List[str] = None
    recovery_attempted: bool = False
    recovery_successful: Optional[bool] = None


@dataclass
class RecoveryStrategy:
    """Defines how to recover from a specific type of error."""
    category: ErrorCategory
    severity: ErrorSeverity
    action: RecoveryAction
    max_retries: int = 3
    retry_delay: float = 1.0
    cleanup_required: bool = False
    custom_handler: Optional[Callable[[ErrorInfo], bool]] = None


class ErrorHandler:
    """Centralized error handling and recovery coordination."""
    
    def __init__(self):
        """Initialize the error handler."""
        self._errors: Dict[str, List[ErrorInfo]] = {}
        self._recovery_strategies: Dict[str, RecoveryStrategy] = {}
        self._rollback_actions: Dict[str, List[Callable[[], bool]]] = {}
        self._lock = threading.Lock()
        
        # Set up default recovery strategies
        self._setup_default_strategies()
    
    def _setup_default_strategies(self):
        """Set up default recovery strategies for common error types."""
        strategies = [
            # Network errors - retry with backoff
            RecoveryStrategy(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                action=RecoveryAction.RETRY,
                max_retries=3,
                retry_delay=2.0
            ),
            
            # File system permission errors - try to fix permissions
            RecoveryStrategy(
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.MEDIUM,
                action=RecoveryAction.RETRY,
                max_retries=2,
                cleanup_required=True
            ),
            
            # Template errors - usually fatal for current template
            RecoveryStrategy(
                category=ErrorCategory.TEMPLATE,
                severity=ErrorSeverity.HIGH,
                action=RecoveryAction.ABORT,
                cleanup_required=True
            ),
            
            # Dependency errors - retry with different approach
            RecoveryStrategy(
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.MEDIUM,
                action=RecoveryAction.RETRY,
                max_retries=2,
                retry_delay=1.0
            ),
            
            # Build errors - usually require manual intervention
            RecoveryStrategy(
                category=ErrorCategory.BUILD,
                severity=ErrorSeverity.HIGH,
                action=RecoveryAction.MANUAL,
                cleanup_required=False
            ),
            
            # Validation errors - can often be skipped
            RecoveryStrategy(
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                action=RecoveryAction.SKIP,
                cleanup_required=False
            ),
            
            # System errors - usually critical
            RecoveryStrategy(
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                action=RecoveryAction.ROLLBACK,
                cleanup_required=True
            )
        ]
        
        for strategy in strategies:
            key = f"{strategy.category.value}:{strategy.severity.value}"
            self._recovery_strategies[key] = strategy
    
    def handle_error(self, project_id: str, category: ErrorCategory, severity: ErrorSeverity,
                    message: str, phase: str = "unknown", 
                    details: Optional[Dict[str, Any]] = None,
                    exception: Optional[Exception] = None) -> RecoveryAction:
        """Handle an error and determine recovery action.
        
        Args:
            project_id: Unique project identifier
            category: Error category
            severity: Error severity level
            message: Error message
            phase: Current phase when error occurred
            details: Additional error details
            exception: Original exception if available
            
        Returns:
            Recommended recovery action
        """
        with self._lock:
            # Create error info
            error_info = ErrorInfo(
                error_id=f"{project_id}:{datetime.now().timestamp()}",
                project_id=project_id,
                category=category,
                severity=severity,
                message=message,
                details=details or {},
                timestamp=datetime.now(),
                phase=phase,
                traceback_info=traceback.format_exc() if exception else None,
                suggested_actions=self._generate_suggested_actions(category, severity, message)
            )
            
            # Store error
            if project_id not in self._errors:
                self._errors[project_id] = []
            self._errors[project_id].append(error_info)
            
            # Determine recovery strategy
            strategy = self._get_recovery_strategy(category, severity)
            
            return strategy.action if strategy else RecoveryAction.ABORT
    
    def attempt_recovery(self, project_id: str, error_info: ErrorInfo, 
                        recovery_context: Optional[Dict[str, Any]] = None) -> bool:
        """Attempt to recover from an error.
        
        Args:
            project_id: Unique project identifier
            error_info: Information about the error
            recovery_context: Additional context for recovery
            
        Returns:
            True if recovery was successful
        """
        strategy = self._get_recovery_strategy(error_info.category, error_info.severity)
        if not strategy:
            return False
        
        error_info.recovery_attempted = True
        
        try:
            if strategy.action == RecoveryAction.RETRY:
                return self._attempt_retry_recovery(error_info, strategy, recovery_context)
            elif strategy.action == RecoveryAction.SKIP:
                return self._attempt_skip_recovery(error_info, recovery_context)
            elif strategy.action == RecoveryAction.ROLLBACK:
                return self._attempt_rollback_recovery(project_id, error_info, recovery_context)
            elif strategy.custom_handler:
                return strategy.custom_handler(error_info)
            else:
                return False
                
        except Exception as e:
            # Recovery itself failed
            error_info.recovery_successful = False
            return False
    
    def register_rollback_action(self, project_id: str, action: Callable[[], bool]):
        """Register a rollback action for a project.
        
        Args:
            project_id: Unique project identifier
            action: Function to call during rollback
        """
        with self._lock:
            if project_id not in self._rollback_actions:
                self._rollback_actions[project_id] = []
            self._rollback_actions[project_id].append(action)
    
    def execute_rollback(self, project_id: str) -> bool:
        """Execute all rollback actions for a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            True if rollback was successful
        """
        with self._lock:
            if project_id not in self._rollback_actions:
                return True  # Nothing to rollback
            
            actions = self._rollback_actions[project_id].copy()
            success = True
            
            # Execute rollback actions in reverse order
            for action in reversed(actions):
                try:
                    if not action():
                        success = False
                except Exception:
                    success = False
            
            # Clear rollback actions after execution
            del self._rollback_actions[project_id]
            
            return success
    
    def get_project_errors(self, project_id: str) -> List[ErrorInfo]:
        """Get all errors for a specific project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            List of error information
        """
        with self._lock:
            return self._errors.get(project_id, []).copy()
    
    def get_error_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of errors for a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Dictionary with error summary
        """
        with self._lock:
            errors = self._errors.get(project_id, [])
            
            if not errors:
                return {"project_id": project_id, "error_count": 0}
            
            # Categorize errors
            by_category = {}
            by_severity = {}
            recoverable_count = 0
            
            for error in errors:
                # Count by category
                cat = error.category.value
                by_category[cat] = by_category.get(cat, 0) + 1
                
                # Count by severity
                sev = error.severity.value
                by_severity[sev] = by_severity.get(sev, 0) + 1
                
                # Count recoverable errors
                if error.recovery_attempted and error.recovery_successful:
                    recoverable_count += 1
            
            latest_error = max(errors, key=lambda e: e.timestamp)
            
            return {
                "project_id": project_id,
                "error_count": len(errors),
                "by_category": by_category,
                "by_severity": by_severity,
                "recoverable_count": recoverable_count,
                "latest_error": {
                    "category": latest_error.category.value,
                    "severity": latest_error.severity.value,
                    "message": latest_error.message,
                    "timestamp": latest_error.timestamp.isoformat()
                }
            }
    
    def clear_project_errors(self, project_id: str):
        """Clear all errors for a specific project.
        
        Args:
            project_id: Unique project identifier
        """
        with self._lock:
            if project_id in self._errors:
                del self._errors[project_id]
            if project_id in self._rollback_actions:
                del self._rollback_actions[project_id]
    
    def add_recovery_strategy(self, category: ErrorCategory, severity: ErrorSeverity,
                            strategy: RecoveryStrategy):
        """Add or update a recovery strategy.
        
        Args:
            category: Error category
            severity: Error severity
            strategy: Recovery strategy to use
        """
        key = f"{category.value}:{severity.value}"
        self._recovery_strategies[key] = strategy
    
    def _get_recovery_strategy(self, category: ErrorCategory, 
                             severity: ErrorSeverity) -> Optional[RecoveryStrategy]:
        """Get the recovery strategy for a specific error type."""
        key = f"{category.value}:{severity.value}"
        return self._recovery_strategies.get(key)
    
    def _generate_suggested_actions(self, category: ErrorCategory, severity: ErrorSeverity,
                                  message: str) -> List[str]:
        """Generate suggested actions for an error."""
        suggestions = []
        
        if category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check internet connection",
                "Verify URL accessibility",
                "Try again in a few moments",
                "Check firewall settings"
            ])
        elif category == ErrorCategory.FILE_SYSTEM:
            suggestions.extend([
                "Check file permissions",
                "Verify disk space availability",
                "Ensure directory is writable",
                "Check for file locks"
            ])
        elif category == ErrorCategory.DEPENDENCY:
            suggestions.extend([
                "Check package manager configuration",
                "Verify package names and versions",
                "Clear package manager cache",
                "Check for conflicting dependencies"
            ])
        elif category == ErrorCategory.BUILD:
            suggestions.extend([
                "Check build tool installation",
                "Verify build configuration",
                "Review build logs for details",
                "Check for missing dependencies"
            ])
        elif category == ErrorCategory.TEMPLATE:
            suggestions.extend([
                "Verify template configuration",
                "Check template file integrity",
                "Try a different template",
                "Review template documentation"
            ])
        
        # Add severity-specific suggestions
        if severity == ErrorSeverity.CRITICAL:
            suggestions.append("Consider starting over with a clean environment")
        elif severity == ErrorSeverity.HIGH:
            suggestions.append("Manual intervention may be required")
        
        return suggestions
    
    def _attempt_retry_recovery(self, error_info: ErrorInfo, strategy: RecoveryStrategy,
                              context: Optional[Dict[str, Any]]) -> bool:
        """Attempt recovery by retrying the failed operation."""
        # This is a placeholder - actual retry logic would be implemented
        # by the calling component based on the recovery recommendation
        error_info.recovery_successful = False
        return False
    
    def _attempt_skip_recovery(self, error_info: ErrorInfo, 
                             context: Optional[Dict[str, Any]]) -> bool:
        """Attempt recovery by skipping the failed operation."""
        # Mark as recovered by skipping
        error_info.recovery_successful = True
        return True
    
    def _attempt_rollback_recovery(self, project_id: str, error_info: ErrorInfo,
                                 context: Optional[Dict[str, Any]]) -> bool:
        """Attempt recovery by rolling back changes."""
        success = self.execute_rollback(project_id)
        error_info.recovery_successful = success
        return success