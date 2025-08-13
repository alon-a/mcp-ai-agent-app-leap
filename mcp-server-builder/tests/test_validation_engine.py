"""Tests for the ValidationEngine implementation."""

import pytest
import tempfile
import json
import subprocess
import time
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.managers.validation_engine import MCPValidationEngine
from src.models.base import (
    ServerStartupResult, ProtocolComplianceResult, FunctionalityTestResult,
    ValidationReport
)
from src.models.enums import ValidationLevel


class TestMCPValidationEngine:
    """Test cases for MCPValidationEngine."""
    
    @pytest.fixture
    def validation_engine(self):
        """Create a ValidationEngine instance for testing."""
        return MCPValidationEngine(timeout=10, validation_level=ValidationLevel.STANDARD)
    
    @pytest.fixture
    def temp_project_dir(self):
        """Create a temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "test_project"
            project_path.mkdir()
            yield str(project_path)
    
    def test_init(self):
        """Test ValidationEngine initialization."""
        engine = MCPValidationEngine(timeout=20, validation_level=ValidationLevel.COMPREHENSIVE)
        assert engine.timeout == 20
        assert engine.validation_level == ValidationLevel.COMPREHENSIVE
        assert engine.active_processes == []
    
    def test_detect_server_entry_point_python_main(self, temp_project_dir):
        """Test detection of Python main.py entry point."""
        engine = MCPValidationEngine()
        
        # Create main.py file
        main_py = Path(temp_project_dir) / "main.py"
        main_py.write_text("# MCP Server main file")
        
        entry_point = engine._detect_server_entry_point(temp_project_dir)
        assert entry_point == "python main.py"
    
    def test_detect_server_entry_point_python_server(self, temp_project_dir):
        """Test detection of Python server.py entry point."""
        engine = MCPValidationEngine()
        
        # Create server.py file
        server_py = Path(temp_project_dir) / "server.py"
        server_py.write_text("# MCP Server file")
        
        entry_point = engine._detect_server_entry_point(temp_project_dir)
        assert entry_point == "python server.py"
    
    def test_detect_server_entry_point_nodejs(self, temp_project_dir):
        """Test detection of Node.js entry point from package.json."""
        engine = MCPValidationEngine()
        
        # Create package.json with start script
        package_json = Path(temp_project_dir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-server",
            "scripts": {
                "start": "node server.js"
            }
        }))
        
        entry_point = engine._detect_server_entry_point(temp_project_dir)
        assert entry_point == "npm start"
    
    def test_detect_server_entry_point_nodejs_main(self, temp_project_dir):
        """Test detection of Node.js entry point from package.json main field."""
        engine = MCPValidationEngine()
        
        # Create package.json with main field
        package_json = Path(temp_project_dir) / "package.json"
        package_json.write_text(json.dumps({
            "name": "test-server",
            "main": "index.js"
        }))
        
        entry_point = engine._detect_server_entry_point(temp_project_dir)
        assert entry_point == "node index.js"
    
    def test_detect_server_entry_point_poetry(self, temp_project_dir):
        """Test detection of Poetry entry point."""
        engine = MCPValidationEngine()
        
        # Create pyproject.toml file
        pyproject_toml = Path(temp_project_dir) / "pyproject.toml"
        pyproject_toml.write_text("[tool.poetry]\nname = 'test-server'")
        
        entry_point = engine._detect_server_entry_point(temp_project_dir)
        assert entry_point == "poetry run python -m server"
    
    def test_detect_server_entry_point_none(self, temp_project_dir):
        """Test when no entry point is detected."""
        engine = MCPValidationEngine()
        
        entry_point = engine._detect_server_entry_point(temp_project_dir)
        assert entry_point is None
    
    @patch('subprocess.Popen')
    def test_start_server_process_success(self, mock_popen, validation_engine):
        """Test successful server process start."""
        mock_process = Mock()
        mock_popen.return_value = mock_process
        
        result = validation_engine._start_server_process("/test/path", "python main.py")
        
        assert result == mock_process
        mock_popen.assert_called_once_with(
            ["python", "main.py"],
            cwd="/test/path",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.PIPE,
            text=True
        )
    
    @patch('subprocess.Popen')
    def test_start_server_process_failure(self, mock_popen, validation_engine):
        """Test server process start failure."""
        mock_popen.side_effect = Exception("Process start failed")
        
        result = validation_engine._start_server_process("/test/path", "python main.py")
        
        assert result is None
    
    def test_validate_server_startup_no_entry_point(self, validation_engine, temp_project_dir):
        """Test server startup validation when no entry point is found."""
        result = validation_engine.validate_server_startup(temp_project_dir)
        assert result is False
    
    @patch.object(MCPValidationEngine, '_detect_server_entry_point')
    @patch.object(MCPValidationEngine, '_start_server_process')
    def test_validate_server_startup_process_start_failure(self, mock_start_process, mock_detect_entry, validation_engine, temp_project_dir):
        """Test server startup validation when process fails to start."""
        mock_detect_entry.return_value = "python main.py"
        mock_start_process.return_value = None
        
        result = validation_engine.validate_server_startup(temp_project_dir)
        assert result is False
    
    @patch.object(MCPValidationEngine, '_detect_server_entry_point')
    @patch.object(MCPValidationEngine, '_start_server_process')
    @patch('time.sleep')
    def test_validate_server_startup_process_terminates(self, mock_sleep, mock_start_process, mock_detect_entry, validation_engine, temp_project_dir):
        """Test server startup validation when process terminates early."""
        mock_detect_entry.return_value = "python main.py"
        
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = 1  # Process has terminated
        mock_process.communicate.return_value = ("stdout", "stderr")
        mock_start_process.return_value = mock_process
        
        result = validation_engine.validate_server_startup(temp_project_dir)
        assert result is False
    
    @patch.object(MCPValidationEngine, '_detect_server_entry_point')
    @patch.object(MCPValidationEngine, '_start_server_process')
    @patch('time.sleep')
    def test_validate_server_startup_success(self, mock_sleep, mock_start_process, mock_detect_entry, validation_engine, temp_project_dir):
        """Test successful server startup validation."""
        mock_detect_entry.return_value = "python main.py"
        
        mock_process = Mock()
        mock_process.pid = 12345
        mock_process.poll.return_value = None  # Process is still running
        mock_start_process.return_value = mock_process
        
        result = validation_engine.validate_server_startup(temp_project_dir)
        assert result is True
    
    def test_validate_mcp_protocol_no_entry_point(self, validation_engine, temp_project_dir):
        """Test MCP protocol validation when no entry point is found."""
        result = validation_engine.validate_mcp_protocol(temp_project_dir)
        assert result is False
    
    @patch.object(MCPValidationEngine, '_detect_server_entry_point')
    @patch.object(MCPValidationEngine, '_start_server_process')
    @patch.object(MCPValidationEngine, '_test_mcp_initialization')
    @patch.object(MCPValidationEngine, '_test_mcp_method')
    @patch('time.sleep')
    def test_validate_mcp_protocol_success(self, mock_sleep, mock_test_method, mock_test_init, mock_start_process, mock_detect_entry, validation_engine, temp_project_dir):
        """Test successful MCP protocol validation."""
        mock_detect_entry.return_value = "python main.py"
        
        mock_process = Mock()
        mock_start_process.return_value = mock_process
        
        mock_test_init.return_value = {
            "success": True,
            "capabilities": ["initialize"],
            "protocol_version": "2024-11-05"
        }
        mock_test_method.return_value = True
        
        result = validation_engine.validate_mcp_protocol(temp_project_dir)
        assert result is True
    
    def test_validate_functionality_no_entry_point(self, validation_engine, temp_project_dir):
        """Test functionality validation when no entry point is found."""
        result = validation_engine.validate_functionality(temp_project_dir)
        expected = {
            "tools": False,
            "resources": False,
            "prompts": False
        }
        assert result == expected
    
    @patch.object(MCPValidationEngine, '_detect_server_entry_point')
    @patch.object(MCPValidationEngine, '_start_server_process')
    @patch.object(MCPValidationEngine, '_test_tools_functionality')
    @patch.object(MCPValidationEngine, '_test_resources_functionality')
    @patch.object(MCPValidationEngine, '_test_prompts_functionality')
    @patch('time.sleep')
    def test_validate_functionality_success(self, mock_sleep, mock_test_prompts, mock_test_resources, mock_test_tools, mock_start_process, mock_detect_entry, validation_engine, temp_project_dir):
        """Test successful functionality validation."""
        mock_detect_entry.return_value = "python main.py"
        
        mock_process = Mock()
        mock_start_process.return_value = mock_process
        
        mock_test_tools.return_value = {
            "tools": {"tool1": True, "tool2": True},
            "errors": [],
            "response_time": 0.1
        }
        mock_test_resources.return_value = {
            "resources": {"resource1": True},
            "errors": [],
            "response_time": 0.1
        }
        mock_test_prompts.return_value = {
            "prompts": {"prompt1": True},
            "errors": [],
            "response_time": 0.1
        }
        
        result = validation_engine.validate_functionality(temp_project_dir)
        expected = {
            "tools": True,
            "resources": True,
            "prompts": True
        }
        assert result == expected
    
    @patch.object(MCPValidationEngine, '_perform_startup_validation')
    @patch.object(MCPValidationEngine, '_perform_protocol_validation')
    @patch.object(MCPValidationEngine, '_perform_functionality_validation')
    def test_run_comprehensive_tests_success(self, mock_functionality, mock_protocol, mock_startup, validation_engine, temp_project_dir):
        """Test comprehensive tests with all validations successful."""
        # Mock successful results
        startup_result = ServerStartupResult(
            success=True,
            process_id=12345,
            startup_time=1.0,
            errors=[],
            logs=["Server started"]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=True,
            supported_capabilities=["initialize", "tools/list"],
            missing_capabilities=[],
            protocol_version="2024-11-05",
            errors=[]
        )
        
        functionality_result = FunctionalityTestResult(
            success=True,
            tested_tools={"tool1": True},
            tested_resources={"resource1": True},
            tested_prompts={"prompt1": True},
            errors=[],
            performance_metrics={"tools_response_time": 0.1}
        )
        
        mock_startup.return_value = startup_result
        mock_protocol.return_value = protocol_result
        mock_functionality.return_value = functionality_result
        
        result = validation_engine.run_comprehensive_tests(temp_project_dir)
        
        assert result["success"] is True
        assert isinstance(result["report"], ValidationReport)
        assert result["startup"] == startup_result
        assert result["protocol"] == protocol_result
        assert result["functionality"] == functionality_result
        assert "performance" in result
        assert "recommendations" in result
        assert "execution_time" in result
    
    @patch.object(MCPValidationEngine, '_perform_startup_validation')
    @patch.object(MCPValidationEngine, '_perform_protocol_validation')
    @patch.object(MCPValidationEngine, '_perform_functionality_validation')
    def test_run_comprehensive_tests_failure(self, mock_functionality, mock_protocol, mock_startup, validation_engine, temp_project_dir):
        """Test comprehensive tests with some validations failing."""
        # Mock failed startup
        startup_result = ServerStartupResult(
            success=False,
            process_id=None,
            startup_time=1.0,
            errors=["Failed to start server"],
            logs=[]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=False,
            supported_capabilities=[],
            missing_capabilities=["initialize"],
            protocol_version=None,
            errors=["Protocol test failed"]
        )
        
        functionality_result = FunctionalityTestResult(
            success=False,
            tested_tools={},
            tested_resources={},
            tested_prompts={},
            errors=["No functionality available"],
            performance_metrics={}
        )
        
        mock_startup.return_value = startup_result
        mock_protocol.return_value = protocol_result
        mock_functionality.return_value = functionality_result
        
        result = validation_engine.run_comprehensive_tests(temp_project_dir)
        
        assert result["success"] is False
        assert isinstance(result["report"], ValidationReport)
        assert result["report"].overall_success is False
    
    def test_test_mcp_initialization_success(self, validation_engine):
        """Test MCP initialization test."""
        mock_process = Mock()
        mock_process.stdin = Mock()
        
        result = validation_engine._test_mcp_initialization(mock_process)
        
        assert result["success"] is True
        assert "initialize" in result["capabilities"]
        assert result["protocol_version"] == "2024-11-05"
    
    def test_test_mcp_initialization_failure(self, validation_engine):
        """Test MCP initialization test failure."""
        mock_process = Mock()
        mock_process.stdin.write.side_effect = Exception("Write failed")
        
        result = validation_engine._test_mcp_initialization(mock_process)
        
        assert result["success"] is False
        assert "errors" in result
    
    def test_test_mcp_method(self, validation_engine):
        """Test MCP method testing."""
        mock_process = Mock()
        
        result = validation_engine._test_mcp_method(mock_process, "tools/list")
        
        # Currently returns True as placeholder
        assert result is True
    
    def test_cleanup_processes(self, validation_engine):
        """Test process cleanup."""
        # Create mock processes
        mock_process1 = Mock()
        mock_process1.poll.return_value = None  # Still running
        mock_process2 = Mock()
        mock_process2.poll.return_value = 0  # Already terminated
        
        validation_engine.active_processes = [mock_process1, mock_process2]
        
        validation_engine._cleanup_processes()
        
        # Should terminate the running process
        mock_process1.terminate.assert_called_once()
        # Should not terminate the already terminated process
        mock_process2.terminate.assert_not_called()
        
        # Processes list should be cleared
        assert validation_engine.active_processes == []
    
    def test_generate_recommendations_startup_failure(self, validation_engine):
        """Test recommendation generation for startup failure."""
        startup_result = ServerStartupResult(
            success=False,
            process_id=None,
            startup_time=1.0,
            errors=["Server failed to start"],
            logs=[]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=True,
            supported_capabilities=["initialize"],
            missing_capabilities=[],
            protocol_version="2024-11-05",
            errors=[]
        )
        
        functionality_result = FunctionalityTestResult(
            success=True,
            tested_tools={"tool1": True},
            tested_resources={},
            tested_prompts={},
            errors=[],
            performance_metrics={}
        )
        
        recommendations = validation_engine._generate_recommendations(
            startup_result, protocol_result, functionality_result
        )
        
        assert "Fix server startup issues before deployment" in recommendations
        assert "Review server logs for startup errors" in recommendations
    
    def test_generate_recommendations_missing_capabilities(self, validation_engine):
        """Test recommendation generation for missing capabilities."""
        startup_result = ServerStartupResult(
            success=True,
            process_id=12345,
            startup_time=1.0,
            errors=[],
            logs=[]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=False,
            supported_capabilities=["initialize"],
            missing_capabilities=["tools/list", "resources/list"],
            protocol_version="2024-11-05",
            errors=[]
        )
        
        functionality_result = FunctionalityTestResult(
            success=True,
            tested_tools={"tool1": True},
            tested_resources={},
            tested_prompts={},
            errors=[],
            performance_metrics={}
        )
        
        recommendations = validation_engine._generate_recommendations(
            startup_result, protocol_result, functionality_result
        )
        
        missing_caps_rec = next(
            (rec for rec in recommendations if "missing MCP capabilities" in rec),
            None
        )
        assert missing_caps_rec is not None
        assert "tools/list" in missing_caps_rec
        assert "resources/list" in missing_caps_rec
    
    def test_generate_recommendations_no_functionality(self, validation_engine):
        """Test recommendation generation for no functionality."""
        startup_result = ServerStartupResult(
            success=True,
            process_id=12345,
            startup_time=1.0,
            errors=[],
            logs=[]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=True,
            supported_capabilities=["initialize"],
            missing_capabilities=[],
            protocol_version="2024-11-05",
            errors=[]
        )
        
        functionality_result = FunctionalityTestResult(
            success=True,
            tested_tools={},
            tested_resources={},
            tested_prompts={},
            errors=[],
            performance_metrics={}
        )
        
        recommendations = validation_engine._generate_recommendations(
            startup_result, protocol_result, functionality_result
        )
        
        assert "Add at least one tool, resource, or prompt to make the server useful" in recommendations
    
    def test_generate_recommendations_slow_startup(self, validation_engine):
        """Test recommendation generation for slow startup."""
        startup_result = ServerStartupResult(
            success=True,
            process_id=12345,
            startup_time=6.0,  # Slow startup
            errors=[],
            logs=[]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=True,
            supported_capabilities=["initialize"],
            missing_capabilities=[],
            protocol_version="2024-11-05",
            errors=[]
        )
        
        functionality_result = FunctionalityTestResult(
            success=True,
            tested_tools={"tool1": True},
            tested_resources={},
            tested_prompts={},
            errors=[],
            performance_metrics={}
        )
        
        recommendations = validation_engine._generate_recommendations(
            startup_result, protocol_result, functionality_result
        )
        
        assert "Consider optimizing server startup time" in recommendations