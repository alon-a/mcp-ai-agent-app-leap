# MCP Server Builder API Reference

## Overview

The MCP Server Builder provides a comprehensive API for creating, managing, and validating MCP (Model Context Protocol) servers. This document covers all public interfaces, classes, and usage patterns.

## Core Interfaces

### ProjectManager

The main interface for orchestrating MCP server project creation and lifecycle management.

```python
from mcp_server_builder.managers.interfaces import ProjectManager
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

# Initialize with optional callbacks
manager = ProjectManagerImpl(
    progress_callback=lambda project_id, percentage, phase: print(f"Progress: {percentage}%"),
    error_callback=lambda project_id, error: print(f"Error: {error}"),
    log_level=LogLevel.INFO
)
```

#### Methods

##### `create_project(name: str, template: str, config: Dict[str, Any]) -> ProjectResult`

Creates a new MCP server project with full orchestration.

**Parameters:**
- `name`: Project name (will be used as directory name)
- `template`: Template identifier (e.g., "python-fastmcp", "typescript-sdk")
- `config`: Project configuration options

**Configuration Options:**
```python
config = {
    'output_directory': '/path/to/output',  # Default: current directory
    'custom_settings': {
        'server_name': 'My MCP Server',
        'description': 'Custom server description',
        'transport_type': 'stdio'
    },
    'environment_variables': {
        'API_KEY': 'your-api-key'
    },
    'additional_dependencies': ['requests', 'pydantic']
}
```

**Returns:** `ProjectResult` with creation status and details

**Example:**
```python
result = manager.create_project(
    name="my-mcp-server",
    template="python-fastmcp",
    config={
        'output_directory': './projects',
        'custom_settings': {
            'server_name': 'Weather Server',
            'description': 'Provides weather information tools'
        }
    }
)

if result.success:
    print(f"Project created at: {result.project_path}")
else:
    print(f"Creation failed: {result.errors}")
```

##### `get_project_status(project_id: str) -> ProjectStatus`

Gets the current status of a project.

**Parameters:**
- `project_id`: Unique project identifier from ProjectResult

**Returns:** Current project status enum value

**Example:**
```python
status = manager.get_project_status(result.project_id)
print(f"Project status: {status.value}")
```

##### `cleanup_project(project_id: str) -> bool`

Cleans up project resources and files.

**Parameters:**
- `project_id`: Unique project identifier

**Returns:** True if cleanup was successful

**Example:**
```python
if manager.cleanup_project(result.project_id):
    print("Project cleaned up successfully")
```

### TemplateEngine

Interface for managing MCP server templates.

```python
from mcp_server_builder.managers.template_engine import TemplateEngineImpl

template_engine = TemplateEngineImpl()
```

#### Methods

##### `list_templates() -> List[ServerTemplate]`

Lists all available server templates.

**Returns:** List of ServerTemplate objects

**Example:**
```python
templates = template_engine.list_templates()
for template in templates:
    print(f"{template.id}: {template.name} ({template.language.value})")
```

##### `get_template(template_id: str) -> Optional[ServerTemplate]`

Gets a specific template by ID.

**Parameters:**
- `template_id`: Template identifier

**Returns:** ServerTemplate if found, None otherwise

**Example:**
```python
template = template_engine.get_template("python-fastmcp")
if template:
    print(f"Template: {template.name}")
    print(f"Dependencies: {template.dependencies}")
```

##### `apply_template(template: ServerTemplate, config: Dict[str, Any]) -> TemplateResult`

Applies a template with given configuration.

**Parameters:**
- `template`: Template to apply
- `config`: Configuration parameters for customization

**Returns:** TemplateResult with application status and details

### FileManager

Interface for managing file operations during project creation.

```python
from mcp_server_builder.managers.file_manager import FileManagerImpl

file_manager = FileManagerImpl()
```

#### Methods

##### `create_directory_structure(path: str, structure: Dict[str, Any]) -> bool`

Creates directory structure at the specified path.

