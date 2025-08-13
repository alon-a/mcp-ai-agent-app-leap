"""Base data models for the MCP Server Builder."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum
from .enums import PackageManager, BuildTool, TransportType, ValidationLevel


class ServerLanguage(Enum):
    """Supported server languages."""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"
    RUST = "rust"
    JAVA = "java"


class ServerFramework(Enum):
    """Supported server frameworks."""
    FASTMCP = "fastmcp"
    LOW_LEVEL = "low-level"
    TYPESCRIPT_SDK = "typescript-sdk"
    FOXY_CONTEXTS = "foxy-contexts"
    QUARKUS = "quarkus"


class ProjectStatus(Enum):
    """Project creation status."""
    CREATED = "created"
    DOWNLOADING = "downloading"
    INSTALLING_DEPS = "installing_deps"
    BUILDING = "building"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TemplateFile:
    """Represents a file in a server template."""
    path: str
    url: str
    checksum: Optional[str] = None
    executable: bool = False


@dataclass
class ServerTemplate:
    """Represents an MCP server template."""
    id: str
    name: str
    description: str
    language: ServerLanguage
    framework: ServerFramework
    files: List[TemplateFile]
    dependencies: List[str]
    build_commands: List[str]
    configuration_schema: Dict[str, Any]


@dataclass
class ProjectConfig:
    """Configuration for creating an MCP server project."""
    name: str
    template_id: str
    output_directory: str
    custom_settings: Dict[str, Any]
    environment_variables: Dict[str, str]
    additional_dependencies: List[str]


@dataclass
class BuildResult:
    """Result of a build operation."""
    success: bool
    project_path: str
    artifacts: List[str]
    logs: List[str]
    errors: List[str]
    execution_time: float
    build_tool: Optional[str] = None
    artifact_report: Optional[Dict[str, Any]] = None
    packaging_info: Optional[Dict[str, Any]] = None


@dataclass
class ProjectResult:
    """Result of project creation."""
    success: bool
    project_id: str
    project_path: str
    template_used: str
    status: ProjectStatus
    errors: List[str]
    created_files: List[str]


@dataclass
class DownloadResult:
    """Result of file download operations."""
    success: bool
    downloaded_files: List[str]
    failed_files: List[str]
    errors: List[str]


@dataclass
class InstallResult:
    """Result of dependency installation."""
    success: bool
    installed_packages: List[str]
    failed_packages: List[str]
    errors: List[str]


@dataclass
class VerificationResult:
    """Result of installation verification."""
    success: bool
    verified_packages: List[str]
    missing_packages: List[str]
    errors: List[str]


@dataclass
class TemplateResult:
    """Result of template application."""
    success: bool
    generated_files: List[str]
    applied_config: Dict[str, Any]
    errors: List[str]


@dataclass
class FileSpec:
    """Specification for a file to be downloaded."""
    url: str
    destination_path: str
    checksum: Optional[str] = None
    executable: bool = False


@dataclass
class ValidationResult:
    """Result of MCP server validation."""
    success: bool
    validation_type: str
    project_path: str
    errors: List[str]
    warnings: List[str]
    details: Dict[str, Any]
    execution_time: float


@dataclass
class ServerStartupResult:
    """Result of server startup validation."""
    success: bool
    process_id: Optional[int]
    startup_time: float
    errors: List[str]
    logs: List[str]


@dataclass
class ProtocolComplianceResult:
    """Result of MCP protocol compliance validation."""
    success: bool
    supported_capabilities: List[str]
    missing_capabilities: List[str]
    protocol_version: Optional[str]
    errors: List[str]


@dataclass
class FunctionalityTestResult:
    """Result of functionality testing."""
    success: bool
    tested_tools: Dict[str, bool]
    tested_resources: Dict[str, bool]
    tested_prompts: Dict[str, bool]
    errors: List[str]
    performance_metrics: Dict[str, float]


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    project_path: str
    validation_level: ValidationLevel
    overall_success: bool
    startup_result: ServerStartupResult
    protocol_result: ProtocolComplianceResult
    functionality_result: FunctionalityTestResult
    performance_metrics: Dict[str, float]
    recommendations: List[str]
    timestamp: str
    total_execution_time: float