"""Tests for error handler implementation."""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock, patch

from src.managers.error_handler import (
    ErrorHandler,
    ErrorSeverity,
    ErrorCategory,
    RecoveryAction,
    ErrorInfo,
    RecoveryStrategy
)


class TestErrorHandler:
    """Test cases for ErrorHandler class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.error_handler = ErrorHandler()
        self.project_id = "test-project-123"
    
    def test_initialization(self):
        """Test error handler initialization."""
        assert self.error_handler is not None
        assert len(self.error_handler._recovery_strategies) > 0
        assert len(self.error_handler._errors) == 0
        assert len(self.error_handler._rollback_actions) == 0
    
    def test_default_recovery_strategies(self):
        """Test that default recovery strategies are set up correctly."""
        strategies = self.error_handler._recovery_strategies
        
        # Check that key error types have strategies
        network_key = f"{ErrorCategory.NETWORK.value}:{ErrorSeverity.MEDIUM.value}"
        assert network_key in strategies
        assert strategies[network_key].action == RecoveryAction.RETRY
        
        template_key = f"{ErrorCategory.TEMPLATE.value}:{ErrorSeverity.HIGH.value}"
        assert template_key in strategies
        assert strategies[template_key].action == RecoveryAction.ABORT
        
        system_key = f"{ErrorCategory.SYSTEM.value}:{ErrorSeverity.CRITICAL.value}"
        assert system_key in strategies
        assert strategies[system_key].action == RecoveryAction.ROLLBACK
    
    def test_handle_error_basic(self):
        """Test basic error handling."""
        action = self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network connection failed",
            phase="file_download"
        )
        
        assert action == RecoveryAction.RETRY
        
        # Check that error was stored
        errors = self.error_handler.get_project_errors(self.project_id)
        assert len(errors) == 1
        
        error = errors[0]
        assert error.project_id == self.project_id
        assert error.category == ErrorCategory.NETWORK
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.message == "Network connection failed"
        assert error.phase == "file_download"
        assert error.suggested_actions is not None
        assert len(error.suggested_actions) > 0
    
    def test_handle_error_with_details(self):
        """Test error handling with additional details."""
        details = {
            "url": "https://example.com/file.txt",
            "status_code": 404,
            "retry_count": 2
        }
        
        action = self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="File not found",
            phase="file_download",
            details=details
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        error = errors[0]
        
        assert error.details == details
        assert error.details["url"] == "https://example.com/file.txt"
        assert error.details["status_code"] == 404
    
    def test_handle_error_with_exception(self):
        """Test error handling with exception information."""
        try:
            raise ValueError("Test exception")
        except ValueError as e:
            action = self.error_handler.handle_error(
                project_id=self.project_id,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message="Validation failed",
                phase="validation",
                exception=e
            )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        error = errors[0]
        
        assert error.traceback_info is not None
        assert "ValueError: Test exception" in error.traceback_info
    
    def test_multiple_errors_same_project(self):
        """Test handling multiple errors for the same project."""
        # Add first error
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="First error",
            phase="download"
        )
        
        # Add second error
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.BUILD,
            severity=ErrorSeverity.HIGH,
            message="Second error",
            phase="build"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        assert len(errors) == 2
        assert errors[0].message == "First error"
        assert errors[1].message == "Second error"
    
    def test_errors_different_projects(self):
        """Test handling errors for different projects."""
        project_id_2 = "test-project-456"
        
        # Add error to first project
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Project 1 error",
            phase="download"
        )
        
        # Add error to second project
        self.error_handler.handle_error(
            project_id=project_id_2,
            category=ErrorCategory.BUILD,
            severity=ErrorSeverity.HIGH,
            message="Project 2 error",
            phase="build"
        )
        
        errors_1 = self.error_handler.get_project_errors(self.project_id)
        errors_2 = self.error_handler.get_project_errors(project_id_2)
        
        assert len(errors_1) == 1
        assert len(errors_2) == 1
        assert errors_1[0].message == "Project 1 error"
        assert errors_2[0].message == "Project 2 error"
    
    def test_register_rollback_action(self):
        """Test registering rollback actions."""
        rollback_called = []
        
        def test_rollback():
            rollback_called.append(True)
            return True
        
        self.error_handler.register_rollback_action(self.project_id, test_rollback)
        
        # Verify rollback action was registered
        assert self.project_id in self.error_handler._rollback_actions
        assert len(self.error_handler._rollback_actions[self.project_id]) == 1
    
    def test_execute_rollback_success(self):
        """Test successful rollback execution."""
        rollback_calls = []
        
        def rollback_1():
            rollback_calls.append("rollback_1")
            return True
        
        def rollback_2():
            rollback_calls.append("rollback_2")
            return True
        
        # Register rollback actions
        self.error_handler.register_rollback_action(self.project_id, rollback_1)
        self.error_handler.register_rollback_action(self.project_id, rollback_2)
        
        # Execute rollback
        success = self.error_handler.execute_rollback(self.project_id)
        
        assert success is True
        assert len(rollback_calls) == 2
        # Should execute in reverse order
        assert rollback_calls == ["rollback_2", "rollback_1"]
        
        # Rollback actions should be cleared after execution
        assert self.project_id not in self.error_handler._rollback_actions
    
    def test_execute_rollback_failure(self):
        """Test rollback execution with failures."""
        rollback_calls = []
        
        def rollback_success():
            rollback_calls.append("success")
            return True
        
        def rollback_failure():
            rollback_calls.append("failure")
            return False
        
        # Register rollback actions
        self.error_handler.register_rollback_action(self.project_id, rollback_success)
        self.error_handler.register_rollback_action(self.project_id, rollback_failure)
        
        # Execute rollback
        success = self.error_handler.execute_rollback(self.project_id)
        
        assert success is False
        assert len(rollback_calls) == 2
        # Should still execute all actions even if one fails
        assert "success" in rollback_calls
        assert "failure" in rollback_calls
    
    def test_execute_rollback_exception(self):
        """Test rollback execution with exceptions."""
        rollback_calls = []
        
        def rollback_exception():
            rollback_calls.append("exception")
            raise Exception("Rollback failed")
        
        def rollback_success():
            rollback_calls.append("success")
            return True
        
        # Register rollback actions
        self.error_handler.register_rollback_action(self.project_id, rollback_success)
        self.error_handler.register_rollback_action(self.project_id, rollback_exception)
        
        # Execute rollback
        success = self.error_handler.execute_rollback(self.project_id)
        
        assert success is False
        assert len(rollback_calls) == 2
    
    def test_execute_rollback_no_actions(self):
        """Test rollback execution when no actions are registered."""
        success = self.error_handler.execute_rollback(self.project_id)
        assert success is True
    
    def test_get_error_summary_no_errors(self):
        """Test error summary for project with no errors."""
        summary = self.error_handler.get_error_summary(self.project_id)
        
        assert summary["project_id"] == self.project_id
        assert summary["error_count"] == 0
    
    def test_get_error_summary_with_errors(self):
        """Test error summary for project with errors."""
        # Add multiple errors
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            phase="download"
        )
        
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.BUILD,
            severity=ErrorSeverity.HIGH,
            message="Build error",
            phase="build"
        )
        
        time.sleep(0.001)  # Small delay to ensure different timestamps
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.LOW,
            message="Another network error",
            phase="validation"
        )
        
        summary = self.error_handler.get_error_summary(self.project_id)
        
        assert summary["project_id"] == self.project_id
        assert summary["error_count"] == 3
        
        # Check categorization
        assert summary["by_category"]["network"] == 2
        assert summary["by_category"]["build"] == 1
        
        # Check severity
        assert summary["by_severity"]["medium"] == 1
        assert summary["by_severity"]["high"] == 1
        assert summary["by_severity"]["low"] == 1
        
        # Check latest error (should be the last one added)
        latest = summary["latest_error"]
        assert latest["category"] == "network"
        assert latest["severity"] == "low"
        assert latest["message"] == "Another network error"
    
    def test_clear_project_errors(self):
        """Test clearing project errors."""
        # Add some errors and rollback actions
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Test error",
            phase="test"
        )
        
        self.error_handler.register_rollback_action(
            self.project_id, 
            lambda: True
        )
        
        # Verify they exist
        assert len(self.error_handler.get_project_errors(self.project_id)) == 1
        assert self.project_id in self.error_handler._rollback_actions
        
        # Clear errors
        self.error_handler.clear_project_errors(self.project_id)
        
        # Verify they're cleared
        assert len(self.error_handler.get_project_errors(self.project_id)) == 0
        assert self.project_id not in self.error_handler._rollback_actions
    
    def test_add_custom_recovery_strategy(self):
        """Test adding custom recovery strategy."""
        custom_strategy = RecoveryStrategy(
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.MEDIUM,
            action=RecoveryAction.SKIP,
            max_retries=1,
            retry_delay=0.5
        )
        
        self.error_handler.add_recovery_strategy(
            ErrorCategory.TEMPLATE,
            ErrorSeverity.MEDIUM,
            custom_strategy
        )
        
        # Test that the custom strategy is used
        action = self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.MEDIUM,
            message="Template error",
            phase="template"
        )
        
        assert action == RecoveryAction.SKIP
    
    def test_suggested_actions_network(self):
        """Test suggested actions for network errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            phase="download"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Check internet connection" in suggestions
        assert "Verify URL accessibility" in suggestions
        assert "Try again in a few moments" in suggestions
    
    def test_suggested_actions_file_system(self):
        """Test suggested actions for file system errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.FILE_SYSTEM,
            severity=ErrorSeverity.MEDIUM,
            message="Permission denied",
            phase="file_creation"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Check file permissions" in suggestions
        assert "Verify disk space availability" in suggestions
        assert "Ensure directory is writable" in suggestions
    
    def test_suggested_actions_dependency(self):
        """Test suggested actions for dependency errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.DEPENDENCY,
            severity=ErrorSeverity.MEDIUM,
            message="Package not found",
            phase="dependency_installation"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Check package manager configuration" in suggestions
        assert "Verify package names and versions" in suggestions
        assert "Clear package manager cache" in suggestions
    
    def test_suggested_actions_build(self):
        """Test suggested actions for build errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.BUILD,
            severity=ErrorSeverity.HIGH,
            message="Build failed",
            phase="build"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Check build tool installation" in suggestions
        assert "Verify build configuration" in suggestions
        assert "Review build logs for details" in suggestions
    
    def test_suggested_actions_template(self):
        """Test suggested actions for template errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.HIGH,
            message="Template invalid",
            phase="template_preparation"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Verify template configuration" in suggestions
        assert "Check template file integrity" in suggestions
        assert "Try a different template" in suggestions
    
    def test_suggested_actions_critical_severity(self):
        """Test suggested actions for critical severity errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message="System error",
            phase="initialization"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Consider starting over with a clean environment" in suggestions
    
    def test_suggested_actions_high_severity(self):
        """Test suggested actions for high severity errors."""
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.BUILD,
            severity=ErrorSeverity.HIGH,
            message="Build error",
            phase="build"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        suggestions = errors[0].suggested_actions
        
        assert "Manual intervention may be required" in suggestions
    
    def test_attempt_recovery_skip(self):
        """Test recovery attempt with skip action."""
        # Create an error
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            message="Validation warning",
            phase="validation"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        error_info = errors[0]
        
        # Attempt recovery
        success = self.error_handler.attempt_recovery(self.project_id, error_info)
        
        assert success is True
        assert error_info.recovery_attempted is True
        assert error_info.recovery_successful is True
    
    def test_attempt_recovery_rollback(self):
        """Test recovery attempt with rollback action."""
        # Register a rollback action
        rollback_called = []
        
        def test_rollback():
            rollback_called.append(True)
            return True
        
        self.error_handler.register_rollback_action(self.project_id, test_rollback)
        
        # Create an error that triggers rollback
        self.error_handler.handle_error(
            project_id=self.project_id,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.CRITICAL,
            message="Critical system error",
            phase="initialization"
        )
        
        errors = self.error_handler.get_project_errors(self.project_id)
        error_info = errors[0]
        
        # Attempt recovery
        success = self.error_handler.attempt_recovery(self.project_id, error_info)
        
        assert success is True
        assert error_info.recovery_attempted is True
        assert error_info.recovery_successful is True
        assert len(rollback_called) == 1
    
    def test_attempt_recovery_no_strategy(self):
        """Test recovery attempt when no strategy exists."""
        # Create a custom error info with no matching strategy
        error_info = ErrorInfo(
            error_id="test-error",
            project_id=self.project_id,
            category=ErrorCategory.CONFIGURATION,  # No default strategy for this
            severity=ErrorSeverity.MEDIUM,
            message="Config error",
            details={},
            timestamp=datetime.now(),
            phase="config"
        )
        
        # Attempt recovery
        success = self.error_handler.attempt_recovery(self.project_id, error_info)
        
        assert success is False
        # The recovery_attempted flag is only set if a strategy exists
        # Since no strategy exists for CONFIGURATION:MEDIUM, it should remain False
    
    def test_thread_safety(self):
        """Test thread safety of error handler operations."""
        import threading
        import time
        
        errors_added = []
        
        def add_errors():
            for i in range(10):
                self.error_handler.handle_error(
                    project_id=f"project-{threading.current_thread().ident}",
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    message=f"Error {i}",
                    phase="test"
                )
                errors_added.append(i)
                time.sleep(0.001)  # Small delay to encourage race conditions
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_errors)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all errors were added
        assert len(errors_added) == 30  # 3 threads * 10 errors each
        
        # Verify errors are properly separated by project
        total_errors = 0
        for project_id in self.error_handler._errors:
            project_errors = self.error_handler.get_project_errors(project_id)
            total_errors += len(project_errors)
        
        assert total_errors == 30


if __name__ == "__main__":
    pytest.main([__file__])