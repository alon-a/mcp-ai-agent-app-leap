"""Tests for validation diagnostics functionality."""

import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.managers.validation_diagnostics import ValidationDiagnostics, DiagnosticResult
from src.models.base import (
    ValidationReport, ServerStartupResult, ProtocolComplianceResult,
    FunctionalityTestResult
)
from src.models.enums import ValidationLevel


@pytest.fixture
def temp_project_dir():
    """Create a temporary project directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()
        yield str(project_path)


@pytest.fixture
def sample_failed_validation_report():
    """Create a sample failed validation report for testing."""
    startup_result = ServerStartupResult(
        success=False,
        process_id=None,
        startup_time=0.0,
        errors=["ImportError: No module named 'mcp'", "Permission denied"],
        logs=[]
    )
    
    protocol_result = ProtocolComplianceResult(
        success=False,
        supported_capabilities=["initialize"],
        missing_capabilities=["tools/list", "resources/list"],
        protocol_version=None,
        errors=["Protocol initialization failed"]
    )
    
    functionality_result = FunctionalityTestResult(
        success=False,
        tested_tools={},
        tested_resources={},
        tested_prompts={},
        errors=["No capabilities found"],
        performance_metrics={}
    )
    
    return ValidationReport(
        project_path="/test/failed_project",
        validation_level=ValidationLevel.STANDARD,
        overall_success=False,
        startup_result=startup_result,
        protocol_result=protocol_result,
        functionality_result=functionality_result,
        performance_metrics={"startup_time": 0.0},
        recommendations=["Fix server startup issues"],
        timestamp="2024-01-01T12:00:00",
        total_execution_time=1.0
    )


class TestValidationDiagnostics:
    """Test cases for ValidationDiagnostics."""
    
    def test_initialization(self):
        """Test diagnostics initialization."""
        diagnostics = ValidationDiagnostics()
        
        assert len(diagnostics.diagnostic_checks) > 0
        assert callable(diagnostics.diagnostic_checks[0])
    
    def test_python_environment_check_success(self, temp_project_dir):
        """Test Python environment check with compatible version."""
        diagnostics = ValidationDiagnostics()
        
        result = diagnostics._check_python_environment(temp_project_dir)
        
        assert isinstance(result, DiagnosticResult)
        assert result.check_name == "python_environment"
        # Should pass with current Python version (assuming >= 3.8)
        assert result.status in ["PASS", "FAIL"]  # Depends on actual Python version
        assert "python_version" in result.details
    
    def test_project_structure_check_missing_directory(self):
        """Test project structure check with missing directory."""
        diagnostics = ValidationDiagnostics()
        
        result = diagnostics._check_project_structure("/nonexistent/path")
        
        assert result.check_name == "project_structure"
        assert result.status == "FAIL"
        assert "does not exist" in result.message
        assert len(result.suggestions) > 0
    
    def test_project_structure_check_empty_directory(self, temp_project_dir):
        """Test project structure check with empty directory."""
        diagnostics = ValidationDiagnostics()
        
        result = diagnostics._check_project_structure(temp_project_dir)
        
        assert result.check_name == "project_structure"
        assert result.status == "FAIL"
        assert "No server entry point files found" in result.message
        assert len(result.suggestions) > 0
    
    def test_project_structure_check_with_server_files(self, temp_project_dir):
        """Test project structure check with server files present."""
        # Create a server file
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("# MCP Server\nprint('Hello, MCP!')")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_project_structure(temp_project_dir)
        
        assert result.check_name == "project_structure"
        assert result.status in ["PASS", "WARNING"]  # May warn about missing config files
        assert "main.py" in result.details["server_files_found"]
    
    def test_dependencies_check_with_requirements(self, temp_project_dir):
        """Test dependencies check with requirements.txt."""
        # Create requirements.txt
        requirements_file = Path(temp_project_dir) / "requirements.txt"
        requirements_file.write_text("requests>=2.25.0\nnumpy==1.21.0\n")
        
        diagnostics = ValidationDiagnostics()
        
        with patch.object(diagnostics, '_is_package_installed', return_value=True):
            result = diagnostics._check_dependencies(temp_project_dir)
        
        assert result.check_name == "dependencies"
        assert result.status == "PASS"
        assert "requirements.txt" in result.details["dependency_files"]
    
    def test_dependencies_check_missing_packages(self, temp_project_dir):
        """Test dependencies check with missing packages."""
        # Create requirements.txt
        requirements_file = Path(temp_project_dir) / "requirements.txt"
        requirements_file.write_text("nonexistent_package>=1.0.0\n")
        
        diagnostics = ValidationDiagnostics()
        
        with patch.object(diagnostics, '_is_package_installed', return_value=False):
            result = diagnostics._check_dependencies(temp_project_dir)
        
        assert result.check_name == "dependencies"
        assert result.status == "FAIL"
        assert "Missing dependencies" in result.message
        assert len(result.suggestions) > 0
    
    def test_file_permissions_check(self, temp_project_dir):
        """Test file permissions check."""
        # Create a server file
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("# MCP Server")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_file_permissions(temp_project_dir)
        
        assert result.check_name == "file_permissions"
        assert result.status == "PASS"  # Should pass with normal file permissions
        assert "main.py" in result.details["file_permissions"]
    
    def test_entry_points_check_valid_python(self, temp_project_dir):
        """Test entry points check with valid Python file."""
        # Create a valid Python server file
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("""
import json

