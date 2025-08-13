# Template Examples and Customizations

This document provides practical examples of MCP server templates and common customization patterns.

## Basic Templates

### 1. Simple Python FastMCP Template

**File: `templates/python-simple/template.json`**
```json
{
    "id": "python-simple",
    "name": "Simple Python FastMCP Server",
    "description": "A minimal Python MCP server using FastMCP framework",
    "language": "python",
    "framework": "fastmcp",
    "files": [
        {
            "path": "main.py",
            "url": "file://./templates/python-simple/files/main.py",
            "executable": true
        },
        {
            "path": "pyproject.toml",
            "url": "file://./templates/python-simple/files/pyproject.toml",
            "executable": false
        }
    ],
    "dependencies": [
        "fastmcp>=0.1.0"
    ],
    "build_commands": [
        "pip install -e ."
    ],
    "configuration_schema": {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Name of the MCP server",
                "default": "Simple Server"
            }
        },
        "required": ["server_name"]
    }
}
```

**File: `templates/python-simple/files/main.py`**
```python
#!/usr/bin/env python3
"""{{server_name}} - A simple MCP server."""

import asyncio
from fastmcp import FastMCP

mcp = FastMCP("{{server_name}}")

@mcp.tool()
def echo(message: str) -> str:
    """Echo a message back."""
    return f"Echo: {message}"

async def main():
    async with mcp.run_server() as server:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

### 2. TypeScript Basic Template

**File: `templates/typescript-basic/template.json`**
```json
{
    "id": "typescript-basic",
    "name": "Basic TypeScript MCP Server",
    "description": "A basic TypeScript MCP server using the official SDK",
    "language": "typescript",
    "framework": "typescript-sdk",
    "files": [
        {
            "path": "src/index.ts",
            "url": "file://./templates/typescript-basic/files/index.ts",
            "executable": false
        },
        {
            "path": "package.json",
            "url": "file://./templates/typescript-basic/files/package.json",
            "executable": false
        },
        {
            "path": "tsconfig.json",
            "url": "file://./templates/typescript-basic/files/tsconfig.json",
            "executable": false
        }
    ],
    "dependencies": [
        "@modelcontextprotocol/sdk",
        "typescript",
        "@types/node"
    ],
    "build_commands": [
        "npm install",
        "npm run build"
    ],
    "configuration_schema": {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Name of the MCP server",
                "default": "TypeScript Server"
            },
            "port": {
                "type": "integer",
                "description": "Port for HTTP transport",
                "default": 3000,
                "minimum": 1024,
                "maximum": 65535
            }
        },
        "required": ["server_name"]
    }
}
```

## Advanced Templates

### 3. Multi-Tool Python Server

**File: `templates/python-multi-tool/template.json`**
```json
{
    "id": "python-multi-tool",
    "name": "Multi-Tool Python MCP Server",
    "description": "Python MCP server with multiple tools, resources, and prompts",
    "language": "python",
    "framework": "fastmcp",
    "files": [
        {
            "path": "src/server.py",
            "url": "file://./templates/python-multi-tool/files/server.py",
            "executable": true
        },
        {
            "path": "src/tools/__init__.py",
            "url": "file://./templates/python-multi-tool/files/tools/__init__.py",
            "executable": false
        },
        {
            "path": "src/tools/file_tools.py",
            "url": "file://./templates/python-multi-tool/files/tools/file_tools.py",
            "executable": false
        },
        {
            "path": "src/tools/web_tools.py",
            "url": "file://./templates/python-multi-tool/files/tools/web_tools.py",
            "executable": false
        },
        {
            "path": "src/resources.py",
            "url": "file://./templates/python-multi-tool/files/resources.py",
            "executable": false
        },
        {
            "path": "pyproject.toml",
            "url": "file://./templates/python-multi-tool/files/pyproject.toml",
            "executable": false
        },
        {
            "path": "config.yaml",
            "url": "file://./templates/python-multi-tool/files/config.yaml",
            "executable": false
        }
    ],
    "dependencies": [
        "fastmcp>=0.1.0",
        "pydantic>=2.0.0",
        "requests>=2.28.0",
        "pyyaml>=6.0.0",
        "python-dotenv>=1.0.0"
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
                "default": "Multi-Tool Server"
            },
            "enable_file_tools": {
                "type": "boolean",
                "description": "Enable file manipulation tools",
                "default": true
            },
            "enable_web_tools": {
                "type": "boolean",
                "description": "Enable web scraping tools",
                "default": true
            },
            "max_file_size": {
                "type": "integer",
                "description": "Maximum file size in MB",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            },
            "allowed_domains": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Allowed domains for web tools",
                "default": ["example.com"]
            }
        },
        "required": ["server_name"]
    }
}
```

### 4. Database-Connected Server

**File: `templates/python-database/template.json`**
```json
{
    "id": "python-database",
    "name": "Database-Connected Python MCP Server",
    "description": "Python MCP server with database connectivity and ORM",
    "language": "python",
    "framework": "fastmcp",
    "files": [
        {
            "path": "src/server.py",
            "url": "file://./templates/python-database/files/server.py",
            "executable": true
        },
        {
            "path": "src/models.py",
            "url": "file://./templates/python-database/files/models.py",
            "executable": false
        },
        {
            "path": "src/database.py",
            "url": "file://./templates/python-database/files/database.py",
            "executable": false
        },
        {
            "path": "migrations/001_initial.sql",
            "url": "file://./templates/python-database/files/migrations/001_initial.sql",
            "executable": false
        },
        {
            "path": "pyproject.toml",
            "url": "file://./templates/python-database/files/pyproject.toml",
            "executable": false
        },
        {
            "path": ".env.example",
            "url": "file://./templates/python-database/files/.env.example",
            "executable": false
        }
    ],
    "dependencies": [
        "fastmcp>=0.1.0",
        "sqlalchemy>=2.0.0",
        "alembic>=1.12.0",
        "psycopg2-binary>=2.9.0",
        "python-dotenv>=1.0.0"
    ],
    "build_commands": [
        "pip install -e .",
        "alembic upgrade head"
    ],
    "configuration_schema": {
        "type": "object",
        "properties": {
            "server_name": {
                "type": "string",
                "description": "Name of the MCP server",
                "default": "Database Server"
            },
            "database_type": {
                "type": "string",
                "enum": ["postgresql", "mysql", "sqlite"],
                "description": "Type of database to use",
                "default": "postgresql"
            },
            "database_url": {
                "type": "string",
                "description": "Database connection URL",
                "default": "postgresql://user:pass@localhost/dbname"
            },
            "enable_migrations": {
                "type": "boolean",
                "description": "Enable database migrations",
                "default": true
            }
        },
        "required": ["server_name", "database_url"]
    }
}
```

## Customization Examples

### 1. Transport-Specific Configuration

```json
{
    "configuration_schema": {
        "type": "object",
        "properties": {
            "transport": {
                "type": "string",
                "enum": ["stdio", "http", "sse"],
                "description": "Transport protocol",
                "default": "stdio"
            },
            "http_config": {
                "type": "object",
                "properties": {
                    "host": {
                        "type": "string",
                        "default": "0.0.0.0"
                    },
                    "port": {
                        "type": "integer",
                        "default": 8080,
                        "minimum": 1024,
                        "maximum": 65535
                    },
                    "cors_origins": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["*"]
                    }
                },
                "description": "HTTP transport configuration"
            }
        },
        "required": ["transport"]
    }
}
```

### 2. Environment-Specific Dependencies

```json
{
    "dependencies": [
        "fastmcp>=0.1.0",
        {
            "package": "uvicorn>=0.20.0",
            "condition": "{{transport}} == 'http'"
        },
        {
            "package": "fastapi>=0.100.0",
            "condition": "{{transport}} == 'http'"
        },
        {
            "package": "python-multipart>=0.0.6",
            "condition": "{{transport}} == 'http'"
        }
    ]
}
```

### 3. Conditional File Inclusion

```json
{
    "files": [
        {
            "path": "src/server.py",
            "url": "file://./templates/base/server.py"
        },
        {
            "path": "src/http_transport.py",
            "url": "file://./templates/transports/http.py",
            "condition": "{{transport}} == 'http'"
        },
        {
            "path": "src/stdio_transport.py",
            "url": "file://./templates/transports/stdio.py",
            "condition": "{{transport}} == 'stdio'"
        },
        {
            "path": "src/sse_transport.py",
            "url": "file://./templates/transports/sse.py",
            "condition": "{{transport}} == 'sse'"
        }
    ]
}
```

### 4. Feature Flags

```json
{
    "configuration_schema": {
        "type": "object",
        "properties": {
            "features": {
                "type": "object",
                "properties": {
                    "authentication": {
                        "type": "boolean",
                        "description": "Enable authentication",
                        "default": false
                    },
                    "rate_limiting": {
                        "type": "boolean",
                        "description": "Enable rate limiting",
                        "default": false
                    },
                    "caching": {
                        "type": "boolean",
                        "description": "Enable response caching",
                        "default": false
                    },
                    "logging": {
                        "type": "object",
                        "properties": {
                            "level": {
                                "type": "string",
                                "enum": ["DEBUG", "INFO", "WARNING", "ERROR"],
                                "default": "INFO"
                            },
                            "format": {
                                "type": "string",
                                "enum": ["json", "text"],
                                "default": "text"
                            }
                        }
                    }
                }
            }
        }
    }
}
```

## Usage Examples

### 1. Creating a Simple Server

```python
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

