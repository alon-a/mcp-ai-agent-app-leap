🚀 Using the MCP Server Builder
Step 1: Installation and Setup
First, you need to install the MCP Server Builder:

# Option 1: Install from PyPI (when published)
pip install mcp-server-builder

# Option 2: Install from source
git clone https://github.com/alon-a/mcp-ai-agent-app-kiro-build.git
cd mcp-ai-agent-app-kiro-build/mcp-server-builder
pip install -e .
Step 2: Basic Usage Through Python API
The MCP Server Builder provides a Python API that you can use programmatically:

from mcp_server_builder.managers.project_manager import ProjectManagerImpl

# Initialize the project manager
manager = ProjectManagerImpl()

# Create your MCP server
result = manager.create_project(
    name="my-file-server",
    template="typescript-sdk",  # This generates TypeScript code like your example
    config={
        'output_directory': './my-servers',
        'custom_settings': {
            'server_name': 'File Management Server',
            'description': 'MCP server for file operations',
            'base_directory': '/path/to/your/directory',
            'transport': 'stdio'
        },
        'environment_variables': {
            'BASE_DIRECTORY': '/path/to/your/directory',
            'DEBUG': 'true'
        }
    }
)

if result.success:
    print(f"✅ Server created at: {result.project_path}")
    print(f"📁 Files created: {len(result.created_files)}")
else:
    print("❌ Creation failed:")
    for error in result.errors:
        print(f"  - {error}")
Step 3: Available Templates
Check what templates are available:

from mcp_server_builder.managers.template_engine import TemplateEngineImpl

engine = TemplateEngineImpl()
templates = engine.list_templates()

print("Available MCP Server Templates:")
for template in templates:
    print(f"📦 {template.id}")
    print(f"   Name: {template.name}")
    print(f"   Language: {template.language.value}")
    print(f"   Framework: {template.framework.value}")
    print(f"   Description: {template.description}")
    print()
Step 4: Creating Different Server Types
File Server (TypeScript)
# This creates the same TypeScript file server you showed
result = manager.create_project(
    name="typescript-file-server",
    template="typescript-sdk",
    config={
        'custom_settings': {
            'server_name': 'File Operations Server',
            'server_type': 'file_system',
            'base_directory': '/safe/directory/path'
        }
    }
)
Python FastMCP Server
result = manager.create_project(
    name="python-file-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'Python File Server',
            'description': 'FastMCP-based file operations'
        },
        'additional_dependencies': [
            'pathlib>=1.0.0',
            'python-magic>=0.4.0'
        ]
    }
)
Database Server
result = manager.create_project(
    name="database-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'Database Query Server',
            'server_type': 'database'
        },
        'environment_variables': {
            'DATABASE_URL': 'postgresql://user:pass@localhost/db'
        },
        'additional_dependencies': [
            'sqlalchemy>=2.0.0',
            'psycopg2-binary>=2.9.0'
        ]
    }
)
Step 5: Progress Monitoring
Monitor the creation process in real-time:

def progress_callback(project_id: str, percentage: float, phase: str):
    print(f"🔄 [{project_id[:8]}] {phase}: {percentage:.1f}%")

def error_callback(project_id: str, error: str):
    print(f"❌ [{project_id[:8]}] ERROR: {error}")

# Create manager with callbacks
manager = ProjectManagerImpl(
    progress_callback=progress_callback,
    error_callback=error_callback
)

# Now create your project with live updates
result = manager.create_project(name, template, config)
Step 6: Validation and Testing
Validate your created server:

from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = result.project_path

# Basic validation
print("🔍 Validating server...")
startup_ok = validator.validate_server_startup(project_path)
protocol_ok = validator.validate_mcp_protocol(project_path)

print(f"Server startup: {'✅' if startup_ok else '❌'}")
print(f"Protocol compliance: {'✅' if protocol_ok else '❌'}")

# Comprehensive testing
test_results = validator.run_comprehensive_tests(project_path)
print(f"Overall test success: {test_results.get('overall_success', False)}")
Step 7: Using Configuration Files
You can also use JSON/YAML configuration files:

config.json:

{
    "name": "my-awesome-server",
    "template": "typescript-sdk",
    "output_directory": "./servers",
    "custom_settings": {
        "server_name": "Awesome MCP Server",
        "description": "A comprehensive MCP server",
        "transport": "http",
        "port": 3000
    },
    "environment_variables": {
        "NODE_ENV": "development",
        "DEBUG": "true"
    },
    "additional_dependencies": [
        "express",
        "cors"
    ]
}
Usage:

import json

# Load configuration
with open('config.json') as f:
    config = json.load(f)

# Create project from config
result = manager.create_project(
    name=config['name'],
    template=config['template'],
    config=config
)
Step 8: Command Line Interface (CLI)
The MCP Server Builder also provides a CLI interface:

# Create a server using CLI
python -m mcp_server_builder create \
    --name "my-server" \
    --template "typescript-sdk" \
    --config config.json

# List available templates
python -m mcp_server_builder list-templates

# Validate a server
python -m mcp_server_builder validate ./my-server

# Run comprehensive tests
python -m mcp_server_builder test ./my-server
Step 9: Integration with the MCP Assistant App
If you're using this within the MCP Assistant App context, you could create a bridge:

def create_mcp_server_via_builder(server_type: str, project_name: str, config: dict):
    """Bridge function to use MCP Server Builder from the App"""
    
    # Map app server types to builder templates
    template_mapping = {
        'file_system': 'typescript-sdk',
        'database': 'python-fastmcp',
        'api_integration': 'typescript-sdk',
        'git_repository': 'python-fastmcp'
    }
    
    template = template_mapping.get(server_type, 'typescript-sdk')
    
    manager = ProjectManagerImpl()
    result = manager.create_project(
        name=project_name,
        template=template,
        config={
            'custom_settings': {
                'server_type': server_type,
                **config
            }
        }
    )
    
    return {
        'success': result.success,
        'project_path': result.project_path,
        'files': result.created_files,
        'errors': result.errors
    }

# Usage from the App
response = create_mcp_server_via_builder(
    server_type='file_system',
    project_name='my-file-server',
    config={
        'server_name': 'File Operations Server',
        'base_directory': '/safe/path'
    }
)
🎯 Key Benefits of Using the MCP Server Builder
Complete Project Setup: Not just code, but entire project structure with configs, tests, docs
Multi-Language Support: Generate servers in Python, TypeScript, Go, Rust, or Java
Production Ready: Includes Docker, Kubernetes, monitoring, and security configurations
Validation Built-in: Automatic MCP protocol compliance testing
Template System: Easily customizable and extensible templates
Progress Tracking: Real-time feedback on project creation
Error Recovery: Automatic cleanup and recovery mechanisms
The MCP Server Builder essentially takes the manual TypeScript code generation approach and automates it into a complete, production-ready development workflow!