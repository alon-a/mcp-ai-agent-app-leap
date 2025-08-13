"""Tests for progress tracker implementation."""

import pytest
import tempfile
import os
import time
import threading
from datetime import datetime
from unittest.mock import Mock, patch

from src.managers.progress_tracker import (
    ProgressTracker,
    LogLevel,
    ProgressEventType,
    ProgressEvent
)


class TestProgressTracker:
    """Test cases for ProgressTracker class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.progress_tracker = ProgressTracker(log_level=LogLevel.DEBUG)
        self.project_id = "test-project-123"
    
    def test_initialization(self):
        """Test progress tracker initialization."""
        assert self.progress_tracker is not None
        assert self.progress_tracker.log_level == LogLevel.DEBUG
        assert self.progress_tracker.enable_real_time is True
        assert len(self.progress_tracker._events) == 0
        assert len(self.progress_tracker._callbacks) == 0
    
    def test_initialization_with_log_file(self):
        """Test initialization with log file."""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            log_file = temp_file.name
        
        try:
            tracker = ProgressTracker(
                log_level=LogLevel.INFO,
                enable_real_time=False,
                log_file=log_file
            )
            
            assert tracker.log_level == LogLevel.INFO
            assert tracker.enable_real_time is False
            
            # Test that log file handler was added
            assert len(tracker.logger.handlers) >= 1
            
        finally:
            if os.path.exists(log_file):
                os.unlink(log_file)
    
    def test_log_level_conversion(self):
        """Test log level conversion to logging module levels."""
        import logging
        
        tracker = ProgressTracker(log_level=LogLevel.SILENT)
        assert tracker._log_level_to_logging_level(LogLevel.SILENT) > logging.CRITICAL
        
        assert tracker._log_level_to_logging_level(LogLevel.ERROR) == logging.ERROR
        assert tracker._log_level_to_logging_level(LogLevel.WARNING) == logging.WARNING
        assert tracker._log_level_to_logging_level(LogLevel.INFO) == logging.INFO
        assert tracker._log_level_to_logging_level(LogLevel.DEBUG) == logging.DEBUG
        assert tracker._log_level_to_logging_level(LogLevel.VERBOSE) == logging.DEBUG
    
    def test_add_remove_callback(self):
        """Test adding and removing progress callbacks."""
        callback_calls = []
        
        def test_callback(event):
            callback_calls.append(event)
        
        # Add callback
        self.progress_tracker.add_callback(test_callback)
        assert len(self.progress_tracker._callbacks) == 1
        
        # Test callback is called
        self.progress_tracker.start_phase(self.project_id, "test_phase", "Testing")
        assert len(callback_calls) == 1
        
        # Remove callback
        self.progress_tracker.remove_callback(test_callback)
        assert len(self.progress_tracker._callbacks) == 0
        
        # Test callback is no longer called
        self.progress_tracker.start_phase(self.project_id, "test_phase_2", "Testing 2")
        assert len(callback_calls) == 1  # Should still be 1
    
    def test_start_phase(self):
        """Test starting a progress phase."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        self.progress_tracker.add_callback(test_callback)
        
        # Start phase
        self.progress_tracker.start_phase(
            self.project_id, 
            "initialization", 
            "Starting initialization"
        )
        
        # Check that event was created and callback called
        assert len(callback_events) == 1
        event = callback_events[0]
        
        assert event.event_type == ProgressEventType.PHASE_START
        assert event.project_id == self.project_id
        assert event.phase == "initialization"
        assert event.message == "Starting initialization"
        assert event.percentage >= 0.0
        assert "phase_start" in event.details
        
        # Check that phase is tracked
        assert self.progress_tracker._current_phase[self.project_id] == "initialization"
        
        # Check that events are stored
        events = self.progress_tracker.get_project_events(self.project_id)
        assert len(events) == 1
        assert events[0].phase == "initialization"
    
    def test_update_progress(self):
        """Test updating progress within a phase."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        self.progress_tracker.add_callback(test_callback)
        
        # Start phase first
        self.progress_tracker.start_phase(self.project_id, "file_download", "Downloading files")
        
        # Update progress
        self.progress_tracker.update_progress(
            self.project_id,
            50.0,
            "Downloaded 5 of 10 files",
            {"files_downloaded": 5, "total_files": 10}
        )
        
        # Check callback was called (should be 2 calls: start + progress)
        assert len(callback_events) == 2
        progress_event = callback_events[1]
        
        assert progress_event.event_type == ProgressEventType.PHASE_PROGRESS
        assert progress_event.project_id == self.project_id
        assert progress_event.phase == "file_download"
        assert progress_event.percentage == 50.0
        assert progress_event.message == "Downloaded 5 of 10 files"
        assert progress_event.details["files_downloaded"] == 5
        assert progress_event.details["total_files"] == 10
    
    def test_update_progress_no_real_time(self):
        """Test progress updates with real-time disabled."""
        tracker = ProgressTracker(enable_real_time=False)
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        tracker.add_callback(test_callback)
        
        # Start phase (should still call callback)
        tracker.start_phase(self.project_id, "test_phase", "Testing")
        assert len(callback_events) == 1
        
        # Update progress (should NOT call callback due to real-time disabled)
        tracker.update_progress(self.project_id, 50.0, "Progress update")
        assert len(callback_events) == 1  # Should still be 1
        
        # But events should still be stored
        events = tracker.get_project_events(self.project_id)
        assert len(events) == 2  # start + progress
    
    def test_complete_phase(self):
        """Test completing a progress phase."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        self.progress_tracker.add_callback(test_callback)
        
        # Start and complete phase
        self.progress_tracker.start_phase(self.project_id, "build_execution", "Building")
        time.sleep(0.01)  # Small delay to measure duration
        self.progress_tracker.complete_phase(
            self.project_id,
            "Build completed successfully",
            {"artifacts_created": 3}
        )
        
        # Check callback was called (start + complete)
        assert len(callback_events) == 2
        complete_event = callback_events[1]
        
        assert complete_event.event_type == ProgressEventType.PHASE_COMPLETE
        assert complete_event.project_id == self.project_id
        assert complete_event.phase == "build_execution"
        assert complete_event.message == "Build completed successfully"
        assert complete_event.percentage > 0.0  # Should have calculated end percentage
        assert "artifacts_created" in complete_event.details
        assert "duration_seconds" in complete_event.details
        assert complete_event.details["duration_seconds"] > 0
    
    def test_log_error(self):
        """Test logging error events."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        self.progress_tracker.add_callback(test_callback)
        
        # Start phase and log error
        self.progress_tracker.start_phase(self.project_id, "dependency_installation", "Installing")
        self.progress_tracker.log_error(
            self.project_id,
            "Package not found: nonexistent-package",
            {"package_name": "nonexistent-package", "exit_code": 1}
        )
        
        # Check callback was called (start + error)
        assert len(callback_events) == 2
        error_event = callback_events[1]
        
        assert error_event.event_type == ProgressEventType.ERROR
        assert error_event.project_id == self.project_id
        assert error_event.phase == "dependency_installation"
        assert error_event.error == "Package not found: nonexistent-package"
        assert error_event.details["package_name"] == "nonexistent-package"
        assert error_event.details["exit_code"] == 1
    
    def test_log_warning(self):
        """Test logging warning events."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        self.progress_tracker.add_callback(test_callback)
        
        # Start phase and log warning
        self.progress_tracker.start_phase(self.project_id, "validation", "Validating")
        self.progress_tracker.log_warning(
            self.project_id,
            "Deprecated configuration option used",
            {"option": "old_setting", "replacement": "new_setting"}
        )
        
        # Check callback was called (start + warning)
        assert len(callback_events) == 2
        warning_event = callback_events[1]
        
        assert warning_event.event_type == ProgressEventType.WARNING
        assert warning_event.project_id == self.project_id
        assert warning_event.phase == "validation"
        assert warning_event.message == "Deprecated configuration option used"
        assert warning_event.details["option"] == "old_setting"
        assert warning_event.details["replacement"] == "new_setting"
    
    def test_log_info(self):
        """Test logging info events."""
        callback_events = []
        
        def test_callback(event):
            callback_events.append(event)
        
        self.progress_tracker.add_callback(test_callback)
        
        # Start phase and log info
        self.progress_tracker.start_phase(self.project_id, "template_customization", "Customizing")
        self.progress_tracker.log_info(
            self.project_id,
            "Applied custom configuration",
            {"config_keys": ["server_name", "port"]}
        )
        
        # Check callback was called (start + info)
        assert len(callback_events) == 2
        info_event = callback_events[1]
        
        assert info_event.event_type == ProgressEventType.INFO
        assert info_event.project_id == self.project_id
        assert info_event.phase == "template_customization"
        assert info_event.message == "Applied custom configuration"
        assert info_event.details["config_keys"] == ["server_name", "port"]
    
    def test_log_debug(self):
        """Test logging debug events."""
        # Debug events don't trigger callbacks by default
        self.progress_tracker.start_phase(self.project_id, "file_download", "Downloading")
        self.progress_tracker.log_debug(
            self.project_id,
            "Processing file: example.txt",
            {"file_size": 1024, "checksum": "abc123"}
        )
        
        # Check that debug event was stored
        events = self.progress_tracker.get_project_events(self.project_id)
        debug_events = [e for e in events if e.event_type == ProgressEventType.DEBUG]
        
        assert len(debug_events) == 1
        debug_event = debug_events[0]
        
        assert debug_event.message == "Processing file: example.txt"
        assert debug_event.details["file_size"] == 1024
        assert debug_event.details["checksum"] == "abc123"
    
    def test_get_project_events(self):
        """Test retrieving project events."""
        # Add various events
        self.progress_tracker.start_phase(self.project_id, "initialization", "Starting")
        self.progress_tracker.update_progress(self.project_id, 25.0, "Quarter done")
        self.progress_tracker.log_info(self.project_id, "Info message")
        self.progress_tracker.log_warning(self.project_id, "Warning message")
        self.progress_tracker.complete_phase(self.project_id, "Done")
        
        events = self.progress_tracker.get_project_events(self.project_id)
        
        assert len(events) == 5
        assert events[0].event_type == ProgressEventType.PHASE_START
        assert events[1].event_type == ProgressEventType.PHASE_PROGRESS
        assert events[2].event_type == ProgressEventType.INFO
        assert events[3].event_type == ProgressEventType.WARNING
        assert events[4].event_type == ProgressEventType.PHASE_COMPLETE
    
    def test_get_project_events_nonexistent(self):
        """Test retrieving events for non-existent project."""
        events = self.progress_tracker.get_project_events("nonexistent-project")
        assert events == []
    
    def test_get_project_summary_no_events(self):
        """Test project summary for project with no events."""
        summary = self.progress_tracker.get_project_summary("nonexistent-project")
        
        assert summary["project_id"] == "nonexistent-project"
        assert summary["status"] == "not_found"
    
    def test_get_project_summary_with_events(self):
        """Test project summary for project with events."""
        # Add various events
        self.progress_tracker.start_phase(self.project_id, "initialization", "Starting")
        self.progress_tracker.complete_phase(self.project_id, "Init done")
        
        self.progress_tracker.start_phase(self.project_id, "file_download", "Downloading")
        self.progress_tracker.update_progress(self.project_id, 75.0, "Almost done")
        self.progress_tracker.log_error(self.project_id, "Download failed")
        self.progress_tracker.log_warning(self.project_id, "Slow connection")
        self.progress_tracker.log_error(self.project_id, "Retry failed")
        
        summary = self.progress_tracker.get_project_summary(self.project_id)
        
        assert summary["project_id"] == self.project_id
        assert summary["current_phase"] == "file_download"
        assert summary["current_percentage"] == 75.0
        assert summary["phases_completed"] == ["initialization"]
        assert summary["error_count"] == 2
        assert summary["warning_count"] == 1
        assert len(summary["latest_errors"]) == 2
        assert len(summary["latest_warnings"]) == 1
        assert summary["start_time"] is not None
        assert summary["last_update"] is not None
    
    def test_get_project_summary_error_limit(self):
        """Test that project summary limits recent errors/warnings."""
        self.progress_tracker.start_phase(self.project_id, "test_phase", "Testing")
        
        # Add more than 3 errors
        for i in range(5):
            self.progress_tracker.log_error(self.project_id, f"Error {i}")
        
        # Add more than 3 warnings
        for i in range(4):
            self.progress_tracker.log_warning(self.project_id, f"Warning {i}")
        
        summary = self.progress_tracker.get_project_summary(self.project_id)
        
        assert summary["error_count"] == 5
        assert summary["warning_count"] == 4
        assert len(summary["latest_errors"]) == 3  # Limited to 3
        assert len(summary["latest_warnings"]) == 3  # Limited to 3
        
        # Should contain the most recent ones
        assert "Error 4" in summary["latest_errors"]
        assert "Warning 3" in summary["latest_warnings"]
    
    def test_clear_project_events(self):
        """Test clearing project events."""
        # Add some events
        self.progress_tracker.start_phase(self.project_id, "test_phase", "Testing")
        self.progress_tracker.update_progress(self.project_id, 50.0, "Half done")
        self.progress_tracker.complete_phase(self.project_id, "Done")
        
        # Verify events exist
        events = self.progress_tracker.get_project_events(self.project_id)
        assert len(events) == 3
        assert self.project_id in self.progress_tracker._current_phase
        
        # Clear events
        self.progress_tracker.clear_project_events(self.project_id)
        
        # Verify events are cleared
        events = self.progress_tracker.get_project_events(self.project_id)
        assert len(events) == 0
        assert self.project_id not in self.progress_tracker._current_phase
    
    def test_phase_percentage_calculation(self):
        """Test phase percentage calculations."""
        # Test known phases
        start_pct = self.progress_tracker._calculate_phase_start_percentage("initialization")
        end_pct = self.progress_tracker._calculate_phase_end_percentage("initialization")
        
        assert start_pct == 0.0  # First phase starts at 0%
        assert end_pct > start_pct  # End should be higher than start
        
        # Test middle phase
        start_pct = self.progress_tracker._calculate_phase_start_percentage("dependency_installation")
        end_pct = self.progress_tracker._calculate_phase_end_percentage("dependency_installation")
        
        assert start_pct > 0.0  # Should be partway through
        assert end_pct > start_pct
        assert end_pct <= 100.0
        
        # Test unknown phase
        start_pct = self.progress_tracker._calculate_phase_start_percentage("unknown_phase")
        end_pct = self.progress_tracker._calculate_phase_end_percentage("unknown_phase")
        
        assert start_pct == 0.0
        assert end_pct == 0.0
    
    def test_callback_exception_handling(self):
        """Test that callback exceptions don't break progress tracking."""
        def failing_callback(event):
            raise Exception("Callback failed")
        
        def working_callback(event):
            working_callback.called = True
        
        working_callback.called = False
        
        self.progress_tracker.add_callback(failing_callback)
        self.progress_tracker.add_callback(working_callback)
        
        # This should not raise an exception despite the failing callback
        self.progress_tracker.start_phase(self.project_id, "test_phase", "Testing")
        
        # Working callback should still be called
        assert working_callback.called is True
        
        # Events should still be stored
        events = self.progress_tracker.get_project_events(self.project_id)
        assert len(events) == 1
    
    def test_thread_safety(self):
        """Test thread safety of progress tracker operations."""
        events_added = []
        
        def add_events():
            thread_id = threading.current_thread().ident
            project_id = f"project-{thread_id}"
            
            for i in range(5):
                self.progress_tracker.start_phase(project_id, f"phase-{i}", f"Phase {i}")
                self.progress_tracker.update_progress(project_id, i * 20, f"Progress {i}")
                self.progress_tracker.complete_phase(project_id, f"Phase {i} done")
                events_added.append((project_id, i))
                time.sleep(0.001)  # Small delay to encourage race conditions
        
        # Start multiple threads
        threads = []
        for _ in range(3):
            thread = threading.Thread(target=add_events)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all events were added
        assert len(events_added) == 15  # 3 threads * 5 phases each
        
        # Verify events are properly separated by project
        total_events = 0
        for project_id in self.progress_tracker._events:
            project_events = self.progress_tracker.get_project_events(project_id)
            total_events += len(project_events)
        
        assert total_events == 45  # 3 threads * 5 phases * 3 events per phase (start, progress, complete)
    
    def test_different_log_levels(self):
        """Test behavior with different log levels."""
        # Test SILENT level
        silent_tracker = ProgressTracker(log_level=LogLevel.SILENT)
        assert len(silent_tracker.logger.handlers) == 0  # No console handler
        
        # Test ERROR level
        error_tracker = ProgressTracker(log_level=LogLevel.ERROR)
        assert error_tracker.logger.level == error_tracker._log_level_to_logging_level(LogLevel.ERROR)
        
        # Test VERBOSE level
        verbose_tracker = ProgressTracker(log_level=LogLevel.VERBOSE)
        assert verbose_tracker.logger.level == verbose_tracker._log_level_to_logging_level(LogLevel.VERBOSE)
    
    def test_phase_weights_configuration(self):
        """Test that phase weights are properly configured."""
        weights = self.progress_tracker.phase_weights
        
        # Check that common phases are defined
        expected_phases = [
            "initialization",
            "template_preparation", 
            "directory_creation",
            "file_download",
            "template_customization",
            "dependency_installation",
            "build_execution",
            "validation"
        ]
        
        for phase in expected_phases:
            assert phase in weights
            assert weights[phase] > 0.0
        
        # Check that weights sum to a reasonable total
        total_weight = sum(weights.values())
        assert total_weight == 100.0  # Should sum to 100 for percentage calculation
    
    def test_multiple_projects_isolation(self):
        """Test that multiple projects are properly isolated."""
        project_id_1 = "project-1"
        project_id_2 = "project-2"
        
        # Add events to first project
        self.progress_tracker.start_phase(project_id_1, "phase-1", "Project 1 Phase 1")
        self.progress_tracker.log_info(project_id_1, "Project 1 info")
        
        # Add events to second project
        self.progress_tracker.start_phase(project_id_2, "phase-2", "Project 2 Phase 2")
        self.progress_tracker.log_error(project_id_2, "Project 2 error")
        
        # Verify isolation
        events_1 = self.progress_tracker.get_project_events(project_id_1)
        events_2 = self.progress_tracker.get_project_events(project_id_2)
        
        assert len(events_1) == 2
        assert len(events_2) == 2
        
        # Verify content isolation
        assert all(e.project_id == project_id_1 for e in events_1)
        assert all(e.project_id == project_id_2 for e in events_2)
        
        assert events_1[0].phase == "phase-1"
        assert events_2[0].phase == "phase-2"
        
        # Verify summaries are isolated
        summary_1 = self.progress_tracker.get_project_summary(project_id_1)
        summary_2 = self.progress_tracker.get_project_summary(project_id_2)
        
        assert summary_1["current_phase"] == "phase-1"
        assert summary_2["current_phase"] == "phase-2"
        assert summary_1["error_count"] == 0
        assert summary_2["error_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__])