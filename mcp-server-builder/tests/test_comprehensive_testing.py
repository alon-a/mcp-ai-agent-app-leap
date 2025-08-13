"""Tests for the Comprehensive Server Testing Framework."""

import pytest
import tempfile
import json
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.managers.comprehensive_testing import (
    ComprehensiveServerTester, PerformanceBenchmark, IntegrationTestResult,
    ComprehensiveTestReport
)
from src.managers.validation_engine import MCPValidationEngine
from src.models.base import ValidationReport, ServerStartupResult, ProtocolComplianceResult, FunctionalityTestResult
from src.models.enums import ValidationLevel


class TestComprehensiveServerTester:
    """Test cases for ComprehensiveServerTester."""
    
    @pytest.fixture
    def validation_engine(self):
        """Create a ValidationEngine instance for testing."""
        return MCPValidationEngine(timeout=10, validation_level=ValidationLevel.STANDARD)
    
    @pytest.fixture
    def comprehensive_tester(self, validation_engine):
        """Create a ComprehensiveServerTester instance for testing."""
        return ComprehensiveServerTester(validation_engine, max_workers=2)
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            
            # Create a simple Python server file
            main_py = project_path / "main.py"
            main_py.write_text("""
import json
import sys

def main():
    while True:
        try:
            line = sys.stdin.readline()
            if not line:
                break
            request = json.loads(line.strip())
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": {}}
            print(json.dumps(response))
            sys.stdout.flush()
        except Exception:
            break

if __name__ == "__main__":
    main()
""")
            
            yield str(project_path)
    
    def test_init(self, validation_engine):
        """Test ComprehensiveServerTester initialization."""
        tester = ComprehensiveServerTester(validation_engine, max_workers=8)
        assert tester.validation_engine == validation_engine
        assert tester.max_workers == 8
        assert tester.active_processes == []
    
    @patch.object(MCPValidationEngine, 'run_comprehensive_tests')
    def test_run_comprehensive_tests_basic_validation_failure(self, mock_basic_tests, comprehensive_tester, temp_project_dir):
        """Test comprehensive tests when basic validation fails."""
        # Mock failed basic validation
        mock_validation_report = Mock(spec=ValidationReport)
        mock_validation_report.overall_success = False
        mock_validation_report.recommendations = ["Fix basic issues"]
        
        mock_basic_tests.return_value = {
            "success": False,
            "report": mock_validation_report
        }
        
        result = comprehensive_tester.run_comprehensive_tests(
            temp_project_dir,
            include_performance=True,
            include_integration=True,
            include_load_testing=True,
            include_security_scan=True
        )
        
        assert isinstance(result, ComprehensiveTestReport)
        assert result.overall_success is False
        assert result.project_path == temp_project_dir
        assert len(result.performance_benchmarks) == 0  # Should skip performance tests
        assert len(result.integration_results) == 0  # Should skip integration tests
    
    @patch.object(MCPValidationEngine, 'run_comprehensive_tests')
    @patch.object(ComprehensiveServerTester, '_run_performance_benchmarks')
    @patch.object(ComprehensiveServerTester, '_run_integration_tests')
    @patch.object(ComprehensiveServerTester, '_run_load_tests')
    @patch.object(ComprehensiveServerTester, '_run_security_scan')
    def test_run_comprehensive_tests_success(
        self, mock_security, mock_load, mock_integration, mock_performance, mock_basic_tests,
        comprehensive_tester, temp_project_dir
    ):
        """Test successful comprehensive tests."""
        # Mock successful basic validation
        mock_validation_report = Mock(spec=ValidationReport)
        mock_validation_report.overall_success = True
        mock_validation_report.recommendations = ["Basic recommendation"]
        
        mock_basic_tests.return_value = {
            "success": True,
            "report": mock_validation_report
        }
        
        # Mock successful performance benchmarks
        mock_performance.return_value = [
            PerformanceBenchmark(
                operation_name="test_op",
                total_requests=100,
                successful_requests=100,
                failed_requests=0,
                average_response_time=0.1,
                min_response_time=0.05,
                max_response_time=0.2,
                percentile_95_response_time=0.15,
                requests_per_second=1000.0,
                error_rate=0.0,
                memory_usage_mb=50.0,
                cpu_usage_percent=10.0
            )
        ]
        
        # Mock successful integration tests
        mock_integration.return_value = [
            IntegrationTestResult(
                client_name="Test Client",
                connection_successful=True,
                handshake_time=0.1,
                supported_features=["tools", "resources"],
                failed_features=[],
                compatibility_score=1.0,
                errors=[]
            )
        ]
        
        # Mock successful load tests
        mock_load.return_value = {
            "success": True,
            "error_rate": 0.01,
            "concurrent_users": 10
        }
        
        # Mock successful security scan
        mock_security.return_value = {
            "success": True,
            "critical_issues": 0,
            "high_issues": 0
        }
        
        result = comprehensive_tester.run_comprehensive_tests(temp_project_dir)
        
        assert isinstance(result, ComprehensiveTestReport)
        assert result.overall_success is True
        assert len(result.performance_benchmarks) == 1
        assert len(result.integration_results) == 1
        assert result.load_test_results["success"] is True
        assert result.security_scan_results["success"] is True
    
    @patch.object(ComprehensiveServerTester, '_start_server_for_testing')
    def test_run_performance_benchmarks_no_server(self, mock_start_server, comprehensive_tester, temp_project_dir):
        """Test performance benchmarks when server fails to start."""
        mock_start_server.return_value = None
        
        result = comprehensive_tester._run_performance_benchmarks(temp_project_dir)
        
        assert result == []
    
    @patch.object(ComprehensiveServerTester, '_start_server_for_testing')
    @patch.object(ComprehensiveServerTester, '_stop_server_process')
    @patch.object(ComprehensiveServerTester, '_benchmark_operation')
    @patch('time.sleep')
    def test_run_performance_benchmarks_success(
        self, mock_sleep, mock_benchmark, mock_stop_server, mock_start_server,
        comprehensive_tester, temp_project_dir
    ):
        """Test successful performance benchmarks."""
        # Mock server process
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock benchmark results
        mock_benchmark.return_value = PerformanceBenchmark(
            operation_name="test_op",
            total_requests=50,
            successful_requests=50,
            failed_requests=0,
            average_response_time=0.1,
            min_response_time=0.05,
            max_response_time=0.2,
            percentile_95_response_time=0.15,
            requests_per_second=500.0,
            error_rate=0.0,
            memory_usage_mb=30.0,
            cpu_usage_percent=5.0
        )
        
        result = comprehensive_tester._run_performance_benchmarks(temp_project_dir)
        
        assert len(result) > 0
        assert all(isinstance(benchmark, PerformanceBenchmark) for benchmark in result)
        mock_stop_server.assert_called_once_with(mock_process)
    
    @patch('subprocess.Popen')
    @patch('psutil.Process')
    @patch('time.sleep')
    def test_benchmark_operation(self, mock_sleep, mock_psutil_process, mock_popen, comprehensive_tester):
        """Test benchmarking a specific operation."""
        # Mock process
        mock_process = Mock()
        mock_process.stdin = Mock()
        mock_process.pid = 12345
        
        # Mock psutil process
        mock_psutil_instance = Mock()
        mock_psutil_instance.memory_info.return_value.rss = 50 * 1024 * 1024  # 50MB
        mock_psutil_instance.cpu_percent.return_value = 10.0
        mock_psutil_process.return_value = mock_psutil_instance
        
        # Request generator
        def request_generator():
            return {"jsonrpc": "2.0", "method": "test", "params": {}}
        
        result = comprehensive_tester._benchmark_operation(
            mock_process, "test_operation", request_generator, 10
        )
        
        assert isinstance(result, PerformanceBenchmark)
        assert result.operation_name == "test_operation"
        assert result.total_requests == 10
        assert result.successful_requests >= 0
        assert result.failed_requests >= 0
        assert result.memory_usage_mb > 0
    
    @patch.object(ComprehensiveServerTester, '_start_server_for_testing')
    def test_run_integration_tests_no_server(self, mock_start_server, comprehensive_tester, temp_project_dir):
        """Test integration tests when server fails to start."""
        mock_start_server.return_value = None
        
        result = comprehensive_tester._run_integration_tests(temp_project_dir)
        
        assert result == []
    
    @patch.object(ComprehensiveServerTester, '_start_server_for_testing')
    @patch.object(ComprehensiveServerTester, '_stop_server_process')
    @patch.object(ComprehensiveServerTester, '_test_client_integration')
    @patch('time.sleep')
    def test_run_integration_tests_success(
        self, mock_sleep, mock_test_client, mock_stop_server, mock_start_server,
        comprehensive_tester, temp_project_dir
    ):
        """Test successful integration tests."""
        # Mock server process
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock integration test results
        mock_test_client.return_value = IntegrationTestResult(
            client_name="Test Client",
            connection_successful=True,
            handshake_time=0.1,
            supported_features=["tools"],
            failed_features=[],
            compatibility_score=1.0,
            errors=[]
        )
        
        result = comprehensive_tester._run_integration_tests(temp_project_dir)
        
        assert len(result) > 0
        assert all(isinstance(integration, IntegrationTestResult) for integration in result)
        mock_stop_server.assert_called_once_with(mock_process)
    
    def test_test_client_integration_success(self, comprehensive_tester):
        """Test successful client integration testing."""
        # Mock server process
        mock_process = Mock()
        mock_process.stdin = Mock()
        
        client_config = {
            "name": "Test Client",
            "capabilities": ["tools", "resources"],
            "protocol_version": "2024-11-05"
        }
        
        with patch.object(comprehensive_tester, '_test_capability_integration', return_value=True), \
             patch.object(comprehensive_tester, '_test_tool_execution_integration', return_value=True), \
             patch.object(comprehensive_tester, '_test_resource_access_integration', return_value=True), \
             patch('time.sleep'):
            
            result = comprehensive_tester._test_client_integration(mock_process, client_config)
        
        assert isinstance(result, IntegrationTestResult)
        assert result.client_name == "Test Client"
        assert result.connection_successful is True
        assert result.compatibility_score > 0.0
        assert "tools" in result.supported_features
        assert "resources" in result.supported_features
    
    def test_test_client_integration_failure(self, comprehensive_tester):
        """Test client integration testing with failures."""
        # Mock server process that fails
        mock_process = Mock()
        mock_process.stdin.write.side_effect = Exception("Connection failed")
        
        client_config = {
            "name": "Failing Client",
            "capabilities": ["tools"],
            "protocol_version": "2024-11-05"
        }
        
        result = comprehensive_tester._test_client_integration(mock_process, client_config)
        
        assert isinstance(result, IntegrationTestResult)
        assert result.client_name == "Failing Client"
        assert result.connection_successful is False
        assert len(result.errors) > 0
        assert result.compatibility_score == 0.0
    
    @patch.object(ComprehensiveServerTester, '_start_server_for_testing')
    def test_run_load_tests_no_server(self, mock_start_server, comprehensive_tester, temp_project_dir):
        """Test load tests when server fails to start."""
        mock_start_server.return_value = None
        
        result = comprehensive_tester._run_load_tests(temp_project_dir)
        
        assert result["success"] is False
        assert len(result["errors"]) > 0
    
    @patch.object(ComprehensiveServerTester, '_start_server_for_testing')
    @patch.object(ComprehensiveServerTester, '_stop_server_process')
    @patch.object(ComprehensiveServerTester, '_execute_load_test')
    @patch('time.sleep')
    def test_run_load_tests_success(
        self, mock_sleep, mock_execute_load, mock_stop_server, mock_start_server,
        comprehensive_tester, temp_project_dir
    ):
        """Test successful load tests."""
        # Mock server process
        mock_process = Mock()
        mock_start_server.return_value = mock_process
        
        # Mock load test results
        mock_execute_load.return_value = {
            "concurrent_users": 5,
            "total_requests": 250,
            "successful_requests": 245,
            "failed_requests": 5,
            "error_rate": 0.02,
            "requests_per_second": 50.0
        }
        
        result = comprehensive_tester._run_load_tests(temp_project_dir)
        
        assert result["success"] is True
        assert result["error_rate"] == 0.02
        assert result["concurrent_users"] == 5
        mock_stop_server.assert_called_once_with(mock_process)
    
    @patch('psutil.Process')
    @patch.object(ComprehensiveServerTester, '_simulate_user_load')
    @patch.object(ComprehensiveServerTester, '_monitor_system_resources')
    def test_execute_load_test(self, mock_monitor, mock_simulate_user, mock_psutil_process, comprehensive_tester):
        """Test load test execution."""
        # Mock process
        mock_process = Mock()
        mock_process.pid = 12345
        
        # Mock psutil process
        mock_psutil_instance = Mock()
        mock_psutil_instance.memory_info.return_value.rss = 100 * 1024 * 1024  # 100MB
        mock_psutil_process.return_value = mock_psutil_instance
        
        # Mock user simulation results
        mock_simulate_user.return_value = {
            "response_times": [0.1, 0.2, 0.15],
            "successful_requests": 48,
            "failed_requests": 2
        }
        
        result = comprehensive_tester._execute_load_test(mock_process, 2, 25)
        
        assert result["concurrent_users"] == 2
        assert result["total_requests"] == 100  # 2 users * 50 requests each (48+2 per user)
        assert result["successful_requests"] == 96  # 2 users * 48 successful each
        assert result["failed_requests"] == 4  # 2 users * 2 failed each
        assert result["error_rate"] == 0.04  # 4/100
    
    def test_simulate_user_load(self, comprehensive_tester):
        """Test user load simulation."""
        # Mock server process
        mock_process = Mock()
        mock_process.stdin = Mock()
        
        with patch('time.sleep'):  # Speed up the test
            result = comprehensive_tester._simulate_user_load(mock_process, 1, 10)
        
        assert "response_times" in result
        assert "successful_requests" in result
        assert "failed_requests" in result
        assert len(result["response_times"]) == 10
        assert result["successful_requests"] + result["failed_requests"] == 10
    
    def test_run_security_scan(self, comprehensive_tester, temp_project_dir):
        """Test security scan execution."""
        # Create some test files
        project_dir = Path(temp_project_dir)
        
        # Create a Python file with security issues
        test_py = project_dir / "test.py"
        test_py.write_text("""
import os
password = "hardcoded_password"
os.system("rm -rf /")  # Dangerous command
eval(user_input)  # Code injection
""")
        
        # Create a requirements file with vulnerable dependency
        requirements = project_dir / "requirements.txt"
        requirements.write_text("requests==2.19.0\nflask==0.12")
        
        result = comprehensive_tester._run_security_scan(temp_project_dir)
        
        assert result["success"] is True
        assert result["total_issues"] > 0
        assert result["scanned_files"] > 0
        assert len(result["issues"]) > 0
        
        # Check that security issues were detected
        issue_types = [issue["type"] for issue in result["issues"]]
        assert "code_security" in issue_types or "dependency_vulnerability" in issue_types
    
    def test_scan_dependency_vulnerabilities(self, comprehensive_tester, temp_project_dir):
        """Test dependency vulnerability scanning."""
        project_dir = Path(temp_project_dir)
        
        # Create requirements.txt with vulnerable packages
        requirements = project_dir / "requirements.txt"
        requirements.write_text("requests==2.19.0\nflask==0.12\npyyaml==3.13")
        
        result = comprehensive_tester._scan_dependency_vulnerabilities(project_dir)
        
        assert result["medium_issues"] > 0 or result["high_issues"] > 0
        assert len(result["issues"]) > 0
        
        # Check that vulnerable packages were detected
        descriptions = [issue["description"] for issue in result["issues"]]
        assert any("Flask" in desc or "requests" in desc or "PyYAML" in desc for desc in descriptions)
    
    def test_scan_code_security_issues(self, comprehensive_tester, temp_project_dir):
        """Test code security issue scanning."""
        project_dir = Path(temp_project_dir)
        
        # Create Python file with security issues
        test_py = project_dir / "vulnerable.py"
        test_py.write_text("""
import os
import subprocess

# Security vulnerabilities
eval("print('hello')")
exec("import sys")
os.system("ls -la")
subprocess.call("rm file", shell=True)
password = "secret123"
api_key = "abc123def456"
""")
        
        result = comprehensive_tester._scan_code_security_issues(project_dir)
        
        assert result["critical_issues"] > 0 or result["high_issues"] > 0 or result["medium_issues"] > 0
        assert len(result["issues"]) > 0
        
        # Check that security issues were detected
        descriptions = [issue["description"] for issue in result["issues"]]
        assert any("eval" in desc or "exec" in desc or "password" in desc for desc in descriptions)
    
    def test_scan_configuration_security(self, comprehensive_tester, temp_project_dir):
        """Test configuration security scanning."""
        project_dir = Path(temp_project_dir)
        
        # Create sensitive files
        env_file = project_dir / ".env"
        env_file.write_text("SECRET_KEY=mysecret\nAPI_KEY=abc123")
        
        secrets_file = project_dir / "secrets.json"
        secrets_file.write_text('{"password": "secret"}')
        
        result = comprehensive_tester._scan_configuration_security(project_dir)
        
        assert result["high_issues"] > 0 or result["critical_issues"] > 0
        assert len(result["issues"]) > 0
        
        # Check that sensitive files were detected
        filenames = [issue["file"] for issue in result["issues"]]
        assert any(".env" in filename or "secrets.json" in filename for filename in filenames)
    
    def test_generate_comprehensive_recommendations(self, comprehensive_tester):
        """Test comprehensive recommendation generation."""
        # Mock validation report
        mock_validation = Mock(spec=ValidationReport)
        mock_validation.recommendations = ["Basic recommendation"]
        mock_validation.overall_success = False
        
        # Create performance benchmarks with issues
        performance_benchmarks = [
            PerformanceBenchmark(
                operation_name="slow_op",
                total_requests=100,
                successful_requests=90,
                failed_requests=10,
                average_response_time=2.0,  # Slow
                min_response_time=1.0,
                max_response_time=5.0,
                percentile_95_response_time=4.0,
                requests_per_second=50.0,
                error_rate=0.1,  # High error rate
                memory_usage_mb=150.0,  # High memory
                cpu_usage_percent=80.0
            )
        ]
        
        # Create integration results with issues
        integration_results = [
            IntegrationTestResult(
                client_name="Problematic Client",
                connection_successful=True,
                handshake_time=0.5,
                supported_features=["tools"],
                failed_features=["resources", "prompts"],
                compatibility_score=0.3,  # Low compatibility
                errors=["Feature not supported"]
            )
        ]
        
        # Load test results with issues
        load_test_results = {
            "error_rate": 0.15,  # High error rate
            "concurrent_users": 5  # Low concurrency
        }
        
        # Security scan results with issues
        security_scan_results = {
            "critical_issues": 2,
            "high_issues": 3,
            "recommendations": ["Fix critical vulnerabilities"]
        }
        
        recommendations = comprehensive_tester._generate_comprehensive_recommendations(
            mock_validation,
            performance_benchmarks,
            integration_results,
            load_test_results,
            security_scan_results
        )
        
        assert len(recommendations) > 0
        assert "Basic recommendation" in recommendations
        assert any("slow_op" in rec for rec in recommendations)
        assert any("Problematic Client" in rec for rec in recommendations)
        assert any("stability under load" in rec for rec in recommendations)
        assert any("URGENT" in rec for rec in recommendations)
    
    def test_cleanup_processes(self, comprehensive_tester):
        """Test process cleanup."""
        # Create mock processes
        mock_process1 = Mock()
        mock_process1.poll.return_value = None  # Still running
        mock_process2 = Mock()
        mock_process2.poll.return_value = 0  # Already terminated
        
        comprehensive_tester.active_processes = [mock_process1, mock_process2]
        
        comprehensive_tester._cleanup_processes()
        
        # Should terminate the running process
        mock_process1.terminate.assert_called_once()
        # Should not terminate the already terminated process
        mock_process2.terminate.assert_not_called()
        
        # Processes list should be cleared
        assert comprehensive_tester.active_processes == []