def main():
    print("MCP Server starting...")

if __name__ == "__main__":
    main()
""")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_entry_points(temp_project_dir)
        
        assert result.check_name == "entry_points"
        assert result.status == "PASS"
        assert "main.py" in result.details["entry_points"]
        assert len(result.details["syntax_errors"]) == 0
    
    def test_entry_points_check_syntax_error(self, temp_project_dir):
        """Test entry points check with syntax error."""
        # Create a Python file with syntax error
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("def invalid_syntax(\nprint('missing closing parenthesis')")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_entry_points(temp_project_dir)
        
        assert result.check_name == "entry_points"
        assert result.status == "FAIL"
        assert len(result.details["syntax_errors"]) > 0
        assert "main.py" in result.details["syntax_errors"][0]
    
    def test_entry_points_check_package_json(self, temp_project_dir):
        """Test entry points check with package.json."""
        # Create package.json
        package_json = Path(temp_project_dir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "mcp-server",
            "version": "1.0.0",
            "main": "server.js",
            "scripts": {
                "start": "node server.js"
            }
        }))
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_entry_points(temp_project_dir)
        
        assert result.check_name == "entry_points"
        assert result.status == "PASS"
        assert any("npm start" in ep for ep in result.details["entry_points"])
    
    def test_mcp_compliance_check_no_mcp(self, temp_project_dir):
        """Test MCP compliance check with no MCP indicators."""
        # Create a non-MCP Python file
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("print('Hello, World!')")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_mcp_compliance(temp_project_dir)
        
        assert result.check_name == "mcp_compliance"
        assert result.status == "FAIL"
        assert "Missing essential MCP elements" in result.message
    
    def test_mcp_compliance_check_with_mcp(self, temp_project_dir):
        """Test MCP compliance check with MCP indicators."""
        # Create an MCP-compliant Python file
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("""
import mcp
from mcp.server import Server

def initialize():
    server = Server("test-server")
    
    @server.tool()
    def sample_tool():
        return "Hello from MCP tool"
    
    return server

if __name__ == "__main__":
    server = initialize()
    server.run()
