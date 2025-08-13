#!/usr/bin/env python3
"""
Demonstration of MCP Server Builder validation reporting and diagnostics features.

This script shows how to use the new validation reporting and diagnostics
functionality to get detailed feedback on MCP server validation results.
"""

import json
import sys
import tempfile
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from managers.validation_engine import MCPValidationEngine
from managers.validation_reporter import ValidationReporter
from managers.validation_diagnostics import ValidationDiagnostics


def create_sample_project(project_path: str, project_type: str = "working"):
    """Create a sample MCP server project for demonstration.
    
    Args:
        project_path: Path where to create the project
        project_type: Type of project ("working", "broken", "minimal")
    """
    project_dir = Path(project_path)
    project_dir.mkdir(exist_ok=True)
    
    if project_type == "working":
        # Create a working MCP server
        server_code = '''
import json
import sys
from typing import Dict, Any

def initialize() -> Dict[str, Any]:
    """Initialize the MCP server."""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {
                "listChanged": True
            },
            "resources": {
                "subscribe": True,
                "listChanged": True
            },
            "prompts": {
                "listChanged": True
            }
        },
        "serverInfo": {
            "name": "demo-server",
            "version": "1.0.0"
        }
    }

def list_tools() -> Dict[str, Any]:
    """List available tools."""
    return {
        "tools": [
            {
                "name": "echo",
                "description": "Echo back the input text",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"}
                    },
                    "required": ["text"]
                }
            }
        ]
    }

def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Call a tool."""
    if name == "echo":
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Echo: {arguments.get('text', '')}"
                }
            ]
        }
    else:
        raise ValueError(f"Unknown tool: {name}")

def main():
    """Main server entry point."""
    print("MCP Demo Server starting...")
    # In a real server, this would handle JSON-RPC communication
    
if __name__ == "__main__":
    main()
'''
        
        requirements = '''
mcp>=1.0.0
fastmcp>=0.1.0
'''
        
    elif project_type == "broken":
        # Create a broken server with syntax errors
        server_code = '''
import json
import sys

def broken_function(
    print("Missing closing parenthesis - syntax error")

def initialize():
    # Missing return statement
    pass

if __name__ == "__main__":
    main()  # Undefined function
'''
        
        requirements = '''
nonexistent_package>=1.0.0
'''
        
    else:  # minimal
        # Create a minimal server with limited functionality
        server_code = '''
print("Minimal MCP server - no actual MCP functionality")
'''
        
        requirements = '''
# No dependencies specified
'''
    
    # Write files
    (project_dir / "main.py").write_text(server_code)
    (project_dir / "requirements.txt").write_text(requirements)


