"""Main project manager implementation for orchestrating MCP server creation."""

import os
import uuid
import json
import time
import shutil
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime

from .interfaces import ProjectManager as ProjectManagerInterface
from .template_engine import TemplateEngineImpl
from .file_manager import FileManagerImpl
from .dependency_manager import DependencyManagerImpl
from .build_system import BuildSystemManager
from .validation_engine import MCPValidationEngine
from .progress_tracker import ProgressTracker, LogLevel, ProgressEvent
from .error_handler import ErrorHandler, ErrorCategory, ErrorSeverity, RecoveryAction
from ..models.base import (
    ProjectConfig, ProjectResult, ProjectStatus, ServerTemplate,
    BuildResult, ValidationResult
)


class ProjectState:
    """Tracks the state of a project during creation."""
    
    def __init__(self, project_id: str, config: ProjectConfig):
        self.project_id = project_id
        self.config = config
        self.status = ProjectStatus.CREATED
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.errors: List[str] = []
        self.created_files: List[str] = []
        self.current_phase = "initialization"
        self.progress_percentage = 0.0
        
    def update_status(self, status: ProjectStatus, phase: str = None):
        """Update project status and phase."""
        self.status = status
        self.updated_at = datetime.now()
        if phase:
            self.current_phase = phase
            
    def add_error(self, error: str):
        """Add an error to the project state."""
        self.errors.append(error)
        
    def add_created_file(self, file_path: str):
        """Add a created file to the tracking list."""
        self.created_files.append(file_path)
        
    def set_progress(self, percentage: float):
        """Set the current progress percentage."""
        self.progress_percentage = min(100.0, max(0.0, percentage))


