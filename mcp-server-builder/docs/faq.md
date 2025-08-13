# Frequently Asked Questions (FAQ)

## General Questions

### What is the MCP Server Builder?

The MCP Server Builder is an automated tool that creates complete MCP (Model Context Protocol) server environments from scratch. It handles folder creation, file downloads, dependency management, and build execution to produce a functional MCP server ready for deployment.

### What programming languages are supported?

Currently supported languages include:
- **Python** (with FastMCP and low-level SDK)
- **TypeScript** (with official TypeScript SDK)
- **Go** (with Foxy Contexts library)
- **Rust** (production-ready implementations)
- **Java** (with Quarkus and declarative SDKs)

### What is the difference between templates?

Templates differ by language and framework:

- **python-fastmcp**: High-level Python framework with decorators for rapid development
- **python-low-level**: Direct MCP protocol implementation for maximum control
- **typescript-sdk**: Official TypeScript SDK with full MCP support
- **go-foxy-contexts**: Go implementation using the Foxy Contexts library
- **rust-production**: Production-ready Rust implementation
- **java-quarkus**: Java implementation using Quarkus framework

## Installation and Setup

### How do I install the MCP Server Builder?

```bash
# Install from PyPI
pip install mcp-server-builder

# Or install from source
git clone https://github.com/your-org/mcp-server-builder.git
cd mcp-server-builder
pip install -e .
```

### What are the system requirements?

**Minimum Requirements:**
- Python 3.8 or higher
- 1 GB available disk space
- Internet connection for template downloads

**Recommended:**
- Python 3.10 or higher
- 2 GB available disk space
- Fast internet connection
- Git installed for template management

### Do I need to install build tools separately?

It depends on the template you're using:

- **Python templates**: Require `pip` (usually included with Python)
- **TypeScript templates**: Require `node` and `npm`
- **Go templates**: Require `go` compiler
- **Rust templates**: Require `rustc` and `cargo`
- **Java templates**: Require JDK and Maven/Gradle

The builder will detect missing tools and provide installation instructions.

## Usage Questions

### How do I create my first MCP server?

```python
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

# Initialize the manager
manager = ProjectManagerImpl()

# Create a simple Python FastMCP server
result = manager.create_project(
    name="my-first-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'My First MCP Server',
            'description': 'A simple example server'
        }
    }
)

if result.success:
    print(f"Server created at: {result.project_path}")
else:
    print(f"Creation failed: {result.errors}")
```

### How do I list available templates?

```python
from mcp_server_builder.managers.template_engine import TemplateEngineImpl

engine = TemplateEngineImpl()
templates = engine.list_templates()

for template in templates:
    print(f"ID: {template.id}")
    print(f"Name: {template.name}")
    print(f"Language: {template.language.value}")
    print(f"Framework: {template.framework.value}")
    print(f"Description: {template.description}")
    print("---")
```

### Can I customize the generated server?

Yes! You can customize servers in several ways:

1. **Configuration parameters:**
```python
config = {
    'custom_settings': {
        'server_name': 'Custom Server Name',
        'description': 'Custom description',
        'transport_type': 'stdio',  # or 'http', 'sse'
        'enable_logging': True,
        'log_level': 'DEBUG'
    }
}
```

2. **Environment variables:**
```python
config = {
    'environment_variables': {
        'API_KEY': 'your-api-key',
        'DEBUG': 'true',
        'TIMEOUT': '30'
    }
}
```

3. **Additional dependencies:**
```python
config = {
    'additional_dependencies': [
        'requests>=2.28.0',
        'pydantic>=2.0.0',
        'python-dotenv'
    ]
}
```

### How do I monitor project creation progress?

```python
def progress_callback(project_id: str, percentage: float, phase: str):
    print(f"Progress: {percentage:.1f}% - {phase}")

def error_callback(project_id: str, error: str):
    print(f"Error: {error}")

manager = ProjectManagerImpl(
    progress_callback=progress_callback,
    error_callback=error_callback
)
```

### Can I create multiple servers at once?

Yes, but it's recommended to create them sequentially to avoid resource conflicts:

```python
servers = [
    ("weather-server", "python-fastmcp"),
    ("file-server", "typescript-sdk"),
    ("data-server", "python-low-level")
]

results = []
for name, template in servers:
    result = manager.create_project(name, template, {})
    results.append(result)
    
    # Optional: wait for completion before starting next
    while manager.get_project_status(result.project_id) not in [
        ProjectStatus.COMPLETED, ProjectStatus.FAILED
    ]:
        time.sleep(1)
```

