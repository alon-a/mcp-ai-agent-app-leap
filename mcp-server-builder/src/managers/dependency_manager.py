"""Dependency management implementation for MCP Server Builder."""

import os
import json
import subprocess
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from packaging import version

from .interfaces import DependencyManager
from ..models.base import InstallResult, VerificationResult
from ..models.enums import PackageManager


logger = logging.getLogger(__name__)


class DependencyManagerImpl(DependencyManager):
    """Implementation of dependency management for MCP server projects."""
    
    def __init__(self):
        """Initialize the dependency manager."""
        self._package_manager_files = {
            PackageManager.NPM: ["package.json"],
            PackageManager.YARN: ["package.json", "yarn.lock"],
            PackageManager.PNPM: ["package.json", "pnpm-lock.yaml"],
            PackageManager.PIP: ["requirements.txt", "setup.py", "pyproject.toml"],
            PackageManager.POETRY: ["pyproject.toml", "poetry.lock"],
            PackageManager.PIPENV: ["Pipfile", "Pipfile.lock"],
            PackageManager.CARGO: ["Cargo.toml", "Cargo.lock"],
            PackageManager.GO_MOD: ["go.mod", "go.sum"],
            PackageManager.MAVEN: ["pom.xml"],
            PackageManager.GRADLE: ["build.gradle", "build.gradle.kts"]
        }
        
        self._package_manager_commands = {
            PackageManager.NPM: "npm",
            PackageManager.YARN: "yarn",
            PackageManager.PNPM: "pnpm",
            PackageManager.PIP: "pip",
            PackageManager.POETRY: "poetry",
            PackageManager.PIPENV: "pipenv",
            PackageManager.CARGO: "cargo",
            PackageManager.GO_MOD: "go",
            PackageManager.MAVEN: "mvn",
            PackageManager.GRADLE: "gradle"
        }
    
    def detect_package_manager(self, project_path: str) -> Optional[str]:
        """Detect the package manager for a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Package manager name if detected, None otherwise
        """
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                logger.warning(f"Project path does not exist: {project_path}")
                return None
            
            detected_managers = self._detect_all_package_managers(project_dir)
            
            if not detected_managers:
                logger.info(f"No package managers detected in {project_path}")
                return None
            
            # Return the primary package manager based on priority
            primary_manager = self._select_primary_package_manager(detected_managers)
            logger.info(f"Detected package manager: {primary_manager.value}")
            return primary_manager.value
            
        except Exception as e:
            logger.error(f"Error detecting package manager: {e}")
            return None
    
    def detect_multiple_package_managers(self, project_path: str) -> List[str]:
        """Detect all package managers in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            List of detected package manager names
        """
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                return []
            
            detected_managers = self._detect_all_package_managers(project_dir)
            return [manager.value for manager in detected_managers]
            
        except Exception as e:
            logger.error(f"Error detecting multiple package managers: {e}")
            return []
    
    def check_version_compatibility(self, project_path: str, package_manager: str) -> Dict[str, Any]:
        """Check version compatibility for a package manager.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager to check
            
        Returns:
            Dictionary with compatibility information
        """
        try:
            pm_enum = PackageManager(package_manager)
            command = self._package_manager_commands[pm_enum]
            
            # Check if package manager is installed
            if not self._is_command_available(command):
                return {
                    "compatible": False,
                    "installed": False,
                    "version": None,
                    "min_version": None,
                    "error": f"{command} is not installed or not in PATH"
                }
            
            # Get installed version
            installed_version = self._get_package_manager_version(command)
            min_version = self._get_minimum_version(pm_enum)
            
            compatible = True
            if installed_version and min_version:
                try:
                    compatible = version.parse(installed_version) >= version.parse(min_version)
                except Exception as e:
                    logger.warning(f"Error comparing versions: {e}")
                    compatible = True  # Assume compatible if we can't parse
            
            return {
                "compatible": compatible,
                "installed": True,
                "version": installed_version,
                "min_version": min_version,
                "error": None if compatible else f"Version {installed_version} is below minimum {min_version}"
            }
            
        except ValueError:
            return {
                "compatible": False,
                "installed": False,
                "version": None,
                "min_version": None,
                "error": f"Unsupported package manager: {package_manager}"
            }
        except Exception as e:
            return {
                "compatible": False,
                "installed": False,
                "version": None,
                "min_version": None,
                "error": str(e)
            }
    
    def install_dependencies(self, project_path: str, dependencies: List[str]) -> InstallResult:
        """Install project dependencies.
        
        Args:
            project_path: Path to the project directory
            dependencies: List of dependencies to install
            
        Returns:
            InstallResult with installation status and details
        """
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                return InstallResult(
                    success=False,
                    installed_packages=[],
                    failed_packages=dependencies,
                    errors=[f"Project path does not exist: {project_path}"]
                )
            
            # Detect package manager
            package_manager = self.detect_package_manager(project_path)
            if not package_manager:
                return InstallResult(
                    success=False,
                    installed_packages=[],
                    failed_packages=dependencies,
                    errors=["No package manager detected in project"]
                )
            
            # Install dependencies using detected package manager
            return self._install_with_package_manager(
                project_path, PackageManager(package_manager), dependencies
            )
            
        except Exception as e:
            logger.error(f"Error installing dependencies: {e}")
            return InstallResult(
                success=False,
                installed_packages=[],
                failed_packages=dependencies,
                errors=[str(e)]
            )
    
    def install_dependencies_with_manager(self, project_path: str, package_manager: str, 
                                        dependencies: List[str], 
                                        custom_sources: Optional[List[str]] = None,
                                        registry_config: Optional[Dict[str, Any]] = None) -> InstallResult:
        """Install dependencies with a specific package manager.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager to use
            dependencies: List of dependencies to install
            custom_sources: Optional list of custom package sources/registries
            registry_config: Optional registry configuration (auth, scopes, etc.)
            
        Returns:
            InstallResult with installation status and details
        """
        try:
            pm_enum = PackageManager(package_manager)
            return self._install_with_package_manager(
                project_path, pm_enum, dependencies, custom_sources, registry_config
            )
        except ValueError:
            return InstallResult(
                success=False,
                installed_packages=[],
                failed_packages=dependencies,
                errors=[f"Unsupported package manager: {package_manager}"]
            )
        except Exception as e:
            logger.error(f"Error installing dependencies with {package_manager}: {e}")
            return InstallResult(
                success=False,
                installed_packages=[],
                failed_packages=dependencies,
                errors=[str(e)]
            )
    
    def resolve_dependency_conflicts(self, project_path: str) -> Dict[str, Any]:
        """Resolve dependency conflicts in a project.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with conflict resolution information
        """
        try:
            package_manager = self.detect_package_manager(project_path)
            if not package_manager:
                return {
                    "success": False,
                    "conflicts": [],
                    "resolutions": [],
                    "error": "No package manager detected"
                }
            
            pm_enum = PackageManager(package_manager)
            return self._resolve_conflicts_for_manager(project_path, pm_enum)
            
        except Exception as e:
            logger.error(f"Error resolving dependency conflicts: {e}")
            return {
                "success": False,
                "conflicts": [],
                "resolutions": [],
                "error": str(e)
            }
    
    def scan_security_vulnerabilities(self, project_path: str) -> Dict[str, Any]:
        """Scan installed packages for security vulnerabilities.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with security scan results
        """
        try:
            package_manager = self.detect_package_manager(project_path)
            if not package_manager:
                return {
                    "success": False,
                    "vulnerabilities": [],
                    "error": "No package manager detected"
                }
            
            pm_enum = PackageManager(package_manager)
            return self._scan_vulnerabilities_for_manager(project_path, pm_enum)
            
        except Exception as e:
            logger.error(f"Error scanning security vulnerabilities: {e}")
            return {
                "success": False,
                "vulnerabilities": [],
                "error": str(e)
            }
    
    def validate_dependency_compatibility(self, project_path: str) -> Dict[str, Any]:
        """Validate compatibility of installed dependencies.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            Dictionary with compatibility validation results
        """
        try:
            package_manager = self.detect_package_manager(project_path)
            if not package_manager:
                return {
                    "success": False,
                    "compatible": False,
                    "issues": [],
                    "error": "No package manager detected"
                }
            
            pm_enum = PackageManager(package_manager)
            return self._validate_compatibility_for_manager(project_path, pm_enum)
            
        except Exception as e:
            logger.error(f"Error validating dependency compatibility: {e}")
            return {
                "success": False,
                "compatible": False,
                "issues": [],
                "error": str(e)
            }
    
    def verify_installation(self, project_path: str) -> VerificationResult:
        """Verify that dependencies are properly installed.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            VerificationResult with verification status and details
        """
        try:
            project_dir = Path(project_path)
            if not project_dir.exists():
                return VerificationResult(
                    success=False,
                    verified_packages=[],
                    missing_packages=[],
                    errors=[f"Project path does not exist: {project_path}"]
                )
            
            # Detect package manager
            package_manager = self.detect_package_manager(project_path)
            if not package_manager:
                return VerificationResult(
                    success=False,
                    verified_packages=[],
                    missing_packages=[],
                    errors=["No package manager detected in project"]
                )
            
            pm_enum = PackageManager(package_manager)
            
            # Get expected dependencies from project files
            expected_deps = self._get_expected_dependencies(project_path, pm_enum)
            
            # Verify each dependency
            verified_packages = []
            missing_packages = []
            errors = []
            
            for dep_name, dep_version in expected_deps.items():
                verification_result = self._verify_single_dependency(
                    project_path, pm_enum, dep_name, dep_version
                )
                
                if verification_result["installed"]:
                    verified_packages.append(dep_name)
                else:
                    missing_packages.append(dep_name)
                    if verification_result["error"]:
                        errors.append(verification_result["error"])
            
            # Perform additional health checks
            health_check_result = self._perform_dependency_health_checks(project_path, pm_enum)
            if health_check_result["errors"]:
                errors.extend(health_check_result["errors"])
            
            success = len(missing_packages) == 0 and len(errors) == 0
            
            return VerificationResult(
                success=success,
                verified_packages=verified_packages,
                missing_packages=missing_packages,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Error verifying installation: {e}")
            return VerificationResult(
                success=False,
                verified_packages=[],
                missing_packages=[],
                errors=[str(e)]
            )
    
    def _detect_all_package_managers(self, project_dir: Path) -> Set[PackageManager]:
        """Detect all package managers in a project directory.
        
        Args:
            project_dir: Path to the project directory
            
        Returns:
            Set of detected package managers
        """
        detected = set()
        
        for manager, files in self._package_manager_files.items():
            for file_name in files:
                file_path = project_dir / file_name
                if file_path.exists():
                    # Additional validation for specific package managers
                    if self._validate_package_manager_file(manager, file_path):
                        detected.add(manager)
                        break  # Found one file for this manager, no need to check others
        
        return detected
    
    def _validate_package_manager_file(self, manager: PackageManager, file_path: Path) -> bool:
        """Validate that a file actually belongs to the specified package manager.
        
        Args:
            manager: Package manager to validate
            file_path: Path to the file to validate
            
        Returns:
            True if the file is valid for the package manager
        """
        try:
            if manager == PackageManager.POETRY and file_path.name == "pyproject.toml":
                # Check if pyproject.toml contains poetry configuration
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    return '[tool.poetry]' in content
            
            elif manager == PackageManager.YARN and file_path.name == "package.json":
                # Check if yarn.lock exists alongside package.json
                yarn_lock = file_path.parent / "yarn.lock"
                return yarn_lock.exists()
            
            elif manager == PackageManager.PNPM and file_path.name == "package.json":
                # Check if pnpm-lock.yaml exists alongside package.json
                pnpm_lock = file_path.parent / "pnpm-lock.yaml"
                return pnpm_lock.exists()
            
            # For other cases, existence of the file is sufficient
            return True
            
        except Exception as e:
            logger.warning(f"Error validating package manager file {file_path}: {e}")
            return True  # Assume valid if we can't validate
    
    def _select_primary_package_manager(self, detected_managers: Set[PackageManager]) -> PackageManager:
        """Select the primary package manager from detected ones.
        
        Args:
            detected_managers: Set of detected package managers
            
        Returns:
            Primary package manager based on priority
        """
        # Priority order (higher priority first)
        priority_order = [
            PackageManager.POETRY,  # Python: Poetry over pip
            PackageManager.YARN,    # Node.js: Yarn over npm
            PackageManager.PNPM,    # Node.js: pnpm over npm
            PackageManager.CARGO,   # Rust
            PackageManager.GO_MOD,  # Go
            PackageManager.MAVEN,   # Java: Maven over Gradle
            PackageManager.GRADLE,  # Java
            PackageManager.NPM,     # Node.js: npm as fallback
            PackageManager.PIP,     # Python: pip as fallback
            PackageManager.PIPENV,  # Python: pipenv
        ]
        
        for manager in priority_order:
            if manager in detected_managers:
                return manager
        
        # Fallback to first detected if none match priority
        return next(iter(detected_managers))
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in the system PATH.
        
        Args:
            command: Command to check
            
        Returns:
            True if command is available
        """
        try:
            subprocess.run([command, "--version"], 
                         capture_output=True, 
                         check=False, 
                         timeout=10)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
            return False
    
    def _get_package_manager_version(self, command: str) -> Optional[str]:
        """Get the version of a package manager.
        
        Args:
            command: Package manager command
            
        Returns:
            Version string if available
        """
        try:
            result = subprocess.run([command, "--version"], 
                                  capture_output=True, 
                                  text=True, 
                                  check=False, 
                                  timeout=10)
            
            if result.returncode == 0:
                version_output = result.stdout.strip()
                # Extract version number from output
                return self._extract_version_number(version_output)
            
        except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as e:
            logger.warning(f"Error getting version for {command}: {e}")
        
        return None
    
    def _extract_version_number(self, version_output: str) -> Optional[str]:
        """Extract version number from version command output.
        
        Args:
            version_output: Output from version command
            
        Returns:
            Extracted version number
        """
        import re
        
        # Common version patterns
        patterns = [
            r'(\d+\.\d+\.\d+)',  # x.y.z
            r'v(\d+\.\d+\.\d+)', # vx.y.z
            r'(\d+\.\d+)',       # x.y
        ]
        
        for pattern in patterns:
            match = re.search(pattern, version_output)
            if match:
                return match.group(1)
        
        return None
    
    def _get_minimum_version(self, package_manager: PackageManager) -> Optional[str]:
        """Get minimum required version for a package manager.
        
        Args:
            package_manager: Package manager enum
            
        Returns:
            Minimum version string
        """
        min_versions = {
            PackageManager.NPM: "6.0.0",
            PackageManager.YARN: "1.22.0",
            PackageManager.PNPM: "6.0.0",
            PackageManager.PIP: "20.0.0",
            PackageManager.POETRY: "1.0.0",
            PackageManager.PIPENV: "2020.0.0",
            PackageManager.CARGO: "1.50.0",
            PackageManager.GO_MOD: "1.16.0",
            PackageManager.MAVEN: "3.6.0",
            PackageManager.GRADLE: "6.0.0"
        }
        
        return min_versions.get(package_manager)
    
    def _install_with_package_manager(self, project_path: str, package_manager: PackageManager,
                                    dependencies: List[str], 
                                    custom_sources: Optional[List[str]] = None,
                                    registry_config: Optional[Dict[str, Any]] = None) -> InstallResult:
        """Install dependencies with a specific package manager.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            dependencies: List of dependencies to install
            custom_sources: Optional list of custom package sources
            registry_config: Optional registry configuration (auth, scopes, etc.)
            
        Returns:
            InstallResult with installation status and details
        """
        command = self._package_manager_commands[package_manager]
        
        # Check if package manager is available
        if not self._is_command_available(command):
            return InstallResult(
                success=False,
                installed_packages=[],
                failed_packages=dependencies,
                errors=[f"{command} is not installed or not in PATH"]
            )
        
        installed_packages = []
        failed_packages = []
        errors = []
        
        # Configure custom registries if provided
        if custom_sources or registry_config:
            self._configure_custom_registries(project_path, package_manager, custom_sources, registry_config)
        
        # Install dependencies one by one for better error tracking
        for dependency in dependencies:
            try:
                install_cmd = self._build_install_command(
                    package_manager, dependency, custom_sources
                )
                
                result = subprocess.run(
                    install_cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout per package
                )
                
                if result.returncode == 0:
                    installed_packages.append(dependency)
                    logger.info(f"Successfully installed {dependency}")
                else:
                    failed_packages.append(dependency)
                    error_msg = f"Failed to install {dependency}: {result.stderr.strip()}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except subprocess.TimeoutExpired:
                failed_packages.append(dependency)
                error_msg = f"Timeout installing {dependency}"
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                failed_packages.append(dependency)
                error_msg = f"Error installing {dependency}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        success = len(failed_packages) == 0
        return InstallResult(
            success=success,
            installed_packages=installed_packages,
            failed_packages=failed_packages,
            errors=errors
        )
    
    def _build_install_command(self, package_manager: PackageManager, dependency: str,
                             custom_sources: Optional[List[str]] = None) -> List[str]:
        """Build the install command for a specific package manager.
        
        Args:
            package_manager: Package manager enum
            dependency: Dependency to install
            custom_sources: Optional custom sources
            
        Returns:
            List of command arguments
        """
        base_command = self._package_manager_commands[package_manager]
        
        if package_manager == PackageManager.NPM:
            cmd = [base_command, "install", dependency]
            if custom_sources:
                for source in custom_sources:
                    cmd.extend(["--registry", source])
        
        elif package_manager == PackageManager.YARN:
            cmd = [base_command, "add", dependency]
            if custom_sources:
                for source in custom_sources:
                    cmd.extend(["--registry", source])
        
        elif package_manager == PackageManager.PNPM:
            cmd = [base_command, "add", dependency]
            if custom_sources:
                for source in custom_sources:
                    cmd.extend(["--registry", source])
        
        elif package_manager == PackageManager.PIP:
            cmd = [base_command, "install", dependency]
            if custom_sources:
                for source in custom_sources:
                    cmd.extend(["-i", source])
        
        elif package_manager == PackageManager.POETRY:
            cmd = [base_command, "add", dependency]
            if custom_sources:
                # Poetry uses different syntax for custom sources
                cmd.extend(["--source", custom_sources[0]])
        
        elif package_manager == PackageManager.PIPENV:
            cmd = [base_command, "install", dependency]
            if custom_sources:
                cmd.extend(["-i", custom_sources[0]])
        
        elif package_manager == PackageManager.CARGO:
            cmd = [base_command, "add", dependency]
            # Cargo doesn't support custom registries in the same way
        
        elif package_manager == PackageManager.GO_MOD:
            cmd = [base_command, "get", dependency]
            # Go modules use GOPROXY environment variable for custom sources
        
        elif package_manager == PackageManager.MAVEN:
            # Maven dependencies are typically added to pom.xml, not via command line
            cmd = [base_command, "dependency:get", f"-Dartifact={dependency}"]
        
        elif package_manager == PackageManager.GRADLE:
            # Gradle dependencies are typically added to build.gradle, not via command line
            # This is a simplified approach
            cmd = [base_command, "dependencies", "--configuration", "compileClasspath"]
        
        else:
            raise ValueError(f"Unsupported package manager: {package_manager}")
        
        return cmd
    
    def _resolve_conflicts_for_manager(self, project_path: str, 
                                     package_manager: PackageManager) -> Dict[str, Any]:
        """Resolve dependency conflicts for a specific package manager.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            
        Returns:
            Dictionary with conflict resolution information
        """
        command = self._package_manager_commands[package_manager]
        
        try:
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                # Check for npm audit or yarn audit
                audit_cmd = [command, "audit"]
                
                result = subprocess.run(
                    audit_cmd,
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                conflicts = self._parse_npm_audit_output(result.stdout)
                
            elif package_manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
                # Use pip-check or similar tools
                conflicts = self._check_python_conflicts(project_path, package_manager)
                
            else:
                # For other package managers, return empty conflicts for now
                conflicts = []
            
            return {
                "success": True,
                "conflicts": conflicts,
                "resolutions": self._suggest_conflict_resolutions(conflicts),
                "error": None
            }
            
        except Exception as e:
            return {
                "success": False,
                "conflicts": [],
                "resolutions": [],
                "error": str(e)
            }
    
    def _parse_npm_audit_output(self, audit_output: str) -> List[Dict[str, Any]]:
        """Parse npm audit output to extract conflicts.
        
        Args:
            audit_output: Output from npm audit command
            
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        try:
            # Try to parse as JSON first
            audit_data = json.loads(audit_output)
            
            if "vulnerabilities" in audit_data:
                for vuln_name, vuln_data in audit_data["vulnerabilities"].items():
                    conflicts.append({
                        "package": vuln_name,
                        "type": "security",
                        "severity": vuln_data.get("severity", "unknown"),
                        "description": vuln_data.get("title", "Security vulnerability")
                    })
        except json.JSONDecodeError:
            # Fallback to text parsing
            lines = audit_output.split('\n')
            for line in lines:
                if "vulnerability" in line.lower() or "conflict" in line.lower():
                    conflicts.append({
                        "package": "unknown",
                        "type": "unknown",
                        "severity": "unknown",
                        "description": line.strip()
                    })
        
        return conflicts
    
    def _check_python_conflicts(self, project_path: str, 
                              package_manager: PackageManager) -> List[Dict[str, Any]]:
        """Check for Python dependency conflicts.
        
        Args:
            project_path: Path to the project directory
            package_manager: Python package manager
            
        Returns:
            List of conflict dictionaries
        """
        conflicts = []
        
        try:
            if package_manager == PackageManager.PIP:
                # Use pip check command
                result = subprocess.run(
                    ["pip", "check"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            conflicts.append({
                                "package": "unknown",
                                "type": "dependency",
                                "severity": "error",
                                "description": line.strip()
                            })
            
            elif package_manager == PackageManager.POETRY:
                # Use poetry check command
                result = subprocess.run(
                    ["poetry", "check"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode != 0:
                    conflicts.append({
                        "package": "poetry",
                        "type": "configuration",
                        "severity": "error",
                        "description": result.stdout.strip()
                    })
        
        except Exception as e:
            logger.warning(f"Error checking Python conflicts: {e}")
        
        return conflicts
    
    def _suggest_conflict_resolutions(self, conflicts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Suggest resolutions for dependency conflicts.
        
        Args:
            conflicts: List of detected conflicts
            
        Returns:
            List of suggested resolutions
        """
        resolutions = []
        
        for conflict in conflicts:
            conflict_type = conflict.get("type", "unknown")
            package = conflict.get("package", "unknown")
            severity = conflict.get("severity", "unknown")
            
            if conflict_type == "security":
                if severity in ["high", "critical"]:
                    resolutions.append({
                        "package": package,
                        "action": "update",
                        "description": f"Update {package} to latest secure version",
                        "command": self._get_update_command(package),
                        "priority": "high"
                    })
                else:
                    resolutions.append({
                        "package": package,
                        "action": "audit_fix",
                        "description": f"Run audit fix for {package}",
                        "command": self._get_audit_fix_command(),
                        "priority": "medium"
                    })
            
            elif conflict_type == "dependency":
                resolutions.append({
                    "package": package,
                    "action": "resolve_version",
                    "description": f"Resolve version conflict for {package}",
                    "command": self._get_resolve_command(package),
                    "priority": "medium"
                })
            
            elif conflict_type == "configuration":
                resolutions.append({
                    "package": package,
                    "action": "fix_config",
                    "description": f"Fix configuration issues for {package}",
                    "command": self._get_config_fix_command(package),
                    "priority": "low"
                })
        
        return resolutions
    
    def _get_update_command(self, package: str) -> str:
        """Get update command for a package.
        
        Args:
            package: Package name
            
        Returns:
            Update command string
        """
        # This would be determined by the detected package manager
        return f"npm update {package}"
    
    def _get_audit_fix_command(self) -> str:
        """Get audit fix command.
        
        Returns:
            Audit fix command string
        """
        return "npm audit fix"
    
    def _get_resolve_command(self, package: str) -> str:
        """Get resolve command for a package.
        
        Args:
            package: Package name
            
        Returns:
            Resolve command string
        """
        return f"npm ls {package}"
    
    def _get_config_fix_command(self, package: str) -> str:
        """Get configuration fix command.
        
        Args:
            package: Package name
            
        Returns:
            Configuration fix command string
        """
        return f"poetry check --fix"
    
    def _configure_custom_registries(self, project_path: str, package_manager: PackageManager,
                                   custom_sources: Optional[List[str]] = None,
                                   registry_config: Optional[Dict[str, Any]] = None) -> None:
        """Configure custom registries for package managers.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            custom_sources: List of custom registry URLs
            registry_config: Registry configuration (auth, scopes, etc.)
        """
        try:
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                self._configure_npm_registries(project_path, custom_sources, registry_config)
            
            elif package_manager in [PackageManager.PIP, PackageManager.PIPENV]:
                self._configure_pip_registries(project_path, custom_sources, registry_config)
            
            elif package_manager == PackageManager.POETRY:
                self._configure_poetry_registries(project_path, custom_sources, registry_config)
            
            elif package_manager == PackageManager.CARGO:
                self._configure_cargo_registries(project_path, custom_sources, registry_config)
            
            elif package_manager == PackageManager.GO_MOD:
                self._configure_go_registries(project_path, custom_sources, registry_config)
                
        except Exception as e:
            logger.warning(f"Error configuring custom registries: {e}")
    
    def _configure_npm_registries(self, project_path: str, custom_sources: Optional[List[str]],
                                registry_config: Optional[Dict[str, Any]]) -> None:
        """Configure npm/yarn/pnpm registries.
        
        Args:
            project_path: Path to the project directory
            custom_sources: List of registry URLs
            registry_config: Registry configuration
        """
        if not custom_sources:
            return
        
        npmrc_path = Path(project_path) / ".npmrc"
        npmrc_content = []
        
        # Set primary registry
        if custom_sources:
            npmrc_content.append(f"registry={custom_sources[0]}")
        
        # Add scoped registries
        if registry_config and "scoped_registries" in registry_config:
            for scope, registry in registry_config["scoped_registries"].items():
                npmrc_content.append(f"@{scope}:registry={registry}")
        
        # Add authentication if provided
        if registry_config and "auth_tokens" in registry_config:
            for registry, token in registry_config["auth_tokens"].items():
                # Extract hostname from registry URL
                from urllib.parse import urlparse
                hostname = urlparse(registry).netloc
                npmrc_content.append(f"//{hostname}/:_authToken={token}")
        
        # Write .npmrc file
        if npmrc_content:
            with open(npmrc_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(npmrc_content))
            logger.info(f"Configured npm registry settings in {npmrc_path}")
    
    def _configure_pip_registries(self, project_path: str, custom_sources: Optional[List[str]],
                                registry_config: Optional[Dict[str, Any]]) -> None:
        """Configure pip registries.
        
        Args:
            project_path: Path to the project directory
            custom_sources: List of registry URLs
            registry_config: Registry configuration
        """
        if not custom_sources:
            return
        
        pip_conf_path = Path(project_path) / "pip.conf"
        pip_content = ["[global]"]
        
        # Set primary index URL
        pip_content.append(f"index-url = {custom_sources[0]}")
        
        # Add extra index URLs
        if len(custom_sources) > 1:
            extra_urls = " ".join(custom_sources[1:])
            pip_content.append(f"extra-index-url = {extra_urls}")
        
        # Add trusted hosts if provided
        if registry_config and "trusted_hosts" in registry_config:
            trusted_hosts = " ".join(registry_config["trusted_hosts"])
            pip_content.append(f"trusted-host = {trusted_hosts}")
        
        # Write pip.conf file
        with open(pip_conf_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(pip_content))
        logger.info(f"Configured pip registry settings in {pip_conf_path}")
    
    def _configure_poetry_registries(self, project_path: str, custom_sources: Optional[List[str]],
                                   registry_config: Optional[Dict[str, Any]]) -> None:
        """Configure poetry registries.
        
        Args:
            project_path: Path to the project directory
            custom_sources: List of registry URLs
            registry_config: Registry configuration
        """
        if not custom_sources:
            return
        
        # Poetry uses pyproject.toml for registry configuration
        pyproject_path = Path(project_path) / "pyproject.toml"
        
        try:
            import toml
            
            # Read existing pyproject.toml or create new one
            if pyproject_path.exists():
                with open(pyproject_path, 'r', encoding='utf-8') as f:
                    pyproject_data = toml.load(f)
            else:
                pyproject_data = {}
            
            # Add tool.poetry.source section
            if "tool" not in pyproject_data:
                pyproject_data["tool"] = {}
            if "poetry" not in pyproject_data["tool"]:
                pyproject_data["tool"]["poetry"] = {}
            if "source" not in pyproject_data["tool"]["poetry"]:
                pyproject_data["tool"]["poetry"]["source"] = []
            
            # Add custom sources
            for i, source_url in enumerate(custom_sources):
                source_name = f"custom-{i+1}"
                source_config = {
                    "name": source_name,
                    "url": source_url
                }
                
                # Set first source as default
                if i == 0:
                    source_config["default"] = True
                
                pyproject_data["tool"]["poetry"]["source"].append(source_config)
            
            # Write updated pyproject.toml
            with open(pyproject_path, 'w', encoding='utf-8') as f:
                toml.dump(pyproject_data, f)
            
            logger.info(f"Configured poetry registry settings in {pyproject_path}")
            
        except ImportError:
            logger.warning("toml package not available, skipping poetry registry configuration")
        except Exception as e:
            logger.error(f"Error configuring poetry registries: {e}")
    
    def _configure_cargo_registries(self, project_path: str, custom_sources: Optional[List[str]],
                                  registry_config: Optional[Dict[str, Any]]) -> None:
        """Configure cargo registries.
        
        Args:
            project_path: Path to the project directory
            custom_sources: List of registry URLs
            registry_config: Registry configuration
        """
        if not custom_sources:
            return
        
        cargo_config_dir = Path(project_path) / ".cargo"
        cargo_config_dir.mkdir(exist_ok=True)
        cargo_config_path = cargo_config_dir / "config.toml"
        
        try:
            import toml
            
            cargo_config = {}
            
            # Add custom registries
            if "registries" not in cargo_config:
                cargo_config["registries"] = {}
            
            for i, source_url in enumerate(custom_sources):
                registry_name = f"custom-{i+1}"
                cargo_config["registries"][registry_name] = {
                    "index": source_url
                }
            
            # Write cargo config
            with open(cargo_config_path, 'w', encoding='utf-8') as f:
                toml.dump(cargo_config, f)
            
            logger.info(f"Configured cargo registry settings in {cargo_config_path}")
            
        except ImportError:
            logger.warning("toml package not available, skipping cargo registry configuration")
        except Exception as e:
            logger.error(f"Error configuring cargo registries: {e}")
    
    def _configure_go_registries(self, project_path: str, custom_sources: Optional[List[str]],
                               registry_config: Optional[Dict[str, Any]]) -> None:
        """Configure Go module registries.
        
        Args:
            project_path: Path to the project directory
            custom_sources: List of registry URLs
            registry_config: Registry configuration
        """
        if not custom_sources:
            return
        
        # Go uses environment variables for proxy configuration
        # We'll create a .env file with the configuration
        env_path = Path(project_path) / ".env"
        env_content = []
        
        # Set GOPROXY
        if custom_sources:
            goproxy = ",".join(custom_sources)
            env_content.append(f"GOPROXY={goproxy}")
        
        # Set GOSUMDB if provided
        if registry_config and "sumdb" in registry_config:
            env_content.append(f"GOSUMDB={registry_config['sumdb']}")
        
        # Set GOPRIVATE if provided
        if registry_config and "private_modules" in registry_config:
            goprivate = ",".join(registry_config["private_modules"])
            env_content.append(f"GOPRIVATE={goprivate}")
        
        # Write .env file
        if env_content:
            with open(env_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            logger.info(f"Configured Go module settings in {env_path}")
    
    def install_with_conflict_resolution(self, project_path: str, dependencies: List[str],
                                       resolution_strategy: str = "auto") -> InstallResult:
        """Install dependencies with automatic conflict resolution.
        
        Args:
            project_path: Path to the project directory
            dependencies: List of dependencies to install
            resolution_strategy: Strategy for resolving conflicts ("auto", "manual", "strict")
            
        Returns:
            InstallResult with installation status and conflict resolution details
        """
        try:
            # First, try normal installation
            initial_result = self.install_dependencies(project_path, dependencies)
            
            if initial_result.success:
                return initial_result
            
            # If installation failed, check for conflicts
            conflicts_info = self.resolve_dependency_conflicts(project_path)
            
            if not conflicts_info["success"] or not conflicts_info["conflicts"]:
                # No conflicts detected, return original error
                return initial_result
            
            logger.info(f"Detected {len(conflicts_info['conflicts'])} conflicts, attempting resolution")
            
            # Apply conflict resolutions based on strategy
            if resolution_strategy == "auto":
                resolution_result = self._apply_automatic_resolutions(
                    project_path, conflicts_info["resolutions"]
                )
            elif resolution_strategy == "strict":
                # In strict mode, fail if any conflicts exist
                return InstallResult(
                    success=False,
                    installed_packages=[],
                    failed_packages=dependencies,
                    errors=[f"Strict mode: {len(conflicts_info['conflicts'])} conflicts detected"]
                )
            else:
                # Manual mode - return conflicts for user to resolve
                return InstallResult(
                    success=False,
                    installed_packages=[],
                    failed_packages=dependencies,
                    errors=[f"Manual resolution required for {len(conflicts_info['conflicts'])} conflicts"]
                )
            
            if resolution_result["success"]:
                # Retry installation after conflict resolution
                retry_result = self.install_dependencies(project_path, dependencies)
                
                # Merge results
                return InstallResult(
                    success=retry_result.success,
                    installed_packages=retry_result.installed_packages,
                    failed_packages=retry_result.failed_packages,
                    errors=retry_result.errors + resolution_result.get("errors", [])
                )
            else:
                return InstallResult(
                    success=False,
                    installed_packages=[],
                    failed_packages=dependencies,
                    errors=initial_result.errors + resolution_result.get("errors", [])
                )
                
        except Exception as e:
            logger.error(f"Error in conflict resolution installation: {e}")
            return InstallResult(
                success=False,
                installed_packages=[],
                failed_packages=dependencies,
                errors=[str(e)]
            )
    
    def _apply_automatic_resolutions(self, project_path: str, 
                                   resolutions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply automatic conflict resolutions.
        
        Args:
            project_path: Path to the project directory
            resolutions: List of resolution suggestions
            
        Returns:
            Dictionary with resolution results
        """
        applied_resolutions = []
        errors = []
        
        # Sort resolutions by priority
        sorted_resolutions = sorted(resolutions, 
                                  key=lambda x: {"high": 3, "medium": 2, "low": 1}.get(x.get("priority", "low"), 1),
                                  reverse=True)
        
        for resolution in sorted_resolutions:
            try:
                action = resolution.get("action")
                command = resolution.get("command")
                package = resolution.get("package")
                
                if not command:
                    continue
                
                logger.info(f"Applying resolution for {package}: {action}")
                
                # Execute resolution command
                result = subprocess.run(
                    command.split(),
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0:
                    applied_resolutions.append({
                        "package": package,
                        "action": action,
                        "success": True
                    })
                    logger.info(f"Successfully applied resolution for {package}")
                else:
                    error_msg = f"Failed to apply resolution for {package}: {result.stderr.strip()}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    
            except subprocess.TimeoutExpired:
                error_msg = f"Timeout applying resolution for {package}"
                errors.append(error_msg)
                logger.error(error_msg)
            except Exception as e:
                error_msg = f"Error applying resolution for {package}: {str(e)}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        return {
            "success": len(errors) == 0,
            "applied_resolutions": applied_resolutions,
            "errors": errors
        } 
   
    def _get_expected_dependencies(self, project_path: str, package_manager: PackageManager) -> Dict[str, Optional[str]]:
        """Get expected dependencies from project configuration files.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            
        Returns:
            Dictionary mapping dependency names to expected versions
        """
        expected_deps = {}
        project_dir = Path(project_path)
        
        try:
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                package_json_path = project_dir / "package.json"
                if package_json_path.exists():
                    with open(package_json_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                    
                    # Get dependencies and devDependencies
                    for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                        if dep_type in package_data:
                            expected_deps.update(package_data[dep_type])
            
            elif package_manager == PackageManager.PIP:
                requirements_path = project_dir / "requirements.txt"
                if requirements_path.exists():
                    with open(requirements_path, 'r', encoding='utf-8') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Parse requirement line (e.g., "requests==2.28.0" or "requests>=2.0.0")
                                import re
                                match = re.match(r'^([a-zA-Z0-9_-]+)([><=!]+.*)?$', line)
                                if match:
                                    dep_name = match.group(1)
                                    dep_version = match.group(2) if match.group(2) else None
                                    expected_deps[dep_name] = dep_version
            
            elif package_manager == PackageManager.POETRY:
                pyproject_path = project_dir / "pyproject.toml"
                if pyproject_path.exists():
                    try:
                        import toml
                        with open(pyproject_path, 'r', encoding='utf-8') as f:
                            pyproject_data = toml.load(f)
                        
                        if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
                            poetry_config = pyproject_data["tool"]["poetry"]
                            for dep_type in ["dependencies", "dev-dependencies"]:
                                if dep_type in poetry_config:
                                    expected_deps.update(poetry_config[dep_type])
                    except ImportError:
                        logger.warning("toml package not available for parsing pyproject.toml")
            
            elif package_manager == PackageManager.CARGO:
                cargo_toml_path = project_dir / "Cargo.toml"
                if cargo_toml_path.exists():
                    try:
                        import toml
                        with open(cargo_toml_path, 'r', encoding='utf-8') as f:
                            cargo_data = toml.load(f)
                        
                        for dep_type in ["dependencies", "dev-dependencies", "build-dependencies"]:
                            if dep_type in cargo_data:
                                expected_deps.update(cargo_data[dep_type])
                    except ImportError:
                        logger.warning("toml package not available for parsing Cargo.toml")
            
            elif package_manager == PackageManager.GO_MOD:
                go_mod_path = project_dir / "go.mod"
                if go_mod_path.exists():
                    with open(go_mod_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Parse go.mod file for require statements
                    import re
                    require_matches = re.findall(r'require\s+([^\s]+)\s+([^\s]+)', content)
                    for dep_name, dep_version in require_matches:
                        expected_deps[dep_name] = dep_version
        
        except Exception as e:
            logger.error(f"Error parsing dependencies for {package_manager}: {e}")
        
        return expected_deps
    
    def _verify_single_dependency(self, project_path: str, package_manager: PackageManager,
                                dep_name: str, expected_version: Optional[str]) -> Dict[str, Any]:
        """Verify installation of a single dependency.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            dep_name: Name of the dependency
            expected_version: Expected version (can be None)
            
        Returns:
            Dictionary with verification results
        """
        try:
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                return self._verify_npm_dependency(project_path, dep_name, expected_version)
            
            elif package_manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
                return self._verify_python_dependency(project_path, dep_name, expected_version)
            
            elif package_manager == PackageManager.CARGO:
                return self._verify_cargo_dependency(project_path, dep_name, expected_version)
            
            elif package_manager == PackageManager.GO_MOD:
                return self._verify_go_dependency(project_path, dep_name, expected_version)
            
            else:
                return {
                    "installed": False,
                    "version": None,
                    "error": f"Verification not implemented for {package_manager}"
                }
        
        except Exception as e:
            return {
                "installed": False,
                "version": None,
                "error": f"Error verifying {dep_name}: {str(e)}"
            }
    
    def _verify_npm_dependency(self, project_path: str, dep_name: str, 
                             expected_version: Optional[str]) -> Dict[str, Any]:
        """Verify npm dependency installation."""
        try:
            # Check if dependency exists in node_modules
            node_modules_path = Path(project_path) / "node_modules" / dep_name
            if not node_modules_path.exists():
                return {
                    "installed": False,
                    "version": None,
                    "error": f"{dep_name} not found in node_modules"
                }
            
            # Get installed version from package.json
            package_json_path = node_modules_path / "package.json"
            if package_json_path.exists():
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                installed_version = package_data.get("version")
            else:
                installed_version = None
            
            # Check version compatibility if expected version is specified
            version_compatible = True
            if expected_version and installed_version:
                version_compatible = self._check_version_compatibility_string(
                    installed_version, expected_version
                )
            
            return {
                "installed": True,
                "version": installed_version,
                "version_compatible": version_compatible,
                "error": None if version_compatible else f"Version mismatch: expected {expected_version}, got {installed_version}"
            }
        
        except Exception as e:
            return {
                "installed": False,
                "version": None,
                "error": str(e)
            }
    
    def _verify_python_dependency(self, project_path: str, dep_name: str,
                                expected_version: Optional[str]) -> Dict[str, Any]:
        """Verify Python dependency installation."""
        try:
            # Use pip show to check if package is installed
            result = subprocess.run(
                ["pip", "show", dep_name],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "installed": False,
                    "version": None,
                    "error": f"{dep_name} not installed"
                }
            
            # Parse pip show output
            installed_version = None
            for line in result.stdout.split('\n'):
                if line.startswith('Version:'):
                    installed_version = line.split(':', 1)[1].strip()
                    break
            
            # Check version compatibility
            version_compatible = True
            if expected_version and installed_version:
                version_compatible = self._check_version_compatibility_string(
                    installed_version, expected_version
                )
            
            return {
                "installed": True,
                "version": installed_version,
                "version_compatible": version_compatible,
                "error": None if version_compatible else f"Version mismatch: expected {expected_version}, got {installed_version}"
            }
        
        except Exception as e:
            return {
                "installed": False,
                "version": None,
                "error": str(e)
            }
    
    def _verify_cargo_dependency(self, project_path: str, dep_name: str,
                               expected_version: Optional[str]) -> Dict[str, Any]:
        """Verify Cargo dependency installation."""
        try:
            # Check Cargo.lock file for installed version
            cargo_lock_path = Path(project_path) / "Cargo.lock"
            if not cargo_lock_path.exists():
                return {
                    "installed": False,
                    "version": None,
                    "error": "Cargo.lock not found - dependencies may not be installed"
                }
            
            try:
                import toml
                with open(cargo_lock_path, 'r', encoding='utf-8') as f:
                    cargo_lock_data = toml.load(f)
                
                # Find the package in the lock file
                installed_version = None
                if "package" in cargo_lock_data:
                    for package in cargo_lock_data["package"]:
                        if package.get("name") == dep_name:
                            installed_version = package.get("version")
                            break
                
                if not installed_version:
                    return {
                        "installed": False,
                        "version": None,
                        "error": f"{dep_name} not found in Cargo.lock"
                    }
                
                # Check version compatibility
                version_compatible = True
                if expected_version and installed_version:
                    version_compatible = self._check_version_compatibility_string(
                        installed_version, expected_version
                    )
                
                return {
                    "installed": True,
                    "version": installed_version,
                    "version_compatible": version_compatible,
                    "error": None if version_compatible else f"Version mismatch: expected {expected_version}, got {installed_version}"
                }
            
            except ImportError:
                return {
                    "installed": False,
                    "version": None,
                    "error": "toml package not available for parsing Cargo.lock"
                }
        
        except Exception as e:
            return {
                "installed": False,
                "version": None,
                "error": str(e)
            }
    
    def _verify_go_dependency(self, project_path: str, dep_name: str,
                            expected_version: Optional[str]) -> Dict[str, Any]:
        """Verify Go dependency installation."""
        try:
            # Use go list to check if module is available
            result = subprocess.run(
                ["go", "list", "-m", dep_name],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "installed": False,
                    "version": None,
                    "error": f"{dep_name} not available"
                }
            
            # Parse go list output (format: "module version")
            output_parts = result.stdout.strip().split()
            installed_version = output_parts[1] if len(output_parts) > 1 else None
            
            # Check version compatibility
            version_compatible = True
            if expected_version and installed_version:
                version_compatible = self._check_version_compatibility_string(
                    installed_version, expected_version
                )
            
            return {
                "installed": True,
                "version": installed_version,
                "version_compatible": version_compatible,
                "error": None if version_compatible else f"Version mismatch: expected {expected_version}, got {installed_version}"
            }
        
        except Exception as e:
            return {
                "installed": False,
                "version": None,
                "error": str(e)
            }
    
    def _check_version_compatibility_string(self, installed_version: str, expected_version: str) -> bool:
        """Check if installed version satisfies expected version constraint.
        
        Args:
            installed_version: Actually installed version
            expected_version: Expected version constraint (e.g., ">=1.0.0", "^2.1.0")
            
        Returns:
            True if versions are compatible
        """
        try:
            from packaging import version, specifiers
            
            # Handle npm-style version ranges
            if expected_version.startswith('^'):
                # Caret range (^1.2.3 means >=1.2.3 <2.0.0)
                base_version = expected_version[1:]
                spec = f">={base_version}"
                # Add upper bound based on major version
                major = version.parse(base_version).major
                spec += f",<{major + 1}.0.0"
            elif expected_version.startswith('~'):
                # Tilde range (~1.2.3 means >=1.2.3 <1.3.0)
                base_version = expected_version[1:]
                parsed_base = version.parse(base_version)
                spec = f">={base_version},<{parsed_base.major}.{parsed_base.minor + 1}.0"
            else:
                # Use as-is (should handle >=, <=, ==, etc.)
                spec = expected_version
            
            spec_set = specifiers.SpecifierSet(spec)
            return version.parse(installed_version) in spec_set
        
        except Exception as e:
            logger.warning(f"Error checking version compatibility: {e}")
            # Fallback to exact string match
            return installed_version == expected_version.lstrip('>=<=!~^')
    
    def _perform_dependency_health_checks(self, project_path: str, 
                                        package_manager: PackageManager) -> Dict[str, Any]:
        """Perform health checks on installed dependencies.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            
        Returns:
            Dictionary with health check results
        """
        errors = []
        warnings = []
        
        try:
            # Check for common dependency issues
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                # Check for missing peer dependencies
                peer_dep_issues = self._check_npm_peer_dependencies(project_path)
                if peer_dep_issues:
                    warnings.extend(peer_dep_issues)
                
                # Check for duplicate dependencies
                duplicate_issues = self._check_npm_duplicate_dependencies(project_path)
                if duplicate_issues:
                    warnings.extend(duplicate_issues)
            
            elif package_manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
                # Check for conflicting Python dependencies
                conflict_issues = self._check_python_dependency_conflicts(project_path)
                if conflict_issues:
                    errors.extend(conflict_issues)
            
            # Check for outdated dependencies
            outdated_issues = self._check_outdated_dependencies(project_path, package_manager)
            if outdated_issues:
                warnings.extend(outdated_issues)
        
        except Exception as e:
            errors.append(f"Error during health checks: {str(e)}")
        
        return {
            "errors": errors,
            "warnings": warnings
        }
    
    def _check_npm_peer_dependencies(self, project_path: str) -> List[str]:
        """Check for missing npm peer dependencies."""
        issues = []
        try:
            result = subprocess.run(
                ["npm", "ls", "--depth=0"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse output for peer dependency warnings
            for line in result.stderr.split('\n'):
                if "peer dep missing" in line.lower() or "unmet peer dependency" in line.lower():
                    issues.append(f"Missing peer dependency: {line.strip()}")
        
        except Exception as e:
            logger.warning(f"Error checking npm peer dependencies: {e}")
        
        return issues
    
    def _check_npm_duplicate_dependencies(self, project_path: str) -> List[str]:
        """Check for duplicate npm dependencies."""
        issues = []
        try:
            result = subprocess.run(
                ["npm", "ls", "--depth=0", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                try:
                    ls_data = json.loads(result.stdout)
                    if "problems" in ls_data:
                        for problem in ls_data["problems"]:
                            if "duplicate" in problem.lower():
                                issues.append(f"Duplicate dependency: {problem}")
                except json.JSONDecodeError:
                    pass
        
        except Exception as e:
            logger.warning(f"Error checking npm duplicate dependencies: {e}")
        
        return issues
    
    def _check_python_dependency_conflicts(self, project_path: str) -> List[str]:
        """Check for Python dependency conflicts."""
        issues = []
        try:
            result = subprocess.run(
                ["pip", "check"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                for line in result.stdout.split('\n'):
                    if line.strip():
                        issues.append(f"Dependency conflict: {line.strip()}")
        
        except Exception as e:
            logger.warning(f"Error checking Python dependency conflicts: {e}")
        
        return issues
    
    def _check_outdated_dependencies(self, project_path: str, 
                                   package_manager: PackageManager) -> List[str]:
        """Check for outdated dependencies."""
        issues = []
        try:
            if package_manager == PackageManager.NPM:
                result = subprocess.run(
                    ["npm", "outdated", "--json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.stdout:
                    try:
                        outdated_data = json.loads(result.stdout)
                        for package, info in outdated_data.items():
                            current = info.get("current", "unknown")
                            latest = info.get("latest", "unknown")
                            issues.append(f"Outdated package {package}: {current} -> {latest}")
                    except json.JSONDecodeError:
                        pass
            
            elif package_manager == PackageManager.PIP:
                result = subprocess.run(
                    ["pip", "list", "--outdated", "--format=json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0 and result.stdout:
                    try:
                        outdated_data = json.loads(result.stdout)
                        for package in outdated_data:
                            name = package.get("name", "unknown")
                            current = package.get("version", "unknown")
                            latest = package.get("latest_version", "unknown")
                            issues.append(f"Outdated package {name}: {current} -> {latest}")
                    except json.JSONDecodeError:
                        pass
        
        except Exception as e:
            logger.warning(f"Error checking outdated dependencies: {e}")
        
        return issues
    
    def _scan_vulnerabilities_for_manager(self, project_path: str, 
                                        package_manager: PackageManager) -> Dict[str, Any]:
        """Scan for security vulnerabilities using package manager tools.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            
        Returns:
            Dictionary with vulnerability scan results
        """
        vulnerabilities = []
        
        try:
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                vulnerabilities = self._scan_npm_vulnerabilities(project_path, package_manager)
            
            elif package_manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
                vulnerabilities = self._scan_python_vulnerabilities(project_path, package_manager)
            
            elif package_manager == PackageManager.CARGO:
                vulnerabilities = self._scan_cargo_vulnerabilities(project_path)
            
            return {
                "success": True,
                "vulnerabilities": vulnerabilities,
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "vulnerabilities": [],
                "error": str(e)
            }
    
    def _scan_npm_vulnerabilities(self, project_path: str, 
                                package_manager: PackageManager) -> List[Dict[str, Any]]:
        """Scan for npm vulnerabilities."""
        vulnerabilities = []
        
        try:
            command = self._package_manager_commands[package_manager]
            result = subprocess.run(
                [command, "audit", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                try:
                    audit_data = json.loads(result.stdout)
                    
                    if "vulnerabilities" in audit_data:
                        for vuln_name, vuln_data in audit_data["vulnerabilities"].items():
                            vulnerabilities.append({
                                "package": vuln_name,
                                "severity": vuln_data.get("severity", "unknown"),
                                "title": vuln_data.get("title", "Unknown vulnerability"),
                                "description": vuln_data.get("overview", ""),
                                "cwe": vuln_data.get("cwe", []),
                                "cvss": vuln_data.get("cvss", {}),
                                "range": vuln_data.get("range", ""),
                                "fixAvailable": vuln_data.get("fixAvailable", False)
                            })
                
                except json.JSONDecodeError:
                    # Fallback to text parsing
                    vulnerabilities = self._parse_npm_audit_output(result.stdout)
        
        except Exception as e:
            logger.error(f"Error scanning npm vulnerabilities: {e}")
        
        return vulnerabilities
    
    def _scan_python_vulnerabilities(self, project_path: str, 
                                   package_manager: PackageManager) -> List[Dict[str, Any]]:
        """Scan for Python vulnerabilities using safety or similar tools."""
        vulnerabilities = []
        
        try:
            # Try to use safety if available
            result = subprocess.run(
                ["safety", "check", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    safety_data = json.loads(result.stdout)
                    for vuln in safety_data:
                        vulnerabilities.append({
                            "package": vuln.get("package", "unknown"),
                            "severity": self._map_safety_severity(vuln.get("vulnerability_id", "")),
                            "title": vuln.get("advisory", "Unknown vulnerability"),
                            "description": vuln.get("advisory", ""),
                            "installed_version": vuln.get("installed_version", ""),
                            "vulnerable_spec": vuln.get("vulnerable_spec", ""),
                            "id": vuln.get("vulnerability_id", "")
                        })
                except json.JSONDecodeError:
                    pass
        
        except FileNotFoundError:
            # safety not installed, try pip-audit if available
            try:
                result = subprocess.run(
                    ["pip-audit", "--format=json"],
                    cwd=project_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                if result.returncode == 0 and result.stdout:
                    try:
                        audit_data = json.loads(result.stdout)
                        for vuln in audit_data.get("vulnerabilities", []):
                            vulnerabilities.append({
                                "package": vuln.get("package", "unknown"),
                                "severity": vuln.get("severity", "unknown"),
                                "title": vuln.get("id", "Unknown vulnerability"),
                                "description": vuln.get("description", ""),
                                "installed_version": vuln.get("installed_version", ""),
                                "fixed_versions": vuln.get("fixed_versions", []),
                                "id": vuln.get("id", "")
                            })
                    except json.JSONDecodeError:
                        pass
            
            except FileNotFoundError:
                logger.warning("Neither safety nor pip-audit available for Python vulnerability scanning")
        
        except Exception as e:
            logger.error(f"Error scanning Python vulnerabilities: {e}")
        
        return vulnerabilities
    
    def _scan_cargo_vulnerabilities(self, project_path: str) -> List[Dict[str, Any]]:
        """Scan for Cargo vulnerabilities using cargo-audit."""
        vulnerabilities = []
        
        try:
            result = subprocess.run(
                ["cargo", "audit", "--json"],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                try:
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            audit_data = json.loads(line)
                            if audit_data.get("type") == "vulnerability":
                                vuln = audit_data.get("vulnerability", {})
                                vulnerabilities.append({
                                    "package": vuln.get("package", "unknown"),
                                    "severity": vuln.get("severity", "unknown"),
                                    "title": vuln.get("title", "Unknown vulnerability"),
                                    "description": vuln.get("description", ""),
                                    "id": vuln.get("id", ""),
                                    "date": vuln.get("date", ""),
                                    "url": vuln.get("url", "")
                                })
                except json.JSONDecodeError:
                    pass
        
        except FileNotFoundError:
            logger.warning("cargo-audit not available for Rust vulnerability scanning")
        except Exception as e:
            logger.error(f"Error scanning Cargo vulnerabilities: {e}")
        
        return vulnerabilities
    
    def _map_safety_severity(self, vulnerability_id: str) -> str:
        """Map safety vulnerability ID to severity level."""
        # This is a simplified mapping - in practice, you'd want a more sophisticated approach
        if vulnerability_id.startswith("CVE-"):
            return "high"
        elif vulnerability_id.startswith("GHSA-"):
            return "medium"
        else:
            return "unknown"
    
    def _validate_compatibility_for_manager(self, project_path: str,
                                          package_manager: PackageManager) -> Dict[str, Any]:
        """Validate dependency compatibility for a specific package manager.
        
        Args:
            project_path: Path to the project directory
            package_manager: Package manager enum
            
        Returns:
            Dictionary with compatibility validation results
        """
        issues = []
        compatible = True
        
        try:
            # Check for version conflicts
            conflict_result = self.resolve_dependency_conflicts(project_path)
            if conflict_result["success"] and conflict_result["conflicts"]:
                for conflict in conflict_result["conflicts"]:
                    issues.append({
                        "type": "version_conflict",
                        "package": conflict.get("package", "unknown"),
                        "description": conflict.get("description", ""),
                        "severity": conflict.get("severity", "unknown")
                    })
                    if conflict.get("severity") in ["high", "error"]:
                        compatible = False
            
            # Check for platform compatibility
            platform_issues = self._check_platform_compatibility(project_path, package_manager)
            if platform_issues:
                issues.extend(platform_issues)
                compatible = False
            
            # Check for engine compatibility (Node.js version, Python version, etc.)
            engine_issues = self._check_engine_compatibility(project_path, package_manager)
            if engine_issues:
                issues.extend(engine_issues)
                # Engine issues are warnings, not errors
            
            return {
                "success": True,
                "compatible": compatible,
                "issues": issues,
                "error": None
            }
        
        except Exception as e:
            return {
                "success": False,
                "compatible": False,
                "issues": [],
                "error": str(e)
            }
    
    def _check_platform_compatibility(self, project_path: str,
                                    package_manager: PackageManager) -> List[Dict[str, Any]]:
        """Check for platform-specific compatibility issues."""
        issues = []
        
        try:
            import platform
            current_platform = platform.system().lower()
            current_arch = platform.machine().lower()
            
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                # Check package.json for platform restrictions
                package_json_path = Path(project_path) / "package.json"
                if package_json_path.exists():
                    with open(package_json_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                    
                    # Check os field
                    if "os" in package_data:
                        allowed_os = package_data["os"]
                        if isinstance(allowed_os, list):
                            if not any(os_name.lower() in current_platform for os_name in allowed_os):
                                issues.append({
                                    "type": "platform_incompatible",
                                    "package": package_data.get("name", "unknown"),
                                    "description": f"Package requires OS: {allowed_os}, current: {current_platform}",
                                    "severity": "error"
                                })
                    
                    # Check cpu field
                    if "cpu" in package_data:
                        allowed_cpu = package_data["cpu"]
                        if isinstance(allowed_cpu, list):
                            if not any(cpu_arch.lower() in current_arch for cpu_arch in allowed_cpu):
                                issues.append({
                                    "type": "architecture_incompatible",
                                    "package": package_data.get("name", "unknown"),
                                    "description": f"Package requires CPU: {allowed_cpu}, current: {current_arch}",
                                    "severity": "error"
                                })
        
        except Exception as e:
            logger.warning(f"Error checking platform compatibility: {e}")
        
        return issues
    
    def _check_engine_compatibility(self, project_path: str,
                                  package_manager: PackageManager) -> List[Dict[str, Any]]:
        """Check for engine compatibility issues (Node.js, Python versions, etc.)."""
        issues = []
        
        try:
            if package_manager in [PackageManager.NPM, PackageManager.YARN, PackageManager.PNPM]:
                # Check Node.js version requirements
                package_json_path = Path(project_path) / "package.json"
                if package_json_path.exists():
                    with open(package_json_path, 'r', encoding='utf-8') as f:
                        package_data = json.load(f)
                    
                    if "engines" in package_data:
                        engines = package_data["engines"]
                        if "node" in engines:
                            required_node = engines["node"]
                            current_node = self._get_node_version()
                            
                            if current_node and not self._check_version_compatibility_string(current_node, required_node):
                                issues.append({
                                    "type": "engine_incompatible",
                                    "package": package_data.get("name", "unknown"),
                                    "description": f"Requires Node.js {required_node}, current: {current_node}",
                                    "severity": "warning"
                                })
            
            elif package_manager in [PackageManager.PIP, PackageManager.POETRY, PackageManager.PIPENV]:
                # Check Python version requirements
                current_python = self._get_python_version()
                
                if package_manager == PackageManager.POETRY:
                    pyproject_path = Path(project_path) / "pyproject.toml"
                    if pyproject_path.exists():
                        try:
                            import toml
                            with open(pyproject_path, 'r', encoding='utf-8') as f:
                                pyproject_data = toml.load(f)
                            
                            if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
                                poetry_config = pyproject_data["tool"]["poetry"]
                                if "dependencies" in poetry_config and "python" in poetry_config["dependencies"]:
                                    required_python = poetry_config["dependencies"]["python"]
                                    
                                    if current_python and not self._check_version_compatibility_string(current_python, required_python):
                                        issues.append({
                                            "type": "engine_incompatible",
                                            "package": poetry_config.get("name", "unknown"),
                                            "description": f"Requires Python {required_python}, current: {current_python}",
                                            "severity": "warning"
                                        })
                        except ImportError:
                            pass
        
        except Exception as e:
            logger.warning(f"Error checking engine compatibility: {e}")
        
        return issues
    
    def _get_node_version(self) -> Optional[str]:
        """Get current Node.js version."""
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return result.stdout.strip().lstrip('v')
        
        except Exception:
            pass
        
        return None
    
    def _get_python_version(self) -> Optional[str]:
        """Get current Python version."""
        try:
            import sys
            return f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        except Exception:
            return None