class ProjectManagerImpl(ProjectManagerInterface):
    """Main project manager that orchestrates all components for MCP server creation."""
    
    def __init__(self, 
                 progress_callback: Optional[Callable[[str, float, str], None]] = None,
                 error_callback: Optional[Callable[[str, str], None]] = None,
                 log_level: LogLevel = LogLevel.INFO,
                 log_file: Optional[str] = None):
        """Initialize the project manager with optional callbacks.
        
        Args:
            progress_callback: Callback for progress updates (project_id, percentage, phase)
            error_callback: Callback for error notifications (project_id, error_message)
            log_level: Logging verbosity level
            log_file: Optional file path for logging output
        """
        self.template_engine = TemplateEngineImpl()
        self.file_manager = FileManagerImpl()
        self.dependency_manager = DependencyManagerImpl()
        self.build_system = BuildSystemManager()
        self.validation_engine = MCPValidationEngine()
        
        # Progress tracking and reporting
        self.progress_tracker = ProgressTracker(
            log_level=log_level,
            enable_real_time=True,
            log_file=log_file
        )
        
        # Centralized error handling and recovery
        self.error_handler = ErrorHandler()
        
        # Project state tracking
        self._projects: Dict[str, ProjectState] = {}
        self._state_file = Path.home() / ".mcp_builder" / "project_states.json"
        
        # Callbacks for progress and error reporting
        self.progress_callback = progress_callback
        self.error_callback = error_callback
        
        # Register callbacks with progress tracker
        if progress_callback or error_callback:
            self.progress_tracker.add_callback(self._handle_progress_event)
        
        # Load existing project states
        self._load_project_states()
        
    def create_project(self, name: str, template: str, config: Dict[str, Any]) -> ProjectResult:
        """Create a new MCP server project with full orchestration.
        
        Args:
            name: Project name
            template: Template identifier
            config: Project configuration options
            
        Returns:
            ProjectResult with creation status and details
        """
        project_id = str(uuid.uuid4())
        
        # Create project configuration
        project_config = ProjectConfig(
            name=name,
            template_id=template,
            output_directory=config.get('output_directory', os.getcwd()),
            custom_settings=config.get('custom_settings', {}),
            environment_variables=config.get('environment_variables', {}),
            additional_dependencies=config.get('additional_dependencies', [])
        )
        
        # Initialize project state
        project_state = ProjectState(project_id, project_config)
        self._projects[project_id] = project_state
        
        try:
            # Phase 1: Template preparation and validation
            self.progress_tracker.start_phase(project_id, "template_preparation", "Preparing and validating template")
            template_obj = self._prepare_template(project_id, template)
            if not template_obj:
                return self._create_failure_result(project_id, "Template preparation failed")
            self.progress_tracker.complete_phase(project_id, "Template prepared successfully")
            
            # Phase 2: Directory structure creation
            self.progress_tracker.start_phase(project_id, "directory_creation", "Creating project directory structure")
            project_path = self._create_project_structure(project_id, project_config)
            if not project_path:
                return self._create_failure_result(project_id, "Directory structure creation failed")
            self.progress_tracker.complete_phase(project_id, "Directory structure created")
            
            # Phase 3: File download and placement
            project_state.update_status(ProjectStatus.DOWNLOADING, "Downloading template files")
            self.progress_tracker.start_phase(project_id, "file_download", "Downloading and placing template files")
            if not self._download_template_files(project_id, template_obj, project_path):
                return self._create_failure_result(project_id, "File download failed")
            self.progress_tracker.complete_phase(project_id, "Template files downloaded and placed")
            
            # Phase 4: Template application and customization
            self.progress_tracker.start_phase(project_id, "template_customization", "Applying template customization")
            if not self._apply_template_customization(project_id, template_obj, project_config, project_path):
                return self._create_failure_result(project_id, "Template customization failed")
            self.progress_tracker.complete_phase(project_id, "Template customization applied")
            
            # Phase 5: Dependency installation
            project_state.update_status(ProjectStatus.INSTALLING_DEPS, "Installing dependencies")
            self.progress_tracker.start_phase(project_id, "dependency_installation", "Installing project dependencies")
            if not self._install_dependencies(project_id, template_obj, project_path):
                return self._create_failure_result(project_id, "Dependency installation failed")
            self.progress_tracker.complete_phase(project_id, "Dependencies installed successfully")
            
            # Phase 6: Build execution
            project_state.update_status(ProjectStatus.BUILDING, "Building project")
            self.progress_tracker.start_phase(project_id, "build_execution", "Executing build commands")
            build_result = self._execute_build(project_id, template_obj, project_path)
            if not build_result or not build_result.success:
                return self._create_failure_result(project_id, "Build execution failed")
            self.progress_tracker.complete_phase(project_id, "Build completed successfully")
            
            # Phase 7: Validation
            project_state.update_status(ProjectStatus.VALIDATING, "Validating server")
            self.progress_tracker.start_phase(project_id, "validation", "Validating MCP server")
            if not self._validate_server(project_id, project_path):
                # Validation failure is not necessarily a project failure
                project_state.add_error("Server validation failed - manual verification recommended")
                self.progress_tracker.log_warning(project_id, "Server validation failed - manual verification recommended")
            self.progress_tracker.complete_phase(project_id, "Validation completed")
            
            # Phase 8: Completion
            project_state.update_status(ProjectStatus.COMPLETED, "Project completed")
            self.progress_tracker.log_info(project_id, "Project creation completed successfully")
            
            # Save project state
            self._save_project_states()
            
            return ProjectResult(
                success=True,
                project_id=project_id,
                project_path=project_path,
                template_used=template,
                status=ProjectStatus.COMPLETED,
                errors=project_state.errors,
                created_files=project_state.created_files
            )
            
        except Exception as e:
            error_msg = f"Unexpected error during project creation: {str(e)}"
            
            # Handle error through centralized error handler
            recovery_action = self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.SYSTEM,
                severity=ErrorSeverity.CRITICAL,
                message=error_msg,
                phase=project_state.current_phase if project_state else "unknown",
                exception=e
            )
            
            # Attempt recovery if possible
            if recovery_action == RecoveryAction.ROLLBACK:
                self.error_handler.execute_rollback(project_id)
            
            project_state.add_error(error_msg)
            project_state.update_status(ProjectStatus.FAILED, "Failed with exception")
            self._report_error(project_id, error_msg)
            return self._create_failure_result(project_id, error_msg)
    
    def get_project_status(self, project_id: str) -> ProjectStatus:
        """Get the current status of a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Current project status
        """
        if project_id in self._projects:
            return self._projects[project_id].status
        return ProjectStatus.FAILED
    
    def cleanup_project(self, project_id: str) -> bool:
        """Clean up project resources and files.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            True if cleanup was successful
        """
        if project_id not in self._projects:
            return False
            
        project_state = self._projects[project_id]
        
        try:
            # Remove created files
            for file_path in project_state.created_files:
                if os.path.exists(file_path):
                    if os.path.isdir(file_path):
                        import shutil
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
            
            # Remove project from tracking
            del self._projects[project_id]
            self._save_project_states()
            
            return True
            
        except Exception as e:
            self._report_error(project_id, f"Cleanup failed: {str(e)}")
            return False
    
    def get_project_details(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Dictionary with project details or None if not found
        """
        if project_id not in self._projects:
            return None
            
        state = self._projects[project_id]
        return {
            'project_id': project_id,
            'name': state.config.name,
            'template_id': state.config.template_id,
            'status': state.status.value,
            'current_phase': state.current_phase,
            'progress_percentage': state.progress_percentage,
            'created_at': state.created_at.isoformat(),
            'updated_at': state.updated_at.isoformat(),
            'errors': state.errors,
            'created_files': state.created_files,
            'output_directory': state.config.output_directory
        }
    
    def list_projects(self) -> List[Dict[str, Any]]:
        """List all tracked projects.
        
        Returns:
            List of project summaries
        """
        return [
            {
                'project_id': project_id,
                'name': state.config.name,
                'status': state.status.value,
                'created_at': state.created_at.isoformat(),
                'template_id': state.config.template_id
            }
            for project_id, state in self._projects.items()
        ]
    
    def get_project_progress(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed progress information for a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Dictionary with progress details or None if not found
        """
        return self.progress_tracker.get_project_summary(project_id)
    
    def get_project_events(self, project_id: str) -> List[ProgressEvent]:
        """Get all progress events for a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            List of progress events
        """
        return self.progress_tracker.get_project_events(project_id)
    
    def set_log_level(self, log_level: LogLevel):
        """Set the logging verbosity level.
        
        Args:
            log_level: New logging level
        """
        self.progress_tracker.log_level = log_level
        self.progress_tracker._setup_logging(None)
    
    def add_progress_callback(self, callback: Callable[[ProgressEvent], None]):
        """Add a callback for progress events.
        
        Args:
            callback: Function to call when progress events occur
        """
        self.progress_tracker.add_callback(callback)
    
    def remove_progress_callback(self, callback: Callable[[ProgressEvent], None]):
        """Remove a progress event callback.
        
        Args:
            callback: Callback function to remove
        """
        self.progress_tracker.remove_callback(callback)    

    # Private helper methods for project orchestration
    
    def _prepare_template(self, project_id: str, template_id: str) -> Optional[ServerTemplate]:
        """Prepare and validate the template for use."""
        try:
            template = self.template_engine.get_template(template_id)
            if not template:
                self.error_handler.handle_error(
                    project_id=project_id,
                    category=ErrorCategory.TEMPLATE,
                    severity=ErrorSeverity.HIGH,
                    message=f"Template '{template_id}' not found",
                    phase="template_preparation"
                )
                return None
            return template
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.TEMPLATE,
                severity=ErrorSeverity.HIGH,
                message=f"Template preparation failed: {str(e)}",
                phase="template_preparation",
                exception=e
            )
            return None
    
    def _create_project_structure(self, project_id: str, config: ProjectConfig) -> Optional[str]:
        """Create the project directory structure."""
        try:
            project_path = os.path.join(config.output_directory, config.name)
            
            # Create main project directory
            os.makedirs(project_path, exist_ok=True)
            self._projects[project_id].add_created_file(project_path)
            
            # Register rollback action for directory cleanup
            self.error_handler.register_rollback_action(
                project_id, 
                lambda: self._cleanup_directory(project_path)
            )
            
            # Create standard MCP server directory structure
            directories = [
                "src",
                "tests", 
                "docs",
                "examples"
            ]
            
            for directory in directories:
                dir_path = os.path.join(project_path, directory)
                os.makedirs(dir_path, exist_ok=True)
                self._projects[project_id].add_created_file(dir_path)
            
            return project_path
            
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.FILE_SYSTEM,
                severity=ErrorSeverity.HIGH,
                message=f"Directory structure creation failed: {str(e)}",
                phase="directory_creation",
                exception=e
            )
            return None
    
    def _download_template_files(self, project_id: str, template: ServerTemplate, project_path: str) -> bool:
        """Download and place template files."""
        try:
            if not template.files:
                return True  # No files to download
                
            file_specs = []
            for template_file in template.files:
                destination = os.path.join(project_path, template_file.path)
                file_specs.append({
                    'url': template_file.url,
                    'destination_path': destination,
                    'checksum': template_file.checksum,
                    'executable': template_file.executable
                })
            
            # Convert to FileSpec objects
            from ..models.base import FileSpec
            specs = [FileSpec(**spec) for spec in file_specs]
            
            result = self.file_manager.download_files(specs)
            
            if result.success:
                for file_path in result.downloaded_files:
                    self._projects[project_id].add_created_file(file_path)
                    # Register rollback action for each downloaded file
                    self.error_handler.register_rollback_action(
                        project_id,
                        lambda fp=file_path: self._cleanup_file(fp)
                    )
                return True
            else:
                for error in result.errors:
                    self.error_handler.handle_error(
                        project_id=project_id,
                        category=ErrorCategory.NETWORK,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"File download error: {error}",
                        phase="file_download"
                    )
                return False
                
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"File download failed: {str(e)}",
                phase="file_download",
                exception=e
            )
            return False
    
    def _apply_template_customization(self, project_id: str, template: ServerTemplate, 
                                    config: ProjectConfig, project_path: str) -> bool:
        """Apply template customization and parameter substitution."""
        try:
            # Apply template with configuration
            template_result = self.template_engine.apply_template(template, config.custom_settings)
            
            if template_result.success:
                for file_path in template_result.generated_files:
                    self._projects[project_id].add_created_file(file_path)
                    # Register rollback action for generated files
                    self.error_handler.register_rollback_action(
                        project_id,
                        lambda fp=file_path: self._cleanup_file(fp)
                    )
                return True
            else:
                for error in template_result.errors:
                    self.error_handler.handle_error(
                        project_id=project_id,
                        category=ErrorCategory.TEMPLATE,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Template customization error: {error}",
                        phase="template_customization"
                    )
                return False
                
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.TEMPLATE,
                severity=ErrorSeverity.MEDIUM,
                message=f"Template customization failed: {str(e)}",
                phase="template_customization",
                exception=e
            )
            return False
    
    def _install_dependencies(self, project_id: str, template: ServerTemplate, project_path: str) -> bool:
        """Install project dependencies."""
        try:
            # Combine template dependencies with additional ones
            all_dependencies = template.dependencies.copy()
            all_dependencies.extend(self._projects[project_id].config.additional_dependencies)
            
            if not all_dependencies:
                return True  # No dependencies to install
            
            result = self.dependency_manager.install_dependencies(project_path, all_dependencies)
            
            if result.success:
                # Register rollback action for dependency cleanup
                self.error_handler.register_rollback_action(
                    project_id,
                    lambda: self._cleanup_dependencies(project_path)
                )
                return True
            else:
                for error in result.errors:
                    self.error_handler.handle_error(
                        project_id=project_id,
                        category=ErrorCategory.DEPENDENCY,
                        severity=ErrorSeverity.MEDIUM,
                        message=f"Dependency installation error: {error}",
                        phase="dependency_installation"
                    )
                return False
                
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.DEPENDENCY,
                severity=ErrorSeverity.MEDIUM,
                message=f"Dependency installation failed: {str(e)}",
                phase="dependency_installation",
                exception=e
            )
            return False
    
    def _execute_build(self, project_id: str, template: ServerTemplate, project_path: str) -> Optional[BuildResult]:
        """Execute build commands for the project."""
        try:
            if not template.build_commands:
                # No build commands, consider it successful
                return BuildResult(
                    success=True,
                    project_path=project_path,
                    artifacts=[],
                    logs=["No build commands specified"],
                    errors=[],
                    execution_time=0.0
                )
            
            result = self.build_system.execute_build(project_path, template.build_commands)
            
            if not result.success:
                for error in result.errors:
                    self.error_handler.handle_error(
                        project_id=project_id,
                        category=ErrorCategory.BUILD,
                        severity=ErrorSeverity.HIGH,
                        message=f"Build error: {error}",
                        phase="build_execution"
                    )
            else:
                # Register rollback action for build artifacts
                if result.artifacts:
                    self.error_handler.register_rollback_action(
                        project_id,
                        lambda: self._cleanup_build_artifacts(project_path, result.artifacts)
                    )
            
            return result
            
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.BUILD,
                severity=ErrorSeverity.HIGH,
                message=f"Build execution failed: {str(e)}",
                phase="build_execution",
                exception=e
            )
            return None
    
    def _validate_server(self, project_id: str, project_path: str) -> bool:
        """Validate the created MCP server."""
        try:
            # Run basic validation tests
            startup_valid = self.validation_engine.validate_server_startup(project_path)
            protocol_valid = self.validation_engine.validate_mcp_protocol(project_path)
            
            if not startup_valid:
                self.error_handler.handle_error(
                    project_id=project_id,
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.LOW,
                    message="Server startup validation failed",
                    phase="validation"
                )
            
            if not protocol_valid:
                self.error_handler.handle_error(
                    project_id=project_id,
                    category=ErrorCategory.VALIDATION,
                    severity=ErrorSeverity.LOW,
                    message="MCP protocol validation failed",
                    phase="validation"
                )
            
            return startup_valid and protocol_valid
            
        except Exception as e:
            self.error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.LOW,
                message=f"Server validation failed: {str(e)}",
                phase="validation",
                exception=e
            )
            return False
    
    def _create_failure_result(self, project_id: str, error_message: str) -> ProjectResult:
        """Create a failure result for project creation."""
        project_state = self._projects.get(project_id)
        if project_state:
            project_state.add_error(error_message)
            project_state.update_status(ProjectStatus.FAILED, "Failed")
            
            return ProjectResult(
                success=False,
                project_id=project_id,
                project_path=project_state.config.output_directory,
                template_used=project_state.config.template_id,
                status=ProjectStatus.FAILED,
                errors=project_state.errors,
                created_files=project_state.created_files
            )
        else:
            return ProjectResult(
                success=False,
                project_id=project_id,
                project_path="",
                template_used="",
                status=ProjectStatus.FAILED,
                errors=[error_message],
                created_files=[]
            )
    
    def _handle_progress_event(self, event: ProgressEvent):
        """Handle progress events from the progress tracker."""
        # Update project state
        if event.project_id in self._projects:
            project_state = self._projects[event.project_id]
            project_state.current_phase = event.phase
            project_state.set_progress(event.percentage)
            
            if event.error:
                project_state.add_error(event.error)
        
        # Call external callbacks
        if self.progress_callback and event.event_type.value in ['phase_progress', 'phase_start', 'phase_complete']:
            self.progress_callback(event.project_id, event.percentage, event.phase)
        
        if self.error_callback and event.error:
            self.error_callback(event.project_id, event.error)
    
    def _report_error(self, project_id: str, error_message: str):
        """Report error through progress tracker and update project state."""
        self.progress_tracker.log_error(project_id, error_message)
        
        if project_id in self._projects:
            self._projects[project_id].add_error(error_message)
    
    def _load_project_states(self):
        """Load project states from persistent storage."""
        try:
            if self._state_file.exists():
                with open(self._state_file, 'r') as f:
                    data = json.load(f)
                    
                # Reconstruct project states (simplified for persistence)
                for project_id, state_data in data.items():
                    # Create minimal project config for loading
                    config = ProjectConfig(
                        name=state_data.get('name', ''),
                        template_id=state_data.get('template_id', ''),
                        output_directory=state_data.get('output_directory', ''),
                        custom_settings={},
                        environment_variables={},
                        additional_dependencies=[]
                    )
                    
                    state = ProjectState(project_id, config)
                    state.status = ProjectStatus(state_data.get('status', 'failed'))
                    state.errors = state_data.get('errors', [])
                    state.created_files = state_data.get('created_files', [])
                    state.current_phase = state_data.get('current_phase', 'unknown')
                    
                    self._projects[project_id] = state
                    
        except Exception:
            # If loading fails, start with empty state
            self._projects = {}
    
    def _save_project_states(self):
        """Save project states to persistent storage."""
        try:
            # Ensure directory exists
            self._state_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for serialization
            data = {}
            for project_id, state in self._projects.items():
                data[project_id] = {
                    'name': state.config.name,
                    'template_id': state.config.template_id,
                    'output_directory': state.config.output_directory,
                    'status': state.status.value,
                    'errors': state.errors,
                    'created_files': state.created_files,
                    'current_phase': state.current_phase,
                    'created_at': state.created_at.isoformat(),
                    'updated_at': state.updated_at.isoformat()
                }
            
            with open(self._state_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception:
            # If saving fails, continue without persistence
            pass
    
    # Helper methods for cleanup and recovery
    
    def _cleanup_directory(self, directory_path: str) -> bool:
        """Clean up a directory and its contents."""
        try:
            if os.path.exists(directory_path) and os.path.isdir(directory_path):
                shutil.rmtree(directory_path)
            return True
        except Exception:
            return False
    
    def _cleanup_file(self, file_path: str) -> bool:
        """Clean up a single file."""
        try:
            if os.path.exists(file_path) and os.path.isfile(file_path):
                os.remove(file_path)
            return True
        except Exception:
            return False
    
    def _cleanup_dependencies(self, project_path: str) -> bool:
        """Clean up installed dependencies."""
        try:
            # This would depend on the package manager
            # For now, we'll just remove common dependency directories
            dependency_dirs = [
                os.path.join(project_path, "node_modules"),
                os.path.join(project_path, "__pycache__"),
                os.path.join(project_path, ".venv"),
                os.path.join(project_path, "venv")
            ]
            
            for dep_dir in dependency_dirs:
                if os.path.exists(dep_dir):
                    shutil.rmtree(dep_dir)
            
            return True
        except Exception:
            return False
    
    def _cleanup_build_artifacts(self, project_path: str, artifacts: List[str]) -> bool:
        """Clean up build artifacts."""
        try:
            for artifact in artifacts:
                artifact_path = os.path.join(project_path, artifact) if not os.path.isabs(artifact) else artifact
                if os.path.exists(artifact_path):
                    if os.path.isdir(artifact_path):
                        shutil.rmtree(artifact_path)
                    else:
                        os.remove(artifact_path)
            return True
        except Exception:
            return False
    
    def get_project_errors(self, project_id: str) -> List[Dict[str, Any]]:
        """Get all errors for a specific project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            List of error information dictionaries
        """
        errors = self.error_handler.get_project_errors(project_id)
        return [
            {
                'error_id': error.error_id,
                'category': error.category.value,
                'severity': error.severity.value,
                'message': error.message,
                'phase': error.phase,
                'timestamp': error.timestamp.isoformat(),
                'suggested_actions': error.suggested_actions,
                'recovery_attempted': error.recovery_attempted,
                'recovery_successful': error.recovery_successful
            }
            for error in errors
        ]
    
    def get_error_summary(self, project_id: str) -> Dict[str, Any]:
        """Get a summary of errors for a project.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            Dictionary with error summary
        """
        return self.error_handler.get_error_summary(project_id)
    
    def attempt_error_recovery(self, project_id: str, error_id: str) -> bool:
        """Attempt to recover from a specific error.
        
        Args:
            project_id: Unique project identifier
            error_id: Specific error identifier
            
        Returns:
            True if recovery was successful
        """
        errors = self.error_handler.get_project_errors(project_id)
        for error in errors:
            if error.error_id == error_id:
                return self.error_handler.attempt_recovery(project_id, error)
        return False
    
    def force_rollback(self, project_id: str) -> bool:
        """Force a complete rollback of project changes.
        
        Args:
            project_id: Unique project identifier
            
        Returns:
            True if rollback was successful
        """
        return self.error_handler.execute_rollback(project_id)