## Template Questions

### How do I create a custom template?

Custom templates are defined using JSON configuration files:

```json
{
    "id": "my-custom-template",
    "name": "My Custom MCP Server",
    "description": "Custom server template",
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
        "server_name": {"type": "string", "required": true},
        "description": {"type": "string", "required": false}
    }
}
```

### Where are templates stored?

Templates are stored in the `src/templates/` directory:

```
src/templates/
├── python-fastmcp/
│   ├── template.json
│   └── files/
├── typescript-sdk/
│   ├── template.json
│   └── files/
└── custom-template/
    ├── template.json
    └── files/
```

### Can I use local files in templates?

Yes, you can reference local files instead of URLs:

```json
{
    "files": [
        {
            "path": "src/server.py",
            "url": "file://./templates/python-fastmcp/files/server.py",
            "executable": false
        }
    ]
}
```

### How do I update existing templates?

1. **Update template definition:**
   Edit the `template.json` file with new configuration

2. **Update template files:**
   Modify files in the template's `files/` directory

3. **Reload templates:**
   ```python
   engine = TemplateEngineImpl()
   engine.reload_templates()  # Refresh template cache
   ```

## Configuration Questions

### What configuration options are available?

Common configuration options include:

```python
config = {
    # Output settings
    'output_directory': '/path/to/output',
    
    # Server customization
    'custom_settings': {
        'server_name': 'My Server',
        'description': 'Server description',
        'transport_type': 'stdio',  # stdio, http, sse
        'enable_logging': True,
        'log_level': 'INFO',
        'port': 8080,  # for HTTP transport
        'host': '0.0.0.0'  # for HTTP transport
    },
    
    # Environment
    'environment_variables': {
        'DEBUG': 'false',
        'API_TIMEOUT': '30',
        'MAX_CONNECTIONS': '100'
    },
    
    # Dependencies
    'additional_dependencies': [
        'package-name>=1.0.0',
        'another-package'
    ]
}
```

### How do I configure different transport types?

**STDIO Transport (default):**
```python
config = {
    'custom_settings': {
        'transport_type': 'stdio'
    }
}
```

**HTTP Transport:**
```python
config = {
    'custom_settings': {
        'transport_type': 'http',
        'host': '0.0.0.0',
        'port': 8080
    }
}
```

**Server-Sent Events (SSE):**
```python
config = {
    'custom_settings': {
        'transport_type': 'sse',
        'host': '0.0.0.0',
        'port': 8080
    }
}
```

### Can I use configuration files instead of code?

Yes, you can use JSON or YAML configuration files:

**config.json:**
```json
{
    "name": "my-server",
    "template": "python-fastmcp",
    "output_directory": "./servers",
    "custom_settings": {
        "server_name": "My MCP Server",
        "transport_type": "stdio"
    },
    "additional_dependencies": [
        "requests>=2.28.0"
    ]
}
```

**Usage:**
```python
import json

with open('config.json') as f:
    config = json.load(f)

result = manager.create_project(
    name=config['name'],
    template=config['template'],
    config=config
)
```

## Troubleshooting Questions

### Why is my project creation failing?

Common causes and solutions:

1. **Template not found:**
   - Check available templates with `engine.list_templates()`
   - Verify template ID spelling

2. **Permission errors:**
   - Check output directory permissions
   - Use a different output directory
   - Run with appropriate privileges

3. **Network issues:**
   - Check internet connectivity
   - Configure proxy settings if needed
   - Use local templates

4. **Dependency conflicts:**
   - Review dependency versions
   - Use virtual environments
   - Specify compatible versions

### How do I debug build failures?

1. **Enable debug logging:**
```python
manager = ProjectManagerImpl(
    log_level=LogLevel.DEBUG,
    log_file='debug.log'
)
```

2. **Check build logs:**
```python
result = manager.create_project(name, template, config)
if not result.success:
    print("Build errors:")
    for error in result.errors:
        print(f"  - {error}")
```

3. **Manual build testing:**
```bash
cd /path/to/project
# Run build commands manually
pip install -e .
python -m pytest
```

### Why is server validation failing?

Common validation issues:

1. **Server won't start:**
   - Check for missing dependencies
   - Verify configuration files
   - Test with minimal configuration

2. **Protocol compliance issues:**
   - Update to latest MCP specification
   - Check required capabilities implementation
   - Verify message format compliance

3. **Functionality tests failing:**
   - Implement required MCP methods
   - Check tool/resource definitions
   - Verify response formats

### How do I clean up failed projects?

