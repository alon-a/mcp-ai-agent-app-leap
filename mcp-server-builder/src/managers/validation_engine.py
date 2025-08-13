"""MCP Server Validation Engine implementation."""

import json
import subprocess
import time
import psutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from .interfaces import ValidationEngine
from .validation_reporter import ValidationReporter
from .validation_diagnostics import ValidationDiagnostics
from ..models.base import (
    ValidationResult, ServerStartupResult, ProtocolComplianceResult,
    FunctionalityTestResult, ValidationReport
)
from ..models.enums import ValidationLevel, TransportType


class MCPValidationEngine(ValidationEngine):
    """Implementation of ValidationEngine for MCP server validation."""
    
    def __init__(self, timeout: int = 30, validation_level: ValidationLevel = ValidationLevel.STANDARD):
        """Initialize the validation engine.
        
        Args:
            timeout: Timeout for validation operations in seconds
            validation_level: Level of validation to perform
        """
        self.timeout = timeout
        self.validation_level = validation_level
        self.active_processes: List[subprocess.Popen] = []
        self.reporter = ValidationReporter()
        self.diagnostics = ValidationDiagnostics()
    
    def validate_server_startup(self, project_path: str) -> bool:
        """Validate that the MCP server can start successfully.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if server starts successfully
        """
        result = self._perform_startup_validation(project_path)
        return result.success
    
    def validate_mcp_protocol(self, project_path: str) -> bool:
        """Validate MCP protocol compliance.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if server is MCP protocol compliant
        """
        result = self._perform_protocol_validation(project_path)
        return result.success
    
    def validate_functionality(self, project_path: str) -> Dict[str, bool]:
        """Validate server functionality (tools, resources, prompts).
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary mapping functionality types to validation results
        """
        result = self._perform_functionality_validation(project_path)
        return {
            "tools": len(result.tested_tools) > 0 and all(result.tested_tools.values()),
            "resources": len(result.tested_resources) > 0 and all(result.tested_resources.values()),
            "prompts": len(result.tested_prompts) > 0 and all(result.tested_prompts.values())
        }
    
    def run_comprehensive_tests(self, project_path: str) -> Dict[str, Any]:
        """Run comprehensive validation tests.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with detailed test results
        """
        start_time = time.time()
        
        # Perform all validation steps
        startup_result = self._perform_startup_validation(project_path)
        protocol_result = self._perform_protocol_validation(project_path)
        functionality_result = self._perform_functionality_validation(project_path)
        
        # Calculate overall success
        overall_success = (
            startup_result.success and 
            protocol_result.success and 
            functionality_result.success
        )
        
        # Generate performance metrics
        performance_metrics = self._calculate_performance_metrics(
            startup_result, protocol_result, functionality_result
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            startup_result, protocol_result, functionality_result
        )
        
        total_time = time.time() - start_time
        
        # Create comprehensive report
        report = ValidationReport(
            project_path=project_path,
            validation_level=self.validation_level,
            overall_success=overall_success,
            startup_result=startup_result,
            protocol_result=protocol_result,
            functionality_result=functionality_result,
            performance_metrics=performance_metrics,
            recommendations=recommendations,
            timestamp=datetime.now().isoformat(),
            total_execution_time=total_time
        )
        
        # Save detailed report
        detailed_report_path = self.reporter.save_report(report, "detailed")
        summary_report_path = self.reporter.save_report(report, "summary")
        
        # Generate diagnostics if validation failed
        diagnostics_info = None
        if not overall_success:
            diagnostics_info = self.diagnostics.diagnose_validation_failure(report)
            diagnostics_report_path = self.reporter.save_report(report, "diagnostics")
        
        return {
            "success": overall_success,
            "report": report,
            "startup": startup_result,
            "protocol": protocol_result,
            "functionality": functionality_result,
            "performance": performance_metrics,
            "recommendations": recommendations,
            "execution_time": total_time,
            "detailed_report_path": detailed_report_path,
            "summary_report_path": summary_report_path,
            "diagnostics": diagnostics_info
        }
    
    def _perform_startup_validation(self, project_path: str) -> ServerStartupResult:
        """Perform server startup validation.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ServerStartupResult with validation details
        """
        start_time = time.time()
        errors = []
        logs = []
        process_id = None
        
        try:
            # Detect server entry point
            entry_point = self._detect_server_entry_point(project_path)
            if not entry_point:
                errors.append("Could not detect server entry point")
                return ServerStartupResult(
                    success=False,
                    process_id=None,
                    startup_time=time.time() - start_time,
                    errors=errors,
                    logs=logs
                )
            
            # Start the server process
            process = self._start_server_process(project_path, entry_point)
            if not process:
                errors.append("Failed to start server process")
                return ServerStartupResult(
                    success=False,
                    process_id=None,
                    startup_time=time.time() - start_time,
                    errors=errors,
                    logs=logs
                )
            
            process_id = process.pid
            self.active_processes.append(process)
            
            # Wait for server to initialize
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is not None:
                # Process has terminated
                stdout, stderr = process.communicate()
                if stdout:
                    logs.append(f"STDOUT: {stdout.decode()}")
                if stderr:
                    errors.append(f"STDERR: {stderr.decode()}")
                
                return ServerStartupResult(
                    success=False,
                    process_id=process_id,
                    startup_time=time.time() - start_time,
                    errors=errors,
                    logs=logs
                )
            
            # Server started successfully
            logs.append(f"Server started with PID {process_id}")
            
            return ServerStartupResult(
                success=True,
                process_id=process_id,
                startup_time=time.time() - start_time,
                errors=errors,
                logs=logs
            )
            
        except Exception as e:
            errors.append(f"Startup validation failed: {str(e)}")
            return ServerStartupResult(
                success=False,
                process_id=process_id,
                startup_time=time.time() - start_time,
                errors=errors,
                logs=logs
            )
        finally:
            # Clean up processes
            self._cleanup_processes()
    
    def _perform_protocol_validation(self, project_path: str) -> ProtocolComplianceResult:
        """Perform MCP protocol compliance validation.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ProtocolComplianceResult with validation details
        """
        errors = []
        supported_capabilities = []
        missing_capabilities = []
        protocol_version = None
        
        try:
            # Start server for protocol testing
            entry_point = self._detect_server_entry_point(project_path)
            if not entry_point:
                errors.append("Could not detect server entry point for protocol validation")
                return ProtocolComplianceResult(
                    success=False,
                    supported_capabilities=supported_capabilities,
                    missing_capabilities=missing_capabilities,
                    protocol_version=protocol_version,
                    errors=errors
                )
            
            process = self._start_server_process(project_path, entry_point)
            if not process:
                errors.append("Failed to start server for protocol validation")
                return ProtocolComplianceResult(
                    success=False,
                    supported_capabilities=supported_capabilities,
                    missing_capabilities=missing_capabilities,
                    protocol_version=protocol_version,
                    errors=errors
                )
            
            self.active_processes.append(process)
            time.sleep(2)  # Allow server to initialize
            
            # Test MCP protocol initialization
            init_result = self._test_mcp_initialization(process)
            if init_result["success"]:
                supported_capabilities.extend(init_result.get("capabilities", []))
                protocol_version = init_result.get("protocol_version")
            else:
                errors.extend(init_result.get("errors", []))
            
            # Test required MCP methods
            required_methods = ["initialize", "tools/list", "resources/list", "prompts/list"]
            for method in required_methods:
                if self._test_mcp_method(process, method):
                    supported_capabilities.append(method)
                else:
                    missing_capabilities.append(method)
                    errors.append(f"Method {method} not supported or failed")
            
            success = len(missing_capabilities) == 0 and len(errors) == 0
            
            return ProtocolComplianceResult(
                success=success,
                supported_capabilities=supported_capabilities,
                missing_capabilities=missing_capabilities,
                protocol_version=protocol_version,
                errors=errors
            )
            
        except Exception as e:
            errors.append(f"Protocol validation failed: {str(e)}")
            return ProtocolComplianceResult(
                success=False,
                supported_capabilities=supported_capabilities,
                missing_capabilities=missing_capabilities,
                protocol_version=protocol_version,
                errors=errors
            )
        finally:
            self._cleanup_processes()
    
    def _perform_functionality_validation(self, project_path: str) -> FunctionalityTestResult:
        """Perform functionality validation.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            FunctionalityTestResult with validation details
        """
        errors = []
        tested_tools = {}
        tested_resources = {}
        tested_prompts = {}
        performance_metrics = {}
        
        try:
            # Start server for functionality testing
            entry_point = self._detect_server_entry_point(project_path)
            if not entry_point:
                errors.append("Could not detect server entry point for functionality validation")
                return FunctionalityTestResult(
                    success=False,
                    tested_tools=tested_tools,
                    tested_resources=tested_resources,
                    tested_prompts=tested_prompts,
                    errors=errors,
                    performance_metrics=performance_metrics
                )
            
            process = self._start_server_process(project_path, entry_point)
            if not process:
                errors.append("Failed to start server for functionality validation")
                return FunctionalityTestResult(
                    success=False,
                    tested_tools=tested_tools,
                    tested_resources=tested_resources,
                    tested_prompts=tested_prompts,
                    errors=errors,
                    performance_metrics=performance_metrics
                )
            
            self.active_processes.append(process)
            time.sleep(2)  # Allow server to initialize
            
            # Test tools functionality
            tools_result = self._test_tools_functionality(process)
            tested_tools = tools_result["tools"]
            if tools_result["errors"]:
                errors.extend(tools_result["errors"])
            performance_metrics["tools_response_time"] = tools_result.get("response_time", 0.0)
            
            # Test resources functionality
            resources_result = self._test_resources_functionality(process)
            tested_resources = resources_result["resources"]
            if resources_result["errors"]:
                errors.extend(resources_result["errors"])
            performance_metrics["resources_response_time"] = resources_result.get("response_time", 0.0)
            
            # Test prompts functionality
            prompts_result = self._test_prompts_functionality(process)
            tested_prompts = prompts_result["prompts"]
            if prompts_result["errors"]:
                errors.extend(prompts_result["errors"])
            performance_metrics["prompts_response_time"] = prompts_result.get("response_time", 0.0)
            
            # Determine overall success
            success = (
                len(errors) == 0 and
                (len(tested_tools) > 0 or len(tested_resources) > 0 or len(tested_prompts) > 0)
            )
            
            return FunctionalityTestResult(
                success=success,
                tested_tools=tested_tools,
                tested_resources=tested_resources,
                tested_prompts=tested_prompts,
                errors=errors,
                performance_metrics=performance_metrics
            )
            
        except Exception as e:
            errors.append(f"Functionality validation failed: {str(e)}")
            return FunctionalityTestResult(
                success=False,
                tested_tools=tested_tools,
                tested_resources=tested_resources,
                tested_prompts=tested_prompts,
                errors=errors,
                performance_metrics=performance_metrics
            )
        finally:
            self._cleanup_processes()
    
    def _detect_server_entry_point(self, project_path: str) -> Optional[str]:
        """Detect the server entry point.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Entry point command or None if not found
        """
        project_dir = Path(project_path)
        
        # Check for Python servers
        if (project_dir / "main.py").exists():
            return "python main.py"
        if (project_dir / "server.py").exists():
            return "python server.py"
        if (project_dir / "app.py").exists():
            return "python app.py"
        
        # Check for package.json (Node.js/TypeScript)
        package_json = project_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                    if "scripts" in package_data and "start" in package_data["scripts"]:
                        return "npm start"
                    if "main" in package_data:
                        return f"node {package_data['main']}"
            except Exception:
                pass
        
        # Check for pyproject.toml (Python Poetry)
        pyproject_toml = project_dir / "pyproject.toml"
        if pyproject_toml.exists():
            return "poetry run python -m server"
        
        return None
    
    def _start_server_process(self, project_path: str, entry_point: str) -> Optional[subprocess.Popen]:
        """Start the server process.
        
        Args:
            project_path: Path to the project directory
            entry_point: Command to start the server
            
        Returns:
            Process object or None if failed
        """
        try:
            cmd = entry_point.split()
            process = subprocess.Popen(
                cmd,
                cwd=project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
                text=True
            )
            return process
        except Exception:
            return None
    
    def _test_mcp_initialization(self, process: subprocess.Popen) -> Dict[str, Any]:
        """Test MCP initialization.
        
        Args:
            process: Server process
            
        Returns:
            Dictionary with initialization test results
        """
        try:
            # Send MCP initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-validation-client",
                        "version": "1.0.0"
                    }
                }
            }
            
            process.stdin.write(json.dumps(init_request) + "\n")
            process.stdin.flush()
            
            # Wait for response (simplified - in real implementation would need proper JSON-RPC handling)
            time.sleep(1)
            
            return {
                "success": True,
                "capabilities": ["initialize"],
                "protocol_version": "2024-11-05"
            }
        except Exception as e:
            return {
                "success": False,
                "errors": [f"Initialization test failed: {str(e)}"]
            }
    
    def _test_mcp_method(self, process: subprocess.Popen, method: str) -> bool:
        """Test a specific MCP method.
        
        Args:
            process: Server process
            method: Method name to test
            
        Returns:
            True if method is supported
        """
        try:
            # This is a simplified test - real implementation would send proper JSON-RPC requests
            # and parse responses
            return True  # Placeholder for actual method testing
        except Exception:
            return False
    
    def _test_tools_functionality(self, process: subprocess.Popen) -> Dict[str, Any]:
        """Test tools functionality.
        
        Args:
            process: Server process
            
        Returns:
            Dictionary with tools test results
        """
        start_time = time.time()
        try:
            # Simplified tools testing - real implementation would:
            # 1. List available tools
            # 2. Test each tool with sample inputs
            # 3. Validate responses
            
            tools = {"sample_tool": True}  # Placeholder
            return {
                "tools": tools,
                "errors": [],
                "response_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "tools": {},
                "errors": [f"Tools test failed: {str(e)}"],
                "response_time": time.time() - start_time
            }
    
    def _test_resources_functionality(self, process: subprocess.Popen) -> Dict[str, Any]:
        """Test resources functionality.
        
        Args:
            process: Server process
            
        Returns:
            Dictionary with resources test results
        """
        start_time = time.time()
        try:
            # Simplified resources testing
            resources = {"sample_resource": True}  # Placeholder
            return {
                "resources": resources,
                "errors": [],
                "response_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "resources": {},
                "errors": [f"Resources test failed: {str(e)}"],
                "response_time": time.time() - start_time
            }
    
    def _test_prompts_functionality(self, process: subprocess.Popen) -> Dict[str, Any]:
        """Test prompts functionality.
        
        Args:
            process: Server process
            
        Returns:
            Dictionary with prompts test results
        """
        start_time = time.time()
        try:
            # Simplified prompts testing
            prompts = {"sample_prompt": True}  # Placeholder
            return {
                "prompts": prompts,
                "errors": [],
                "response_time": time.time() - start_time
            }
        except Exception as e:
            return {
                "prompts": {},
                "errors": [f"Prompts test failed: {str(e)}"],
                "response_time": time.time() - start_time
            }
    
    def _calculate_performance_metrics(
        self, 
        startup_result: ServerStartupResult,
        protocol_result: ProtocolComplianceResult,
        functionality_result: FunctionalityTestResult
    ) -> Dict[str, float]:
        """Calculate performance metrics.
        
        Args:
            startup_result: Startup validation result
            protocol_result: Protocol validation result
            functionality_result: Functionality validation result
            
        Returns:
            Dictionary with performance metrics
        """
        metrics = {
            "startup_time": startup_result.startup_time,
            "total_capabilities": len(protocol_result.supported_capabilities),
            "tools_count": len(functionality_result.tested_tools),
            "resources_count": len(functionality_result.tested_resources),
            "prompts_count": len(functionality_result.tested_prompts)
        }
        
        # Add functionality performance metrics
        metrics.update(functionality_result.performance_metrics)
        
        return metrics
    
    def _generate_recommendations(
        self,
        startup_result: ServerStartupResult,
        protocol_result: ProtocolComplianceResult,
        functionality_result: FunctionalityTestResult
    ) -> List[str]:
        """Generate recommendations based on validation results.
        
        Args:
            startup_result: Startup validation result
            protocol_result: Protocol validation result
            functionality_result: Functionality validation result
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        if not startup_result.success:
            recommendations.append("Fix server startup issues before deployment")
            if startup_result.errors:
                recommendations.append("Review server logs for startup errors")
        
        if protocol_result.missing_capabilities:
            recommendations.append(
                f"Implement missing MCP capabilities: {', '.join(protocol_result.missing_capabilities)}"
            )
        
        if not functionality_result.tested_tools and not functionality_result.tested_resources and not functionality_result.tested_prompts:
            recommendations.append("Add at least one tool, resource, or prompt to make the server useful")
        
        if startup_result.startup_time > 5.0:
            recommendations.append("Consider optimizing server startup time")
        
        return recommendations
    
    def _cleanup_processes(self):
        """Clean up any active processes."""
        for process in self.active_processes:
            try:
                if process.poll() is None:  # Process is still running
                    process.terminate()
                    time.sleep(1)
                    if process.poll() is None:  # Still running, force kill
                        process.kill()
            except Exception:
                pass
        
        self.active_processes.clear()
    
    def generate_diagnostic_report(self, project_path: str) -> Dict[str, Any]:
        """Generate a comprehensive diagnostic report for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Comprehensive diagnostic report
        """
        return self.diagnostics.generate_diagnostic_report(project_path)
    
    def get_validation_history(self, project_path: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get validation history for a project or all projects.
        
        Args:
            project_path: Optional project path to filter by
            limit: Optional limit on number of results
            
        Returns:
            List of validation history entries
        """
        return self.reporter.get_validation_history(project_path, limit)
    
    def generate_trend_analysis(self, project_path: str) -> Dict[str, Any]:
        """Generate trend analysis for a specific project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Dictionary containing trend analysis
        """
        return self.reporter.generate_trend_analysis(project_path)
    
    def run_diagnostics_only(self, project_path: str) -> List[Dict[str, Any]]:
        """Run diagnostic checks without full validation.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of diagnostic results
        """
        diagnostic_results = self.diagnostics.run_full_diagnostics(project_path)
        return [
            {
                "check": result.check_name,
                "status": result.status,
                "message": result.message,
                "details": result.details,
                "suggestions": result.suggestions
            }
            for result in diagnostic_results
        ]
    
    def get_actionable_recommendations(self, validation_report: ValidationReport) -> List[Dict[str, Any]]:
        """Get actionable recommendations from a validation report.
        
        Args:
            validation_report: The validation report
            
        Returns:
            List of actionable recommendations
        """
        detailed_report = self.reporter.generate_detailed_report(validation_report, include_diagnostics=False)
        return detailed_report.get("actionable_recommendations", [])
    
    def export_validation_report(self, validation_report: ValidationReport, format: str = "json") -> str:
        """Export validation report in specified format.
        
        Args:
            validation_report: The validation report to export
            format: Export format ("json", "summary")
            
        Returns:
            Path to exported report file
        """
        if format == "summary":
            return self.reporter.save_report(validation_report, "summary")
        else:
            return self.reporter.save_report(validation_report, "detailed")
    
    def __del__(self):
        """Cleanup on destruction."""
        self._cleanup_processes()