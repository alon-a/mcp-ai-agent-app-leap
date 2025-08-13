"""Artifact management for MCP Server Builder."""

import os
import hashlib
import time
import shutil
import zipfile
import tarfile
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass

from ..models.artifacts import (
    ArtifactInfo, ArtifactCollection, ArtifactValidationResult,
    PackagingResult, ArtifactReport, ArtifactDetector,
    ArtifactType, ArtifactStatus
)
from ..models.enums import BuildTool


logger = logging.getLogger(__name__)


class ArtifactManager:
    """Manages build artifact detection, validation, and packaging."""
    
    def __init__(self):
        """Initialize the artifact manager."""
        self.detector = ArtifactDetector()
        
        # File size limits (in bytes)
        self.max_single_file_size = 100 * 1024 * 1024  # 100MB
        self.max_total_size = 500 * 1024 * 1024  # 500MB
        
        # Validation rules
        self.validation_rules = {
            ArtifactType.EXECUTABLE: self._validate_executable,
            ArtifactType.LIBRARY: self._validate_library,
            ArtifactType.PACKAGE: self._validate_package,
            ArtifactType.CONFIGURATION: self._validate_configuration,
        }
    
    def detect_and_collect_artifacts(self, project_path: str, build_tool: str, 
                                   output_directories: Optional[List[str]] = None) -> ArtifactCollection:
        """Detect and collect build artifacts from a project.
        
        Args:
            project_path: Path to the project directory
            build_tool: Build tool used (e.g., 'npm-scripts', 'cargo-build')
            output_directories: Optional list of specific directories to scan
            
        Returns:
            ArtifactCollection with detected artifacts
        """
        logger.info(f"Detecting artifacts for project: {project_path}")
        logger.info(f"Build tool: {build_tool}")
        
        start_time = time.time()
        artifacts = []
        total_size = 0
        
        try:
            # Determine directories to scan
            scan_dirs = self._get_scan_directories(project_path, build_tool, output_directories)
            logger.info(f"Scanning directories: {scan_dirs}")
            
            # Scan each directory for artifacts
            for scan_dir in scan_dirs:
                if not os.path.exists(scan_dir):
                    logger.warning(f"Scan directory does not exist: {scan_dir}")
                    continue
                
                dir_artifacts = self._scan_directory_for_artifacts(
                    scan_dir, project_path, build_tool
                )
                artifacts.extend(dir_artifacts)
                total_size += sum(artifact.size for artifact in dir_artifacts)
            
            # Remove duplicates (same file found in multiple scans)
            artifacts = self._deduplicate_artifacts(artifacts)
            total_size = sum(artifact.size for artifact in artifacts)
            
            logger.info(f"Found {len(artifacts)} artifacts, total size: {total_size} bytes")
            
            # Perform initial validation
            validation_results = self._perform_bulk_validation(artifacts)
            
            collection_time = time.time() - start_time
            
            return ArtifactCollection(
                project_path=project_path,
                build_tool=build_tool,
                artifacts=artifacts,
                total_size=total_size,
                collection_time=collection_time,
                validation_results=validation_results
            )
            
        except Exception as e:
            logger.error(f"Error collecting artifacts: {str(e)}", exc_info=True)
            return ArtifactCollection(
                project_path=project_path,
                build_tool=build_tool,
                artifacts=[],
                total_size=0,
                collection_time=time.time() - start_time,
                validation_results={"error": str(e)}
            )
    
    def validate_artifacts(self, artifacts: List[ArtifactInfo]) -> List[ArtifactValidationResult]:
        """Validate a list of artifacts.
        
        Args:
            artifacts: List of artifacts to validate
            
        Returns:
            List of validation results
        """
        logger.info(f"Validating {len(artifacts)} artifacts")
        
        validation_results = []
        
        for artifact in artifacts:
            try:
                result = self._validate_single_artifact(artifact)
                validation_results.append(result)
                
                if not result.is_valid:
                    logger.warning(f"Artifact validation failed: {artifact.path}")
                    for error in result.errors:
                        logger.warning(f"  Error: {error}")
                
            except Exception as e:
                logger.error(f"Error validating artifact {artifact.path}: {str(e)}")
                validation_results.append(ArtifactValidationResult(
                    artifact_path=artifact.path,
                    is_valid=False,
                    validation_checks={},
                    errors=[f"Validation error: {str(e)}"],
                    warnings=[]
                ))
        
        valid_count = sum(1 for result in validation_results if result.is_valid)
        logger.info(f"Validation complete: {valid_count}/{len(artifacts)} artifacts valid")
        
        return validation_results
    
    def package_artifacts(self, artifacts: List[ArtifactInfo], output_path: str,
                         package_format: str = "zip") -> PackagingResult:
        """Package artifacts into a single archive.
        
        Args:
            artifacts: List of artifacts to package
            output_path: Path for the output package
            package_format: Format for packaging ('zip' or 'tar.gz')
            
        Returns:
            PackagingResult with packaging details
        """
        logger.info(f"Packaging {len(artifacts)} artifacts to {output_path}")
        logger.info(f"Package format: {package_format}")
        
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            packaged_artifacts = []
            errors = []
            
            if package_format.lower() == "zip":
                package_size = self._create_zip_package(artifacts, output_path, packaged_artifacts, errors)
            elif package_format.lower() in ["tar.gz", "tgz"]:
                package_size = self._create_tar_package(artifacts, output_path, packaged_artifacts, errors)
            else:
                error_msg = f"Unsupported package format: {package_format}"
                logger.error(error_msg)
                return PackagingResult(
                    success=False,
                    package_path=None,
                    packaged_artifacts=[],
                    package_size=0,
                    errors=[error_msg]
                )
            
            success = len(errors) == 0 and package_size > 0
            
            if success:
                logger.info(f"Packaging successful: {output_path} ({package_size} bytes)")
            else:
                logger.error(f"Packaging failed with {len(errors)} errors")
            
            return PackagingResult(
                success=success,
                package_path=output_path if success else None,
                packaged_artifacts=packaged_artifacts,
                package_size=package_size,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Error during packaging: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return PackagingResult(
                success=False,
                package_path=None,
                packaged_artifacts=[],
                package_size=0,
                errors=[error_msg]
            )
    
    def generate_artifact_report(self, collection: ArtifactCollection,
                               validation_results: Optional[List[ArtifactValidationResult]] = None,
                               packaging_result: Optional[PackagingResult] = None) -> ArtifactReport:
        """Generate a comprehensive artifact report.
        
        Args:
            collection: Artifact collection
            validation_results: Optional validation results
            packaging_result: Optional packaging result
            
        Returns:
            ArtifactReport with comprehensive information
        """
        logger.info("Generating artifact report")
        
        # Update artifact statuses based on validation results
        if validation_results:
            validation_map = {result.artifact_path: result for result in validation_results}
            for artifact in collection.artifacts:
                validation_result = validation_map.get(artifact.path)
                if validation_result:
                    artifact.status = ArtifactStatus.VALID if validation_result.is_valid else ArtifactStatus.INVALID
        
        # Calculate summary statistics
        valid_artifacts = sum(1 for a in collection.artifacts if a.status == ArtifactStatus.VALID)
        invalid_artifacts = sum(1 for a in collection.artifacts if a.status == ArtifactStatus.INVALID)
        missing_artifacts = sum(1 for a in collection.artifacts if a.status == ArtifactStatus.MISSING)
        
        # Create validation summary
        validation_summary = {
            "total": len(collection.artifacts),
            "valid": valid_artifacts,
            "invalid": invalid_artifacts,
            "missing": missing_artifacts,
            "unknown": len(collection.artifacts) - valid_artifacts - invalid_artifacts - missing_artifacts
        }
        
        # Collect errors and warnings
        errors = []
        warnings = []
        
        if validation_results:
            for result in validation_results:
                errors.extend(result.errors)
                warnings.extend(result.warnings)
        
        if packaging_result and not packaging_result.success:
            errors.extend(packaging_result.errors)
        
        # Determine overall build success
        build_success = (
            len(collection.artifacts) > 0 and
            invalid_artifacts == 0 and
            len(errors) == 0
        )
        
        report = ArtifactReport(
            project_path=collection.project_path,
            build_tool=collection.build_tool,
            build_success=build_success,
            total_artifacts=len(collection.artifacts),
            valid_artifacts=valid_artifacts,
            invalid_artifacts=invalid_artifacts,
            missing_artifacts=missing_artifacts,
            total_size=collection.total_size,
            artifacts=collection.artifacts,
            validation_summary=validation_summary,
            packaging_info=packaging_result,
            report_time=time.time(),
            errors=list(set(errors)),  # Remove duplicates
            warnings=list(set(warnings))  # Remove duplicates
        )
        
        logger.info(f"Report generated: {valid_artifacts}/{len(collection.artifacts)} valid artifacts")
        return report
    
    def save_artifact_report(self, report: ArtifactReport, report_path: str) -> bool:
        """Save artifact report to file.
        
        Args:
            report: Artifact report to save
            report_path: Path to save the report
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            
            # Save report
            success = report.save_to_file(report_path)
            
            if success:
                logger.info(f"Artifact report saved to: {report_path}")
            else:
                logger.error(f"Failed to save artifact report to: {report_path}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error saving artifact report: {str(e)}", exc_info=True)
            return False
    
    # Private helper methods
    
    def _get_scan_directories(self, project_path: str, build_tool: str,
                            output_directories: Optional[List[str]]) -> List[str]:
        """Get directories to scan for artifacts."""
        if output_directories:
            # Use provided directories
            return [os.path.join(project_path, d) if not os.path.isabs(d) else d 
                   for d in output_directories]
        
        # Use build tool specific directories
        patterns = self.detector.BUILD_TOOL_PATTERNS.get(build_tool, {})
        directories = patterns.get('directories', ['.'])
        
        # Always include project root for common files like package.json
        scan_dirs = set([project_path])  # Add project root
        
        # Add build tool specific directories
        for d in directories:
            if d == '.':
                scan_dirs.add(project_path)
            else:
                scan_dirs.add(os.path.join(project_path, d))
        
        return list(scan_dirs)
    
    def _scan_directory_for_artifacts(self, directory: str, project_path: str, 
                                    build_tool: str) -> List[ArtifactInfo]:
        """Scan a directory for build artifacts."""
        artifacts = []
        
        try:
            # If scanning project root, only scan files in root, not subdirectories
            # to avoid duplicating artifacts found in specific build directories
            if directory == project_path:
                # Only scan files in the root directory
                for file in os.listdir(directory):
                    file_path = os.path.join(directory, file)
                    
                    # Skip directories and hidden files
                    if os.path.isdir(file_path) or file.startswith('.'):
                        continue
                    
                    # Check if file is likely an artifact
                    if self.detector.is_likely_artifact(file_path, build_tool):
                        artifact_info = self._create_artifact_info(file_path, project_path)
                        if artifact_info:
                            artifacts.append(artifact_info)
            else:
                # For build directories, scan recursively
                for root, dirs, files in os.walk(directory):
                    # Skip hidden directories and common non-artifact directories
                    dirs[:] = [d for d in dirs if not d.startswith('.') and 
                              d not in ['node_modules', '__pycache__', '.git']]
                    
                    for file in files:
                        file_path = os.path.join(root, file)
                        
                        # Skip hidden files
                        if file.startswith('.'):
                            continue
                        
                        # Check if file is likely an artifact
                        if self.detector.is_likely_artifact(file_path, build_tool):
                            artifact_info = self._create_artifact_info(file_path, project_path)
                            if artifact_info:
                                artifacts.append(artifact_info)
        
        except Exception as e:
            logger.error(f"Error scanning directory {directory}: {str(e)}")
        
        return artifacts
    
    def _create_artifact_info(self, file_path: str, project_path: str) -> Optional[ArtifactInfo]:
        """Create ArtifactInfo for a file."""
        try:
            if not os.path.exists(file_path):
                return None
            
            # Get file stats
            stat = os.stat(file_path)
            size = stat.st_size
            created_time = stat.st_ctime
            
            # Skip files that are too large
            if size > self.max_single_file_size:
                logger.warning(f"Skipping large file: {file_path} ({size} bytes)")
                return None
            
            # Calculate checksum
            checksum = self._calculate_file_checksum(file_path)
            
            # Determine artifact type
            artifact_type = self.detector.detect_artifact_type(file_path)
            
            # Create relative path
            try:
                relative_path = os.path.relpath(file_path, project_path)
            except ValueError:
                # Handle case where paths are on different drives (Windows)
                relative_path = file_path
            
            # Gather metadata
            metadata = {
                "extension": Path(file_path).suffix,
                "is_executable": os.access(file_path, os.X_OK),
                "permissions": oct(stat.st_mode)[-3:] if hasattr(stat, 'st_mode') else None
            }
            
            return ArtifactInfo(
                path=file_path,
                relative_path=relative_path,
                size=size,
                checksum=checksum,
                artifact_type=artifact_type,
                status=ArtifactStatus.UNKNOWN,  # Will be determined during validation
                created_time=created_time,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error creating artifact info for {file_path}: {str(e)}")
            return None
    
    def _calculate_file_checksum(self, file_path: str) -> str:
        """Calculate SHA256 checksum of a file."""
        try:
            hash_sha256 = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {file_path}: {str(e)}")
            return ""
    
    def _deduplicate_artifacts(self, artifacts: List[ArtifactInfo]) -> List[ArtifactInfo]:
        """Remove duplicate artifacts based on path."""
        seen_paths = set()
        unique_artifacts = []
        
        for artifact in artifacts:
            if artifact.path not in seen_paths:
                seen_paths.add(artifact.path)
                unique_artifacts.append(artifact)
        
        return unique_artifacts
    
    def _perform_bulk_validation(self, artifacts: List[ArtifactInfo]) -> Dict[str, Any]:
        """Perform bulk validation checks on artifacts."""
        validation_results = {
            "total_artifacts": len(artifacts),
            "total_size": sum(a.size for a in artifacts),
            "size_check": True,
            "file_existence_check": True,
            "errors": []
        }
        
        # Check total size
        if validation_results["total_size"] > self.max_total_size:
            validation_results["size_check"] = False
            validation_results["errors"].append(
                f"Total artifact size ({validation_results['total_size']} bytes) "
                f"exceeds maximum ({self.max_total_size} bytes)"
            )
        
        # Check file existence
        missing_files = []
        for artifact in artifacts:
            if not os.path.exists(artifact.path):
                missing_files.append(artifact.path)
                artifact.status = ArtifactStatus.MISSING
        
        if missing_files:
            validation_results["file_existence_check"] = False
            validation_results["errors"].extend([f"Missing file: {f}" for f in missing_files])
        
        return validation_results
    
    def _validate_single_artifact(self, artifact: ArtifactInfo) -> ArtifactValidationResult:
        """Validate a single artifact."""
        validation_checks = {}
        errors = []
        warnings = []
        
        # Basic existence check
        exists = os.path.exists(artifact.path)
        validation_checks["exists"] = exists
        
        if not exists:
            errors.append(f"File does not exist: {artifact.path}")
            return ArtifactValidationResult(
                artifact_path=artifact.path,
                is_valid=False,
                validation_checks=validation_checks,
                errors=errors,
                warnings=warnings
            )
        
        # Size check
        current_size = os.path.getsize(artifact.path)
        size_matches = current_size == artifact.size
        validation_checks["size_matches"] = size_matches
        
        if not size_matches:
            errors.append(f"File size mismatch: expected {artifact.size}, got {current_size}")
        
        # Checksum check
        current_checksum = self._calculate_file_checksum(artifact.path)
        checksum_matches = current_checksum == artifact.checksum
        validation_checks["checksum_matches"] = checksum_matches
        
        if not checksum_matches:
            errors.append(f"Checksum mismatch: expected {artifact.checksum}, got {current_checksum}")
        
        # Type-specific validation
        if artifact.artifact_type in self.validation_rules:
            try:
                type_validation = self.validation_rules[artifact.artifact_type](artifact)
                validation_checks.update(type_validation.get("checks", {}))
                errors.extend(type_validation.get("errors", []))
                warnings.extend(type_validation.get("warnings", []))
            except Exception as e:
                errors.append(f"Type validation error: {str(e)}")
        
        is_valid = len(errors) == 0 and all(validation_checks.values())
        
        return ArtifactValidationResult(
            artifact_path=artifact.path,
            is_valid=is_valid,
            validation_checks=validation_checks,
            errors=errors,
            warnings=warnings
        )
    
    def _validate_executable(self, artifact: ArtifactInfo) -> Dict[str, Any]:
        """Validate executable artifacts."""
        checks = {}
        errors = []
        warnings = []
        
        # Check if file is actually executable
        is_executable = os.access(artifact.path, os.X_OK)
        checks["is_executable"] = is_executable
        
        if not is_executable:
            warnings.append(f"File is not executable: {artifact.path}")
        
        return {"checks": checks, "errors": errors, "warnings": warnings}
    
    def _validate_library(self, artifact: ArtifactInfo) -> Dict[str, Any]:
        """Validate library artifacts."""
        checks = {}
        errors = []
        warnings = []
        
        # Basic file format validation
        path = Path(artifact.path)
        
        if path.suffix in ['.dll', '.so', '.dylib']:
            # Binary library - basic checks only
            checks["is_binary"] = True
        elif path.suffix == '.jar':
            # Java archive - check if it's a valid zip
            try:
                with zipfile.ZipFile(artifact.path, 'r') as jar:
                    jar.testzip()
                checks["valid_jar"] = True
            except Exception as e:
                checks["valid_jar"] = False
                errors.append(f"Invalid JAR file: {str(e)}")
        
        return {"checks": checks, "errors": errors, "warnings": warnings}
    
    def _validate_package(self, artifact: ArtifactInfo) -> Dict[str, Any]:
        """Validate package artifacts."""
        checks = {}
        errors = []
        warnings = []
        
        path = Path(artifact.path)
        
        if path.suffix == '.zip':
            try:
                with zipfile.ZipFile(artifact.path, 'r') as zip_file:
                    zip_file.testzip()
                checks["valid_zip"] = True
            except Exception as e:
                checks["valid_zip"] = False
                errors.append(f"Invalid ZIP file: {str(e)}")
        
        elif path.suffix in ['.tar.gz', '.tgz']:
            try:
                with tarfile.open(artifact.path, 'r:gz') as tar:
                    tar.getnames()  # Basic validation
                checks["valid_tar"] = True
            except Exception as e:
                checks["valid_tar"] = False
                errors.append(f"Invalid TAR.GZ file: {str(e)}")
        
        return {"checks": checks, "errors": errors, "warnings": warnings}
    
    def _validate_configuration(self, artifact: ArtifactInfo) -> Dict[str, Any]:
        """Validate configuration artifacts."""
        checks = {}
        errors = []
        warnings = []
        
        path = Path(artifact.path)
        
        if path.suffix == '.json':
            try:
                import json
                with open(artifact.path, 'r') as f:
                    json.load(f)
                checks["valid_json"] = True
            except Exception as e:
                checks["valid_json"] = False
                errors.append(f"Invalid JSON file: {str(e)}")
        
        elif path.suffix in ['.yaml', '.yml']:
            try:
                import yaml
                with open(artifact.path, 'r') as f:
                    yaml.safe_load(f)
                checks["valid_yaml"] = True
            except Exception as e:
                checks["valid_yaml"] = False
                errors.append(f"Invalid YAML file: {str(e)}")
        
        return {"checks": checks, "errors": errors, "warnings": warnings}
    
    def _create_zip_package(self, artifacts: List[ArtifactInfo], output_path: str,
                          packaged_artifacts: List[str], errors: List[str]) -> int:
        """Create a ZIP package of artifacts."""
        try:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for artifact in artifacts:
                    if os.path.exists(artifact.path):
                        try:
                            # Use relative path in archive
                            arcname = artifact.relative_path
                            zip_file.write(artifact.path, arcname)
                            packaged_artifacts.append(arcname)
                        except Exception as e:
                            errors.append(f"Error adding {artifact.path} to ZIP: {str(e)}")
                    else:
                        errors.append(f"File not found: {artifact.path}")
            
            return os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
        except Exception as e:
            errors.append(f"Error creating ZIP package: {str(e)}")
            return 0
    
    def _create_tar_package(self, artifacts: List[ArtifactInfo], output_path: str,
                          packaged_artifacts: List[str], errors: List[str]) -> int:
        """Create a TAR.GZ package of artifacts."""
        try:
            with tarfile.open(output_path, 'w:gz') as tar_file:
                for artifact in artifacts:
                    if os.path.exists(artifact.path):
                        try:
                            # Use relative path in archive
                            arcname = artifact.relative_path
                            tar_file.add(artifact.path, arcname)
                            packaged_artifacts.append(arcname)
                        except Exception as e:
                            errors.append(f"Error adding {artifact.path} to TAR: {str(e)}")
                    else:
                        errors.append(f"File not found: {artifact.path}")
            
            return os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
        except Exception as e:
            errors.append(f"Error creating TAR package: {str(e)}")
            return 0