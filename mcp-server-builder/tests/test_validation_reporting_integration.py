"""Integration tests for validation reporting and diagnostics."""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.managers.validation_engine import MCPValidationEngine
from src.models.enums import ValidationLevel


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        yield str(project_path)


@pytest.fixture
def temp_reports_dir():
    """Create a temporary directory for validation reports."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


class TestValidationReportingIntegration:
    """Integration tests for validation reporting and diagnostics."""
    
    def test_comprehensive_validation_with_reporting(self, temp_project_dir, temp_reports_dir):
        """Test comprehensive validation with automatic report generation."""
        # Create a simple MCP server project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("""
import json
import sys

def initialize():
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
            "resources": {},
            "prompts": {}
        },
        "serverInfo": {
            "name": "test-server",
            "version": "1.0.0"
        }
    }

def main():
    print("MCP Server starting...")
    
if __name__ == "__main__":
    main()
""")
        
        requirements_file = Path(temp_project_dir) / "requirements.txt"
        requirements_file.write_text("mcp>=1.0.0\n")
        
        # Initialize validation engine with custom reports directory
        engine = MCPValidationEngine()
        engine.reporter.reports_directory = Path(temp_reports_dir)
        engine.reporter.reports_directory.mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "detailed").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "summaries").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "diagnostics").mkdir(exist_ok=True)
        
        # Mock the actual server execution to avoid complexity
        with patch.object(engine, '_start_server_process') as mock_start:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None  # Process is running
            mock_start.return_value = mock_process
            
            with patch.object(engine, '_test_mcp_initialization') as mock_init:
                mock_init.return_value = {
                    "success": True,
                    "capabilities": ["initialize", "tools/list"],
                    "protocol_version": "2024-11-05"
                }
                
                with patch.object(engine, '_test_mcp_method') as mock_method:
                    mock_method.return_value = True
                    
                    with patch.object(engine, '_test_tools_functionality') as mock_tools:
                        mock_tools.return_value = {
                            "tools": {"sample_tool": True},
                            "errors": [],
                            "response_time": 0.1
                        }
                        
                        with patch.object(engine, '_test_resources_functionality') as mock_resources:
                            mock_resources.return_value = {
                                "resources": {"sample_resource": True},
                                "errors": [],
                                "response_time": 0.2
                            }
                            
                            with patch.object(engine, '_test_prompts_functionality') as mock_prompts:
                                mock_prompts.return_value = {
                                    "prompts": {},
                                    "errors": [],
                                    "response_time": 0.1
                                }
                                
                                # Run comprehensive validation
                                result = engine.run_comprehensive_tests(temp_project_dir)
        
        # Verify validation results
        assert result["success"] is True
        assert "report" in result
        assert "detailed_report_path" in result
        assert "summary_report_path" in result
        
        # Verify reports were created
        detailed_report_path = result["detailed_report_path"]
        summary_report_path = result["summary_report_path"]
        
        assert Path(detailed_report_path).exists()
        assert Path(summary_report_path).exists()
        
        # Verify detailed report content
        with open(detailed_report_path) as f:
            detailed_report = json.load(f)
        
        assert "metadata" in detailed_report
        assert "executive_summary" in detailed_report
        assert "detailed_results" in detailed_report
        assert "performance_analysis" in detailed_report
        assert "actionable_recommendations" in detailed_report
        assert "next_steps" in detailed_report
        
        # Verify summary report content
        with open(summary_report_path) as f:
            summary_report = json.load(f)
        
        assert summary_report["overall_success"] is True
        assert "results_summary" in summary_report
        assert "performance_score" in summary_report
    
    def test_failed_validation_with_diagnostics(self, temp_project_dir, temp_reports_dir):
        """Test failed validation with automatic diagnostics generation."""
        # Create a broken MCP server project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("""
