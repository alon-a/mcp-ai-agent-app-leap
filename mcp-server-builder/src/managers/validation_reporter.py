"""Validation reporting and diagnostics system."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import asdict
from ..models.base import (
    ValidationReport, ValidationResult, ServerStartupResult,
    ProtocolComplianceResult, FunctionalityTestResult
)
from ..models.enums import ValidationLevel


class ValidationReporter:
    """Handles validation reporting, diagnostics, and history tracking."""
    
    def __init__(self, reports_directory: str = ".mcp_validation_reports"):
        """Initialize the validation reporter.
        
        Args:
            reports_directory: Directory to store validation reports
        """
        self.reports_directory = Path(reports_directory)
        self.reports_directory.mkdir(exist_ok=True)
        
        # Create subdirectories for organization
        (self.reports_directory / "detailed").mkdir(exist_ok=True)
        (self.reports_directory / "summaries").mkdir(exist_ok=True)
        (self.reports_directory / "diagnostics").mkdir(exist_ok=True)
    
    def generate_detailed_report(
        self, 
        validation_report: ValidationReport,
        include_diagnostics: bool = True
    ) -> Dict[str, Any]:
        """Generate a detailed validation report with actionable feedback.
        
        Args:
            validation_report: The validation report to process
            include_diagnostics: Whether to include diagnostic information
            
        Returns:
            Dictionary containing the detailed report
        """
        report = {
            "metadata": {
                "report_id": self._generate_report_id(validation_report),
                "generated_at": datetime.now().isoformat(),
                "project_path": validation_report.project_path,
                "validation_level": validation_report.validation_level.value,
                "overall_success": validation_report.overall_success,
                "total_execution_time": validation_report.total_execution_time
            },
            "executive_summary": self._generate_executive_summary(validation_report),
            "detailed_results": {
                "startup_validation": self._format_startup_results(validation_report.startup_result),
                "protocol_compliance": self._format_protocol_results(validation_report.protocol_result),
                "functionality_testing": self._format_functionality_results(validation_report.functionality_result)
            },
            "performance_analysis": self._analyze_performance(validation_report.performance_metrics),
            "actionable_recommendations": self._generate_actionable_recommendations(validation_report),
            "next_steps": self._generate_next_steps(validation_report)
        }
        
        if include_diagnostics:
            report["diagnostics"] = self._generate_diagnostics(validation_report)
        
        return report
    
    def generate_summary_report(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Generate a concise summary report.
        
        Args:
            validation_report: The validation report to summarize
            
        Returns:
            Dictionary containing the summary report
        """
        return {
            "project": validation_report.project_path,
            "timestamp": validation_report.timestamp,
            "overall_success": validation_report.overall_success,
            "validation_level": validation_report.validation_level.value,
            "execution_time": validation_report.total_execution_time,
            "results_summary": {
                "startup": validation_report.startup_result.success,
                "protocol": validation_report.protocol_result.success,
                "functionality": validation_report.functionality_result.success
            },
            "error_count": (
                len(validation_report.startup_result.errors) +
                len(validation_report.protocol_result.errors) +
                len(validation_report.functionality_result.errors)
            ),
            "recommendations_count": len(validation_report.recommendations),
            "performance_score": self._calculate_performance_score(validation_report.performance_metrics)
        }
    
    def save_report(
        self, 
        validation_report: ValidationReport, 
        report_type: str = "detailed"
    ) -> str:
        """Save a validation report to disk.
        
        Args:
            validation_report: The validation report to save
            report_type: Type of report ("detailed", "summary", "diagnostics")
            
        Returns:
            Path to the saved report file
        """
        report_id = self._generate_report_id(validation_report)
        
        if report_type == "detailed":
            report_data = self.generate_detailed_report(validation_report)
            filename = f"detailed_report_{report_id}.json"
            filepath = self.reports_directory / "detailed" / filename
        elif report_type == "summary":
            report_data = self.generate_summary_report(validation_report)
            filename = f"summary_{report_id}.json"
            filepath = self.reports_directory / "summaries" / filename
        elif report_type == "diagnostics":
            report_data = self._generate_diagnostics(validation_report)
            filename = f"diagnostics_{report_id}.json"
            filepath = self.reports_directory / "diagnostics" / filename
        else:
            raise ValueError(f"Unknown report type: {report_type}")
        
        with open(filepath, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        # Also update the history index
        self._update_history_index(validation_report, str(filepath))
        
        return str(filepath)
    
    def get_validation_history(
        self, 
        project_path: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get validation history for a project or all projects.
        
        Args:
            project_path: Optional project path to filter by
            limit: Optional limit on number of results
            
        Returns:
            List of validation history entries
        """
        history_file = self.reports_directory / "validation_history.json"
        
        if not history_file.exists():
            return []
        
        try:
            with open(history_file, 'r') as f:
                history = json.load(f)
        except Exception:
            return []
        
        # Filter by project path if specified
        if project_path:
            history = [entry for entry in history if entry.get("project_path") == project_path]
        
        # Sort by timestamp (most recent first)
        history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Apply limit if specified
        if limit:
            history = history[:limit]
        
        return history
    
    def generate_trend_analysis(self, project_path: str) -> Dict[str, Any]:
        """Generate trend analysis for a specific project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Dictionary containing trend analysis
        """
        history = self.get_validation_history(project_path)
        
        if len(history) < 2:
            return {
                "message": "Insufficient data for trend analysis (need at least 2 validation runs)",
                "data_points": len(history)
            }
        
        # Analyze trends
        success_trend = [entry["overall_success"] for entry in history]
        execution_time_trend = [entry.get("execution_time", 0) for entry in history]
        error_count_trend = [entry.get("error_count", 0) for entry in history]
        
        return {
            "total_validations": len(history),
            "success_rate": sum(success_trend) / len(success_trend) * 100,
            "trends": {
                "success": self._calculate_trend(success_trend),
                "execution_time": self._calculate_trend(execution_time_trend),
                "error_count": self._calculate_trend(error_count_trend)
            },
            "latest_vs_previous": {
                "success_improved": success_trend[0] > success_trend[1] if len(success_trend) > 1 else None,
                "execution_time_change": execution_time_trend[0] - execution_time_trend[1] if len(execution_time_trend) > 1 else None,
                "error_count_change": error_count_trend[0] - error_count_trend[1] if len(error_count_trend) > 1 else None
            },
            "recommendations": self._generate_trend_recommendations(history)
        }
    
    def _generate_report_id(self, validation_report: ValidationReport) -> str:
        """Generate a unique report ID.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Unique report ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        project_name = Path(validation_report.project_path).name
        return f"{project_name}_{timestamp}"
    
    def _generate_executive_summary(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Generate an executive summary of the validation.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Executive summary dictionary
        """
        total_errors = (
            len(validation_report.startup_result.errors) +
            len(validation_report.protocol_result.errors) +
            len(validation_report.functionality_result.errors)
        )
        
        status = "PASS" if validation_report.overall_success else "FAIL"
        
        summary = {
            "status": status,
            "confidence_level": self._calculate_confidence_level(validation_report),
            "readiness_assessment": self._assess_deployment_readiness(validation_report),
            "critical_issues": total_errors,
            "key_findings": []
        }
        
        # Add key findings
        if not validation_report.startup_result.success:
            summary["key_findings"].append("Server fails to start properly")
        
        if validation_report.protocol_result.missing_capabilities:
            summary["key_findings"].append(
                f"Missing {len(validation_report.protocol_result.missing_capabilities)} MCP capabilities"
            )
        
        if not any([
            validation_report.functionality_result.tested_tools,
            validation_report.functionality_result.tested_resources,
            validation_report.functionality_result.tested_prompts
        ]):
            summary["key_findings"].append("No functional capabilities detected")
        
        return summary
    
    def _format_startup_results(self, startup_result: ServerStartupResult) -> Dict[str, Any]:
        """Format startup validation results.
        
        Args:
            startup_result: The startup validation result
            
        Returns:
            Formatted startup results
        """
        return {
            "status": "PASS" if startup_result.success else "FAIL",
            "startup_time_seconds": startup_result.startup_time,
            "process_id": startup_result.process_id,
            "errors": startup_result.errors,
            "logs": startup_result.logs,
            "analysis": {
                "startup_performance": "Good" if startup_result.startup_time < 5.0 else "Slow",
                "error_severity": "High" if startup_result.errors else "None"
            }
        }
    
    def _format_protocol_results(self, protocol_result: ProtocolComplianceResult) -> Dict[str, Any]:
        """Format protocol compliance results.
        
        Args:
            protocol_result: The protocol compliance result
            
        Returns:
            Formatted protocol results
        """
        compliance_percentage = (
            len(protocol_result.supported_capabilities) / 
            (len(protocol_result.supported_capabilities) + len(protocol_result.missing_capabilities)) * 100
            if (protocol_result.supported_capabilities or protocol_result.missing_capabilities)
            else 0
        )
        
        return {
            "status": "PASS" if protocol_result.success else "FAIL",
            "compliance_percentage": compliance_percentage,
            "protocol_version": protocol_result.protocol_version,
            "supported_capabilities": protocol_result.supported_capabilities,
            "missing_capabilities": protocol_result.missing_capabilities,
            "errors": protocol_result.errors,
            "analysis": {
                "compliance_level": self._assess_compliance_level(compliance_percentage),
                "critical_missing": [cap for cap in protocol_result.missing_capabilities if cap in ["initialize", "tools/list"]]
            }
        }
    
    def _format_functionality_results(self, functionality_result: FunctionalityTestResult) -> Dict[str, Any]:
        """Format functionality test results.
        
        Args:
            functionality_result: The functionality test result
            
        Returns:
            Formatted functionality results
        """
        total_capabilities = (
            len(functionality_result.tested_tools) +
            len(functionality_result.tested_resources) +
            len(functionality_result.tested_prompts)
        )
        
        return {
            "status": "PASS" if functionality_result.success else "FAIL",
            "total_capabilities": total_capabilities,
            "tools": {
                "count": len(functionality_result.tested_tools),
                "results": functionality_result.tested_tools,
                "success_rate": self._calculate_success_rate(functionality_result.tested_tools)
            },
            "resources": {
                "count": len(functionality_result.tested_resources),
                "results": functionality_result.tested_resources,
                "success_rate": self._calculate_success_rate(functionality_result.tested_resources)
            },
            "prompts": {
                "count": len(functionality_result.tested_prompts),
                "results": functionality_result.tested_prompts,
                "success_rate": self._calculate_success_rate(functionality_result.tested_prompts)
            },
            "performance_metrics": functionality_result.performance_metrics,
            "errors": functionality_result.errors
        }
    
    def _analyze_performance(self, performance_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Analyze performance metrics.
        
        Args:
            performance_metrics: Performance metrics dictionary
            
        Returns:
            Performance analysis
        """
        analysis = {
            "overall_score": self._calculate_performance_score(performance_metrics),
            "metrics": performance_metrics,
            "benchmarks": {}
        }
        
        # Add benchmark comparisons
        if "startup_time" in performance_metrics:
            startup_time = performance_metrics["startup_time"]
            if startup_time < 2.0:
                analysis["benchmarks"]["startup"] = "Excellent"
            elif startup_time < 5.0:
                analysis["benchmarks"]["startup"] = "Good"
            elif startup_time < 10.0:
                analysis["benchmarks"]["startup"] = "Acceptable"
            else:
                analysis["benchmarks"]["startup"] = "Poor"
        
        # Analyze response times
        response_times = [
            performance_metrics.get("tools_response_time", 0),
            performance_metrics.get("resources_response_time", 0),
            performance_metrics.get("prompts_response_time", 0)
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        if avg_response_time < 0.1:
            analysis["benchmarks"]["responsiveness"] = "Excellent"
        elif avg_response_time < 0.5:
            analysis["benchmarks"]["responsiveness"] = "Good"
        elif avg_response_time < 1.0:
            analysis["benchmarks"]["responsiveness"] = "Acceptable"
        else:
            analysis["benchmarks"]["responsiveness"] = "Poor"
        
        return analysis
    
    def _generate_actionable_recommendations(self, validation_report: ValidationReport) -> List[Dict[str, Any]]:
        """Generate actionable recommendations with priority and steps.
        
        Args:
            validation_report: The validation report
            
        Returns:
            List of actionable recommendations
        """
        recommendations = []
        
        # Startup issues (Critical priority)
        if not validation_report.startup_result.success:
            recommendations.append({
                "priority": "CRITICAL",
                "category": "Startup",
                "issue": "Server fails to start",
                "impact": "Server cannot be used",
                "action_steps": [
                    "Review server logs for error messages",
                    "Check dependency installation",
                    "Verify entry point configuration",
                    "Test server startup manually"
                ],
                "estimated_effort": "1-2 hours"
            })
        
        # Protocol compliance issues (High priority)
        if validation_report.protocol_result.missing_capabilities:
            recommendations.append({
                "priority": "HIGH",
                "category": "Protocol Compliance",
                "issue": f"Missing {len(validation_report.protocol_result.missing_capabilities)} MCP capabilities",
                "impact": "Reduced compatibility with MCP clients",
                "action_steps": [
                    f"Implement missing capabilities: {', '.join(validation_report.protocol_result.missing_capabilities)}",
                    "Review MCP protocol specification",
                    "Add proper JSON-RPC response handling",
                    "Test with MCP client tools"
                ],
                "estimated_effort": "2-4 hours"
            })
        
        # Performance issues (Medium priority)
        if validation_report.performance_metrics.get("startup_time", 0) > 5.0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Performance",
                "issue": "Slow server startup time",
                "impact": "Poor user experience",
                "action_steps": [
                    "Profile server initialization code",
                    "Optimize dependency loading",
                    "Consider lazy loading of resources",
                    "Review server architecture"
                ],
                "estimated_effort": "2-3 hours"
            })
        
        # Functionality issues (Medium priority)
        total_capabilities = (
            len(validation_report.functionality_result.tested_tools) +
            len(validation_report.functionality_result.tested_resources) +
            len(validation_report.functionality_result.tested_prompts)
        )
        
        if total_capabilities == 0:
            recommendations.append({
                "priority": "MEDIUM",
                "category": "Functionality",
                "issue": "No functional capabilities detected",
                "impact": "Server provides no useful functionality",
                "action_steps": [
                    "Add at least one tool, resource, or prompt",
                    "Implement proper capability registration",
                    "Test functionality with sample inputs",
                    "Document available capabilities"
                ],
                "estimated_effort": "1-3 hours"
            })
        
        return recommendations
    
    def _generate_next_steps(self, validation_report: ValidationReport) -> List[str]:
        """Generate next steps based on validation results.
        
        Args:
            validation_report: The validation report
            
        Returns:
            List of next steps
        """
        if validation_report.overall_success:
            return [
                "✅ Server validation passed - ready for deployment",
                "Consider running additional integration tests",
                "Document server capabilities and usage",
                "Set up monitoring and logging for production"
            ]
        else:
            next_steps = ["❌ Server validation failed - address issues before deployment"]
            
            # Add specific next steps based on failures
            if not validation_report.startup_result.success:
                next_steps.append("🔧 Fix server startup issues first")
            
            if validation_report.protocol_result.missing_capabilities:
                next_steps.append("📋 Implement missing MCP protocol capabilities")
            
            if not validation_report.functionality_result.success:
                next_steps.append("⚙️ Add and test server functionality")
            
            next_steps.append("🔄 Re-run validation after fixes")
            
            return next_steps
    
    def _generate_diagnostics(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Generate diagnostic information for troubleshooting.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Diagnostic information dictionary
        """
        diagnostics = {
            "environment_info": self._collect_environment_info(),
            "project_analysis": self._analyze_project_structure(validation_report.project_path),
            "error_analysis": self._analyze_errors(validation_report),
            "troubleshooting_guide": self._generate_troubleshooting_guide(validation_report)
        }
        
        return diagnostics
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect environment information for diagnostics.
        
        Returns:
            Environment information dictionary
        """
        import platform
        import sys
        
        return {
            "python_version": sys.version,
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "timestamp": datetime.now().isoformat()
        }
    
    def _analyze_project_structure(self, project_path: str) -> Dict[str, Any]:
        """Analyze project structure for diagnostics.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Project structure analysis
        """
        project_dir = Path(project_path)
        
        analysis = {
            "project_exists": project_dir.exists(),
            "is_directory": project_dir.is_dir() if project_dir.exists() else False,
            "files_found": [],
            "missing_files": [],
            "permissions": {}
        }
        
        if project_dir.exists():
            # Check for common server files
            common_files = [
                "main.py", "server.py", "app.py", "__init__.py",
                "package.json", "pyproject.toml", "requirements.txt",
                "Cargo.toml", "go.mod"
            ]
            
            for file in common_files:
                file_path = project_dir / file
                if file_path.exists():
                    analysis["files_found"].append(file)
                    try:
                        analysis["permissions"][file] = oct(file_path.stat().st_mode)[-3:]
                    except Exception:
                        analysis["permissions"][file] = "unknown"
                else:
                    analysis["missing_files"].append(file)
        
        return analysis
    
    def _analyze_errors(self, validation_report: ValidationReport) -> Dict[str, Any]:
        """Analyze errors from validation results.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Error analysis dictionary
        """
        all_errors = (
            validation_report.startup_result.errors +
            validation_report.protocol_result.errors +
            validation_report.functionality_result.errors
        )
        
        error_categories = {
            "import_errors": [],
            "permission_errors": [],
            "network_errors": [],
            "configuration_errors": [],
            "other_errors": []
        }
        
        for error in all_errors:
            error_lower = error.lower()
            if "import" in error_lower or "module" in error_lower:
                error_categories["import_errors"].append(error)
            elif "permission" in error_lower or "access" in error_lower:
                error_categories["permission_errors"].append(error)
            elif "network" in error_lower or "connection" in error_lower:
                error_categories["network_errors"].append(error)
            elif "config" in error_lower or "setting" in error_lower:
                error_categories["configuration_errors"].append(error)
            else:
                error_categories["other_errors"].append(error)
        
        return {
            "total_errors": len(all_errors),
            "error_categories": error_categories,
            "most_common_category": max(error_categories.keys(), key=lambda k: len(error_categories[k])) if all_errors else None
        }
    
    def _generate_troubleshooting_guide(self, validation_report: ValidationReport) -> Dict[str, List[str]]:
        """Generate troubleshooting guide based on validation results.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Troubleshooting guide dictionary
        """
        guide = {}
        
        if not validation_report.startup_result.success:
            guide["startup_issues"] = [
                "Check if all dependencies are installed correctly",
                "Verify the server entry point exists and is executable",
                "Review server logs for specific error messages",
                "Test running the server manually from command line",
                "Check file permissions on server files"
            ]
        
        if validation_report.protocol_result.missing_capabilities:
            guide["protocol_issues"] = [
                "Review MCP protocol specification documentation",
                "Ensure proper JSON-RPC message handling",
                "Implement missing protocol methods",
                "Test with a simple MCP client",
                "Validate JSON-RPC request/response format"
            ]
        
        if not validation_report.functionality_result.success:
            guide["functionality_issues"] = [
                "Add at least one tool, resource, or prompt to the server",
                "Ensure proper capability registration in server code",
                "Test individual functions with sample inputs",
                "Check for runtime errors in capability implementations",
                "Verify proper error handling in server functions"
            ]
        
        return guide
    
    def _update_history_index(self, validation_report: ValidationReport, report_path: str):
        """Update the validation history index.
        
        Args:
            validation_report: The validation report
            report_path: Path to the saved report
        """
        history_file = self.reports_directory / "validation_history.json"
        
        # Load existing history
        history = []
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    history = json.load(f)
            except Exception:
                history = []
        
        # Add new entry
        entry = {
            "timestamp": validation_report.timestamp,
            "project_path": validation_report.project_path,
            "overall_success": validation_report.overall_success,
            "execution_time": validation_report.total_execution_time,
            "validation_level": validation_report.validation_level.value,
            "error_count": (
                len(validation_report.startup_result.errors) +
                len(validation_report.protocol_result.errors) +
                len(validation_report.functionality_result.errors)
            ),
            "report_path": report_path
        }
        
        history.append(entry)
        
        # Keep only last 100 entries per project
        project_entries = {}
        for entry in history:
            project = entry["project_path"]
            if project not in project_entries:
                project_entries[project] = []
            project_entries[project].append(entry)
        
        # Trim to last 100 entries per project
        trimmed_history = []
        for project, entries in project_entries.items():
            entries.sort(key=lambda x: x["timestamp"], reverse=True)
            trimmed_history.extend(entries[:100])
        
        # Save updated history
        with open(history_file, 'w') as f:
            json.dump(trimmed_history, f, indent=2)
    
    def _calculate_confidence_level(self, validation_report: ValidationReport) -> str:
        """Calculate confidence level for deployment.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Confidence level string
        """
        if validation_report.overall_success:
            return "HIGH"
        elif validation_report.startup_result.success:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _assess_deployment_readiness(self, validation_report: ValidationReport) -> str:
        """Assess deployment readiness.
        
        Args:
            validation_report: The validation report
            
        Returns:
            Deployment readiness assessment
        """
        if validation_report.overall_success:
            return "READY"
        elif validation_report.startup_result.success and validation_report.protocol_result.success:
            return "READY_WITH_LIMITATIONS"
        else:
            return "NOT_READY"
    
    def _assess_compliance_level(self, compliance_percentage: float) -> str:
        """Assess MCP protocol compliance level.
        
        Args:
            compliance_percentage: Compliance percentage
            
        Returns:
            Compliance level string
        """
        if compliance_percentage >= 90:
            return "Excellent"
        elif compliance_percentage >= 75:
            return "Good"
        elif compliance_percentage >= 50:
            return "Acceptable"
        else:
            return "Poor"
    
    def _calculate_success_rate(self, results: Dict[str, bool]) -> float:
        """Calculate success rate from results dictionary.
        
        Args:
            results: Dictionary of test results
            
        Returns:
            Success rate as percentage
        """
        if not results:
            return 0.0
        
        successful = sum(1 for success in results.values() if success)
        return (successful / len(results)) * 100
    
    def _calculate_performance_score(self, performance_metrics: Dict[str, float]) -> float:
        """Calculate overall performance score.
        
        Args:
            performance_metrics: Performance metrics dictionary
            
        Returns:
            Performance score (0-100)
        """
        score = 100.0
        
        # Penalize slow startup
        startup_time = performance_metrics.get("startup_time", 0)
        if startup_time > 10:
            score -= 30
        elif startup_time > 5:
            score -= 15
        elif startup_time > 2:
            score -= 5
        
        # Penalize slow response times
        response_times = [
            performance_metrics.get("tools_response_time", 0),
            performance_metrics.get("resources_response_time", 0),
            performance_metrics.get("prompts_response_time", 0)
        ]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        if avg_response_time > 2:
            score -= 20
        elif avg_response_time > 1:
            score -= 10
        elif avg_response_time > 0.5:
            score -= 5
        
        return max(0.0, score)
    
    def _calculate_trend(self, values: List[Union[bool, float]]) -> str:
        """Calculate trend direction from a list of values.
        
        Args:
            values: List of values to analyze
            
        Returns:
            Trend direction string
        """
        if len(values) < 2:
            return "insufficient_data"
        
        # Convert booleans to numbers for trend calculation
        numeric_values = [float(v) for v in values]
        
        # Simple trend calculation (comparing first and last values)
        if numeric_values[0] > numeric_values[-1]:
            return "improving"
        elif numeric_values[0] < numeric_values[-1]:
            return "declining"
        else:
            return "stable"
    
    def _generate_trend_recommendations(self, history: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on validation history trends.
        
        Args:
            history: Validation history entries
            
        Returns:
            List of trend-based recommendations
        """
        recommendations = []
        
        if len(history) < 2:
            return ["Run more validations to establish trends"]
        
        # Analyze success rate trend
        recent_successes = [entry["overall_success"] for entry in history[:5]]
        success_rate = sum(recent_successes) / len(recent_successes)
        
        if success_rate < 0.5:
            recommendations.append("Success rate is declining - review recent changes")
        elif success_rate == 1.0:
            recommendations.append("Excellent success rate - maintain current practices")
        
        # Analyze execution time trend
        recent_times = [entry.get("execution_time", 0) for entry in history[:3]]
        if len(recent_times) >= 2 and recent_times[0] > recent_times[1] * 1.5:
            recommendations.append("Validation time is increasing - investigate performance issues")
        
        return recommendations