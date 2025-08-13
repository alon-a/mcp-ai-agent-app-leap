# Getting Started with MCP Server Builder

## Overview

The MCP Server Builder is an automated tool that creates complete MCP (Model Context Protocol) server environments from scratch. This guide will walk you through your first steps with the builder, from installation to creating your first MCP server.

## What You'll Learn

- How to install and set up the MCP Server Builder
- How to create your first MCP server
- How to customize server configuration
- How to validate and test your server
- Common use cases and patterns

## Prerequisites

Before you begin, ensure you have:

- **Python 3.8 or higher** installed
- **pip** package manager
- **Internet connection** for downloading templates
- **Basic familiarity** with command line/terminal

Optional but recommended:
- **Git** for version control
- **Virtual environment** tools (venv, conda, etc.)
- **Code editor** (VS Code, PyCharm, etc.)

## Installation

### Method 1: Install from PyPI (Recommended)

```bash
pip install mcp-server-builder
```

### Method 2: Install from Source

```bash
git clone https://github.com/your-org/mcp-server-builder.git
cd mcp-server-builder
pip install -e .
```

### Method 3: Using Virtual Environment

```bash
# Create virtual environment
python -m venv mcp-builder-env

# Activate virtual environment
# On Windows:
mcp-builder-env\Scripts\activate
# On macOS/Linux:
source mcp-builder-env/bin/activate

# Install the builder
pip install mcp-server-builder
```

### Verify Installation

```bash
python -c "import mcp_server_builder; print('✅ Installation successful')"
```

## Your First MCP Server

Let's create your first MCP server using the Python FastMCP template.

### Step 1: Basic Server Creation

Create a simple Python script to generate your server:

**File: `create_my_server.py`**
```python
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

# Initialize the project manager
manager = ProjectManagerImpl()

# Create your first server
result = manager.create_project(
    name="my-first-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'My First MCP Server',
            'description': 'A simple example server for learning'
        }
    }
)

# Check the result
if result.success:
    print(f"🎉 Server created successfully!")
    print(f"📁 Location: {result.project_path}")
    print(f"📋 Project ID: {result.project_id}")
else:
    print("❌ Server creation failed:")
    for error in result.errors:
        print(f"  - {error}")
```

Run the script:
```bash
python create_my_server.py
```

### Step 2: Explore Your Server

Navigate to the created server directory:
```bash
cd my-first-server
ls -la
```

You should see:
```
my-first-server/
├── main.py              # Main server file
├── pyproject.toml       # Python project configuration
├── README.md           # Documentation
├── src/                # Source code directory
├── tests/              # Test files
└── docs/               # Documentation
```

### Step 3: Examine the Generated Code

Look at the main server file:

**File: `main.py`**
```python
#!/usr/bin/env python3
"""My First MCP Server - A simple example server for learning

A Model Context Protocol server built with FastMCP.
"""

import asyncio
from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("My First MCP Server")

@mcp.tool()
def hello_world(name: str = "World") -> str:
    """Say hello to someone.
    
    Args:
        name: Name to greet
        
    Returns:
        Greeting message
    """
    return f"Hello, {name}!"

@mcp.resource("config://settings")
def get_settings() -> dict:
    """Get server configuration settings."""
    return {
        "server_name": "My First MCP Server",
        "version": "1.0.0",
        "transport": "stdio"
    }

async def main():
    """Run the MCP server."""
    async with mcp.run_server() as server:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Install Dependencies and Run

```bash
# Install the server in development mode
pip install -e .

# Run the server
python main.py
```

Your server is now running and ready to accept MCP protocol messages!

## Understanding Templates

### Available Templates

List all available templates:

```python
from mcp_server_builder.managers.template_engine import TemplateEngineImpl

engine = TemplateEngineImpl()
templates = engine.list_templates()

print("Available templates:")
for template in templates:
    print(f"  📦 {template.id}")
    print(f"     Name: {template.name}")
    print(f"     Language: {template.language.value}")
    print(f"     Framework: {template.framework.value}")
    print(f"     Description: {template.description}")
    print()
```

### Template Categories

**Python Templates:**
- `python-fastmcp`: High-level Python framework with decorators
- `python-lowlevel`: Direct MCP protocol implementation

**TypeScript Templates:**
- `typescript-sdk`: Official TypeScript SDK implementation

**Other Languages:**
- `go-foxy-contexts`: Go implementation using Foxy Contexts
- `rust-production`: Production-ready Rust implementation
- `java-quarkus`: Java implementation with Quarkus

## Customizing Your Server

### Basic Customization

```python
result = manager.create_project(
    name="custom-weather-server",
    template="python-fastmcp",
    config={
        'output_directory': './my-servers',  # Custom output location
        'custom_settings': {
            'server_name': 'Weather Information Server',
            'description': 'Provides weather data and forecasts',
            'transport': 'stdio'  # or 'http', 'sse'
        },
        'environment_variables': {
            'WEATHER_API_KEY': 'your-api-key-here',
            'DEBUG': 'true'
        },
        'additional_dependencies': [
            'requests>=2.28.0',
            'python-dotenv>=1.0.0'
        ]
    }
)
```

### Advanced Customization

```python
# More complex configuration
config = {
    'output_directory': './production-servers',
    'custom_settings': {
        'server_name': 'Production Data Server',
        'description': 'High-performance data processing server',
        'transport': 'http',
        'host': '0.0.0.0',
        'port': 8080,
        'enable_cors': True,
        'cors_origins': ['https://myapp.com'],
        'enable_logging': True,
        'log_level': 'INFO'
    },
    'environment_variables': {
        'DATABASE_URL': 'postgresql://user:pass@localhost/db',
        'REDIS_URL': 'redis://localhost:6379',
        'SECRET_KEY': 'your-secret-key',
        'ENVIRONMENT': 'production'
    },
    'additional_dependencies': [
        'sqlalchemy>=2.0.0',
        'redis>=4.5.0',
        'uvicorn>=0.20.0',
        'fastapi>=0.100.0'
    ]
}