**Parameters:**
- `path`: Base path for directory creation
- `structure`: Directory structure definition

**Example:**
```python
structure = {
    'src': {},
    'tests': {},
    'docs': {},
    'examples': {}
}
success = file_manager.create_directory_structure("/path/to/project", structure)
```

##### `download_files(files: List[FileSpec]) -> DownloadResult`

Downloads files from remote sources.

**Parameters:**
- `files`: List of FileSpec objects specifying files to download

**Example:**
```python
from mcp_server_builder.models.base import FileSpec

files = [
    FileSpec(
        url="https://example.com/server.py",
        destination_path="/path/to/project/src/server.py",
        checksum="sha256:abc123...",
        executable=False
    )
]
result = file_manager.download_files(files)
```

### DependencyManager

Interface for managing project dependencies.

```python
from mcp_server_builder.managers.dependency_manager import DependencyManagerImpl

dep_manager = DependencyManagerImpl()
```

#### Methods

##### `detect_package_manager(project_path: str) -> Optional[str]`

Detects the package manager for a project.

**Parameters:**
- `project_path`: Path to the project directory

**Returns:** Package manager name if detected

**Example:**
```python
package_manager = dep_manager.detect_package_manager("/path/to/project")
print(f"Detected package manager: {package_manager}")
```

##### `install_dependencies(project_path: str, dependencies: List[str]) -> InstallResult`

Installs project dependencies.

**Parameters:**
- `project_path`: Path to the project directory
- `dependencies`: List of dependencies to install

**Example:**
```python
result = dep_manager.install_dependencies(
    "/path/to/project",
    ["fastmcp", "pydantic", "requests"]
)
if result.success:
    print(f"Installed: {result.installed_packages}")
```

### BuildSystem

Interface for managing build operations.

```python
from mcp_server_builder.managers.build_system import BuildSystemManager

build_system = BuildSystemManager()
```

#### Methods

##### `execute_build(project_path: str, commands: List[str]) -> BuildResult`

Executes build commands for a project.

**Parameters:**
- `project_path`: Path to the project directory
- `commands`: List of build commands to execute

**Example:**
```python
result = build_system.execute_build(
    "/path/to/project",
    ["python -m pip install -e .", "python -m pytest"]
)
if result.success:
    print(f"Build artifacts: {result.artifacts}")
```

### ValidationEngine

Interface for validating MCP server functionality.

```python
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
```

#### Methods

##### `validate_server_startup(project_path: str) -> bool`

Validates that the MCP server can start successfully.

**Parameters:**
- `project_path`: Path to the project directory

**Returns:** True if server starts successfully

##### `validate_mcp_protocol(project_path: str) -> bool`

Validates MCP protocol compliance.

**Parameters:**
- `project_path`: Path to the project directory

**Returns:** True if server is MCP protocol compliant

##### `run_comprehensive_tests(project_path: str) -> Dict[str, Any]`

Runs comprehensive validation tests.

**Parameters:**
- `project_path`: Path to the project directory

**Returns:** Dictionary with detailed test results

**Example:**
```python
# Basic validation
startup_ok = validator.validate_server_startup("/path/to/project")
protocol_ok = validator.validate_mcp_protocol("/path/to/project")

# Comprehensive testing
test_results = validator.run_comprehensive_tests("/path/to/project")
print(f"Test results: {test_results}")
```

## Data Models

### ServerTemplate

Represents an MCP server template with all necessary information for project creation.

```python
@dataclass
class ServerTemplate:
    id: str                           # Unique template identifier
    name: str                         # Human-readable name
    description: str                  # Template description
    language: ServerLanguage          # Programming language
    framework: ServerFramework        # Framework type
    files: List[TemplateFile]         # Template files
    dependencies: List[str]           # Required dependencies
    build_commands: List[str]         # Build commands
    configuration_schema: Dict[str, Any]  # Configuration schema
```

### ProjectConfig

Configuration for creating an MCP server project.

