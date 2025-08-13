"""Tests for enhanced output formatting and user feedback."""

import pytest
import sys
import io
from unittest.mock import patch, MagicMock
import time

from src.cli.output import (
    OutputFormatter, 
    ProgressIndicator, 
    VerbosityLevel,
    create_summary_report,
    create_detailed_report,
    create_progress_summary,
    create_status_table,
    create_step_by_step_guide,
    format_validation_results,
    format_duration,
    format_file_size
)


class TestOutputFormatter:
    """Test the enhanced OutputFormatter class."""
    
    def test_verbosity_levels(self):
        """Test different verbosity levels."""
        # Test quiet mode
        formatter = OutputFormatter(use_colors=False, verbosity=0)
        assert formatter.verbosity_level == VerbosityLevel.QUIET
        
        # Test normal mode
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        assert formatter.verbosity_level == VerbosityLevel.NORMAL
        
        # Test verbose mode
        formatter = OutputFormatter(use_colors=False, verbosity=2)
        assert formatter.verbosity_level == VerbosityLevel.VERBOSE
        
        # Test debug mode
        formatter = OutputFormatter(use_colors=False, verbosity=3)
        assert formatter.verbosity_level == VerbosityLevel.DEBUG
    
    def test_quiet_mode_suppression(self, capsys):
        """Test that quiet mode suppresses non-error output."""
        formatter = OutputFormatter(use_colors=False, verbosity=0)
        
        # These should be suppressed in quiet mode
        formatter.success("Success message")
        formatter.info("Info message")
        formatter.warning("Warning message")
        formatter.key_value("Key", "Value")
        
        captured = capsys.readouterr()
        assert captured.out == ""
        
        # Errors should still be shown
        formatter.error("Error message")
        captured = capsys.readouterr()
        assert "Error message" in captured.err
    
    def test_status_update_with_timestamp(self, capsys):
        """Test status updates with timestamps in verbose mode."""
        formatter = OutputFormatter(use_colors=False, verbosity=2)
        
        formatter.status_update("Processing data", "INFO")
        captured = capsys.readouterr()
        
        # Should contain timestamp in verbose mode
        assert "[" in captured.out and "]" in captured.out
        assert "Processing data" in captured.out
    
    def test_step_tracking(self, capsys):
        """Test step start and completion tracking."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        # Test step start
        formatter.step_start("Initialize project", 1, 5)
        captured = capsys.readouterr()
        assert "[1/5]" in captured.out
        assert "Starting: Initialize project" in captured.out
        
        # Test step completion
        formatter.step_complete("Initialize project", 1.5)
        captured = capsys.readouterr()
        assert "Completed: Initialize project" in captured.out
        assert "1.5s" in captured.out
    
    def test_enhanced_verbose_levels(self, capsys):
        """Test enhanced verbose message levels."""
        formatter = OutputFormatter(use_colors=False, verbosity=3)
        
        # Test different verbose levels
        formatter.verbose("Level 1 message", 1)
        formatter.verbose("Level 2 message", 2)
        formatter.verbose("Level 3 message", 3)
        
        captured = capsys.readouterr()
        assert "Level 1 message" in captured.out
        assert "Level 2 message" in captured.out
        assert "Level 3 message" in captured.out


class TestProgressIndicator:
    """Test the enhanced ProgressIndicator class."""
    
    def test_progress_with_duration(self, capsys):
        """Test progress indicator with duration tracking."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        progress = ProgressIndicator("Testing", formatter)
        
        # Test that progress indicator tracks time
        progress.start()
        assert progress.start_time is not None
        
        progress.stop("Test completed")
        
        captured = capsys.readouterr()
        assert "Test completed" in captured.out
        # Just check that some duration is shown (will be very small but > 0)
        assert "(" in captured.out and ")" in captured.out
    
    def test_progress_message_update(self):
        """Test updating progress message."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        progress = ProgressIndicator("Initial message", formatter)
        
        progress.update_message("Updated message")
        assert progress.message == "Updated message"


class TestSummaryReports:
    """Test enhanced summary reporting functions."""
    
    def test_summary_report_with_warnings_errors(self, capsys):
        """Test summary report with warnings and errors."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        data = {"Files Created": 5, "Dependencies": ["dep1", "dep2"]}
        warnings = ["Warning 1", "Warning 2"]
        errors = ["Error 1"]
        next_steps = ["Step 1", "Step 2"]
        
        create_summary_report(
            "Test Report",
            data,
            formatter,
            next_steps=next_steps,
            warnings=warnings,
            errors=errors
        )
        
        captured = capsys.readouterr()
        captured_err = capsys.readouterr().err
        
        assert "Test Report" in captured.out
        assert "❌ Errors" in captured.out
        assert "⚠️ Warnings" in captured.out
        assert "🚀 Next Steps" in captured.out
        # Errors go to stderr
        assert "Error 1" in captured_err or "Error 1" in captured.out
        assert "Warning 1" in captured.out
    
    def test_detailed_report(self, capsys):
        """Test detailed multi-section report."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        sections = {
            "Section 1": {"Key1": "Value1", "Key2": ["item1", "item2"]},
            "Section 2": {"Key3": "Value3"}
        }
        
        create_detailed_report("Detailed Test Report", sections, formatter)
        
        captured = capsys.readouterr()
        assert "Detailed Test Report" in captured.out
        assert "Section 1" in captured.out
        assert "Section 2" in captured.out
        assert "Key1: Value1" in captured.out


class TestProgressSummary:
    """Test progress summary functionality."""
    
    def test_progress_summary_with_eta(self, capsys):
        """Test progress summary with ETA calculation."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        with patch('time.time', return_value=10.0):
            create_progress_summary(
                "Building project",
                total_steps=10,
                completed_steps=3,
                current_step="Installing dependencies",
                formatter=formatter,
                start_time=5.0  # 5 seconds elapsed
            )
        
        captured = capsys.readouterr()
        assert "Building project" in captured.out
        assert "30%" in captured.out  # 3/10 = 30%
        assert "Elapsed:" in captured.out
        assert "ETA:" in captured.out