result = manager.create_project(
    name="production-data-server",
    template="python-fastmcp",
    config=config
)
```

## Progress Monitoring

### Real-time Progress Tracking

```python
def progress_callback(project_id: str, percentage: float, phase: str):
    """Handle progress updates."""
    print(f"[{project_id[:8]}] {phase}: {percentage:.1f}%")

def error_callback(project_id: str, error: str):
    """Handle error notifications."""
    print(f"[{project_id[:8]}] ERROR: {error}")

# Create manager with callbacks
manager = ProjectManagerImpl(
    progress_callback=progress_callback,
    error_callback=error_callback
)

# Create project with progress monitoring
result = manager.create_project(
    name="monitored-server",
    template="python-fastmcp",
    config={'custom_settings': {'server_name': 'Monitored Server'}}
)
```

### Detailed Progress Information

```python
# Get detailed progress information
progress = manager.get_project_progress(result.project_id)
if progress:
    print(f"Current phase: {progress['current_phase']}")
    print(f"Progress: {progress['progress_percentage']:.1f}%")
    print(f"Status: {progress['status']}")

# Get all progress events
events = manager.get_project_events(result.project_id)
for event in events[-5:]:  # Last 5 events
    print(f"{event.timestamp}: {event.message}")
```

## Validation and Testing

### Basic Validation

```python
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = result.project_path

# Test server startup
startup_ok = validator.validate_server_startup(project_path)
print(f"Server startup: {'✅' if startup_ok else '❌'}")

# Test MCP protocol compliance
protocol_ok = validator.validate_mcp_protocol(project_path)
print(f"Protocol compliance: {'✅' if protocol_ok else '❌'}")

# Test functionality
functionality = validator.validate_functionality(project_path)
for func_type, result in functionality.items():
    print(f"{func_type}: {'✅' if result else '❌'}")
```

### Comprehensive Testing

```python
# Run comprehensive tests
test_results = validator.run_comprehensive_tests(project_path)

print("Comprehensive Test Results:")
print(f"  Overall success: {test_results.get('overall_success', False)}")
print(f"  Startup time: {test_results.get('startup_time', 0):.2f}s")
print(f"  Tools tested: {len(test_results.get('tools', {}))}")
print(f"  Resources tested: {len(test_results.get('resources', {}))}")
print(f"  Performance score: {test_results.get('performance_score', 0)}")

if test_results.get('errors'):
    print("Errors found:")
    for error in test_results['errors']:
        print(f"  - {error}")
```

## Common Use Cases

### 1. File Processing Server

```python
result = manager.create_project(
    name="file-processor",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'File Processing Server',
            'description': 'Processes and analyzes files'
        },
        'additional_dependencies': [
            'pandas>=2.0.0',
            'openpyxl>=3.1.0',
            'python-magic>=0.4.0'
        ]
    }
)
```

### 2. Web API Integration Server

```python
result = manager.create_project(
    name="api-integration-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'API Integration Server',
            'description': 'Integrates with external APIs',
            'transport': 'http',
            'port': 3000
        },
        'environment_variables': {
            'API_BASE_URL': 'https://api.example.com',
            'API_KEY': 'your-api-key'
        },
        'additional_dependencies': [
            'httpx>=0.24.0',
            'pydantic-settings>=2.0.0',
            'fastapi>=0.100.0',
            'uvicorn>=0.20.0'
        ]
    }
)
```

### 3. Database Query Server

```python
result = manager.create_project(
    name="database-query-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'Database Query Server',
            'description': 'Provides database query capabilities'
        },
        'environment_variables': {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        },
        'additional_dependencies': [
            'sqlalchemy>=2.0.0',
            'psycopg2-binary>=2.9.0',
            'alembic>=1.12.0'
        ]
    }
)
```

### 4. TypeScript Server

```python
result = manager.create_project(
    name="typescript-server",
    template="typescript-sdk",
    config={
        'custom_settings': {
            'server_name': 'TypeScript MCP Server',
            'description': 'A TypeScript-based MCP server',
            'port': 3000
        }
    }
)
```

## Project Management

### Listing Projects

```python
# List all projects
projects = manager.list_projects()
print("Your MCP Server Projects:")
for project in projects:
    print(f"  📦 {project['name']}")
    print(f"     Status: {project['status']}")
    print(f"     Template: {project['template_id']}")
    print(f"     Created: {project['created_at']}")
    print()