manager = ProjectManagerImpl()

result = manager.create_project(
    name="my-simple-server",
    template="python-simple",
    config={
        'custom_settings': {
            'server_name': 'My Simple MCP Server'
        }
    }
)

if result.success:
    print(f"Server created at: {result.project_path}")
```

### 2. Creating a Multi-Tool Server

```python
result = manager.create_project(
    name="my-multi-tool-server",
    template="python-multi-tool",
    config={
        'custom_settings': {
            'server_name': 'Advanced Tool Server',
            'enable_file_tools': True,
            'enable_web_tools': True,
            'max_file_size': 50,
            'allowed_domains': ['github.com', 'stackoverflow.com']
        },
        'additional_dependencies': [
            'beautifulsoup4>=4.12.0',
            'lxml>=4.9.0'
        ]
    }
)
```

### 3. Creating a Database Server

```python
result = manager.create_project(
    name="my-database-server",
    template="python-database",
    config={
        'custom_settings': {
            'server_name': 'Data Management Server',
            'database_type': 'postgresql',
            'database_url': 'postgresql://user:pass@localhost/mydb',
            'enable_migrations': True
        },
        'environment_variables': {
            'DATABASE_URL': 'postgresql://user:pass@localhost/mydb',
            'DEBUG': 'false'
        }
    }
)
```

### 4. Creating a TypeScript Server

```python
result = manager.create_project(
    name="my-typescript-server",
    template="typescript-basic",
    config={
        'custom_settings': {
            'server_name': 'TypeScript MCP Server',
            'port': 3000
        }
    }
)
```

## Configuration File Examples

### 1. JSON Configuration

**File: `server-config.json`**
```json
{
    "name": "weather-server",
    "template": "python-multi-tool",
    "output_directory": "./servers",
    "custom_settings": {
        "server_name": "Weather Information Server",
        "enable_file_tools": false,
        "enable_web_tools": true,
        "allowed_domains": [
            "api.openweathermap.org",
            "weather.gov"
        ]
    },
    "environment_variables": {
        "WEATHER_API_KEY": "your-api-key-here",
        "DEBUG": "false"
    },
    "additional_dependencies": [
        "httpx>=0.24.0",
        "pydantic-settings>=2.0.0"
    ]
}
```

**Usage:**
```python
import json
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

