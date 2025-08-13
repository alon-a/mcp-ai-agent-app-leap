# Template Development Guide

## Overview

This guide covers how to create custom MCP server templates for the MCP Server Builder. Templates define the structure, files, dependencies, and build process for generating MCP servers in different languages and frameworks.

## Template Structure

### Template Definition File

Templates are defined using JSON or YAML files that specify all the information needed to create an MCP server project. Here's the basic structure:

```json
{
    "id": "my-custom-template",
    "name": "My Custom MCP Server",
    "description": "A custom MCP server template with specific functionality",
    "language": "python",
    "framework": "fastmcp",
    "files": [
        {
            "path": "src/server.py",
            "url": "https://example.com/templates/server.py",
            "checksum": "sha256:abc123...",
            "executable": false
        }
    ],
    "dependencies": [
        "fastmcp>=0.1.0",
        "pydantic>=2.0.0"
    ],
    "build_commands": [
        "pip install -e .",
        "python -m pytest tests/"
    ],
    "configuration_schema": {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Name of the MCP server",
                "default": "My Custom Server"
            }
        },
        "required": ["server_name"]
    }
}
```

### Required Fields

#### Basic Information
- **`id`** (string): Unique identifier for the template (kebab-case recommended)
- **`name`** (string): Human-readable name for the template
- **`description`** (string): Detailed description of what the template creates
- **`language`** (string): Programming language (`python`, `typescript`, `go`, `rust`, `java`)
- **`framework`** (string): Framework type (`fastmcp`, `low-level`, `typescript-sdk`, etc.)

#### Files and Dependencies
- **`files`** (array): List of files to download and include in the project
- **`dependencies`** (array): List of package dependencies to install
- **`build_commands`** (array): Commands to execute during the build process

#### Configuration
- **`configuration_schema`** (object): JSON Schema defining customizable parameters

### File Specifications

Each file in the `files` array must specify:

```json
{
    "path": "relative/path/in/project.py",
    "url": "https://source.com/file.py",
    "checksum": "sha256:hash-value",
    "executable": false
}
```

**Fields:**
- **`path`**: Relative path where the file should be placed in the project
- **`url`**: Source URL for downloading the file (HTTP/HTTPS or `file://` for local files)
- **`checksum`**: Optional SHA256 checksum for integrity verification
- **`executable`**: Whether the file should be marked as executable (default: false)

## Creating Your First Template

### Step 1: Plan Your Template

Before creating a template, consider:

1. **Target Use Case**: What type of MCP server will this create?
2. **Language and Framework**: Which programming language and MCP framework?
3. **Required Files**: What files are needed for a working server?
4. **Dependencies**: What packages/libraries are required?
5. **Build Process**: How should the server be built and tested?
6. **Customization**: What should users be able to configure?

### Step 2: Create Template Files

Create the actual source files that will be included in generated projects:

**Example: `server.py`**
```python
#!/usr/bin/env python3
"""
{{server_name}} - {{description}}

A Model Context Protocol server built with FastMCP.
"""

import asyncio
from fastmcp import FastMCP

# Create MCP server instance
mcp = FastMCP("{{server_name}}")

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
        "server_name": "{{server_name}}",
        "version": "{{server_version}}",
        "transport": "{{transport}}"
    }

async def main():
    """Run the MCP server."""
    async with mcp.run_server() as server:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

**Example: `pyproject.toml`**
```toml
[build-system]
requires = ["setuptools>=61.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "{{server_name}}"
version = "{{server_version}}"
description = "{{description}}"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
    "fastmcp>=0.1.0",
    "pydantic>=2.0.0"
]

[project.scripts]
{{server_name}} = "{{server_name}}.server:main"
```

### Step 3: Create Template Definition

Create a JSON or YAML file defining your template:

**`my-custom-template.json`**
```json
{
    "id": "python-custom-fastmcp",
    "name": "Python Custom FastMCP Server",
    "description": "A customizable Python MCP server using FastMCP with example tools and resources",
    "language": "python",
    "framework": "fastmcp",
    "files": [
        {
            "path": "src/server.py",
            "url": "file://./templates/python-custom-fastmcp/server.py",
            "executable": false
        },
        {
            "path": "pyproject.toml",
            "url": "file://./templates/python-custom-fastmcp/pyproject.toml",
            "executable": false
        },
        {
            "path": "README.md",
            "url": "file://./templates/python-custom-fastmcp/README.md",
            "executable": false
        },
        {
            "path": "tests/test_server.py",
            "url": "file://./templates/python-custom-fastmcp/test_server.py",
            "executable": false
        }
    ],
    "dependencies": [
        "fastmcp>=0.1.0",
        "pydantic>=2.0.0",
        "pytest>=7.0.0"
    ],
    "build_commands": [
        "pip install -e .",
        "python -m pytest tests/ -v"
    ],
    "configuration_schema": {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Name of the MCP server",
                "default": "My Custom Server"
            },
            "server_version": {
                "type": "string",
                "description": "Version of the server",
                "default": "1.0.0"
            },
            "description": {
                "type": "string",
                "description": "Description of the server",
                "default": "A custom MCP server"
            },
            "transport": {
                "type": "string",
                "enum": ["stdio", "http", "sse"],
                "description": "Transport protocol to use",
                "default": "stdio"
            },
            "enable_logging": {
                "type": "boolean",
                "description": "Enable detailed logging",
                "default": true
            }
        },
        "required": ["server_name", "server_version"]
    }
}
```

### Step 4: Test Your Template

Create a test script to validate your template:

```python
#!/usr/bin/env python3
"""Test script for custom template."""