```

### Project Details

```python
# Get detailed project information
details = manager.get_project_details(result.project_id)
if details:
    print(f"Project: {details['name']}")
    print(f"Status: {details['status']}")
    print(f"Progress: {details['progress_percentage']:.1f}%")
    print(f"Current phase: {details['current_phase']}")
    print(f"Output directory: {details['output_directory']}")
    print(f"Created files: {len(details['created_files'])}")
    
    if details['errors']:
        print("Errors:")
        for error in details['errors']:
            print(f"  - {error}")
```

### Cleanup

```python
# Clean up a specific project
if manager.cleanup_project(result.project_id):
    print("✅ Project cleaned up successfully")
else:
    print("❌ Failed to clean up project")

# Clean up all failed projects
projects = manager.list_projects()
for project in projects:
    if project['status'] == 'failed':
        manager.cleanup_project(project['project_id'])
        print(f"Cleaned up failed project: {project['name']}")
```

## Configuration Files

### Using JSON Configuration

**File: `server-config.json`**
```json
{
    "name": "json-configured-server",
    "template": "python-fastmcp",
    "output_directory": "./servers",
    "custom_settings": {
        "server_name": "JSON Configured Server",
        "description": "Server created from JSON configuration"
    },
    "environment_variables": {
        "DEBUG": "true"
    },
    "additional_dependencies": [
        "requests>=2.28.0"
    ]
}
```

**Usage:**
```python
import json

# Load configuration from file
with open('server-config.json') as f:
    config = json.load(f)

# Create project from configuration
result = manager.create_project(
    name=config['name'],
    template=config['template'],
    config=config
)
```

### Using YAML Configuration

**File: `server-config.yaml`**
```yaml
name: yaml-configured-server
template: python-fastmcp
output_directory: ./servers

custom_settings:
  server_name: YAML Configured Server
  description: Server created from YAML configuration

environment_variables:
  DEBUG: "true"
  LOG_LEVEL: INFO

additional_dependencies:
  - requests>=2.28.0
  - pyyaml>=6.0.0
```

**Usage:**
```python
import yaml

# Load configuration from YAML file
with open('server-config.yaml') as f:
    config = yaml.safe_load(f)

# Create project from configuration
result = manager.create_project(
    name=config['name'],
    template=config['template'],
    config=config
)
```

## Troubleshooting

### Common Issues

1. **Import Error**
   ```
   ModuleNotFoundError: No module named 'mcp_server_builder'
   ```
   **Solution:** Ensure the package is installed: `pip install mcp-server-builder`

2. **Permission Denied**
   ```
   Permission denied: '/path/to/output'
   ```
   **Solution:** Use a different output directory or fix permissions:
   ```python
   config = {'output_directory': os.path.expanduser('~/mcp-servers')}
   ```

3. **Network Timeout**
   ```
   Connection timeout during file download
   ```
   **Solution:** Check internet connection or use local templates

4. **Template Not Found**
   ```
   Template 'my-template' not found
   ```
   **Solution:** List available templates and use correct ID:
   ```python
   templates = engine.list_templates()
   for t in templates:
       print(t.id)
   ```

### Getting Help

1. **Enable Debug Logging**
   ```python
   from mcp_server_builder.managers.progress_tracker import LogLevel
   
   manager = ProjectManagerImpl(
       log_level=LogLevel.DEBUG,
       log_file='debug.log'
   )
   ```

2. **Check System Requirements**
   ```python
   import sys, platform
   print(f"Python: {sys.version}")
   print(f"Platform: {platform.system()} {platform.release()}")
   ```

3. **Validate Configuration**
   ```python
   # Test configuration before creating project
   try:
       result = manager.create_project(name, template, config)
       if not result.success:
           print("Configuration issues:")
           for error in result.errors:
               print(f"  - {error}")
   except Exception as e:
       print(f"Error: {e}")
   ```

## Next Steps

Now that you've created your first MCP server, you can:

1. **Customize Your Server**: Add your own tools, resources, and prompts
2. **Explore Templates**: Try different templates for various use cases
3. **Learn Advanced Features**: Study the API reference and template development guide
4. **Deploy Your Server**: Set up your server in production environments
5. **Create Custom Templates**: Build your own templates for specific patterns

### Recommended Reading

- [API Reference](api-reference.md) - Complete API documentation
- [Template Development Guide](template-development-guide.md) - Create custom templates
- [Troubleshooting Guide](troubleshooting.md) - Solve common issues
- [FAQ](faq.md) - Frequently asked questions

### Example Projects

Check out the `examples/` directory for complete example projects:
- Simple tool server
- File processing server
- Web API integration server
- Database query server
- Multi-transport server

Congratulations! You're now ready to build powerful MCP servers with the MCP Server Builder. Happy coding! 🚀