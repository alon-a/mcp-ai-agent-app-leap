"""Tests for the comprehensive testing CLI."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from src.cli.comprehensive_test import (
    run_comprehensive_test, format_text_output, format_json_output
)
from src.managers.comprehensive_testing import ComprehensiveTestReport
from src.models.base import ValidationReport, ServerStartupResult, ProtocolComplianceResult, FunctionalityTestResult
from src.models.enums import ValidationLevel


class TestComprehensiveTestCLI:
    """Test cases for comprehensive testing CLI."""
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # Create a simple Python server file
            main_py = project_path / "main.py"
            main_py.write_text("print('Hello MCP Server')")
            
            yield str(project_path)
    
    @pytest.fixture
    def mock_args(self, temp_project_dir):
        """Create mock CLI arguments."""
        args = Mock()
        args.project_path = temp_project_dir
        args.skip_performance = False
        args.skip_integration = False
        args.skip_load_testing = False
        args.skip_security = False
        args.validation_level = 'standard'
        args.max_workers = 2
        args.timeout = 10
        args.output_format = 'text'
        args.output_file = None
        args.verbose = False
        return args
    
    @pytest.fixture
    def sample_test_report(self):
        """Create a sample test report for testing."""
        validation_report = ValidationReport(
            project_path="/test/path",
            validation_level=ValidationLevel.STANDARD,
            overall_success=True,
            startup_result=ServerStartupResult(True, 12345, 1.0, [], ["Server started"]),
            protocol_result=ProtocolComplianceResult(True, ["initialize", "tools/list"], [], "2024-11-05", []),
            functionality_result=FunctionalityTestResult(True, {"tool1": True}, {"resource1": True}, {"prompt1": True}, [], {}),
            performance_metrics={"startup_time": 1.0},
            recommendations=["Basic recommendation"],
            timestamp="2024-01-01T00:00:00",
            total_execution_time=5.0
        )
        
        return ComprehensiveTestReport(
            project_path="/test/path",
            test_timestamp="2024-01-01T00:00:00",
            overall_success=True,
            basic_validation=validation_report,
            performance_benchmarks=[],
            integration_results=[],
            load_test_results={"success": True, "error_rate": 0.01},
            security_scan_results={"success": True, "critical_issues": 0},
            recommendations=["Test recommendation"],
            total_test_duration=10.5
        )
    
    def test_run_comprehensive_test_nonexistent_path(self):
        """Test CLI with nonexistent project path."""
        args = Mock()
        args.project_path = "/nonexistent/path"
        args.verbose = False
        
        result = run_comprehensive_test(args)
        assert result == 1
    
    def test_run_comprehensive_test_file_instead_of_directory(self, temp_project_dir):
        """Test CLI with file path instead of directory."""
        # Create a file instead of using directory
        file_path = Path(temp_project_dir) / "test_file.txt"
        file_path.write_text("test content")
        
        args = Mock()
        args.project_path = str(file_path)
        args.verbose = False
        
        result = run_comprehensive_test(args)
        assert result == 1
    
    @patch('src.cli.comprehensive_test.ComprehensiveServerTester')
    @patch('src.cli.comprehensive_test.MCPValidationEngine')
    def test_run_comprehensive_test_success(self, mock_validation_engine, mock_tester, mock_args, sample_test_report):
        """Test successful comprehensive test run."""
        # Mock the tester to return our sample report
        mock_tester_instance = Mock()
        mock_tester_instance.run_comprehensive_tests.return_value = sample_test_report
        mock_tester.return_value = mock_tester_instance
        
        result = run_comprehensive_test(mock_args)
        
        assert result == 0
        mock_tester_instance.run_comprehensive_tests.assert_called_once()
    
    @patch('src.cli.comprehensive_test.ComprehensiveServerTester')
    @patch('src.cli.comprehensive_test.MCPValidationEngine')
    def test_run_comprehensive_test_failure(self, mock_validation_engine, mock_tester, mock_args, sample_test_report):
        """Test comprehensive test run with failures."""
        # Modify sample report to indicate failure
        sample_test_report.overall_success = False
        
        mock_tester_instance = Mock()
        mock_tester_instance.run_comprehensive_tests.return_value = sample_test_report
        mock_tester.return_value = mock_tester_instance
        
        result = run_comprehensive_test(mock_args)
        
        assert result == 1
    
    @patch('src.cli.comprehensive_test.ComprehensiveServerTester')
    @patch('src.cli.comprehensive_test.MCPValidationEngine')
    def test_run_comprehensive_test_json_output(self, mock_validation_engine, mock_tester, mock_args, sample_test_report):
        """Test comprehensive test with JSON output."""
        mock_args.output_format = 'json'
        
        mock_tester_instance = Mock()
        mock_tester_instance.run_comprehensive_tests.return_value = sample_test_report
        mock_tester.return_value = mock_tester_instance
        
        result = run_comprehensive_test(mock_args)
        
        assert result == 0
    
    @patch('src.cli.comprehensive_test.ComprehensiveServerTester')
    @patch('src.cli.comprehensive_test.MCPValidationEngine')
    def test_run_comprehensive_test_with_output_file(self, mock_validation_engine, mock_tester, mock_args, sample_test_report, tmp_path):
        """Test comprehensive test with output file."""
        output_file = tmp_path / "test_results.txt"
        mock_args.output_file = str(output_file)
        
        mock_tester_instance = Mock()
        mock_tester_instance.run_comprehensive_tests.return_value = sample_test_report
        mock_tester.return_value = mock_tester_instance
        
        result = run_comprehensive_test(mock_args)
        
        assert result == 0
        assert output_file.exists()
        assert len(output_file.read_text()) > 0
    
    @patch('src.cli.comprehensive_test.ComprehensiveServerTester')
    @patch('src.cli.comprehensive_test.MCPValidationEngine')
    def test_run_comprehensive_test_exception(self, mock_validation_engine, mock_tester, mock_args):
        """Test comprehensive test with exception."""
        mock_tester.side_effect = Exception("Test exception")
        
        result = run_comprehensive_test(mock_args)
        
        assert result == 1
    
    def test_format_text_output_success(self, sample_test_report):
        """Test text output formatting for successful report."""
        output = format_text_output(sample_test_report, verbose=False)
        
        assert "MCP Server Comprehensive Test Report" in output
        assert "PASS" in output
        assert sample_test_report.project_path in output
        assert "Test recommendation" in output
    
    def test_format_text_output_verbose(self, sample_test_report):
        """Test verbose text output formatting."""
        # Modify report to have some failures for verbose output
        sample_test_report.overall_success = False
        sample_test_report.basic_validation.overall_success = False
        sample_test_report.basic_validation.startup_result.success = False
        sample_test_report.basic_validation.startup_result.errors = ["Startup failed"]
        
        output = format_text_output(sample_test_report, verbose=True)
        
        assert "Detailed Issues:" in output
        assert "Startup Errors:" in output
        assert "Startup failed" in output
    
    def test_format_json_output(self, sample_test_report):
        """Test JSON output formatting."""
        output = format_json_output(sample_test_report)
        
        # Parse JSON to verify it's valid
        data = json.loads(output)
        
        assert data["project_path"] == sample_test_report.project_path
        assert data["overall_success"] == sample_test_report.overall_success
        assert data["total_test_duration"] == sample_test_report.total_test_duration
        assert "basic_validation" in data
        assert "performance_benchmarks" in data
        assert "integration_results" in data
        assert "load_test_results" in data
        assert "security_scan_results" in data
        assert "recommendations" in data
    
    def test_validation_level_mapping(self, mock_args):
        """Test validation level string to enum mapping."""
        # Test different validation levels
        validation_levels = ['basic', 'standard', 'comprehensive']
        
        for level in validation_levels:
            mock_args.validation_level = level
            # This should not raise an exception
            with patch('src.cli.comprehensive_test.ComprehensiveServerTester'), \
                 patch('src.cli.comprehensive_test.MCPValidationEngine') as mock_engine:
                
                mock_tester_instance = Mock()
                mock_report = Mock()
                mock_report.overall_success = True
                mock_report.project_path = "/test/path"
                mock_report.test_timestamp = "2024-01-01T00:00:00"
                mock_report.total_test_duration = 10.0
                mock_report.basic_validation = Mock()
                mock_report.basic_validation.overall_success = True
                mock_report.basic_validation.startup_result = Mock()
                mock_report.basic_validation.startup_result.success = True
                mock_report.basic_validation.protocol_result = Mock()
                mock_report.basic_validation.protocol_result.success = True
                mock_report.basic_validation.functionality_result = Mock()
                mock_report.basic_validation.functionality_result.success = True
                mock_report.performance_benchmarks = []
                mock_report.integration_results = []
                mock_report.load_test_results = {}
                mock_report.security_scan_results = {}
                mock_report.recommendations = []
                
                mock_tester_instance.run_comprehensive_tests.return_value = mock_report
                
                with patch('src.cli.comprehensive_test.ComprehensiveServerTester', return_value=mock_tester_instance):
                    result = run_comprehensive_test(mock_args)
                    assert result == 0
    
    def test_skip_options(self, mock_args, sample_test_report):
        """Test skip options for different test types."""
        mock_args.skip_performance = True
        mock_args.skip_integration = True
        mock_args.skip_load_testing = True
        mock_args.skip_security = True
        
        with patch('src.cli.comprehensive_test.ComprehensiveServerTester') as mock_tester, \
             patch('src.cli.comprehensive_test.MCPValidationEngine'):
            
            mock_tester_instance = Mock()
            mock_tester_instance.run_comprehensive_tests.return_value = sample_test_report
            mock_tester.return_value = mock_tester_instance
            
            result = run_comprehensive_test(mock_args)
            
            assert result == 0
            # Verify that the comprehensive tester was called with skip flags
            mock_tester_instance.run_comprehensive_tests.assert_called_once_with(
                project_path=mock_args.project_path,
                include_performance=False,  # skip_performance = True -> include_performance = False
                include_integration=False,
                include_load_testing=False,
                include_security_scan=False
            )