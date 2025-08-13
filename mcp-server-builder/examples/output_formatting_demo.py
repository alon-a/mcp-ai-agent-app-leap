#!/usr/bin/env python3
"""
Demonstration of enhanced output formatting and user feedback capabilities.

This script showcases the various output formatting features implemented
for the MCP Server Builder CLI, including:
- Different verbosity levels
- Colored output and progress indicators
- Summary reports and next-steps guidance
- Status tables and step-by-step guides
- Validation result formatting
"""

import time
import sys
import os

# Add the src directory to the path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.cli.output import (
    OutputFormatter,
    ProgressIndicator,
    VerbosityLevel,
    create_summary_report,
    create_detailed_report,
    create_progress_summary,
    create_status_table,
    create_step_by_step_guide,
    format_validation_results
)


def demo_basic_output(formatter):
    """Demonstrate basic output formatting."""
    formatter.header("Basic Output Formatting Demo")
    
    formatter.success("This is a success message")
    formatter.info("This is an info message")
    formatter.warning("This is a warning message")
    formatter.error("This is an error message")
    
    formatter.section("Verbose Messages")
    formatter.verbose("Level 1 verbose message", 1)
    formatter.verbose("Level 2 detailed message", 2)
    formatter.verbose("Level 3 debug message", 3)
    
    formatter.section("Key-Value Pairs")
    formatter.key_value("Project Name", "my-mcp-server")
    formatter.key_value("Template", "python-fastmcp")
    formatter.key_value("Dependencies", ["fastmcp", "pydantic", "httpx"])


def demo_progress_indicators(formatter):
    """Demonstrate progress indicators."""
    formatter.header("Progress Indicators Demo")
    
    # Simple progress indicator
    progress = ProgressIndicator("Downloading files", formatter)
    progress.start()
    time.sleep(1)
    progress.update_message("Installing dependencies")
    time.sleep(1)
    progress.stop("Installation completed")
    
    # Progress summary
    formatter.section("Progress Summary")
    create_progress_summary(
        "Building MCP Server",
        total_steps=5,
        completed_steps=3,
        current_step="Running tests",
        formatter=formatter,
        start_time=time.time() - 30  # Simulate 30 seconds elapsed
    )


def demo_summary_reports(formatter):
    """Demonstrate summary reports."""
    formatter.header("Summary Reports Demo")
    
    # Basic summary report
    project_data = {
        "Project Name": "my-mcp-server",
        "Template Used": "python-fastmcp",
        "Files Created": ["main.py", "requirements.txt", "README.md", "tests/test_main.py"],
        "Dependencies Installed": ["fastmcp", "pydantic", "httpx", "pytest"],
        "Build Time": "2.3s"
    }
    
    next_steps = [
        "cd my-mcp-server",
        "Review the generated files",
        "Customize your server implementation",
        "Run tests with: pytest",
        "Start your server with: python main.py"
    ]
    
    warnings = ["Template uses experimental features"]
    
    create_summary_report(
        "Project Creation Complete",
        project_data,
        formatter,
        next_steps=next_steps,
        warnings=warnings
    )


def demo_detailed_reports(formatter):
    """Demonstrate detailed multi-section reports."""
    formatter.header("Detailed Reports Demo")
    
    sections = {
        "📁 Project Structure": {
            "Root Directory": "my-mcp-server/",
            "Source Files": ["main.py", "models.py", "handlers.py"],
            "Test Files": ["tests/test_main.py", "tests/test_models.py"],
            "Config Files": ["pyproject.toml", "requirements.txt"]
        },
        "📦 Dependencies": {
            "Runtime Dependencies": ["fastmcp>=0.1.0", "pydantic>=2.0.0"],
            "Development Dependencies": ["pytest>=7.0.0", "black>=22.0.0"],
            "Total Size": "15.2 MB"
        },
        "🔧 Build Configuration": {
            "Python Version": "3.8+",
            "Build Tool": "pip",
            "Test Framework": "pytest",
            "Linting": "black + ruff"
        }
    }
    
    create_detailed_report("Project Analysis", sections, formatter)


