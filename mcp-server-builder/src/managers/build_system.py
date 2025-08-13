"""Build system management for MCP Server Builder."""

import os
import json
import subprocess
import logging
import time
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from queue import Queue, Empty

from .interfaces import BuildSystem
from .artifact_manager import ArtifactManager
from ..models.base import BuildResult
from ..models.enums import BuildTool, PackageManager
from ..models.artifacts import ArtifactReport


logger = logging.getLogger(__name__)


@dataclass
class BuildConfig:
    """Configuration for build operations."""
    build_tool: BuildTool
    commands: List[str]
    environment: Dict[str, str]
    working_directory: str
    timeout: int = 300  # 5 minutes default
    output_directory: Optional[str] = None


class BuildSystemManager(BuildSystem):
    """Concrete implementation of BuildSystem interface."""
    
    def __init__(self):
        """Initialize the build system manager."""
        self.artifact_manager = ArtifactManager()
        self.build_tool_detectors = {
            BuildTool.NPM_SCRIPTS: self._detect_npm_scripts,
            BuildTool.TSC: self._detect_typescript,
            BuildTool.WEBPACK: self._detect_webpack,
            BuildTool.VITE: self._detect_vite,
            BuildTool.PYTHON_SETUPTOOLS: self._detect_setuptools,
            BuildTool.POETRY_BUILD: self._detect_poetry,
            BuildTool.CARGO_BUILD: self._detect_cargo,
            BuildTool.GO_BUILD: self._detect_go,
            BuildTool.MAVEN_BUILD: self._detect_maven,
            BuildTool.GRADLE_BUILD: self._detect_gradle,
        }
        
        self.default_commands = {
            BuildTool.NPM_SCRIPTS: ["npm run build"],
            BuildTool.TSC: ["tsc"],
            BuildTool.WEBPACK: ["npx webpack"],
            BuildTool.VITE: ["npx vite build"],
            BuildTool.PYTHON_SETUPTOOLS: ["python setup.py build"],
            BuildTool.POETRY_BUILD: ["poetry build"],
            BuildTool.CARGO_BUILD: ["cargo build --release"],
            BuildTool.GO_BUILD: ["go build"],
            BuildTool.MAVEN_BUILD: ["mvn compile"],
            BuildTool.GRADLE_BUILD: ["./gradlew build"],
        }
    
    def detect_build_system(self, project_path: str) -> Optional[str]:
        """Detect the build system for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Build system name if detected, None otherwise
        """
        logger.info(f"Detecting build system for project: {project_path}")
        
        if not os.path.exists(project_path):
            logger.error(f"Project path does not exist: {project_path}")
            return None
        
        # Try to detect each build tool
        detected_tools = []
        for build_tool, detector in self.build_tool_detectors.items():
            if detector(project_path):
                detected_tools.append(build_tool)
                logger.info(f"Detected build tool: {build_tool.value}")
        
        if not detected_tools:
            logger.warning(f"No build system detected for project: {project_path}")
            return None
        
        # Return the first detected tool (prioritize by order in enum)
        primary_tool = detected_tools[0]
        if len(detected_tools) > 1:
            logger.info(f"Multiple build tools detected: {[t.value for t in detected_tools]}")
            logger.info(f"Using primary tool: {primary_tool.value}")
        
        return primary_tool.value
    
    def get_build_config(self, project_path: str, custom_commands: Optional[List[str]] = None) -> Optional[BuildConfig]:
        """Get build configuration for a project.
        
        Args:
            project_path: Path to the project directory
            custom_commands: Optional custom build commands
            
        Returns:
            BuildConfig if build system detected, None otherwise
        """
        build_system_name = self.detect_build_system(project_path)
        if not build_system_name:
            return None
        
        build_tool = BuildTool(build_system_name)
        commands = custom_commands or self.default_commands.get(build_tool, [])
        
        # Get environment variables specific to the build tool
        environment = self._get_build_environment(build_tool, project_path)
        
        # Determine output directory
        output_dir = self._get_output_directory(build_tool, project_path)
        
        return BuildConfig(
            build_tool=build_tool,
            commands=commands,
            environment=environment,
            working_directory=project_path,
            output_directory=output_dir
        )
    
    def customize_build_config(self, config: BuildConfig, customizations: Dict[str, Any]) -> BuildConfig:
        """Customize build configuration with user-provided options.
        
        Args:
            config: Base build configuration
            customizations: Dictionary of customization options
            
        Returns:
            Updated build configuration
        """
        # Update commands if provided
        if "commands" in customizations:
            config.commands = customizations["commands"]
        
        # Update environment variables
        if "environment" in customizations:
            config.environment.update(customizations["environment"])
        
        # Update timeout
        if "timeout" in customizations:
            config.timeout = customizations["timeout"]
        
        # Update output directory
        if "output_directory" in customizations:
            config.output_directory = customizations["output_directory"]
        
        logger.info(f"Customized build config for {config.build_tool.value}")
        return config
    
    def execute_build(self, project_path: str, commands: List[str]) -> BuildResult:
        """Execute build commands for a project.
        
        Args:
            project_path: Path to the project directory
            commands: List of build commands to execute
            
        Returns:
            BuildResult with build status and details
        """
        logger.info(f"Starting build execution for project: {project_path}")
        logger.info(f"Build commands: {commands}")
        
        if not os.path.exists(project_path):
            error_msg = f"Project path does not exist: {project_path}"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                project_path=project_path,
                artifacts=[],
                logs=[],
                errors=[error_msg],
                execution_time=0.0
            )
        
        if not commands:
            error_msg = "No build commands provided"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                project_path=project_path,
                artifacts=[],
                logs=[],
                errors=[error_msg],
                execution_time=0.0
            )
        
        # Get build configuration
        build_config = self.get_build_config(project_path, commands)
        if not build_config:
            error_msg = "Could not determine build configuration"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                project_path=project_path,
                artifacts=[],
                logs=[],
                errors=[error_msg],
                execution_time=0.0
            )
        
        build_result = self._execute_build_with_config(build_config)
        
        # Store build result for future reference
        self.store_build_result(build_result)
        
        return build_result
    
    def _execute_build_with_config(self, config: BuildConfig) -> BuildResult:
        """Execute build commands with the given configuration.
        
        Args:
            config: Build configuration containing commands, environment, etc.
            
        Returns:
            BuildResult with build status and details
        """
        import time
        start_time = time.time()
        
        logs = []
        errors = []
        artifacts = []
        
        logger.info(f"Executing build with {config.build_tool.value}")
        logger.info(f"Working directory: {config.working_directory}")
        logger.info(f"Commands: {config.commands}")
        logger.info(f"Timeout: {config.timeout} seconds")
        
        try:
            # Execute each command in sequence
            for i, command in enumerate(config.commands):
                logger.info(f"Executing command {i+1}/{len(config.commands)}: {command}")
                
                command_result = self._execute_single_command(
                    command=command,
                    working_directory=config.working_directory,
                    environment=config.environment,
                    timeout=config.timeout
                )
                
                # Add command logs
                logs.extend(command_result["logs"])
                
                if not command_result["success"]:
                    errors.extend(command_result["errors"])
                    execution_time = time.time() - start_time
                    
                    logger.error(f"Build command failed: {command}")
                    return BuildResult(
                        success=False,
                        project_path=config.working_directory,
                        artifacts=artifacts,
                        logs=logs,
                        errors=errors,
                        execution_time=execution_time
                    )
                
                logger.info(f"Command {i+1} completed successfully")
            
            # Collect build artifacts if build was successful
            artifacts = []
            artifact_report = None
            if config.output_directory:
                artifact_collection = self.artifact_manager.detect_and_collect_artifacts(
                    config.working_directory, 
                    config.build_tool.value,
                    [config.output_directory]
                )
                artifacts = [artifact.relative_path for artifact in artifact_collection.artifacts]
                logger.info(f"Collected {len(artifacts)} build artifacts")
                
                # Generate comprehensive artifact report
                validation_results = self.artifact_manager.validate_artifacts(artifact_collection.artifacts)
                full_report = self.artifact_manager.generate_artifact_report(
                    artifact_collection, validation_results
                )
                artifact_report = {
                    "total_artifacts": full_report.total_artifacts,
                    "valid_artifacts": full_report.valid_artifacts,
                    "invalid_artifacts": full_report.invalid_artifacts,
                    "total_size": full_report.total_size,
                    "validation_summary": full_report.validation_summary,
                    "report_time": full_report.report_time
                }
                
                # Save detailed artifact report to project directory
                report_path = os.path.join(config.working_directory, "build-artifacts-report.json")
                self.artifact_manager.save_artifact_report(full_report, report_path)
                logger.info(f"Detailed artifact report saved to: {report_path}")
            
            execution_time = time.time() - start_time
            logger.info(f"Build completed successfully in {execution_time:.2f} seconds")
            
            return BuildResult(
                success=True,
                project_path=config.working_directory,
                artifacts=artifacts,
                logs=logs,
                errors=errors,
                execution_time=execution_time,
                build_tool=config.build_tool.value,
                artifact_report=artifact_report
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"Unexpected error during build execution: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            return BuildResult(
                success=False,
                project_path=config.working_directory,
                artifacts=artifacts,
                logs=logs,
                errors=errors,
                execution_time=execution_time
            )
    
    def _execute_single_command(self, command: str, working_directory: str, 
                               environment: Dict[str, str], timeout: int) -> Dict[str, Any]:
        """Execute a single build command with monitoring and timeout.
        
        Args:
            command: Command to execute
            working_directory: Directory to run command in
            environment: Environment variables
            timeout: Timeout in seconds
            
        Returns:
            Dictionary with execution results
        """
        import shlex
        import threading
        from queue import Queue, Empty
        
        logs = []
        errors = []
        
        try:
            # Parse command into arguments
            if os.name == 'nt':  # Windows
                # On Windows, use shell=True for better command parsing
                cmd_args = command
                use_shell = True
            else:  # Unix-like systems
                cmd_args = shlex.split(command)
                use_shell = False
            
            logger.debug(f"Parsed command: {cmd_args}")
            
            # Start the process
            process = subprocess.Popen(
                cmd_args,
                cwd=working_directory,
                env=environment,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=use_shell,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Create queues for capturing output
            stdout_queue = Queue()
            stderr_queue = Queue()
            
            # Start threads to capture output
            stdout_thread = threading.Thread(
                target=self._capture_output,
                args=(process.stdout, stdout_queue, "STDOUT")
            )
            stderr_thread = threading.Thread(
                target=self._capture_output,
                args=(process.stderr, stderr_queue, "STDERR")
            )
            
            stdout_thread.daemon = True
            stderr_thread.daemon = True
            stdout_thread.start()
            stderr_thread.start()
            
            # Monitor process with timeout
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                logger.warning(f"Command timed out after {timeout} seconds: {command}")
                process.kill()
                process.wait()
                errors.append(f"Command timed out after {timeout} seconds")
                return {
                    "success": False,
                    "logs": logs,
                    "errors": errors
                }
            
            # Collect all output
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
            
            # Get captured output
            while True:
                try:
                    line = stdout_queue.get_nowait()
                    logs.append(f"[STDOUT] {line}")
                    logger.debug(f"Build output: {line}")
                except Empty:
                    break
            
            while True:
                try:
                    line = stderr_queue.get_nowait()
                    if process.returncode == 0:
                        # If command succeeded, treat stderr as logs (many tools output to stderr)
                        logs.append(f"[STDERR] {line}")
                        logger.debug(f"Build stderr: {line}")
                    else:
                        # If command failed, treat stderr as errors
                        errors.append(f"[STDERR] {line}")
                        logger.warning(f"Build error: {line}")
                except Empty:
                    break
            
            # Check return code
            if process.returncode == 0:
                logger.debug(f"Command completed successfully: {command}")
                return {
                    "success": True,
                    "logs": logs,
                    "errors": errors
                }
            else:
                error_msg = f"Command failed with exit code {process.returncode}: {command}"
                logger.error(error_msg)
                errors.append(error_msg)
                return {
                    "success": False,
                    "logs": logs,
                    "errors": errors
                }
                
        except FileNotFoundError as e:
            error_msg = f"Command not found: {command} - {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            return {
                "success": False,
                "logs": logs,
                "errors": errors
            }
        except Exception as e:
            error_msg = f"Error executing command '{command}': {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            return {
                "success": False,
                "logs": logs,
                "errors": errors
            }
    
    def _capture_output(self, pipe, queue: Queue, stream_name: str):
        """Capture output from a subprocess pipe.
        
        Args:
            pipe: Subprocess pipe (stdout or stderr)
            queue: Queue to store captured lines
            stream_name: Name of the stream for logging
        """
        try:
            for line in iter(pipe.readline, ''):
                if line:
                    queue.put(line.rstrip())
        except Exception as e:
            logger.error(f"Error capturing {stream_name}: {str(e)}")
        finally:
            pipe.close()
    

    
    def get_build_artifacts(self, project_path: str) -> List[str]:
        """Get list of build artifacts.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of paths to build artifacts
        """
        logger.info(f"Getting build artifacts for project: {project_path}")
        
        # Detect build system
        build_system_name = self.detect_build_system(project_path)
        if not build_system_name:
            logger.warning(f"No build system detected for project: {project_path}")
            return []
        
        # Get build configuration to determine output directories
        build_config = self.get_build_config(project_path)
        output_directories = None
        if build_config and build_config.output_directory:
            output_directories = [build_config.output_directory]
        
        # Collect artifacts using artifact manager
        artifact_collection = self.artifact_manager.detect_and_collect_artifacts(
            project_path, build_system_name, output_directories
        )
        
        # Return list of artifact paths
        artifact_paths = [artifact.path for artifact in artifact_collection.artifacts]
        logger.info(f"Found {len(artifact_paths)} build artifacts")
        

        
        return artifact_paths
    
    def validate_build_artifacts(self, project_path: str) -> ArtifactReport:
        """Validate build artifacts and generate a comprehensive report.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            ArtifactReport with validation results
        """
        logger.info(f"Validating build artifacts for project: {project_path}")
        
        # Detect build system
        build_system_name = self.detect_build_system(project_path)
        if not build_system_name:
            logger.warning(f"No build system detected for project: {project_path}")
            # Return empty report
            from ..models.artifacts import ArtifactCollection
            empty_collection = ArtifactCollection(
                project_path=project_path,
                build_tool="unknown",
                artifacts=[],
                total_size=0,
                collection_time=0.0,
                validation_results={"error": "No build system detected"}
            )
            return self.artifact_manager.generate_artifact_report(empty_collection)
        
        # Collect artifacts
        artifact_collection = self.artifact_manager.detect_and_collect_artifacts(
            project_path, build_system_name
        )
        
        # Validate artifacts
        validation_results = self.artifact_manager.validate_artifacts(artifact_collection.artifacts)
        
        # Generate comprehensive report
        report = self.artifact_manager.generate_artifact_report(
            artifact_collection, validation_results
        )
        
        logger.info(f"Artifact validation complete: {report.valid_artifacts}/{report.total_artifacts} valid")
        return report
    
    def package_build_artifacts(self, project_path: str, output_path: str, 
                              package_format: str = "zip") -> bool:
        """Package build artifacts into a single archive.
        
        Args:
            project_path: Path to the project directory
            output_path: Path for the output package
            package_format: Format for packaging ('zip' or 'tar.gz')
            
        Returns:
            True if packaging was successful, False otherwise
        """
        logger.info(f"Packaging build artifacts for project: {project_path}")
        
        # Detect build system
        build_system_name = self.detect_build_system(project_path)
        if not build_system_name:
            logger.error(f"No build system detected for project: {project_path}")
            return False
        
        # Collect artifacts
        artifact_collection = self.artifact_manager.detect_and_collect_artifacts(
            project_path, build_system_name
        )
        
        if not artifact_collection.artifacts:
            logger.warning(f"No artifacts found to package in project: {project_path}")
            return False
        
        # Package artifacts
        packaging_result = self.artifact_manager.package_artifacts(
            artifact_collection.artifacts, output_path, package_format
        )
        
        if packaging_result.success:
            logger.info(f"Artifacts packaged successfully: {output_path}")
        else:
            logger.error(f"Packaging failed: {packaging_result.errors}")
        
        return packaging_result.success
    
    def store_build_result(self, build_result: BuildResult, storage_path: Optional[str] = None) -> bool:
        """Store build result to persistent storage.
        
        Args:
            build_result: Build result to store
            storage_path: Optional custom storage path
            
        Returns:
            True if storage was successful, False otherwise
        """
        try:
            if storage_path is None:
                storage_path = os.path.join(build_result.project_path, "build-result.json")
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(storage_path), exist_ok=True)
            
            # Convert build result to dictionary for JSON serialization
            result_data = {
                "success": build_result.success,
                "project_path": build_result.project_path,
                "artifacts": build_result.artifacts,
                "logs": build_result.logs,
                "errors": build_result.errors,
                "execution_time": build_result.execution_time,
                "build_tool": build_result.build_tool,
                "artifact_report": build_result.artifact_report,
                "packaging_info": build_result.packaging_info,
                "timestamp": time.time()
            }
            
            # Save to JSON file
            with open(storage_path, 'w') as f:
                json.dump(result_data, f, indent=2, default=str)
            
            logger.info(f"Build result stored to: {storage_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error storing build result: {str(e)}", exc_info=True)
            return False
    
    def load_build_result(self, storage_path: str) -> Optional[BuildResult]:
        """Load build result from persistent storage.
        
        Args:
            storage_path: Path to stored build result
            
        Returns:
            BuildResult if loaded successfully, None otherwise
        """
        try:
            if not os.path.exists(storage_path):
                logger.warning(f"Build result file not found: {storage_path}")
                return None
            
            with open(storage_path, 'r') as f:
                result_data = json.load(f)
            
            # Reconstruct BuildResult object
            build_result = BuildResult(
                success=result_data.get("success", False),
                project_path=result_data.get("project_path", ""),
                artifacts=result_data.get("artifacts", []),
                logs=result_data.get("logs", []),
                errors=result_data.get("errors", []),
                execution_time=result_data.get("execution_time", 0.0),
                build_tool=result_data.get("build_tool"),
                artifact_report=result_data.get("artifact_report"),
                packaging_info=result_data.get("packaging_info")
            )
            
            logger.info(f"Build result loaded from: {storage_path}")
            return build_result
            
        except Exception as e:
            logger.error(f"Error loading build result: {str(e)}", exc_info=True)
            return None
    
    def get_build_history(self, project_path: str) -> List[Dict[str, Any]]:
        """Get build history for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of build history entries
        """
        history = []
        
        try:
            # Look for build result files
            build_result_path = os.path.join(project_path, "build-result.json")
            if os.path.exists(build_result_path):
                build_result = self.load_build_result(build_result_path)
                if build_result:
                    history.append({
                        "timestamp": time.time(),  # Use current time as fallback
                        "success": build_result.success,
                        "build_tool": build_result.build_tool,
                        "artifacts_count": len(build_result.artifacts),
                        "execution_time": build_result.execution_time,
                        "errors_count": len(build_result.errors)
                    })
            
            # Look for artifact reports
            artifact_report_path = os.path.join(project_path, "build-artifacts-report.json")
            if os.path.exists(artifact_report_path):
                try:
                    with open(artifact_report_path, 'r') as f:
                        report_data = json.load(f)
                    
                    if history:
                        # Add artifact info to existing entry
                        history[0]["artifact_report"] = {
                            "total_artifacts": report_data.get("total_artifacts", 0),
                            "valid_artifacts": report_data.get("valid_artifacts", 0),
                            "total_size": report_data.get("total_size", 0)
                        }
                except Exception as e:
                    logger.warning(f"Error reading artifact report: {str(e)}")
            
            logger.info(f"Retrieved {len(history)} build history entries for project: {project_path}")
            
        except Exception as e:
            logger.error(f"Error retrieving build history: {str(e)}", exc_info=True)
        
        return history
    
    def generate_build_summary(self, project_path: str) -> Dict[str, Any]:
        """Generate a comprehensive build summary for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with comprehensive build summary
        """
        logger.info(f"Generating build summary for project: {project_path}")
        
        summary = {
            "project_path": project_path,
            "build_system": None,
            "last_build": None,
            "artifacts": {
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "total_size": 0
            },
            "build_history": [],
            "recommendations": []
        }
        
        try:
            # Detect build system
            build_system = self.detect_build_system(project_path)
            summary["build_system"] = build_system
            
            # Get build history
            history = self.get_build_history(project_path)
            summary["build_history"] = history
            
            if history:
                summary["last_build"] = history[0]
            
            # Get current artifact status
            if build_system:
                artifact_collection = self.artifact_manager.detect_and_collect_artifacts(
                    project_path, build_system
                )
                
                summary["artifacts"]["total"] = len(artifact_collection.artifacts)
                summary["artifacts"]["total_size"] = artifact_collection.total_size
                
                # Validate artifacts
                validation_results = self.artifact_manager.validate_artifacts(artifact_collection.artifacts)
                valid_count = sum(1 for result in validation_results if result.is_valid)
                invalid_count = len(validation_results) - valid_count
                
                summary["artifacts"]["valid"] = valid_count
                summary["artifacts"]["invalid"] = invalid_count
            
            # Generate recommendations
            recommendations = []
            
            if not build_system:
                recommendations.append("No build system detected. Consider adding build configuration.")
            elif summary["artifacts"]["total"] == 0:
                recommendations.append("No build artifacts found. Run build commands to generate artifacts.")
            elif summary["artifacts"]["invalid"] > 0:
                recommendations.append(f"{summary['artifacts']['invalid']} invalid artifacts found. Check build process.")
            
            if summary["artifacts"]["total_size"] > 100 * 1024 * 1024:  # 100MB
                recommendations.append("Large artifact size detected. Consider optimizing build output.")
            
            summary["recommendations"] = recommendations
            
            logger.info(f"Build summary generated: {summary['artifacts']['total']} artifacts, "
                       f"{len(recommendations)} recommendations")
            
        except Exception as e:
            logger.error(f"Error generating build summary: {str(e)}", exc_info=True)
            summary["error"] = str(e)
        
        return summary
    
    def export_build_report(self, project_path: str, output_path: str, 
                           include_artifacts: bool = True) -> bool:
        """Export comprehensive build report to file.
        
        Args:
            project_path: Path to the project directory
            output_path: Path for the output report file
            include_artifacts: Whether to include detailed artifact information
            
        Returns:
            True if export was successful, False otherwise
        """
        try:
            logger.info(f"Exporting build report for project: {project_path}")
            
            # Generate build summary
            summary = self.generate_build_summary(project_path)
            
            # Add detailed artifact information if requested
            if include_artifacts and summary.get("build_system"):
                artifact_collection = self.artifact_manager.detect_and_collect_artifacts(
                    project_path, summary["build_system"]
                )
                
                validation_results = self.artifact_manager.validate_artifacts(artifact_collection.artifacts)
                full_report = self.artifact_manager.generate_artifact_report(
                    artifact_collection, validation_results
                )
                
                summary["detailed_artifacts"] = [
                    {
                        "path": artifact.relative_path,
                        "size": artifact.size,
                        "type": artifact.artifact_type.value,
                        "status": artifact.status.value,
                        "checksum": artifact.checksum[:16] + "..." if len(artifact.checksum) > 16 else artifact.checksum
                    }
                    for artifact in full_report.artifacts
                ]
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Save report
            with open(output_path, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            logger.info(f"Build report exported to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting build report: {str(e)}", exc_info=True)
            return False
    
    # Build tool detection methods
    
    def _detect_npm_scripts(self, project_path: str) -> bool:
        """Detect if project uses npm/yarn/pnpm scripts for building."""
        package_json_path = os.path.join(project_path, "package.json")
        if not os.path.exists(package_json_path):
            return False
        
        try:
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
            
            scripts = package_data.get("scripts", {})
            has_build_script = "build" in scripts
            
            # Check for any package manager lock files
            has_lock_file = (
                os.path.exists(os.path.join(project_path, "package-lock.json")) or
                os.path.exists(os.path.join(project_path, "yarn.lock")) or
                os.path.exists(os.path.join(project_path, "pnpm-lock.yaml"))
            )
            
            return has_build_script and has_lock_file
        except (json.JSONDecodeError, IOError):
            return False
    
    def _detect_typescript(self, project_path: str) -> bool:
        """Detect if project uses TypeScript compiler directly."""
        return (os.path.exists(os.path.join(project_path, "tsconfig.json")) and
                not self._has_bundler_config(project_path))
    
    def _detect_webpack(self, project_path: str) -> bool:
        """Detect if project uses Webpack."""
        webpack_configs = ["webpack.config.js", "webpack.config.ts", "webpack.config.mjs"]
        return any(os.path.exists(os.path.join(project_path, config)) for config in webpack_configs)
    
    def _detect_vite(self, project_path: str) -> bool:
        """Detect if project uses Vite."""
        vite_configs = ["vite.config.js", "vite.config.ts", "vite.config.mjs"]
        return any(os.path.exists(os.path.join(project_path, config)) for config in vite_configs)
    
    def _detect_setuptools(self, project_path: str) -> bool:
        """Detect if project uses Python setuptools."""
        return (os.path.exists(os.path.join(project_path, "setup.py")) or
                os.path.exists(os.path.join(project_path, "pyproject.toml")))
    
    def _detect_poetry(self, project_path: str) -> bool:
        """Detect if project uses Poetry."""
        pyproject_path = os.path.join(project_path, "pyproject.toml")
        if not os.path.exists(pyproject_path):
            return False
        
        try:
            import tomli
            with open(pyproject_path, 'rb') as f:
                pyproject_data = tomli.load(f)
            
            return "tool" in pyproject_data and "poetry" in pyproject_data["tool"]
        except (ImportError, Exception):
            # Fallback: check for poetry.lock
            return os.path.exists(os.path.join(project_path, "poetry.lock"))
    
    def _detect_cargo(self, project_path: str) -> bool:
        """Detect if project uses Cargo (Rust)."""
        return os.path.exists(os.path.join(project_path, "Cargo.toml"))
    
    def _detect_go(self, project_path: str) -> bool:
        """Detect if project uses Go modules."""
        return os.path.exists(os.path.join(project_path, "go.mod"))
    
    def _detect_maven(self, project_path: str) -> bool:
        """Detect if project uses Maven."""
        return os.path.exists(os.path.join(project_path, "pom.xml"))
    
    def _detect_gradle(self, project_path: str) -> bool:
        """Detect if project uses Gradle."""
        gradle_files = ["build.gradle", "build.gradle.kts"]
        return any(os.path.exists(os.path.join(project_path, f)) for f in gradle_files)
    
    # Helper methods
    
    def _has_bundler_config(self, project_path: str) -> bool:
        """Check if project has bundler configuration files."""
        bundler_configs = [
            "webpack.config.js", "webpack.config.ts", "webpack.config.mjs",
            "vite.config.js", "vite.config.ts", "vite.config.mjs",
            "rollup.config.js", "rollup.config.ts"
        ]
        return any(os.path.exists(os.path.join(project_path, config)) for config in bundler_configs)
    
    def _get_build_environment(self, build_tool: BuildTool, project_path: str) -> Dict[str, str]:
        """Get environment variables for the build tool.
        
        Args:
            build_tool: The detected build tool
            project_path: Path to the project directory
            
        Returns:
            Dictionary of environment variables
        """
        env = os.environ.copy()
        
        # Add tool-specific environment variables
        if build_tool in [BuildTool.NPM_SCRIPTS, BuildTool.WEBPACK, BuildTool.VITE, BuildTool.TSC]:
            env["NODE_ENV"] = "production"
        elif build_tool == BuildTool.CARGO_BUILD:
            env["CARGO_TARGET_DIR"] = os.path.join(project_path, "target")
        elif build_tool in [BuildTool.PYTHON_SETUPTOOLS, BuildTool.POETRY_BUILD]:
            env["PYTHONPATH"] = project_path
        
        return env
    
    def _get_output_directory(self, build_tool: BuildTool, project_path: str) -> Optional[str]:
        """Get the expected output directory for build artifacts.
        
        Args:
            build_tool: The detected build tool
            project_path: Path to the project directory
            
        Returns:
            Path to output directory if known, None otherwise
        """
        output_dirs = {
            BuildTool.NPM_SCRIPTS: "dist",
            BuildTool.TSC: "dist",
            BuildTool.WEBPACK: "dist",
            BuildTool.VITE: "dist",
            BuildTool.PYTHON_SETUPTOOLS: "dist",
            BuildTool.POETRY_BUILD: "dist",
            BuildTool.CARGO_BUILD: "target/release",
            BuildTool.GO_BUILD: ".",
            BuildTool.MAVEN_BUILD: "target",
            BuildTool.GRADLE_BUILD: "build",
        }
        
        output_dir = output_dirs.get(build_tool)
        if output_dir:
            return os.path.join(project_path, output_dir)
        
        return None