from mcp_server_builder.managers.template_engine import TemplateEngineImpl
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

def test_custom_template():
    """Test the custom template."""
    
    # Load template engine with custom template directory
    engine = TemplateEngineImpl(template_directory="./templates")
    
    # List available templates
    templates = engine.list_templates()
    print("Available templates:")
    for template in templates:
        print(f"  - {template.id}: {template.name}")
    
    # Get our custom template
    template = engine.get_template("python-custom-fastmcp")
    if not template:
        print("❌ Custom template not found!")
        return False
    
    print(f"✅ Found template: {template.name}")
    
    # Test template application
    config = {
        "server_name": "Test Server",
        "server_version": "0.1.0",
        "description": "A test server",
        "transport": "stdio"
    }
    
    result = engine.apply_template(template, config)
    if result.success:
        print("✅ Template application successful")
        print(f"Generated files: {result.generated_files}")
    else:
        print("❌ Template application failed:")
        for error in result.errors:
            print(f"  - {error}")
        return False
    
    # Test project creation
    manager = ProjectManagerImpl()
    project_result = manager.create_project(
        name="test-custom-server",
        template="python-custom-fastmcp",
        config={"custom_settings": config}
    )
    
    if project_result.success:
        print("✅ Project creation successful")
        print(f"Project path: {project_result.project_path}")
    else:
        print("❌ Project creation failed:")
        for error in project_result.errors:
            print(f"  - {error}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_custom_template()
    exit(0 if success else 1)
```

## Template Configuration Schema

The configuration schema defines what parameters users can customize when using your template. It uses JSON Schema format.

### Basic Schema Structure

```json
{
    "type": "object",
    "properties": {
        "parameter_name": {
            "type": "string|number|boolean|array|object",
            "description": "Human-readable description",
            "default": "default_value",
            "enum": ["option1", "option2"],
            "minimum": 1,
            "maximum": 100
        }
    },
    "required": ["required_parameter"]
}
```

### Common Parameter Types

#### String Parameters
```json
{
    "server_name": {
        "type": "string",
        "description": "Name of the MCP server",
        "default": "My Server",
        "minLength": 1,
        "maxLength": 50,
        "pattern": "^[a-zA-Z][a-zA-Z0-9-_]*$"
    }
}
```

#### Enum Parameters
```json
{
    "transport": {
        "type": "string",
        "enum": ["stdio", "http", "sse"],
        "description": "Transport protocol to use",
        "default": "stdio"
    }
}
```

#### Boolean Parameters
```json
{
    "enable_logging": {
        "type": "boolean",
        "description": "Enable detailed logging",
        "default": true
    }
}
```

#### Numeric Parameters
```json
{
    "port": {
        "type": "integer",
        "description": "Port number for HTTP transport",
        "default": 8080,
        "minimum": 1024,
        "maximum": 65535
    }
}
```

#### Array Parameters
```json
{
    "additional_tools": {
        "type": "array",
        "items": {"type": "string"},
        "description": "List of additional tools to include",
        "default": []
    }
}
```

## Parameter Substitution

Templates support parameter substitution using `{{parameter_name}}` syntax in file contents and paths.

### In File Contents

```python
# server.py template
SERVER_NAME = "{{server_name}}"
SERVER_VERSION = "{{server_version}}"
DEBUG_MODE = {{enable_logging}}

def get_server_info():
    return {
        "name": "{{server_name}}",
        "version": "{{server_version}}",
        "transport": "{{transport}}"
    }
```

### In File Paths

```json
{
    "files": [
        {
            "path": "src/{{server_name}}/main.py",
            "url": "file://./templates/main.py"
        }
    ]
}
```

### Advanced Substitution

For more complex substitutions, you can use conditional logic:

```python
# In template file
{% if transport == "http" %}
from fastapi import FastAPI
app = FastAPI()
{% elif transport == "stdio" %}
import sys
import json
{% endif %}
```

## Language-Specific Templates

### Python Templates

**Key considerations:**
- Use `pyproject.toml` for modern Python packaging
- Include proper dependency specifications with version constraints
- Add pytest configuration for testing
- Consider virtual environment setup

**Example dependencies:**
```json
{
    "dependencies": [
        "fastmcp>=0.1.0",
        "pydantic>=2.0.0",
        "python-dotenv>=1.0.0"
    ]
}
```

**Example build commands:**
```json
{
    "build_commands": [
        "python -m pip install --upgrade pip",
        "pip install -e .",
        "python -m pytest tests/ -v"
    ]
}
```

### TypeScript Templates

**Key considerations:**
- Include `package.json` with proper scripts
- Add `tsconfig.json` for TypeScript configuration
- Consider both CommonJS and ESM module formats
- Include type definitions

**Example dependencies:**
```json
{
    "dependencies": [
        "@modelcontextprotocol/sdk",
        "typescript",
        "@types/node"
    ]
}
```

**Example build commands:**
```json
{
    "build_commands": [
        "npm install",
        "npm run build",
        "npm test"
    ]
}
```

### Go Templates

**Key considerations:**
- Use `go.mod` for dependency management
- Follow Go project structure conventions
- Include proper module naming

**Example dependencies:**
```json
{
    "dependencies": [
        "github.com/foxycontexts/mcp-go@latest"
    ]
}
```

**Example build commands:**
```json
{
    "build_commands": [
        "go mod tidy",
        "go build -o server ./cmd/server",
        "go test ./..."
    ]
}
```

## Best Practices

### Template Design

1. **Keep it Simple**: Start with minimal functionality and add complexity gradually
2. **Follow Conventions**: Use standard project structures for each language
3. **Include Documentation**: Always include README.md with usage instructions
4. **Add Tests**: Include basic test files and test commands
5. **Version Dependencies**: Specify version constraints for all dependencies

### File Organization

```
templates/
├── my-template/
│   ├── template.json          # Template definition
│   ├── files/                 # Template files
│   │   ├── src/
│   │   │   └── server.py
│   │   ├── tests/
│   │   │   └── test_server.py
│   │   ├── pyproject.toml
│   │   └── README.md
│   └── examples/              # Usage examples
│       └── config.json
```

### Configuration Schema Design

1. **Provide Defaults**: Always include sensible default values
2. **Add Descriptions**: Write clear descriptions for all parameters
3. **Use Validation**: Add appropriate constraints (min/max, patterns, enums)
4. **Group Related Parameters**: Use nested objects for related settings

### Error Handling

1. **Validate Early**: Check template validity during loading
2. **Provide Clear Messages**: Include helpful error messages
3. **Handle Missing Files**: Gracefully handle missing template files
4. **Test Edge Cases**: Test with invalid configurations

## Advanced Features

### Conditional File Inclusion

You can conditionally include files based on configuration:

```json
{
    "files": [
        {
            "path": "src/http_server.py",
            "url": "file://./templates/http_server.py",
            "condition": "{{transport}} == 'http'"
        },
        {
            "path": "src/stdio_server.py",
            "url": "file://./templates/stdio_server.py",
            "condition": "{{transport}} == 'stdio'"
        }
    ]
}
```

### Dynamic Dependencies

Dependencies can be conditional based on configuration:

```json
{
    "dependencies": [
        "fastmcp>=0.1.0",
        {
            "package": "fastapi>=0.100.0",
            "condition": "{{transport}} == 'http'"
        },
        {
            "package": "uvicorn>=0.20.0",
            "condition": "{{transport}} == 'http'"
        }
    ]
}
```

### Multi-Language Templates

For templates that generate multiple language bindings:

```json
{
    "id": "multi-lang-server",
    "name": "Multi-Language MCP Server",
    "language": "multi",
    "framework": "custom",
    "files": [
        {
            "path": "python/server.py",
            "url": "file://./templates/python_server.py",
            "condition": "{{include_python}}"
        },
        {
            "path": "typescript/server.ts",
            "url": "file://./templates/typescript_server.ts",
            "condition": "{{include_typescript}}"
        }
    ],
    "configuration_schema": {
        "properties": {
            "include_python": {
                "type": "boolean",
                "default": true
            },
            "include_typescript": {
                "type": "boolean",
                "default": false
            }
        }
    }
}
```

## Testing Templates

### Unit Testing

Create unit tests for your template:

```python
import unittest
from mcp_server_builder.managers.template_engine import TemplateEngineImpl

class TestCustomTemplate(unittest.TestCase):
    
    def setUp(self):
        self.engine = TemplateEngineImpl(template_directory="./templates")
    
    def test_template_loads(self):
        """Test that the template loads successfully."""
        template = self.engine.get_template("my-custom-template")
        self.assertIsNotNone(template)
        self.assertEqual(template.id, "my-custom-template")
    
    def test_template_application(self):
        """Test template parameter substitution."""
        template = self.engine.get_template("my-custom-template")
        config = {"server_name": "Test Server"}
        
        result = self.engine.apply_template(template, config)
        self.assertTrue(result.success)
        self.assertIn("Test Server", str(result.applied_config))
    
    def test_invalid_config(self):
        """Test handling of invalid configuration."""
        template = self.engine.get_template("my-custom-template")
        config = {}  # Missing required parameters
        
        result = self.engine.apply_template(template, config)
        self.assertFalse(result.success)
        self.assertTrue(len(result.errors) > 0)

if __name__ == "__main__":
    unittest.main()
```

### Integration Testing

Test the complete project creation process:

```python
import tempfile
import shutil
from pathlib import Path
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

def test_end_to_end_creation():
    """Test complete project creation with custom template."""
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = ProjectManagerImpl()
        
        result = manager.create_project(
            name="test-project",
            template="my-custom-template",
            config={
                "output_directory": temp_dir,
                "custom_settings": {
                    "server_name": "Integration Test Server",
                    "server_version": "0.1.0"
                }
            }
        )
        
        assert result.success, f"Project creation failed: {result.errors}"
        
        # Verify project structure
        project_path = Path(result.project_path)
        assert project_path.exists()
        assert (project_path / "src" / "server.py").exists()
        assert (project_path / "pyproject.toml").exists()
        
        # Verify parameter substitution
        server_file = project_path / "src" / "server.py"
        content = server_file.read_text()
        assert "Integration Test Server" in content
```

## Publishing Templates

### Template Repository Structure

Organize templates in a repository:

```
mcp-templates/
├── README.md
├── templates/
│   ├── python-fastmcp/
│   │   ├── template.json
│   │   └── files/
│   ├── typescript-sdk/
│   │   ├── template.yaml
│   │   └── files/
│   └── go-foxy-contexts/
│       ├── template.json
│       └── files/
├── examples/
│   └── usage-examples.py
└── tests/
    └── test_all_templates.py
```

### Template Registry

Consider creating a template registry for sharing:

```json
{
    "registry": {
        "name": "Community MCP Templates",
        "version": "1.0.0",
        "templates": [
            {
                "id": "python-fastmcp-advanced",
                "name": "Advanced Python FastMCP Server",
                "version": "1.2.0",
                "author": "Your Name",
                "url": "https://github.com/user/templates/python-fastmcp-advanced",
                "description": "Advanced Python MCP server with authentication and caching",
                "tags": ["python", "fastmcp", "advanced", "auth"]
            }
        ]
    }
}
```

## Troubleshooting

### Common Issues

1. **Template Not Loading**
   - Check JSON/YAML syntax
   - Verify all required fields are present
   - Ensure file paths are correct

2. **Parameter Substitution Failing**
   - Check parameter names match schema
   - Verify template syntax `{{parameter}}`
   - Ensure required parameters are provided

3. **Build Failures**
   - Test build commands manually
   - Check dependency specifications
   - Verify file permissions

4. **Validation Errors**
   - Review configuration schema
   - Check parameter types and constraints
   - Test with minimal configuration

### Debugging Tips

1. **Enable Debug Logging**
   ```python
   from mcp_server_builder.managers.progress_tracker import LogLevel
   
   manager = ProjectManagerImpl(log_level=LogLevel.DEBUG)
   ```

2. **Test Template Loading**
   ```python
   from mcp_server_builder.models.template_loader import TemplateLoader
   
   loader = TemplateLoader()
   try:
       template = loader.load_from_file("my-template.json")
       print("✅ Template loaded successfully")
   except Exception as e:
       print(f"❌ Template loading failed: {e}")
   ```

3. **Validate Configuration Schema**
   ```python
   import jsonschema
   
   try:
       jsonschema.validate(config, template.configuration_schema)
       print("✅ Configuration valid")
   except jsonschema.ValidationError as e:
       print(f"❌ Configuration invalid: {e.message}")
   ```

## Examples

### Complete Python FastMCP Template

See the `examples/` directory for complete template examples including:

- **python-fastmcp-complete**: Full-featured Python FastMCP server
- **typescript-sdk-basic**: Basic TypeScript MCP server
- **go-minimal**: Minimal Go MCP server
- **multi-tool-server**: Server with multiple tools and resources

Each example includes:
- Complete template definition
- All template files
- Configuration examples
- Test scripts
- Documentation

This guide should help you create robust, reusable MCP server templates that make it easy for developers to bootstrap new MCP servers with your preferred patterns and configurations.