def demo_status_tables(formatter):
    """Demonstrate status tables."""
    formatter.header("Status Tables Demo")
    
    # Task status table
    task_headers = ["Task", "Status", "Duration", "Details"]
    task_rows = [
        ["Create project structure", "✅ Complete", "0.2s", "5 directories created"],
        ["Download template files", "✅ Complete", "1.1s", "8 files downloaded"],
        ["Install dependencies", "✅ Complete", "12.3s", "4 packages installed"],
        ["Run build commands", "⚠️ Warning", "2.1s", "1 warning generated"],
        ["Validate server", "❌ Failed", "0.5s", "Connection timeout"]
    ]
    
    create_status_table(task_headers, task_rows, formatter, "Build Process Status")
    
    # Validation results table
    validation_headers = ["Test Category", "Passed", "Failed", "Skipped"]
    validation_rows = [
        ["Protocol Compliance", "8", "0", "0"],
        ["Tool Registration", "5", "1", "0"],
        ["Resource Access", "3", "0", "1"],
        ["Error Handling", "4", "2", "0"]
    ]
    
    create_status_table(validation_headers, validation_rows, formatter, "Validation Test Results")


def demo_step_by_step_guides(formatter):
    """Demonstrate step-by-step guides."""
    formatter.header("Step-by-Step Guides Demo")
    
    setup_steps = [
        {
            "title": "Initialize Project",
            "description": "Create a new MCP server project from template",
            "command": "mcp-builder create my-server --template python-fastmcp",
            "note": "This will create a new directory with your project"
        },
        {
            "title": "Install Dependencies",
            "description": "Install required Python packages",
            "command": "cd my-server && pip install -r requirements.txt"
        },
        {
            "title": "Configure Server",
            "description": "Edit the main configuration file",
            "command": "nano main.py",
            "note": "Add your custom tools and resources here"
        },
        {
            "title": "Test Server",
            "description": "Run the test suite to verify functionality",
            "command": "pytest tests/",
            "note": "All tests should pass before deployment"
        },
        {
            "title": "Start Server",
            "description": "Launch your MCP server",
            "command": "python main.py",
            "note": "Server will start on the default port"
        }
    ]
    
    create_step_by_step_guide("Getting Started with Your MCP Server", setup_steps, formatter)


def demo_validation_results(formatter):
    """Demonstrate validation result formatting."""
    formatter.header("Validation Results Demo")
    
    # Successful validation
    success_results = {
        "total_tests": 15,
        "passed_tests": 15,
        "failed_tests": 0,
        "warnings": [],
        "errors": []
    }
    
    formatter.section("Successful Validation")
    format_validation_results(success_results, formatter)
    
    # Failed validation with issues
    failed_results = {
        "total_tests": 15,
        "passed_tests": 10,
        "failed_tests": 5,
        "warnings": [
            "Tool 'search_files' has no description",
            "Resource 'config' is not documented",
            "Server startup time is slow (>2s)"
        ],
        "errors": [
            "Tool 'invalid_tool' failed to register",
            "Resource 'missing_file' not found",
            "Protocol version mismatch",
            "Authentication failed for test client",
            "Server crashed during stress test"
        ]
    }
    
    formatter.section("Failed Validation with Issues")
    format_validation_results(failed_results, formatter)


def main():
    """Run the output formatting demonstration."""
    print("🎨 MCP Server Builder - Enhanced Output Formatting Demo")
    print("=" * 60)
    
    # Test different verbosity levels
    verbosity_levels = [
        (0, "Quiet Mode (errors only)"),
        (1, "Normal Mode"),
        (2, "Verbose Mode"),
        (3, "Debug Mode")
    ]
    
    for verbosity, description in verbosity_levels:
        print(f"\n{'='*20} {description} {'='*20}")
        formatter = OutputFormatter(verbosity=verbosity)
        
        if verbosity == 0:
            # In quiet mode, only show errors
            formatter.error("This error message will be shown")
            formatter.success("This success message will be hidden")
            formatter.info("This info message will be hidden")
        else:
            # Show a subset of demos for each verbosity level
            demo_basic_output(formatter)
            
            if verbosity >= 2:
                demo_progress_indicators(formatter)
                demo_summary_reports(formatter)
            
            if verbosity >= 3:
                demo_detailed_reports(formatter)
                demo_status_tables(formatter)
                demo_step_by_step_guides(formatter)
                demo_validation_results(formatter)
        
        print("\n" + "-" * 60)
    
    print("\n✨ Demo completed! Try running with different verbosity levels:")
    print("   python output_formatting_demo.py")


if __name__ == "__main__":
    main()