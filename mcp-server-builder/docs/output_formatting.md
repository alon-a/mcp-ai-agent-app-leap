# Enhanced Output Formatting and User Feedback

This document describes the enhanced output formatting and user feedback system implemented for the MCP Server Builder CLI.

## Overview

The enhanced output formatting system provides:

- **Multiple verbosity levels** with appropriate message filtering
- **Colored output and progress indicators** for better visual feedback
- **Comprehensive summary reports** with warnings, errors, and next steps
- **Status tables and step-by-step guides** for complex operations
- **Validation result formatting** with detailed diagnostics

## Features

### Verbosity Levels

The system supports four verbosity levels:

- **Quiet Mode (0)**: Only error messages are displayed
- **Normal Mode (1)**: Standard output with success, info, warning, and error messages
- **Verbose Mode (2)**: Includes detailed progress information and timestamps
- **Debug Mode (3)**: Full diagnostic output with trace-level information

### Output Types

#### Basic Messages

```python
formatter = OutputFormatter(verbosity=1)

formatter.success("Operation completed successfully")
formatter.info("Processing data...")
formatter.warning("Deprecated feature used")
formatter.error("Connection failed")
```

#### Verbose Messages

```python
formatter.verbose("Detailed operation info", level=1)
formatter.verbose("Internal processing details", level=2)
formatter.debug("Debug trace information")
```

#### Status Updates

```python
formatter.status_update("Installing dependencies", "INFO")
formatter.step_start("Building project", 2, 5)
formatter.step_complete("Building project", duration=3.2)
```

### Progress Indicators

#### Animated Progress

```python
progress = ProgressIndicator("Processing files", formatter)
progress.start()
# ... long running operation ...
progress.update_message("Finalizing")
progress.stop("Processing completed")
```

#### Progress Summary

```python
create_progress_summary(
    operation="Building MCP Server",
    total_steps=10,
    completed_steps=6,
    current_step="Running tests",
    formatter=formatter,
    start_time=start_time
)
```

### Summary Reports

#### Basic Summary

```python
data = {
    "Project Name": "my-server",
    "Files Created": ["main.py", "config.json"],
    "Build Time": "2.3s"
}

next_steps = [
    "Review generated files",
    "Run tests",
    "Deploy server"
]

create_summary_report(
    "Project Created",
    data,
    formatter,
    next_steps=next_steps
)
```

#### Detailed Multi-Section Reports

```python
sections = {
    "Project Structure": {
        "Files": ["main.py", "tests.py"],
        "Directories": ["src/", "tests/"]
    },
    "Dependencies": {
        "Runtime": ["fastmcp", "pydantic"],
        "Development": ["pytest", "black"]
    }
}

create_detailed_report("Project Analysis", sections, formatter)
```

### Status Tables

```python
headers = ["Task", "Status", "Duration"]
rows = [
    ["Setup", "Complete", "1.2s"],
    ["Build", "Running", "3.1s"],
    ["Test", "Pending", "-"]
]

create_status_table(headers, rows, formatter, "Build Status")
```

### Step-by-Step Guides

```python
steps = [
    {
        "title": "Initialize Project",
        "description": "Create project structure",
        "command": "mcp-builder create my-server",
        "note": "This creates a new directory"
    },
    {
        "title": "Install Dependencies",
        "command": "pip install -r requirements.txt"
    }
]

create_step_by_step_guide("Getting Started", steps, formatter)
```

### Validation Results

```python
results = {
    "total_tests": 10,
    "passed_tests": 8,
    "failed_tests": 2,
    "warnings": ["Deprecated API used"],
    "errors": ["Connection timeout", "Invalid config"]
}

format_validation_results(results, formatter)
```

## Color Support

The system automatically detects terminal color support:

- **Auto-detection**: Based on TTY status and environment variables
- **Environment variables**: 
  - `NO_COLOR`: Disable colors
  - `FORCE_COLOR`: Force color output
- **Windows support**: Includes colorama integration and ANSI support detection

## Usage Examples

### CLI Integration

```python
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v', action='count', default=0)
    parser.add_argument('--quiet', '-q', action='store_true')
    args = parser.parse_args()
    
    verbosity = 0 if args.quiet else args.verbose
    formatter = OutputFormatter(verbosity=verbosity)
    
    # Use formatter throughout your CLI
    formatter.info("Starting operation...")
```

### Progress Tracking

```python
def build_project(formatter):
    steps = ["Setup", "Download", "Install", "Build", "Test"]
    
    for i, step in enumerate(steps):
        formatter.step_start(step, i+1, len(steps))
        
        progress = ProgressIndicator(f"Running {step.lower()}", formatter)
        progress.start()
        
        # Simulate work
        time.sleep(2)
        
        progress.stop(f"{step} completed")
        formatter.step_complete(step, 2.0)
```

### Error Handling with Reports

```python
def handle_build_failure(errors, warnings, formatter):
    data = {
        "Build Status": "Failed",
        "Errors": len(errors),
        "Warnings": len(warnings),
        "Duration": "45.2s"
    }
    
    next_steps = [
        "Review error messages above",
        "Check configuration files",
        "Run with --verbose for more details",
        "Contact support if issues persist"
    ]
    
    create_summary_report(
        "Build Failed",
        data,
        formatter,
        next_steps=next_steps,
        errors=errors,
        warnings=warnings
    )
```

## Testing

The output formatting system includes comprehensive tests covering:

- Verbosity level handling
- Color detection and formatting
- Progress indicator functionality
- Summary report generation
- Status table formatting
- Validation result display

Run tests with:

```bash
python -m pytest tests/test_output_formatting.py -v
```

## Demo

A comprehensive demonstration is available:

```bash
python examples/output_formatting_demo.py
```

This shows all formatting features across different verbosity levels.

## Requirements Satisfied

This implementation satisfies the following requirements:

- **6.2**: Progress indicators for each major step with completion status logging
- **6.4**: Summary reports with next steps and actionable guidance

The enhanced output formatting provides:

1. **Formatted output for different verbosity levels**: Four distinct levels with appropriate message filtering
2. **Colored output and progress indicators**: Automatic color detection, animated progress, and visual feedback
3. **Summary reports and next-steps guidance**: Comprehensive reporting with actionable next steps, warnings, and error handling

## Integration

The enhanced output formatting is integrated throughout the MCP Server Builder CLI:

- Project creation workflows
- Template listing and information
- Validation processes
- Configuration management
- Error reporting and recovery

All CLI commands now provide consistent, user-friendly output with appropriate verbosity levels and visual feedback.