# Broken server with syntax error
def broken_function(
    print("Missing closing parenthesis")
""")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        engine.reporter.reports_directory = Path(temp_reports_dir)
        engine.reporter.reports_directory.mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "detailed").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "summaries").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "diagnostics").mkdir(exist_ok=True)
        
        # Mock failed server startup
        with patch.object(engine, '_start_server_process') as mock_start:
            mock_start.return_value = None  # Failed to start
            
            # Run comprehensive validation
            result = engine.run_comprehensive_tests(temp_project_dir)
        
        # Verify validation failed
        assert result["success"] is False
        assert "diagnostics" in result
        
        # Verify diagnostics information
        diagnostics = result["diagnostics"]
        assert "failure_analysis" in diagnostics
        assert "diagnostic_results" in diagnostics
        assert "root_cause_analysis" in diagnostics
        assert "fix_recommendations" in diagnostics
    
    def test_validation_history_tracking(self, temp_project_dir, temp_reports_dir):
        """Test validation history tracking across multiple runs."""
        # Create a simple project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("print('Hello, MCP!')")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        engine.reporter.reports_directory = Path(temp_reports_dir)
        engine.reporter.reports_directory.mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "detailed").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "summaries").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "diagnostics").mkdir(exist_ok=True)
        
        # Mock server execution for multiple runs
        with patch.object(engine, '_start_server_process') as mock_start:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_start.return_value = mock_process
            
            with patch.object(engine, '_test_mcp_initialization') as mock_init:
                mock_init.return_value = {"success": True, "capabilities": ["initialize"]}
                
                with patch.object(engine, '_test_mcp_method') as mock_method:
                    mock_method.return_value = True
                    
                    with patch.object(engine, '_test_tools_functionality') as mock_tools:
                        mock_tools.return_value = {"tools": {}, "errors": [], "response_time": 0.1}
                        
                        with patch.object(engine, '_test_resources_functionality') as mock_resources:
                            mock_resources.return_value = {"resources": {}, "errors": [], "response_time": 0.1}
                            
                            with patch.object(engine, '_test_prompts_functionality') as mock_prompts:
                                mock_prompts.return_value = {"prompts": {}, "errors": [], "response_time": 0.1}
                                
                                # Run validation multiple times
                                for i in range(3):
                                    engine.run_comprehensive_tests(temp_project_dir)
        
        # Check validation history
        history = engine.get_validation_history(temp_project_dir)
        
        # Should have at least 3 entries for this project (may have more from other tests)
        project_entries = [entry for entry in history if entry["project_path"] == temp_project_dir]
        assert len(project_entries) >= 3
        assert all(entry["project_path"] == temp_project_dir for entry in project_entries)
    
    def test_trend_analysis_generation(self, temp_project_dir, temp_reports_dir):
        """Test trend analysis generation."""
        # Create a project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("print('Hello, MCP!')")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        engine.reporter.reports_directory = Path(temp_reports_dir)
        engine.reporter.reports_directory.mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "detailed").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "summaries").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "diagnostics").mkdir(exist_ok=True)
        
        # Mock validation runs with different outcomes
        with patch.object(engine, '_start_server_process') as mock_start:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_start.return_value = mock_process
            
            with patch.object(engine, '_test_mcp_initialization') as mock_init:
                mock_init.return_value = {"success": True, "capabilities": ["initialize"]}
                
                with patch.object(engine, '_test_mcp_method') as mock_method:
                    mock_method.return_value = True
                    
                    with patch.object(engine, '_test_tools_functionality') as mock_tools:
                        mock_tools.return_value = {"tools": {}, "errors": [], "response_time": 0.1}
                        
                        with patch.object(engine, '_test_resources_functionality') as mock_resources:
                            mock_resources.return_value = {"resources": {}, "errors": [], "response_time": 0.1}
                            
                            with patch.object(engine, '_test_prompts_functionality') as mock_prompts:
                                mock_prompts.return_value = {"prompts": {}, "errors": [], "response_time": 0.1}
                                
                                # Run successful validation
                                engine.run_comprehensive_tests(temp_project_dir)
                                
                                # Run failed validation
                                mock_start.return_value = None  # Simulate failure
                                engine.run_comprehensive_tests(temp_project_dir)
        
        # Generate trend analysis
        trend_analysis = engine.generate_trend_analysis(temp_project_dir)
        
        assert "total_validations" in trend_analysis
        assert "success_rate" in trend_analysis
        assert "trends" in trend_analysis
        assert "recommendations" in trend_analysis
    
    def test_diagnostic_report_generation(self, temp_project_dir):
        """Test standalone diagnostic report generation."""
        # Create a project with some issues
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("# Empty server file")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        
        # Generate diagnostic report
        diagnostic_report = engine.generate_diagnostic_report(temp_project_dir)
        
        assert "project_path" in diagnostic_report
        assert "diagnostic_summary" in diagnostic_report
        assert "detailed_results" in diagnostic_report
        assert "system_info" in diagnostic_report
        assert "environment_analysis" in diagnostic_report
        
        # Check that diagnostic checks were run
        detailed_results = diagnostic_report["detailed_results"]
        assert len(detailed_results) > 0
        
        # Verify diagnostic check structure
        for result in detailed_results:
            assert "check" in result
            assert "status" in result
            assert "message" in result
            assert "suggestions" in result
    
    def test_diagnostics_only_execution(self, temp_project_dir):
        """Test running diagnostics without full validation."""
        # Create a project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("print('Hello, MCP!')")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        
        # Run diagnostics only
        diagnostic_results = engine.run_diagnostics_only(temp_project_dir)
        
        assert len(diagnostic_results) > 0
        
        # Verify diagnostic result structure
        for result in diagnostic_results:
            assert "check" in result
            assert "status" in result
            assert "message" in result
            assert "details" in result
            assert "suggestions" in result
            
            assert result["status"] in ["PASS", "FAIL", "WARNING", "INFO"]
    
    def test_actionable_recommendations_extraction(self, temp_project_dir, temp_reports_dir):
        """Test extraction of actionable recommendations."""
        # Create a broken project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("# Minimal server")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        engine.reporter.reports_directory = Path(temp_reports_dir)
        engine.reporter.reports_directory.mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "detailed").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "summaries").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "diagnostics").mkdir(exist_ok=True)
        
        # Mock failed validation
        with patch.object(engine, '_start_server_process') as mock_start:
            mock_start.return_value = None  # Failed to start
            
            # Run validation
            result = engine.run_comprehensive_tests(temp_project_dir)
        
        # Extract actionable recommendations
        validation_report = result["report"]
        recommendations = engine.get_actionable_recommendations(validation_report)
        
        assert len(recommendations) > 0
        
        # Verify recommendation structure
        for rec in recommendations:
            assert "priority" in rec
            assert "category" in rec
            assert "issue" in rec
            assert "impact" in rec
            assert "action_steps" in rec
            assert "estimated_effort" in rec
            
            assert rec["priority"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert isinstance(rec["action_steps"], list)
            assert len(rec["action_steps"]) > 0
    
    def test_report_export_functionality(self, temp_project_dir, temp_reports_dir):
        """Test report export in different formats."""
        # Create a simple project
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("print('Hello, MCP!')")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        engine.reporter.reports_directory = Path(temp_reports_dir)
        engine.reporter.reports_directory.mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "detailed").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "summaries").mkdir(exist_ok=True)
        (engine.reporter.reports_directory / "diagnostics").mkdir(exist_ok=True)
        
        # Mock validation
        with patch.object(engine, '_start_server_process') as mock_start:
            mock_process = Mock()
            mock_process.pid = 12345
            mock_process.poll.return_value = None
            mock_start.return_value = mock_process
            
            with patch.object(engine, '_test_mcp_initialization') as mock_init:
                mock_init.return_value = {"success": True, "capabilities": ["initialize"]}
                
                with patch.object(engine, '_test_mcp_method') as mock_method:
                    mock_method.return_value = True
                    
                    with patch.object(engine, '_test_tools_functionality') as mock_tools:
                        mock_tools.return_value = {"tools": {}, "errors": [], "response_time": 0.1}
                        
                        with patch.object(engine, '_test_resources_functionality') as mock_resources:
                            mock_resources.return_value = {"resources": {}, "errors": [], "response_time": 0.1}
                            
                            with patch.object(engine, '_test_prompts_functionality') as mock_prompts:
                                mock_prompts.return_value = {"prompts": {}, "errors": [], "response_time": 0.1}
                                
                                # Run validation
                                result = engine.run_comprehensive_tests(temp_project_dir)
        
        validation_report = result["report"]
        
        # Export in different formats
        detailed_path = engine.export_validation_report(validation_report, "json")
        summary_path = engine.export_validation_report(validation_report, "summary")
        
        assert Path(detailed_path).exists()
        assert Path(summary_path).exists()
        
        # Verify file contents
        with open(detailed_path) as f:
            detailed_content = json.load(f)
        assert "metadata" in detailed_content
        
        with open(summary_path) as f:
            summary_content = json.load(f)
        assert "project" in summary_content


if __name__ == "__main__":
    pytest.main([__file__])