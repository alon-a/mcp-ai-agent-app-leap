"""Tests for the ProjectManager implementation."""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch

from src.managers.project_manager import ProjectManagerImpl
from src.managers.progress_tracker import LogLevel
from src.models.base import ProjectStatus


class TestProjectManagerImpl:
    """Test cases for ProjectManagerImpl."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManagerImpl(log_level=LogLevel.DEBUG)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_project_manager_initialization(self):
        """Test that ProjectManager initializes correctly."""
        assert self.project_manager is not None
        assert self.project_manager.template_engine is not None
        assert self.project_manager.file_manager is not None
        assert self.project_manager.dependency_manager is not None
        assert self.project_manager.build_system is not None
        assert self.project_manager.validation_engine is not None
        assert self.project_manager.progress_tracker is not None
        assert self.project_manager.error_handler is not None
    
    def test_project_state_tracking(self):
        """Test project state tracking functionality."""
        # Test that we can track project states
        assert len(self.project_manager._projects) == 0
        
        # Test project listing when empty
        projects = self.project_manager.list_projects()
        assert projects == []
    
    def test_progress_tracking_integration(self):
        """Test that progress tracking is properly integrated."""
        project_id = "test-project-123"
        
        # Test progress callback registration
        callback_called = []
        
        def test_callback(event):
            callback_called.append(event)
        
        self.project_manager.add_progress_callback(test_callback)
        
        # Simulate progress tracking
        self.project_manager.progress_tracker.start_phase(
            project_id, "test_phase", "Testing progress tracking"
        )
        
        assert len(callback_called) > 0
        assert callback_called[0].project_id == project_id
        assert callback_called[0].phase == "test_phase"
    
    def test_error_handling_integration(self):
        """Test that error handling is properly integrated."""
        project_id = "test-project-456"
        
        # Test error handling
        from src.managers.error_handler import ErrorCategory, ErrorSeverity
        
        recovery_action = self.project_manager.error_handler.handle_error(
            project_id=project_id,
            category=ErrorCategory.TEMPLATE,
            severity=ErrorSeverity.MEDIUM,
            message="Test error message",
            phase="test_phase"
        )
        
        # Verify error was recorded
        errors = self.project_manager.get_project_errors(project_id)
        assert len(errors) == 1
        assert errors[0]['message'] == "Test error message"
        assert errors[0]['category'] == "template"
        assert errors[0]['severity'] == "medium"
    
    def test_rollback_functionality(self):
        """Test rollback functionality."""
        project_id = "test-project-789"
        
        # Register a rollback action
        rollback_called = []
        
        def test_rollback():
            rollback_called.append(True)
            return True
        
        self.project_manager.error_handler.register_rollback_action(project_id, test_rollback)
        
        # Execute rollback
        success = self.project_manager.force_rollback(project_id)
        
        assert success is True
        assert len(rollback_called) == 1
    
    @patch('src.managers.template_engine.TemplateEngineImpl')
    def test_create_project_template_not_found(self, mock_template_engine):
        """Test project creation when template is not found."""
        # Mock template engine to return None
        mock_template_engine.return_value.get_template.return_value = None
        
        # Replace the template engine with our mock
        self.project_manager.template_engine = mock_template_engine.return_value
        
        # Attempt to create project
        result = self.project_manager.create_project(
            name="test-project",
            template="nonexistent-template",
            config={'output_directory': self.temp_dir}
        )
        
        # Verify failure
        assert result.success is False
        assert "Template preparation failed" in result.errors
        assert result.status == ProjectStatus.FAILED
    
    def test_project_details_retrieval(self):
        """Test retrieving project details."""
        # Test with non-existent project
        details = self.project_manager.get_project_details("nonexistent")
        assert details is None
        
        # Test project status for non-existent project
        status = self.project_manager.get_project_status("nonexistent")
        assert status == ProjectStatus.FAILED
    
    def test_cleanup_project(self):
        """Test project cleanup functionality."""
        project_id = "test-cleanup-project"
        
        # Test cleanup of non-existent project
        success = self.project_manager.cleanup_project(project_id)
        assert success is False
    
    def test_error_summary(self):
        """Test error summary functionality."""
        project_id = "test-error-summary"
        
        # Test error summary for project with no errors
        summary = self.project_manager.get_error_summary(project_id)
        assert summary['error_count'] == 0
        
        # Add an error and test summary
        from src.managers.error_handler import ErrorCategory, ErrorSeverity
        
        self.project_manager.error_handler.handle_error(
            project_id=project_id,
            category=ErrorCategory.BUILD,
            severity=ErrorSeverity.HIGH,
            message="Test build error",
            phase="build"
        )
        
        summary = self.project_manager.get_error_summary(project_id)
        assert summary['error_count'] == 1
        assert 'build' in summary['by_category']
        assert 'high' in summary['by_severity']


if __name__ == "__main__":
    pytest.main([__file__])