```python
@dataclass
class ProjectConfig:
    name: str                         # Project name
    template_id: str                  # Template identifier
    output_directory: str             # Output directory path
    custom_settings: Dict[str, Any]   # Custom configuration
    environment_variables: Dict[str, str]  # Environment variables
    additional_dependencies: List[str]     # Additional dependencies
```

### ProjectResult

Result of project creation operation.

```python
@dataclass
class ProjectResult:
    success: bool                     # Whether creation succeeded
    project_id: str                   # Unique project identifier
    project_path: str                 # Path to created project
    template_used: str                # Template that was used
    status: ProjectStatus             # Current project status
    errors: List[str]                 # Any errors that occurred
    created_files: List[str]          # List of created files
```

### BuildResult

Result of build operation.

```python
@dataclass
class BuildResult:
    success: bool                     # Whether build succeeded
    project_path: str                 # Project path
    artifacts: List[str]              # Generated artifacts
    logs: List[str]                   # Build logs
    errors: List[str]                 # Build errors
    execution_time: float             # Time taken
    build_tool: Optional[str]         # Build tool used
    artifact_report: Optional[Dict[str, Any]]  # Artifact details
    packaging_info: Optional[Dict[str, Any]]   # Packaging information
```

## Enums

### ProjectStatus

```python
class ProjectStatus(Enum):
    CREATED = "created"
    DOWNLOADING = "downloading"
    INSTALLING_DEPS = "installing_deps"
    BUILDING = "building"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
```

### ServerLanguage

```python
class ServerLanguage(Enum):
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"
```

### ServerFramework

```python
class ServerFramework(Enum):
    FASTMCP = "fastmcp"
    LOW_LEVEL = "low-level"
    TYPESCRIPT_SDK = "typescript-sdk"
    FOXY_CONTEXTS = "foxy-contexts"
    QUARKUS = "quarkus"
```

## Usage Patterns

### Basic Project Creation

```python
from mcp_server_builder.managers.project_manager import ProjectManagerImpl
from mcp_server_builder.managers.progress_tracker import LogLevel

# Initialize manager
manager = ProjectManagerImpl(log_level=LogLevel.INFO)

# Create project
result = manager.create_project(
    name="weather-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'Weather MCP Server',
            'description': 'Provides weather information and forecasts'
        }
    }
)

# Check result
if result.success:
    print(f"✅ Project created successfully at: {result.project_path}")
    print(f"📁 Created files: {len(result.created_files)}")
else:
    print(f"❌ Project creation failed:")
    for error in result.errors:
        print(f"  - {error}")
```

### Advanced Project Creation with Callbacks

```python
def progress_callback(project_id: str, percentage: float, phase: str):
    print(f"[{project_id[:8]}] {phase}: {percentage:.1f}%")

def error_callback(project_id: str, error: str):
    print(f"[{project_id[:8]}] ERROR: {error}")

# Initialize with callbacks
manager = ProjectManagerImpl(
    progress_callback=progress_callback,
    error_callback=error_callback,
    log_level=LogLevel.DEBUG
)

# Create project with advanced configuration
config = {
    'output_directory': './my-servers',
    'custom_settings': {
        'server_name': 'Advanced MCP Server',
        'description': 'Server with custom tools and resources',
        'transport_type': 'stdio',
        'enable_logging': True
    },
    'environment_variables': {
        'DEBUG': 'true',
        'API_TIMEOUT': '30'
    },
    'additional_dependencies': [
        'requests>=2.28.0',
        'pydantic>=2.0.0',
        'python-dotenv'
    ]
}

result = manager.create_project(
    name="advanced-server",
    template="python-fastmcp",
    config=config
)
```

### Template Management