class TestPerformanceBenchmark:
    """Test cases for PerformanceBenchmark dataclass."""
    
    def test_performance_benchmark_creation(self):
        """Test PerformanceBenchmark creation."""
        benchmark = PerformanceBenchmark(
            operation_name="test_op",
            total_requests=100,
            successful_requests=95,
            failed_requests=5,
            average_response_time=0.1,
            min_response_time=0.05,
            max_response_time=0.5,
            percentile_95_response_time=0.3,
            requests_per_second=1000.0,
            error_rate=0.05,
            memory_usage_mb=50.0,
            cpu_usage_percent=10.0
        )
        
        assert benchmark.operation_name == "test_op"
        assert benchmark.total_requests == 100
        assert benchmark.successful_requests == 95
        assert benchmark.failed_requests == 5
        assert benchmark.error_rate == 0.05


class TestIntegrationTestResult:
    """Test cases for IntegrationTestResult dataclass."""
    
    def test_integration_test_result_creation(self):
        """Test IntegrationTestResult creation."""
        result = IntegrationTestResult(
            client_name="Test Client",
            connection_successful=True,
            handshake_time=0.1,
            supported_features=["tools", "resources"],
            failed_features=["prompts"],
            compatibility_score=0.8,
            errors=["Minor issue"]
        )
        
        assert result.client_name == "Test Client"
        assert result.connection_successful is True
        assert result.handshake_time == 0.1
        assert "tools" in result.supported_features
        assert "prompts" in result.failed_features
        assert result.compatibility_score == 0.8
        assert len(result.errors) == 1


class TestComprehensiveTestReport:
    """Test cases for ComprehensiveTestReport dataclass."""
    
    def test_comprehensive_test_report_creation(self):
        """Test ComprehensiveTestReport creation."""
        mock_validation = Mock(spec=ValidationReport)
        
        report = ComprehensiveTestReport(
            project_path="/test/path",
            test_timestamp="2024-01-01T00:00:00",
            overall_success=True,
            basic_validation=mock_validation,
            performance_benchmarks=[],
            integration_results=[],
            load_test_results={},
            security_scan_results={},
            recommendations=["Test recommendation"],
            total_test_duration=10.5
        )
        
        assert report.project_path == "/test/path"
        assert report.overall_success is True
        assert report.basic_validation == mock_validation
        assert len(report.recommendations) == 1
        assert report.total_test_duration == 10.5