def demonstrate_validation_reporting():
    """Demonstrate validation reporting features."""
    print("=" * 60)
    print("MCP Server Builder - Validation Reporting Demo")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create sample projects
        working_project = Path(temp_dir) / "working_server"
        broken_project = Path(temp_dir) / "broken_server"
        minimal_project = Path(temp_dir) / "minimal_server"
        
        create_sample_project(str(working_project), "working")
        create_sample_project(str(broken_project), "broken")
        create_sample_project(str(minimal_project), "minimal")
        
        # Initialize validation engine
        engine = MCPValidationEngine()
        
        print("\n1. Testing Working Server")
        print("-" * 30)
        
        # Test working server (mock the validation for demo)
        print(f"Validating project: {working_project}")
        
        # Run diagnostics only (no full validation to avoid complexity)
        diagnostic_results = engine.run_diagnostics_only(str(working_project))
        
        print(f"Diagnostic checks completed: {len(diagnostic_results)} checks")
        for result in diagnostic_results[:3]:  # Show first 3 results
            status_icon = "✅" if result["status"] == "PASS" else "❌" if result["status"] == "FAIL" else "⚠️"
            print(f"  {status_icon} {result['check']}: {result['message']}")
        
        print("\n2. Testing Broken Server")
        print("-" * 30)
        
        print(f"Validating project: {broken_project}")
        diagnostic_results = engine.run_diagnostics_only(str(broken_project))
        
        failed_checks = [r for r in diagnostic_results if r["status"] == "FAIL"]
        print(f"Found {len(failed_checks)} failed diagnostic checks:")
        
        for result in failed_checks[:3]:  # Show first 3 failures
            print(f"  ❌ {result['check']}: {result['message']}")
            if result["suggestions"]:
                print(f"     💡 Suggestion: {result['suggestions'][0]}")
        
        print("\n3. Generating Comprehensive Diagnostic Report")
        print("-" * 45)
        
        diagnostic_report = engine.generate_diagnostic_report(str(broken_project))
        
        print("Diagnostic Summary:")
        summary = diagnostic_report["diagnostic_summary"]
        print(f"  Total checks: {summary['total_checks']}")
        print(f"  Passed: {summary['passed']}")
        print(f"  Failed: {summary['failed']}")
        print(f"  Warnings: {summary['warnings']}")
        print(f"  Health Score: {summary['health_score']}")
        
        if summary["critical_issues"]:
            print(f"  Critical Issues: {', '.join(summary['critical_issues'])}")
        
        print("\n4. Environment Analysis")
        print("-" * 25)
        
        env_analysis = diagnostic_report["environment_analysis"]
        print(f"Project Type: {env_analysis['project_type']}")
        print(f"Configuration Files: {', '.join(env_analysis['configuration_files'])}")
        if env_analysis["detected_frameworks"]:
            print(f"Detected Frameworks: {', '.join(env_analysis['detected_frameworks'])}")
        
        print("\n5. Validation History and Trends")
        print("-" * 35)
        
        # Simulate some validation history
        reporter = ValidationReporter()
        
        # Get validation history (will be empty for this demo)
        history = engine.get_validation_history(str(working_project))
        print(f"Validation history entries: {len(history)}")
        
        if len(history) >= 2:
            trend_analysis = engine.generate_trend_analysis(str(working_project))
            print(f"Success rate: {trend_analysis['success_rate']:.1f}%")
            print(f"Total validations: {trend_analysis['total_validations']}")
        else:
            print("Not enough validation history for trend analysis")
        
        print("\n6. Actionable Recommendations")
        print("-" * 35)
        
        # Create a mock failed validation report for recommendations
        from models.base import (
            ValidationReport, ServerStartupResult, ProtocolComplianceResult,
            FunctionalityTestResult
        )
        from models.enums import ValidationLevel
        from datetime import datetime
        
        # Create a failed validation report
        startup_result = ServerStartupResult(
            success=False,
            process_id=None,
            startup_time=0.0,
            errors=["ImportError: No module named 'mcp'"],
            logs=[]
        )
        
        protocol_result = ProtocolComplianceResult(
            success=False,
            supported_capabilities=[],
            missing_capabilities=["initialize", "tools/list"],
            protocol_version=None,
            errors=["Server failed to start"]
        )
        
        functionality_result = FunctionalityTestResult(
            success=False,
            tested_tools={},
            tested_resources={},
            tested_prompts={},
            errors=["No functionality could be tested"],
            performance_metrics={}
        )
        
        mock_report = ValidationReport(
            project_path=str(broken_project),
            validation_level=ValidationLevel.STANDARD,
            overall_success=False,
            startup_result=startup_result,
            protocol_result=protocol_result,
            functionality_result=functionality_result,
            performance_metrics={"startup_time": 0.0},
            recommendations=[],
            timestamp=datetime.now().isoformat(),
            total_execution_time=1.0
        )
        
        recommendations = engine.get_actionable_recommendations(mock_report)
        
        print(f"Generated {len(recommendations)} actionable recommendations:")
        for i, rec in enumerate(recommendations[:2], 1):  # Show first 2
            print(f"\n  {i}. {rec['title']} (Priority: {rec['priority']})")
            print(f"     Issue: {rec['issue']}")
            print(f"     Impact: {rec['impact']}")
            print(f"     Steps:")
            for step in rec['action_steps'][:2]:  # Show first 2 steps
                print(f"       • {step}")
            if len(rec['action_steps']) > 2:
                print(f"       • ... and {len(rec['action_steps']) - 2} more steps")
            print(f"     Estimated Effort: {rec['estimated_effort']}")
        
        print("\n" + "=" * 60)
        print("Demo completed! The validation reporting system provides:")
        print("• Detailed diagnostic reports with actionable feedback")
        print("• Comprehensive error analysis and troubleshooting guides")
        print("• Validation history tracking and trend analysis")
        print("• Automated fix recommendations with priority levels")
        print("• Environment analysis and project health scoring")
        print("=" * 60)


if __name__ == "__main__":
    demonstrate_validation_reporting()