with open('server-config.json') as f:
    config = json.load(f)

manager = ProjectManagerImpl()
result = manager.create_project(
    name=config['name'],
    template=config['template'],
    config=config
)
```

### 2. YAML Configuration

**File: `server-config.yaml`**
```yaml
name: file-manager-server
template: python-multi-tool
output_directory: ./servers

custom_settings:
  server_name: File Management Server
  enable_file_tools: true
  enable_web_tools: false
  max_file_size: 100

environment_variables:
  MAX_CONCURRENT_OPERATIONS: "10"
  TEMP_DIR: "/tmp/mcp-server"

additional_dependencies:
  - "watchdog>=3.0.0"
  - "pathlib2>=2.3.0"
```

### 3. Development vs Production Configs

**File: `dev-config.json`**
```json
{
    "name": "dev-server",
    "template": "python-database",
    "custom_settings": {
        "server_name": "Development Server",
        "database_type": "sqlite",
        "database_url": "sqlite:///dev.db"
    },
    "environment_variables": {
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG"
    }
}
```

**File: `prod-config.json`**
```json
{
    "name": "prod-server",
    "template": "python-database",
    "custom_settings": {
        "server_name": "Production Server",
        "database_type": "postgresql",
        "database_url": "postgresql://user:pass@prod-db:5432/app"
    },
    "environment_variables": {
        "DEBUG": "false",
        "LOG_LEVEL": "WARNING"
    }
}
```

## Best Practices for Template Usage

### 1. Start Simple

Begin with basic templates and add complexity gradually:

```python
# Start with simple template
result = manager.create_project(
    name="prototype-server",
    template="python-simple",
    config={'custom_settings': {'server_name': 'Prototype'}}
)

# Later upgrade to multi-tool template
result = manager.create_project(
    name="production-server",
    template="python-multi-tool",
    config={
        'custom_settings': {
            'server_name': 'Production Server',
            'enable_file_tools': True,
            'enable_web_tools': True
        }
    }
)
```

### 2. Use Environment Variables

Keep sensitive data in environment variables:

```python
import os

config = {
    'custom_settings': {
        'server_name': 'Secure Server',
        'database_url': 'postgresql://user:pass@localhost/db'
    },
    'environment_variables': {
        'DATABASE_PASSWORD': os.getenv('DB_PASSWORD'),
        'API_KEY': os.getenv('API_KEY'),
        'SECRET_KEY': os.getenv('SECRET_KEY')
    }
}
```

### 3. Version Your Dependencies

Always specify version constraints:

```python
config = {
    'additional_dependencies': [
        'requests>=2.28.0,<3.0.0',
        'pydantic>=2.0.0,<3.0.0',
        'fastapi>=0.100.0,<1.0.0'
    ]
}
```

### 4. Test Your Configuration

Test configurations before deployment:

```python
def test_server_config(config):
    """Test server configuration."""
    manager = ProjectManagerImpl()
    
    # Create in temporary directory
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        config['output_directory'] = temp_dir
        
        result = manager.create_project(
            name="test-server",
            template=config['template'],
            config=config
        )
        
        if result.success:
            print("✅ Configuration valid")
            return True
        else:
            print("❌ Configuration invalid:")
            for error in result.errors:
                print(f"  - {error}")
            return False

# Test before using
if test_server_config(my_config):
    # Proceed with actual creation
    pass
```

These examples demonstrate the flexibility and power of the MCP Server Builder template system. You can create templates for any MCP server pattern and customize them extensively to meet your specific needs.