class TestStatusTable:
    """Test status table formatting."""
    
    def test_status_table_creation(self, capsys):
        """Test creating a formatted status table."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        headers = ["Name", "Status", "Duration"]
        rows = [
            ["Task 1", "Complete", "1.2s"],
            ["Task 2", "Failed", "0.5s"],
            ["Task 3", "Running", "2.1s"]
        ]
        
        create_status_table(headers, rows, formatter, "Task Status")
        
        captured = capsys.readouterr()
        assert "Task Status" in captured.out
        assert "Name" in captured.out
        assert "Status" in captured.out
        assert "Task 1" in captured.out
        assert "Complete" in captured.out
        assert "+" in captured.out  # Table borders
    
    def test_empty_status_table(self, capsys):
        """Test status table with no data."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        create_status_table(["Header"], [], formatter)
        
        captured = capsys.readouterr()
        assert "No data to display" in captured.out


class TestStepByStepGuide:
    """Test step-by-step guide formatting."""
    
    def test_step_guide_creation(self, capsys):
        """Test creating a step-by-step guide."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        steps = [
            {
                "title": "Setup Environment",
                "description": "Initialize the development environment",
                "command": "npm install",
                "note": "This may take a few minutes"
            },
            {
                "title": "Run Tests",
                "command": "npm test"
            }
        ]
        
        create_step_by_step_guide("Getting Started", steps, formatter)
        
        captured = capsys.readouterr()
        assert "Getting Started" in captured.out
        assert "1. Setup Environment" in captured.out
        assert "Initialize the development environment" in captured.out
        assert "$ npm install" in captured.out
        assert "Note: This may take a few minutes" in captured.out
        assert "2. Run Tests" in captured.out


class TestValidationResults:
    """Test validation results formatting."""
    
    def test_validation_results_success(self, capsys):
        """Test formatting successful validation results."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        results = {
            "total_tests": 10,
            "passed_tests": 10,
            "failed_tests": 0,
            "warnings": [],
            "errors": []
        }
        
        format_validation_results(results, formatter)
        
        captured = capsys.readouterr()
        assert "All 10 validation tests passed!" in captured.out
        assert "100.0%" in captured.out
    
    def test_validation_results_with_failures(self, capsys):
        """Test formatting validation results with failures."""
        formatter = OutputFormatter(use_colors=False, verbosity=1)
        
        results = {
            "total_tests": 10,
            "passed_tests": 7,
            "failed_tests": 3,
            "warnings": ["Warning 1", "Warning 2"],
            "errors": ["Error 1", "Error 2", "Error 3"]
        }
        
        format_validation_results(results, formatter)
        
        captured = capsys.readouterr()
        captured_err = captured.err
        
        # The error message goes to stderr
        assert "3 of 10 validation tests failed" in captured_err or "3 of 10 validation tests failed" in captured.out
        assert "70.0%" in captured.out
        assert "❌ Errors Found" in captured.out
        assert "⚠️ Warnings" in captured.out


class TestUtilityFunctions:
    """Test utility formatting functions."""
    
    def test_format_duration(self):
        """Test duration formatting."""
        assert format_duration(0.5) == "500ms"
        assert format_duration(1.5) == "1.5s"
        assert format_duration(65) == "1m 5s"
        assert format_duration(3665) == "1h 1m"
    
    def test_format_file_size(self):
        """Test file size formatting."""
        assert format_file_size(0) == "0 B"
        assert format_file_size(1024) == "1.0 KB"
        assert format_file_size(1048576) == "1.0 MB"
        assert format_file_size(1073741824) == "1.0 GB"


class TestColorSupport:
    """Test color support detection and handling."""
    
    def test_color_detection_no_tty(self):
        """Test color detection when not in a TTY."""
        with patch('sys.stdout.isatty', return_value=False):
            formatter = OutputFormatter()
            assert formatter.use_colors is False
    
    def test_color_detection_no_color_env(self):
        """Test color detection with NO_COLOR environment variable."""
        with patch.dict('os.environ', {'NO_COLOR': '1'}):
            formatter = OutputFormatter()
            assert formatter.use_colors is False
    
    def test_color_detection_force_color_env(self):
        """Test color detection with FORCE_COLOR environment variable."""
        with patch.dict('os.environ', {'FORCE_COLOR': '1'}):
            with patch('sys.stdout.isatty', return_value=True):
                formatter = OutputFormatter()
                assert formatter.use_colors is True


if __name__ == "__main__":
    pytest.main([__file__])