```python
# Clean up specific project
success = manager.cleanup_project(project_id)

# Clean up all failed projects
projects = manager.list_projects()
for project in projects:
    if project['status'] == 'failed':
        manager.cleanup_project(project['project_id'])
```

## Performance Questions

### How can I speed up project creation?

1. **Use local templates:**
   - Store frequently used templates locally
   - Avoid network downloads when possible

2. **Reduce logging:**
   ```python
   manager = ProjectManagerImpl(log_level=LogLevel.WARNING)
   ```

3. **Pre-install build tools:**
   - Install Node.js, Python, etc. beforehand
   - Use package manager caches

4. **Use faster storage:**
   - Use SSD instead of HDD
   - Avoid network-mounted directories

### Why is the builder using too much memory?

1. **Process projects sequentially:**
   - Don't create multiple projects simultaneously
   - Clean up completed projects promptly

2. **Monitor memory usage:**
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

3. **Use appropriate log levels:**
   - Avoid DEBUG level in production
   - Disable file logging if not needed

## Integration Questions

### Can I integrate this with CI/CD pipelines?

Yes! Example GitHub Actions workflow:

```yaml
name: Create MCP Server
on: [push]

jobs:
  create-server:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      
      - name: Install MCP Server Builder
        run: pip install mcp-server-builder
      
      - name: Create Server
        run: |
          python -c "
          from mcp_server_builder.managers.project_manager import ProjectManagerImpl
          manager = ProjectManagerImpl()
          result = manager.create_project('ci-server', 'python-fastmcp', {})
          print(f'Success: {result.success}')
          "
```

### How do I use this in a web application?

Example Flask integration:

```python
from flask import Flask, request, jsonify
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

app = Flask(__name__)
manager = ProjectManagerImpl()

@app.route('/create-server', methods=['POST'])
def create_server():
    data = request.json
    
    result = manager.create_project(
        name=data['name'],
        template=data['template'],
        config=data.get('config', {})
    )
    
    return jsonify({
        'success': result.success,
        'project_id': result.project_id,
        'project_path': result.project_path,
        'errors': result.errors
    })

@app.route('/project-status/<project_id>')
def project_status(project_id):
    status = manager.get_project_status(project_id)
    details = manager.get_project_details(project_id)
    
    return jsonify({
        'status': status.value,
        'details': details
    })
```

### Can I extend the builder with custom functionality?

Yes! You can extend the builder by:

1. **Creating custom managers:**
```python
from mcp_server_builder.managers.interfaces import ValidationEngine

class CustomValidationEngine(ValidationEngine):
    def validate_custom_requirements(self, project_path: str) -> bool:
        # Your custom validation logic
        return True
```

2. **Adding custom templates:**
   - Create template definitions in `src/templates/`
   - Register with the template engine

3. **Custom progress callbacks:**
```python
def custom_progress_handler(event):
    # Send to external monitoring system
    send_to_monitoring(event.project_id, event.percentage)

manager.add_progress_callback(custom_progress_handler)
```

## Support Questions

### Where can I get help?

1. **Documentation:**
   - API Reference: `docs/api-reference.md`
   - Troubleshooting Guide: `docs/troubleshooting.md`
   - This FAQ: `docs/faq.md`

2. **Issue Reporting:**
   - GitHub Issues: [repository-url]/issues
   - Include system information and error logs

3. **Community:**
   - Discord/Slack community channels
   - Stack Overflow with `mcp-server-builder` tag

### How do I report bugs?

When reporting bugs, please include:

1. **System Information:**
   ```python
   import platform, sys
   print(f"OS: {platform.system()} {platform.release()}")
   print(f"Python: {sys.version}")
   ```

2. **Error Details:**
   - Complete error messages
   - Stack traces
   - Debug logs

3. **Reproduction Steps:**
   - Exact code used
   - Configuration parameters
   - Expected vs actual behavior

### How do I contribute?

1. **Fork the repository**
2. **Create a feature branch**
3. **Make your changes**
4. **Add tests for new functionality**
5. **Submit a pull request**

See `CONTRIBUTING.md` for detailed guidelines.

### What's the project roadmap?

Planned features include:

- **Additional Language Support:** C#, PHP, Ruby
- **Cloud Integration:** AWS Lambda, Google Cloud Functions
- **GUI Interface:** Web-based project creation interface
- **Template Marketplace:** Community template sharing
- **Advanced Validation:** Performance testing, security scanning
- **IDE Integration:** VS Code extension, IntelliJ plugin

Check the GitHub project board for current development status.