```python
from mcp_server_builder.managers.template_engine import TemplateEngineImpl

template_engine = TemplateEngineImpl()

# List available templates
print("Available templates:")
for template in template_engine.list_templates():
    print(f"  {template.id}: {template.name}")
    print(f"    Language: {template.language.value}")
    print(f"    Framework: {template.framework.value}")
    print(f"    Dependencies: {len(template.dependencies)}")
    print()

# Get specific template details
template = template_engine.get_template("python-fastmcp")
if template:
    print(f"Template: {template.name}")
    print(f"Description: {template.description}")
    print(f"Build commands: {template.build_commands}")
    print(f"Configuration schema: {template.configuration_schema}")
```

### Project Monitoring and Management

```python
# Get project status
status = manager.get_project_status(result.project_id)
print(f"Project status: {status.value}")

# Get detailed project information
details = manager.get_project_details(result.project_id)
if details:
    print(f"Project: {details['name']}")
    print(f"Status: {details['status']}")
    print(f"Progress: {details['progress_percentage']:.1f}%")
    print(f"Current phase: {details['current_phase']}")
    print(f"Created: {details['created_at']}")

# List all projects
projects = manager.list_projects()
for project in projects:
    print(f"{project['name']} ({project['status']}) - {project['template_id']}")

# Get progress events
events = manager.get_project_events(result.project_id)
for event in events[-5:]:  # Last 5 events
    print(f"{event.timestamp}: {event.phase} - {event.message}")
```

### Validation and Testing

```python
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()

# Basic validation
project_path = result.project_path
startup_ok = validator.validate_server_startup(project_path)
protocol_ok = validator.validate_mcp_protocol(project_path)

print(f"Server startup: {'✅' if startup_ok else '❌'}")
print(f"Protocol compliance: {'✅' if protocol_ok else '❌'}")

# Comprehensive testing
test_results = validator.run_comprehensive_tests(project_path)
print(f"Comprehensive test results:")
print(f"  Overall success: {test_results.get('overall_success', False)}")
print(f"  Tools tested: {len(test_results.get('tools', {}))}")
print(f"  Resources tested: {len(test_results.get('resources', {}))}")
print(f"  Performance score: {test_results.get('performance_score', 0)}")
```

## Error Handling

The MCP Server Builder provides comprehensive error handling with specific error categories and recovery mechanisms.

### Error Categories

- **TEMPLATE**: Template-related errors (not found, invalid configuration)
- **FILE_SYSTEM**: File operations errors (permissions, disk space)
- **NETWORK**: Network-related errors (download failures, timeouts)
- **DEPENDENCY**: Package installation errors (not found, conflicts)
- **BUILD**: Build process errors (compilation failures, missing tools)
- **VALIDATION**: Server validation errors (startup failures, protocol issues)
- **SYSTEM**: System-level errors (unexpected exceptions)

### Error Handling Example

```python
try:
    result = manager.create_project(name, template, config)
    if not result.success:
        print("Project creation failed:")
        for error in result.errors:
            print(f"  - {error}")
            
        # Attempt cleanup
        if manager.cleanup_project(result.project_id):
            print("Cleaned up partial project")
            
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Recovery Actions

The system automatically attempts recovery for certain error types:

- **Retry Logic**: Automatic retry for transient network and file system errors
- **Fallback Templates**: Alternative templates when primary selection fails
- **Partial Recovery**: Continue with available components when non-critical parts fail
- **Rollback Capability**: Clean removal of partially created projects

## Performance Considerations

### Memory Usage

- Template files are loaded on-demand to minimize memory usage
- Large file downloads use streaming to avoid memory issues
- Project state is persisted to disk to handle system restarts

### Concurrent Operations

- Multiple projects can be created concurrently
- Thread-safe operations for shared resources
- Progress tracking supports concurrent project monitoring

### Optimization Tips

```python
# Use appropriate log levels for production
manager = ProjectManagerImpl(log_level=LogLevel.WARNING)

# Batch operations when creating multiple projects
configs = [config1, config2, config3]
results = []
for i, config in enumerate(configs):
    result = manager.create_project(f"project-{i}", template, config)
    results.append(result)

# Clean up completed projects to free resources
for result in results:
    if result.status == ProjectStatus.COMPLETED:
        manager.cleanup_project(result.project_id)
```