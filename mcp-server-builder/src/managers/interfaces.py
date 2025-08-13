"""Core interfaces for MCP Server Builder managers."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models.base import (
    ProjectConfig, ProjectResult, ProjectStatus, ServerTemplate,
    TemplateResult, FileSpec, DownloadResult, InstallResult,
    VerificationResult, BuildResult
)


class ProjectManager(ABC):
    """Interface for managing MCP server project creation and lifecycle."""
    
    @abstractmethod
    def create_project(self, name: str, template: str, config: Dict[str, Any]) -> ProjectResult:
        """Create a new MCP server project.
        
        Args:
            name: Project name
            template: Template identifier
            config: Project configuration options
            
        Returns:
            ProjectResult with creation status and details
        """
        pass
    
    @abstractmethod
    def get_project_status(self, project_id: str) -> ProjectStatus:
        """Get the current status of a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Current project status
        """
        pass
    
    @abstractmethod
    def cleanup_project(self, project_id: str) -> bool:
        """Clean up project resources and files.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            True if cleanup was successful
        """
        pass


class TemplateEngine(ABC):
    """Interface for managing MCP server templates."""
    
    @abstractmethod
    def list_templates(self) -> List[ServerTemplate]:
        """List all available server templates.
        
        Returns:
            List of available templates
        """
        pass
    
    @abstractmethod
    def get_template(self, template_id: str) -> Optional[ServerTemplate]:
        """Get a specific template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            ServerTemplate if found, None otherwise
        """
        pass
    
    @abstractmethod
    def apply_template(self, template: ServerTemplate, config: Dict[str, Any]) -> TemplateResult:
        """Apply a template with given configuration.
        
        Args:
            template: Template to apply
            config: Configuration parameters
            
        Returns:
            TemplateResult with application status and details
        """
        pass


class FileManager(ABC):
    """Interface for managing file operations."""
    
    @abstractmethod
    def create_directory_structure(self, path: str, structure: Dict[str, Any]) -> bool:
        """Create directory structure at the specified path.
        
        Args:
            path: Base path for directory creation
            structure: Directory structure definition
            
        Returns:
            True if creation was successful
        """
        pass
    
    @abstractmethod
    def download_files(self, files: List[FileSpec]) -> DownloadResult:
        """Download files from remote sources.
        
        Args:
            files: List of file specifications to download
            
        Returns:
            DownloadResult with download status and details
        """
        pass
    
    @abstractmethod
    def set_permissions(self, path: str, permissions: str) -> bool:
        """Set file or directory permissions.
        
        Args:
            path: Path to file or directory
            permissions: Permission string (e.g., '755', '644')
            
        Returns:
            True if permissions were set successfully
        """
        pass


class DependencyManager(ABC):
    """Interface for managing project dependencies."""
    
    @abstractmethod
    def detect_package_manager(self, project_path: str) -> Optional[str]:
        """Detect the package manager for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Package manager name if detected, None otherwise
        """
        pass
    
    @abstractmethod
    def install_dependencies(self, project_path: str, dependencies: List[str]) -> InstallResult:
        """Install project dependencies.
        
        Args:
            project_path: Path to the project directory
            dependencies: List of dependencies to install
            
        Returns:
            InstallResult with installation status and details
        """
        pass
    
    @abstractmethod
    def verify_installation(self, project_path: str) -> VerificationResult:
        """Verify that dependencies are properly installed.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            VerificationResult with verification status and details
        """
        pass
    
    @abstractmethod
    def scan_security_vulnerabilities(self, project_path: str) -> Dict[str, Any]:
        """Scan installed packages for security vulnerabilities.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with security scan results
        """
        pass
    
    @abstractmethod
    def validate_dependency_compatibility(self, project_path: str) -> Dict[str, Any]:
        """Validate compatibility of installed dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with compatibility validation results
        """
        pass


class BuildSystem(ABC):
    """Interface for managing build operations."""
    
    @abstractmethod
    def detect_build_system(self, project_path: str) -> Optional[str]:
        """Detect the build system for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Build system name if detected, None otherwise
        """
        pass
    
    @abstractmethod
    def execute_build(self, project_path: str, commands: List[str]) -> BuildResult:
        """Execute build commands for a project.
        
        Args:
            project_path: Path to the project directory
            commands: List of build commands to execute
            
        Returns:
            BuildResult with build status and details
        """
        pass
    
    @abstractmethod
    def get_build_artifacts(self, project_path: str) -> List[str]:
        """Get list of build artifacts.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of paths to build artifacts
        """
        pass


class ValidationEngine(ABC):
    """Interface for validating MCP server functionality."""
    
    @abstractmethod
    def validate_server_startup(self, project_path: str) -> bool:
        """Validate that the MCP server can start successfully.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if server starts successfully
        """
        pass
    
    @abstractmethod
    def validate_mcp_protocol(self, project_path: str) -> bool:
        """Validate MCP protocol compliance.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if server is MCP protocol compliant
        """
        pass
    
    @abstractmethod
    def validate_functionality(self, project_path: str) -> Dict[str, bool]:
        """Validate server functionality (tools, resources, prompts).
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary mapping functionality types to validation results
        """
        pass
    
    @abstractmethod
    def run_comprehensive_tests(self, project_path: str) -> Dict[str, Any]:
        """Run comprehensive validation tests.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with detailed test results
        """
        pass