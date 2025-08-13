"""Diagnostic tools for troubleshooting failed validations."""

import json
import subprocess
import sys
import os
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from ..models.base import ValidationReport, ValidationResult


@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    check_name: str
    status: str  # "PASS", "FAIL", "WARNING", "INFO"
    message: str
    details: Dict[str, Any]
    suggestions: List[str]


class ValidationDiagnostics:
    """Diagnostic tools for troubleshooting validation failures."""
    
    def __init__(self):
        """Initialize the diagnostics system."""
        self.diagnostic_checks = [
            self._check_python_environment,
            self._check_project_structure,
            self._check_dependencies,
            self._check_file_permissions,
            self._check_entry_points,
            self._check_mcp_compliance,
            self._check_system_resources,
            self._check_network_connectivity
        ]
    
    def run_full_diagnostics(self, project_path: str) -> List[DiagnosticResult]:
        """Run all diagnostic checks on a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of diagnostic results
        """
        results = []
        
        for check_func in self.diagnostic_checks:
            try:
                result = check_func(project_path)
                results.append(result)
            except Exception as e:
                results.append(DiagnosticResult(
                    check_name=check_func.__name__,
                    status="FAIL",
                    message=f"Diagnostic check failed: {str(e)}",
                    details={"error": str(e)},
                    suggestions=["Contact support if this error persists"]
                ))
        
        return results
    
    def diagnose_validation_failure(
        self, 
        validation_report: ValidationReport
    ) -> Dict[str, Any]:
        """Diagnose specific validation failures.
        
        Args:
            validation_report: The failed validation report
            
        Returns:
            Diagnostic analysis dictionary
        """
        diagnosis = {
            "project_path": validation_report.project_path,
            "failure_analysis": self._analyze_failure_patterns(validation_report),
            "diagnostic_results": self.run_full_diagnostics(validation_report.project_path),
            "root_cause_analysis": self._perform_root_cause_analysis(validation_report),
            "fix_recommendations": self._generate_fix_recommendations(validation_report),
            "automated_fixes": self._suggest_automated_fixes(validation_report)
        }
        
        return diagnosis
    
    def generate_diagnostic_report(
        self, 
        project_path: str, 
        validation_report: Optional[ValidationReport] = None
    ) -> Dict[str, Any]:
        """Generate a comprehensive diagnostic report.
        
        Args:
            project_path: Path to the project directory
            validation_report: Optional validation report for context
            
        Returns:
            Comprehensive diagnostic report
        """
        diagnostic_results = self.run_full_diagnostics(project_path)
        
        report = {
            "project_path": project_path,
            "diagnostic_summary": self._summarize_diagnostics(diagnostic_results),
            "detailed_results": [
                {
                    "check": result.check_name,
                    "status": result.status,
                    "message": result.message,
                    "details": result.details,
                    "suggestions": result.suggestions
                }
                for result in diagnostic_results
            ],
            "system_info": self._collect_system_info(),
            "environment_analysis": self._analyze_environment(project_path)
        }
        
        if validation_report:
            report["validation_context"] = self._analyze_validation_context(validation_report)
        
        return report
    
    def _check_python_environment(self, project_path: str) -> DiagnosticResult:
        """Check Python environment and version.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for Python environment
        """
        details = {
            "python_version": sys.version,
            "python_executable": sys.executable,
            "python_path": sys.path[:5]  # First 5 entries
        }
        
        # Check Python version compatibility
        version_info = sys.version_info
        if version_info.major < 3 or (version_info.major == 3 and version_info.minor < 8):
            return DiagnosticResult(
                check_name="python_environment",
                status="FAIL",
                message=f"Python version {version_info.major}.{version_info.minor} is too old",
                details=details,
                suggestions=[
                    "Upgrade to Python 3.8 or newer",
                    "Use pyenv or conda to manage Python versions",
                    "Check project requirements for minimum Python version"
                ]
            )
        
        return DiagnosticResult(
            check_name="python_environment",
            status="PASS",
            message=f"Python {version_info.major}.{version_info.minor}.{version_info.micro} is compatible",
            details=details,
            suggestions=[]
        )
    
    def _check_project_structure(self, project_path: str) -> DiagnosticResult:
        """Check project structure and required files.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for project structure
        """
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            return DiagnosticResult(
                check_name="project_structure",
                status="FAIL",
                message="Project directory does not exist",
                details={"project_path": str(project_dir)},
                suggestions=["Verify the project path is correct", "Check if the project was created successfully"]
            )
        
        # Check for common server files
        server_files = ["main.py", "server.py", "app.py", "__init__.py"]
        config_files = ["package.json", "pyproject.toml", "requirements.txt", "setup.py"]
        
        found_server_files = [f for f in server_files if (project_dir / f).exists()]
        found_config_files = [f for f in config_files if (project_dir / f).exists()]
        
        details = {
            "project_exists": True,
            "server_files_found": found_server_files,
            "config_files_found": found_config_files,
            "directory_contents": [f.name for f in project_dir.iterdir() if f.is_file()][:10]
        }
        
        if not found_server_files:
            return DiagnosticResult(
                check_name="project_structure",
                status="FAIL",
                message="No server entry point files found",
                details=details,
                suggestions=[
                    "Create a main.py, server.py, or app.py file",
                    "Ensure the server entry point is properly named",
                    "Check if files were created in the correct directory"
                ]
            )
        
        if not found_config_files:
            return DiagnosticResult(
                check_name="project_structure",
                status="WARNING",
                message="No configuration files found",
                details=details,
                suggestions=[
                    "Add a requirements.txt or pyproject.toml for Python projects",
                    "Add a package.json for Node.js/TypeScript projects",
                    "Include proper dependency management files"
                ]
            )
        
        return DiagnosticResult(
            check_name="project_structure",
            status="PASS",
            message="Project structure looks good",
            details=details,
            suggestions=[]
        )
    
    def _check_dependencies(self, project_path: str) -> DiagnosticResult:
        """Check if dependencies are properly installed.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for dependencies
        """
        project_dir = Path(project_path)
        details = {"dependency_files": [], "installed_packages": []}
        
        # Check for Python dependencies
        requirements_file = project_dir / "requirements.txt"
        pyproject_file = project_dir / "pyproject.toml"
        
        missing_deps = []
        
        if requirements_file.exists():
            details["dependency_files"].append("requirements.txt")
            try:
                with open(requirements_file) as f:
                    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
                
                for req in requirements:
                    # Simple package name extraction (ignoring version specifiers)
                    package_name = req.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip()
                    if not self._is_package_installed(package_name):
                        missing_deps.append(package_name)
                    else:
                        details["installed_packages"].append(package_name)
            except Exception as e:
                return DiagnosticResult(
                    check_name="dependencies",
                    status="FAIL",
                    message=f"Error reading requirements.txt: {str(e)}",
                    details=details,
                    suggestions=["Check requirements.txt file format", "Ensure file is readable"]
                )
        
        if pyproject_file.exists():
            details["dependency_files"].append("pyproject.toml")
            # Note: Full TOML parsing would require additional dependency
            # This is a simplified check
        
        # Check for Node.js dependencies
        package_json = project_dir / "package.json"
        if package_json.exists():
            details["dependency_files"].append("package.json")
            node_modules = project_dir / "node_modules"
            if not node_modules.exists():
                missing_deps.append("node_modules (run npm install)")
        
        if missing_deps:
            return DiagnosticResult(
                check_name="dependencies",
                status="FAIL",
                message=f"Missing dependencies: {', '.join(missing_deps)}",
                details=details,
                suggestions=[
                    "Run 'pip install -r requirements.txt' for Python projects",
                    "Run 'npm install' for Node.js projects",
                    "Check if virtual environment is activated",
                    "Verify package names and versions"
                ]
            )
        
        return DiagnosticResult(
            check_name="dependencies",
            status="PASS",
            message="Dependencies appear to be installed",
            details=details,
            suggestions=[]
        )
    
    def _check_file_permissions(self, project_path: str) -> DiagnosticResult:
        """Check file permissions for server files.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for file permissions
        """
        project_dir = Path(project_path)
        
        if not project_dir.exists():
            return DiagnosticResult(
                check_name="file_permissions",
                status="FAIL",
                message="Project directory does not exist",
                details={},
                suggestions=["Verify project path"]
            )
        
        permission_issues = []
        details = {"file_permissions": {}}
        
        # Check common server files
        server_files = ["main.py", "server.py", "app.py"]
        
        for filename in server_files:
            file_path = project_dir / filename
            if file_path.exists():
                try:
                    # Check if file is readable
                    with open(file_path, 'r') as f:
                        f.read(1)  # Try to read one character
                    
                    # Get file permissions (Unix-like systems)
                    if hasattr(os, 'access'):
                        readable = os.access(file_path, os.R_OK)
                        executable = os.access(file_path, os.X_OK)
                        details["file_permissions"][filename] = {
                            "readable": readable,
                            "executable": executable
                        }
                        
                        if not readable:
                            permission_issues.append(f"{filename} is not readable")
                    
                except PermissionError:
                    permission_issues.append(f"Cannot read {filename}")
                except Exception as e:
                    permission_issues.append(f"Error accessing {filename}: {str(e)}")
        
        if permission_issues:
            return DiagnosticResult(
                check_name="file_permissions",
                status="FAIL",
                message=f"Permission issues found: {', '.join(permission_issues)}",
                details=details,
                suggestions=[
                    "Check file ownership and permissions",
                    "Run 'chmod +r' on unreadable files",
                    "Ensure proper user permissions on project directory"
                ]
            )
        
        return DiagnosticResult(
            check_name="file_permissions",
            status="PASS",
            message="File permissions are correct",
            details=details,
            suggestions=[]
        )
    
    def _check_entry_points(self, project_path: str) -> DiagnosticResult:
        """Check if server entry points are valid.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for entry points
        """
        project_dir = Path(project_path)
        details = {"entry_points": [], "syntax_errors": []}
        
        # Check Python entry points
        python_files = ["main.py", "server.py", "app.py"]
        
        for filename in python_files:
            file_path = project_dir / filename
            if file_path.exists():
                details["entry_points"].append(filename)
                
                # Check for basic syntax errors
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Try to compile the Python code
                    compile(content, str(file_path), 'exec')
                    
                except SyntaxError as e:
                    details["syntax_errors"].append(f"{filename}: {str(e)}")
                except Exception as e:
                    details["syntax_errors"].append(f"{filename}: {str(e)}")
        
        # Check package.json scripts
        package_json = project_dir / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    package_data = json.load(f)
                
                if "scripts" in package_data:
                    if "start" in package_data["scripts"]:
                        details["entry_points"].append("npm start")
                
                if "main" in package_data:
                    details["entry_points"].append(f"node {package_data['main']}")
                    
            except Exception as e:
                details["syntax_errors"].append(f"package.json: {str(e)}")
        
        if details["syntax_errors"]:
            return DiagnosticResult(
                check_name="entry_points",
                status="FAIL",
                message=f"Syntax errors in entry points: {', '.join(details['syntax_errors'])}",
                details=details,
                suggestions=[
                    "Fix syntax errors in server files",
                    "Use a Python linter to check code quality",
                    "Validate JSON format in package.json"
                ]
            )
        
        if not details["entry_points"]:
            return DiagnosticResult(
                check_name="entry_points",
                status="FAIL",
                message="No valid entry points found",
                details=details,
                suggestions=[
                    "Create a main.py, server.py, or app.py file",
                    "Add a 'start' script to package.json",
                    "Ensure entry point files are properly named"
                ]
            )
        
        return DiagnosticResult(
            check_name="entry_points",
            status="PASS",
            message=f"Found valid entry points: {', '.join(details['entry_points'])}",
            details=details,
            suggestions=[]
        )
    
    def _check_mcp_compliance(self, project_path: str) -> DiagnosticResult:
        """Check for basic MCP compliance indicators.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for MCP compliance
        """
        project_dir = Path(project_path)
        details = {"mcp_indicators": [], "missing_elements": []}
        
        # Check for MCP-related imports and code patterns
        python_files = list(project_dir.glob("*.py"))
        
        mcp_patterns = [
            "mcp",
            "jsonrpc",
            "tools",
            "resources",
            "prompts",
            "initialize",
            "capabilities"
        ]
        
        found_patterns = set()
        
        for py_file in python_files:
            try:
                with open(py_file, 'r') as f:
                    content = f.read().lower()
                
                for pattern in mcp_patterns:
                    if pattern in content:
                        found_patterns.add(pattern)
                        
            except Exception:
                continue
        
        details["mcp_indicators"] = list(found_patterns)
        
        # Check for essential MCP elements
        essential_elements = ["mcp", "initialize"]
        missing_essential = [elem for elem in essential_elements if elem not in found_patterns]
        
        if missing_essential:
            details["missing_elements"] = missing_essential
            return DiagnosticResult(
                check_name="mcp_compliance",
                status="FAIL",
                message=f"Missing essential MCP elements: {', '.join(missing_essential)}",
                details=details,
                suggestions=[
                    "Import MCP SDK or framework",
                    "Implement MCP initialization handler",
                    "Add proper MCP protocol support",
                    "Review MCP documentation and examples"
                ]
            )
        
        if len(found_patterns) < 3:
            return DiagnosticResult(
                check_name="mcp_compliance",
                status="WARNING",
                message="Limited MCP functionality detected",
                details=details,
                suggestions=[
                    "Add more MCP capabilities (tools, resources, prompts)",
                    "Implement proper JSON-RPC handling",
                    "Review MCP server examples"
                ]
            )
        
        return DiagnosticResult(
            check_name="mcp_compliance",
            status="PASS",
            message="MCP compliance indicators found",
            details=details,
            suggestions=[]
        )
    
    def _check_system_resources(self, project_path: str) -> DiagnosticResult:
        """Check system resources and environment.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for system resources
        """
        import psutil
        
        details = {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": round(psutil.virtual_memory().total / (1024**3), 2),
            "memory_available_gb": round(psutil.virtual_memory().available / (1024**3), 2),
            "disk_free_gb": round(psutil.disk_usage(str(Path(project_path).parent)).free / (1024**3), 2)
        }
        
        warnings = []
        
        # Check memory
        if details["memory_available_gb"] < 0.5:
            warnings.append("Low available memory (< 0.5 GB)")
        
        # Check disk space
        if details["disk_free_gb"] < 1.0:
            warnings.append("Low disk space (< 1 GB)")
        
        if warnings:
            return DiagnosticResult(
                check_name="system_resources",
                status="WARNING",
                message=f"Resource constraints: {', '.join(warnings)}",
                details=details,
                suggestions=[
                    "Free up memory by closing unnecessary applications",
                    "Clean up disk space",
                    "Consider running on a system with more resources"
                ]
            )
        
        return DiagnosticResult(
            check_name="system_resources",
            status="PASS",
            message="System resources are adequate",
            details=details,
            suggestions=[]
        )
    
    def _check_network_connectivity(self, project_path: str) -> DiagnosticResult:
        """Check network connectivity for external dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Diagnostic result for network connectivity
        """
        import socket
        
        details = {"connectivity_tests": {}}
        
        # Test common package repositories
        test_hosts = [
            ("pypi.org", 443),
            ("registry.npmjs.org", 443),
            ("github.com", 443)
        ]
        
        failed_connections = []
        
        for host, port in test_hosts:
            try:
                socket.create_connection((host, port), timeout=5)
                details["connectivity_tests"][host] = "SUCCESS"
            except Exception as e:
                details["connectivity_tests"][host] = f"FAILED: {str(e)}"
                failed_connections.append(host)
        
        if failed_connections:
            return DiagnosticResult(
                check_name="network_connectivity",
                status="WARNING",
                message=f"Network connectivity issues: {', '.join(failed_connections)}",
                details=details,
                suggestions=[
                    "Check internet connection",
                    "Verify firewall settings",
                    "Check proxy configuration if applicable",
                    "Try running validation again later"
                ]
            )
        
        return DiagnosticResult(
            check_name="network_connectivity",
            status="PASS",
            message="Network connectivity is good",
            details=details,
            suggestions=[]
        )
    
    def _is_package_installed(self, package_name: str) -> bool:
        """Check if a Python package is installed.
        
        Args:
            package_name: Name of the package to check
            
        Returns:
            True if package is installed
        """
        try:
            __import__(package_name.replace("-", "_"))
            return True
        except ImportError:
            return False
    
    def _analyze_failure_patterns(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Analyze patterns in validation failures.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Failure pattern analysis
        """
        patterns = {
            "failure_types": [],
            "common_errors": [],
            "failure_sequence": []
        }
        
        # Analyze failure types
        if not validation_report.startup_result.success:
            patterns["failure_types"].append("startup_failure")
            patterns["failure_sequence"].append("startup")
        
        if not validation_report.protocol_result.success:
            patterns["failure_types"].append("protocol_failure")
            patterns["failure_sequence"].append("protocol")
        
        if not validation_report.functionality_result.success:
            patterns["failure_types"].append("functionality_failure")
            patterns["failure_sequence"].append("functionality")
        
        # Collect all errors
        all_errors = (
            validation_report.startup_result.errors +
            validation_report.protocol_result.errors +
            validation_report.functionality_result.errors
        )
        
        # Find common error patterns
        error_keywords = {}
        for error in all_errors:
            words = error.lower().split()
            for word in words:
                if len(word) > 3:  # Ignore short words
                    error_keywords[word] = error_keywords.get(word, 0) + 1
        
        # Get most common error keywords
        patterns["common_errors"] = sorted(
            error_keywords.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5]
        
        return patterns
    
    def _perform_root_cause_analysis(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Perform root cause analysis of validation failures.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Root cause analysis
        """
        analysis = {
            "primary_cause": None,
            "contributing_factors": [],
            "evidence": []
        }
        
        # Determine primary cause based on failure sequence
        if not validation_report.startup_result.success:
            analysis["primary_cause"] = "server_startup_failure"
            analysis["evidence"].extend(validation_report.startup_result.errors)
            
            # Check for common startup issues
            startup_errors = " ".join(validation_report.startup_result.errors).lower()
            if "import" in startup_errors or "module" in startup_errors:
                analysis["contributing_factors"].append("missing_dependencies")
            if "permission" in startup_errors:
                analysis["contributing_factors"].append("permission_issues")
            if "syntax" in startup_errors:
                analysis["contributing_factors"].append("code_syntax_errors")
                
        elif validation_report.protocol_result.missing_capabilities:
            analysis["primary_cause"] = "incomplete_mcp_implementation"
            analysis["evidence"].append(f"Missing capabilities: {validation_report.protocol_result.missing_capabilities}")
            analysis["contributing_factors"].append("protocol_compliance_issues")
            
        elif not validation_report.functionality_result.success:
            analysis["primary_cause"] = "functionality_implementation_issues"
            analysis["evidence"].extend(validation_report.functionality_result.errors)
            
            # Check if no capabilities are implemented
            total_capabilities = (
                len(validation_report.functionality_result.tested_tools) +
                len(validation_report.functionality_result.tested_resources) +
                len(validation_report.functionality_result.tested_prompts)
            )
            if total_capabilities == 0:
                analysis["contributing_factors"].append("no_capabilities_implemented")
        
        return analysis
    
    def _generate_fix_recommendations(self, validation_report: ValidationReport) -> List[Dict[str, Any]]:
        """Generate specific fix recommendations based on failures.
        
        Args:
            validation_report: The validation report
            
        Returns:
            List of fix recommendations
        """
        recommendations = []
        
        # Startup failure fixes
        if not validation_report.startup_result.success:
            recommendations.append({
                "category": "startup",
                "priority": "critical",
                "title": "Fix Server Startup Issues",
                "steps": [
                    "Review server logs for specific error messages",
                    "Check that all required dependencies are installed",
                    "Verify the server entry point file exists and is executable",
                    "Test running the server manually from command line"
                ],
                "validation_command": "python main.py"  # or detected entry point
            })
        
        # Protocol compliance fixes
        if validation_report.protocol_result.missing_capabilities:
            recommendations.append({
                "category": "protocol",
                "priority": "high",
                "title": "Implement Missing MCP Capabilities",
                "steps": [
                    f"Add support for: {', '.join(validation_report.protocol_result.missing_capabilities)}",
                    "Review MCP protocol specification",
                    "Implement proper JSON-RPC request/response handling",
                    "Add initialization and capability advertisement"
                ],
                "validation_command": "Test with MCP client"
            })
        
        # Functionality fixes
        if not validation_report.functionality_result.success:
            total_capabilities = (
                len(validation_report.functionality_result.tested_tools) +
                len(validation_report.functionality_result.tested_resources) +
                len(validation_report.functionality_result.tested_prompts)
            )
            
            if total_capabilities == 0:
                recommendations.append({
                    "category": "functionality",
                    "priority": "medium",
                    "title": "Add Server Capabilities",
                    "steps": [
                        "Implement at least one tool, resource, or prompt",
                        "Register capabilities with the MCP server framework",
                        "Test individual capabilities with sample inputs",
                        "Add proper error handling for capability functions"
                    ],
                    "validation_command": "Test individual capabilities"
                })
        
        return recommendations
    
    def _suggest_automated_fixes(self, validation_report: ValidationReport) -> List[Dict[str, Any]]:
        """Suggest automated fixes that could be applied.
        
        Args:
            validation_report: The validation report
            
        Returns:
            List of automated fix suggestions
        """
        automated_fixes = []
        
        # Check for missing requirements.txt
        project_dir = Path(validation_report.project_path)
        if not (project_dir / "requirements.txt").exists():
            automated_fixes.append({
                "type": "create_file",
                "description": "Create basic requirements.txt file",
                "file_path": "requirements.txt",
                "content": "# Add your project dependencies here\n",
                "risk_level": "low"
            })
        
        # Check for missing __init__.py
        if not (project_dir / "__init__.py").exists():
            automated_fixes.append({
                "type": "create_file",
                "description": "Create __init__.py to make directory a Python package",
                "file_path": "__init__.py",
                "content": '"""MCP Server Package."""\n',
                "risk_level": "low"
            })
        
        return automated_fixes
    
    def _summarize_diagnostics(self, diagnostic_results: List[DiagnosticResult]) -> Dict[str, Any]:
        """Summarize diagnostic results.
        
        Args:
            diagnostic_results: List of diagnostic results
            
        Returns:
            Summary of diagnostics
        """
        summary = {
            "total_checks": len(diagnostic_results),
            "passed": len([r for r in diagnostic_results if r.status == "PASS"]),
            "failed": len([r for r in diagnostic_results if r.status == "FAIL"]),
            "warnings": len([r for r in diagnostic_results if r.status == "WARNING"]),
            "critical_issues": [],
            "recommendations_count": 0
        }
        
        for result in diagnostic_results:
            if result.status == "FAIL":
                summary["critical_issues"].append(result.check_name)
            summary["recommendations_count"] += len(result.suggestions)
        
        # Overall health score
        if summary["failed"] == 0:
            summary["health_score"] = "GOOD"
        elif summary["failed"] <= 2:
            summary["health_score"] = "FAIR"
        else:
            summary["health_score"] = "POOR"
        
        return summary
    
    def _collect_system_info(self) -> Dict[str, Any]:
        """Collect system information for diagnostics.
        
        Returns:
            System information dictionary
        """
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "machine": platform.machine(),
            "system": platform.system()
        }
    
    def _analyze_environment(self, project_path: str) -> Dict[str, Any]:
        """Analyze the project environment.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Environment analysis
        """
        project_dir = Path(project_path)
        
        analysis = {
            "project_type": "unknown",
            "detected_frameworks": [],
            "configuration_files": []
        }
        
        # Detect project type
        if (project_dir / "requirements.txt").exists() or (project_dir / "pyproject.toml").exists():
            analysis["project_type"] = "python"
        elif (project_dir / "package.json").exists():
            analysis["project_type"] = "nodejs"
        elif (project_dir / "Cargo.toml").exists():
            analysis["project_type"] = "rust"
        elif (project_dir / "go.mod").exists():
            analysis["project_type"] = "go"
        
        # Detect frameworks
        if analysis["project_type"] == "python":
            # Check for common Python MCP frameworks
            try:
                for py_file in project_dir.glob("*.py"):
                    with open(py_file, 'r') as f:
                        content = f.read()
                    
                    if "fastmcp" in content.lower():
                        analysis["detected_frameworks"].append("FastMCP")
                    elif "mcp" in content.lower():
                        analysis["detected_frameworks"].append("MCP SDK")
                        
            except Exception:
                pass
        
        # List configuration files
        config_patterns = ["*.json", "*.toml", "*.yaml", "*.yml", "*.ini", "*.cfg", "*.txt"]
        for pattern in config_patterns:
            analysis["configuration_files"].extend([
                f.name for f in project_dir.glob(pattern)
            ])
        
        return analysis
    
    def _analyze_validation_context(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Analyze validation context for additional insights.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Validation context analysis
        """
        return {
            "validation_level": validation_report.validation_level.value,
            "execution_time": validation_report.total_execution_time,
            "performance_issues": validation_report.performance_metrics.get("startup_time", 0) > 5.0,
            "error_distribution": {
                "startup_errors": len(validation_report.startup_result.errors),
                "protocol_errors": len(validation_report.protocol_result.errors),
                "functionality_errors": len(validation_report.functionality_result.errors)
            }
        }