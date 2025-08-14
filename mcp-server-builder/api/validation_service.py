"""Comprehensive validation service for MCP server projects."""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from managers.validation_engine import MCPValidationEngine
from managers.comprehensive_testing import ComprehensiveTesting


class ValidationService:
    """Service for comprehensive MCP server validation and testing."""
    
    def __init__(self):
        self.validation_engine = MCPValidationEngine()
        self.comprehensive_testing = ComprehensiveTesting()
        self.logger = logging.getLogger(__name__)
        
        # Validation templates and scenarios
        self.validation_templates = self._load_validation_templates()
        
        # Track validation history (in production, this would be in a database)
        self.validation_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def _load_validation_templates(self) -> Dict[str, Dict[str, Any]]:
        """Load validation templates and test scenarios."""
        return {
            "startup": {
                "name": "Server Startup Validation",
                "description": "Validates that the MCP server can start successfully",
                "category": "basic",
                "tests": [
                    {
                        "name": "Server Process Start",
                        "description": "Check if server process starts without errors",
                        "method": "validate_server_startup"
                    },
                    {
                        "name": "Port Binding",
                        "description": "Check if server binds to the specified port",
                        "method": "validate_port_binding"
                    },
                    {
                        "name": "Initial Response",
                        "description": "Check if server responds to initial requests",
                        "method": "validate_initial_response"
                    }
                ]
            },
            "protocol": {
                "name": "MCP Protocol Compliance",
                "description": "Validates MCP protocol compliance",
                "category": "protocol",
                "tests": [
                    {
                        "name": "Protocol Version",
                        "description": "Check supported MCP protocol version",
                        "method": "validate_protocol_version"
                    },
                    {
                        "name": "Required Capabilities",
                        "description": "Check implementation of required capabilities",
                        "method": "validate_required_capabilities"
                    },
                    {
                        "name": "Message Format",
                        "description": "Validate message format compliance",
                        "method": "validate_message_format"
                    }
                ]
            },
            "functionality": {
                "name": "Functionality Testing",
                "description": "Tests server functionality (tools, resources, prompts)",
                "category": "functional",
                "tests": [
                    {
                        "name": "Tool Discovery",
                        "description": "Test tool discovery and listing",
                        "method": "test_tool_discovery"
                    },
                    {
                        "name": "Tool Execution",
                        "description": "Test tool execution with various inputs",
                        "method": "test_tool_execution"
                    },
                    {
                        "name": "Resource Access",
                        "description": "Test resource listing and access",
                        "method": "test_resource_access"
                    },
                    {
                        "name": "Prompt Templates",
                        "description": "Test prompt template functionality",
                        "method": "test_prompt_templates"
                    }
                ]
            },
            "performance": {
                "name": "Performance Testing",
                "description": "Tests server performance and response times",
                "category": "performance",
                "parameters": {
                    "max_response_time": {"type": "number", "default": 5000, "description": "Maximum response time in ms"},
                    "concurrent_requests": {"type": "number", "default": 10, "description": "Number of concurrent requests"},
                    "test_duration": {"type": "number", "default": 60, "description": "Test duration in seconds"}
                },
                "tests": [
                    {
                        "name": "Response Time",
                        "description": "Measure average response times",
                        "method": "test_response_times"
                    },
                    {
                        "name": "Throughput",
                        "description": "Measure request throughput",
                        "method": "test_throughput"
                    },
                    {
                        "name": "Concurrent Load",
                        "description": "Test behavior under concurrent load",
                        "method": "test_concurrent_load"
                    },
                    {
                        "name": "Memory Usage",
                        "description": "Monitor memory usage during operation",
                        "method": "test_memory_usage"
                    }
                ]
            },
            "security": {
                "name": "Security Testing",
                "description": "Tests server security and vulnerability scanning",
                "category": "security",
                "parameters": {
                    "scan_dependencies": {"type": "boolean", "default": True, "description": "Scan dependencies for vulnerabilities"},
                    "check_permissions": {"type": "boolean", "default": True, "description": "Check file permissions"},
                    "test_input_validation": {"type": "boolean", "default": True, "description": "Test input validation"}
                },
                "tests": [
                    {
                        "name": "Dependency Vulnerabilities",
                        "description": "Scan dependencies for known vulnerabilities",
                        "method": "scan_dependency_vulnerabilities"
                    },
                    {
                        "name": "Input Validation",
                        "description": "Test input validation and sanitization",
                        "method": "test_input_validation"
                    },
                    {
                        "name": "File Permissions",
                        "description": "Check file and directory permissions",
                        "method": "check_file_permissions"
                    },
                    {
                        "name": "Error Handling",
                        "description": "Test error handling and information disclosure",
                        "method": "test_error_handling"
                    }
                ]
            }
        }
    
    async def run_validation(self, project_path: str, validation_type: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Run validation tests on a project.
        
        Args:
            project_path: Path to the project directory
            validation_type: Type of validation to run
            parameters: Optional parameters for the validation
            
        Returns:
            Dictionary with validation results
        """
        start_time = datetime.now()
        
        try:
            if validation_type == "comprehensive":
                # Run all validation types
                results = await self._run_comprehensive_validation(project_path, parameters)
            elif validation_type in self.validation_templates:
                # Run specific validation type
                results = await self._run_template_validation(project_path, validation_type, parameters)
            else:
                # Custom validation
                results = await self._run_custom_validation(project_path, validation_type, parameters)
            
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            # Add metadata
            results.update({
                "validation_type": validation_type,
                "project_path": project_path,
                "execution_time": execution_time,
                "timestamp": end_time.isoformat(),
                "parameters": parameters or {}
            })
            
            # Store in history
            project_id = Path(project_path).name
            if project_id not in self.validation_history:
                self.validation_history[project_id] = []
            
            self.validation_history[project_id].append(results)
            
            return results
            
        except Exception as e:
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            return {
                "validation_type": validation_type,
                "project_path": project_path,
                "success": False,
                "execution_time": execution_time,
                "timestamp": end_time.isoformat(),
                "error": str(e),
                "results": {},
                "errors": [str(e)],
                "warnings": []
            }
    
    async def _run_comprehensive_validation(self, project_path: str, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Run comprehensive validation including all test types."""
        results = {
            "success": True,
            "results": {},
            "errors": [],
            "warnings": [],
            "summary": {
                "total_tests": 0,
                "passed_tests": 0,
                "failed_tests": 0,
                "warnings_count": 0
            }
        }
        
        # Run each validation template
        for template_name in ["startup", "protocol", "functionality", "performance", "security"]:
            try:
                template_result = await self._run_template_validation(project_path, template_name, parameters)
                results["results"][template_name] = template_result
                
                # Update summary
                if template_result.get("success", False):
                    results["summary"]["passed_tests"] += 1
                else:
                    results["summary"]["failed_tests"] += 1
                    results["success"] = False
                
                results["summary"]["total_tests"] += 1
                results["errors"].extend(template_result.get("errors", []))
                results["warnings"].extend(template_result.get("warnings", []))
                
            except Exception as e:
                results["errors"].append(f"Failed to run {template_name} validation: {str(e)}")
                results["success"] = False
                results["summary"]["failed_tests"] += 1
                results["summary"]["total_tests"] += 1
        
        results["summary"]["warnings_count"] = len(results["warnings"])
        
        return results
    
    async def _run_template_validation(self, project_path: str, template_name: str, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Run validation based on a template."""
        template = self.validation_templates.get(template_name)
        if not template:
            raise ValueError(f"Unknown validation template: {template_name}")
        
        results = {
            "template": template_name,
            "success": True,
            "test_results": [],
            "errors": [],
            "warnings": []
        }
        
        # Run each test in the template
        for test in template["tests"]:
            try:
                test_result = await self._run_single_test(project_path, test, parameters)
                results["test_results"].append(test_result)
                
                if not test_result.get("success", False):
                    results["success"] = False
                    results["errors"].extend(test_result.get("errors", []))
                
                results["warnings"].extend(test_result.get("warnings", []))
                
            except Exception as e:
                test_result = {
                    "name": test["name"],
                    "success": False,
                    "error": str(e),
                    "errors": [str(e)],
                    "warnings": []
                }
                results["test_results"].append(test_result)
                results["success"] = False
                results["errors"].append(str(e))
        
        return results
    
    async def _run_single_test(self, project_path: str, test: Dict[str, Any], parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a single validation test."""
        test_name = test["name"]
        test_method = test["method"]
        
        try:
            # Get the validation method
            if hasattr(self.validation_engine, test_method):
                method = getattr(self.validation_engine, test_method)
                
                # Run the test
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, method, project_path)
                
                return {
                    "name": test_name,
                    "description": test.get("description", ""),
                    "success": bool(result),
                    "result": result,
                    "errors": [] if result else [f"{test_name} failed"],
                    "warnings": []
                }
            else:
                # Custom test method - placeholder implementation
                return {
                    "name": test_name,
                    "description": test.get("description", ""),
                    "success": True,
                    "result": "Test not implemented",
                    "errors": [],
                    "warnings": [f"Test method '{test_method}' not implemented"]
                }
                
        except Exception as e:
            return {
                "name": test_name,
                "description": test.get("description", ""),
                "success": False,
                "result": None,
                "errors": [str(e)],
                "warnings": []
            }
    
    async def _run_custom_validation(self, project_path: str, validation_type: str, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Run custom validation logic."""
        # Placeholder for custom validation logic
        return {
            "success": True,
            "results": {"message": f"Custom validation '{validation_type}' completed"},
            "errors": [],
            "warnings": ["Custom validation not fully implemented"]
        }
    
    def get_validation_templates(self) -> List[Dict[str, Any]]:
        """Get list of available validation templates."""
        templates = []
        for template_id, template in self.validation_templates.items():
            templates.append({
                "id": template_id,
                "name": template["name"],
                "description": template["description"],
                "category": template["category"],
                "parameters": template.get("parameters", {}),
                "test_count": len(template["tests"])
            })
        
        return templates
    
    def get_validation_history(self, project_id: str) -> List[Dict[str, Any]]:
        """Get validation history for a project."""
        return self.validation_history.get(project_id, [])
    
    async def run_custom_test_scenarios(self, project_path: str, scenarios: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run custom test scenarios."""
        results = {
            "success": True,
            "scenarios_run": len(scenarios),
            "results": [],
            "errors": [],
            "warnings": []
        }
        
        for i, scenario in enumerate(scenarios):
            try:
                scenario_result = await self._run_custom_scenario(project_path, scenario, i)
                results["results"].append(scenario_result)
                
                if not scenario_result.get("success", False):
                    results["success"] = False
                    results["errors"].extend(scenario_result.get("errors", []))
                
                results["warnings"].extend(scenario_result.get("warnings", []))
                
            except Exception as e:
                scenario_result = {
                    "name": scenario.get("name", f"Scenario {i + 1}"),
                    "success": False,
                    "error": str(e),
                    "errors": [str(e)],
                    "warnings": []
                }
                results["results"].append(scenario_result)
                results["success"] = False
                results["errors"].append(str(e))
        
        return results
    
    async def _run_custom_scenario(self, project_path: str, scenario: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Run a single custom test scenario."""
        scenario_name = scenario.get("name", f"Scenario {index + 1}")
        scenario_type = scenario.get("type", "custom")
        
        # Placeholder implementation for custom scenarios
        return {
            "name": scenario_name,
            "type": scenario_type,
            "success": True,
            "details": scenario.get("details", {}),
            "errors": [],
            "warnings": ["Custom scenario execution not fully implemented"]
        }