""")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_mcp_compliance(temp_project_dir)
        
        assert result.check_name == "mcp_compliance"
        assert result.status in ["PASS", "WARNING"]
        assert "mcp" in result.details["mcp_indicators"]
        assert "initialize" in result.details["mcp_indicators"]
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_resources_check_adequate(self, mock_disk, mock_memory, mock_cpu, temp_project_dir):
        """Test system resources check with adequate resources."""
        # Mock adequate system resources
        mock_cpu.return_value = 4
        mock_memory.return_value = Mock(total=8*1024**3, available=4*1024**3)  # 8GB total, 4GB available
        mock_disk.return_value = Mock(free=10*1024**3)  # 10GB free
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_system_resources(temp_project_dir)
        
        assert result.check_name == "system_resources"
        assert result.status == "PASS"
        assert result.details["memory_available_gb"] >= 0.5
        assert result.details["disk_free_gb"] >= 1.0
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_system_resources_check_low_resources(self, mock_disk, mock_memory, mock_cpu, temp_project_dir):
        """Test system resources check with low resources."""
        # Mock low system resources
        mock_cpu.return_value = 1
        mock_memory.return_value = Mock(total=1024**3, available=0.3*1024**3)  # 1GB total, 0.3GB available
        mock_disk.return_value = Mock(free=0.5*1024**3)  # 0.5GB free
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_system_resources(temp_project_dir)
        
        assert result.check_name == "system_resources"
        assert result.status == "WARNING"
        assert "Low available memory" in result.message or "Low disk space" in result.message
    
    @patch('socket.create_connection')
    def test_network_connectivity_check_success(self, mock_socket, temp_project_dir):
        """Test network connectivity check with successful connections."""
        # Mock successful connections
        mock_socket.return_value = Mock()
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_network_connectivity(temp_project_dir)
        
        assert result.check_name == "network_connectivity"
        assert result.status == "PASS"
        assert all("SUCCESS" in status for status in result.details["connectivity_tests"].values())
    
    @patch('socket.create_connection')
    def test_network_connectivity_check_failure(self, mock_socket, temp_project_dir):
        """Test network connectivity check with connection failures."""
        # Mock connection failures
        mock_socket.side_effect = Exception("Connection failed")
        
        diagnostics = ValidationDiagnostics()
        result = diagnostics._check_network_connectivity(temp_project_dir)
        
        assert result.check_name == "network_connectivity"
        assert result.status == "WARNING"
        assert "Network connectivity issues" in result.message
    
    def test_run_full_diagnostics(self, temp_project_dir):
        """Test running full diagnostics suite."""
        diagnostics = ValidationDiagnostics()
        
        results = diagnostics.run_full_diagnostics(temp_project_dir)
        
        assert len(results) > 0
        assert all(isinstance(result, DiagnosticResult) for result in results)
        
        # Check that all expected diagnostic checks are present
        check_names = [result.check_name for result in results]
        expected_checks = [
            "python_environment",
            "project_structure", 
            "dependencies",
            "file_permissions",
            "entry_points",
            "mcp_compliance",
            "system_resources",
            "network_connectivity"
        ]
        
        for expected_check in expected_checks:
            assert any(expected_check in name for name in check_names)
    
    def test_diagnose_validation_failure(self, sample_failed_validation_report):
        """Test diagnosing validation failure."""
        diagnostics = ValidationDiagnostics()
        
        diagnosis = diagnostics.diagnose_validation_failure(sample_failed_validation_report)
        
        assert "project_path" in diagnosis
        assert "failure_analysis" in diagnosis
        assert "diagnostic_results" in diagnosis
        assert "root_cause_analysis" in diagnosis
        assert "fix_recommendations" in diagnosis
        assert "automated_fixes" in diagnosis
        
        # Check failure analysis
        failure_analysis = diagnosis["failure_analysis"]
        assert "failure_types" in failure_analysis
        assert "startup_failure" in failure_analysis["failure_types"]
    
    def test_generate_diagnostic_report(self, temp_project_dir):
        """Test generating comprehensive diagnostic report."""
        diagnostics = ValidationDiagnostics()
        
        report = diagnostics.generate_diagnostic_report(temp_project_dir)
        
        assert "project_path" in report
        assert "diagnostic_summary" in report
        assert "detailed_results" in report
        assert "system_info" in report
        assert "environment_analysis" in report
        
        # Check diagnostic summary
        summary = report["diagnostic_summary"]
        assert "total_checks" in summary
        assert "passed" in summary
        assert "failed" in summary
        assert "warnings" in summary
        assert "health_score" in summary
    
    def test_root_cause_analysis_startup_failure(self, sample_failed_validation_report):
        """Test root cause analysis for startup failure."""
        diagnostics = ValidationDiagnostics()
        
        analysis = diagnostics._perform_root_cause_analysis(sample_failed_validation_report)
        
        assert analysis["primary_cause"] == "server_startup_failure"
        assert "missing_dependencies" in analysis["contributing_factors"]
        assert "permission_issues" in analysis["contributing_factors"]
        assert len(analysis["evidence"]) > 0
    
    def test_generate_fix_recommendations(self, sample_failed_validation_report):
        """Test generating fix recommendations."""
        diagnostics = ValidationDiagnostics()
        
        recommendations = diagnostics._generate_fix_recommendations(sample_failed_validation_report)
        
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "category" in rec
            assert "priority" in rec
            assert "title" in rec
            assert "steps" in rec
            assert isinstance(rec["steps"], list)
            assert len(rec["steps"]) > 0
    
    def test_suggest_automated_fixes(self, sample_failed_validation_report):
        """Test suggesting automated fixes."""
        diagnostics = ValidationDiagnostics()
        
        automated_fixes = diagnostics._suggest_automated_fixes(sample_failed_validation_report)
        
        # Should suggest creating missing files
        assert len(automated_fixes) > 0
        
        for fix in automated_fixes:
            assert "type" in fix
            assert "description" in fix
            assert "risk_level" in fix
    
    def test_is_package_installed_success(self):
        """Test package installation check for installed package."""
        diagnostics = ValidationDiagnostics()
        
        # Test with a standard library module that should be available
        result = diagnostics._is_package_installed("json")
        assert result is True
    
    def test_is_package_installed_failure(self):
        """Test package installation check for non-existent package."""
        diagnostics = ValidationDiagnostics()
        
        # Test with a package that definitely doesn't exist
        result = diagnostics._is_package_installed("definitely_nonexistent_package_12345")
        assert result is False
    
    def test_analyze_environment_python_project(self, temp_project_dir):
        """Test environment analysis for Python project."""
        # Create Python project files
        requirements_file = Path(temp_project_dir) / "requirements.txt"
        requirements_file.write_text("mcp>=1.0.0\n")
        
        server_file = Path(temp_project_dir) / "main.py"
        server_file.write_text("import mcp\nfrom fastmcp import FastMCP")
        
        diagnostics = ValidationDiagnostics()
        analysis = diagnostics._analyze_environment(temp_project_dir)
        
        assert analysis["project_type"] == "python"
        assert "requirements.txt" in analysis["configuration_files"]
        assert "FastMCP" in analysis["detected_frameworks"]
    
    def test_analyze_environment_nodejs_project(self, temp_project_dir):
        """Test environment analysis for Node.js project."""
        # Create Node.js project files
        package_json = Path(temp_project_dir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "mcp-server",
            "version": "1.0.0",
            "dependencies": {
                "@modelcontextprotocol/sdk": "^1.0.0"
            }
        }))
        
        diagnostics = ValidationDiagnostics()
        analysis = diagnostics._analyze_environment(temp_project_dir)
        
        assert analysis["project_type"] == "nodejs"
        assert "package.json" in analysis["configuration_files"]


if __name__ == "__main__":
    pytest.main([__file__])