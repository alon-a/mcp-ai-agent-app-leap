"""File management implementation for MCP Server Builder."""

import os
import stat
import shutil
import hashlib
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time
from urllib.parse import urlparse

from .interfaces import FileManager
from ..models.base import FileSpec, DownloadResult


logger = logging.getLogger(__name__)


class FileManagerImpl(FileManager):
    """Implementation of FileManager interface for handling file operations."""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        """Initialize FileManager with retry configuration.
        
        Args:
            max_retries: Maximum number of retry attempts for failed operations
            retry_delay: Delay in seconds between retry attempts
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._created_paths: List[str] = []  # Track created paths for rollback
    
    def create_directory_structure(self, path: str, structure: Dict[str, Any]) -> bool:
        """Create directory structure at the specified path.
        
        Args:
            path: Base path for directory creation
            structure: Directory structure definition as nested dict
                      e.g., {"src": {"models": {}, "managers": {}}, "tests": {}}
            
        Returns:
            True if creation was successful
        """
        try:
            base_path = Path(path)
            logger.info(f"Creating directory structure at: {base_path}")
            
            # Create the base directory if it doesn't exist
            if not base_path.exists():
                base_path.mkdir(parents=True, exist_ok=True)
                self._created_paths.append(str(base_path))
                logger.debug(f"Created base directory: {base_path}")
            
            # Recursively create the directory structure
            self._create_nested_directories(base_path, structure)
            
            logger.info(f"Successfully created directory structure at: {base_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create directory structure at {path}: {e}")
            return False
    
    def _create_nested_directories(self, base_path: Path, structure: Dict[str, Any]) -> None:
        """Recursively create nested directory structure.
        
        Args:
            base_path: Base path for directory creation
            structure: Nested dictionary representing directory structure
        """
        for name, subdirs in structure.items():
            dir_path = base_path / name
            
            # Create directory if it doesn't exist
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                self._created_paths.append(str(dir_path))
                logger.debug(f"Created directory: {dir_path}")
            
            # Recursively create subdirectories if any
            if isinstance(subdirs, dict) and subdirs:
                self._create_nested_directories(dir_path, subdirs)
    
    def set_permissions(self, path: str, permissions: str) -> bool:
        """Set file or directory permissions.
        
        Args:
            path: Path to file or directory
            permissions: Permission string in octal format (e.g., '755', '644')
            
        Returns:
            True if permissions were set successfully
        """
        try:
            target_path = Path(path)
            
            if not target_path.exists():
                logger.error(f"Path does not exist: {path}")
                return False
            
            # Convert permission string to octal mode
            mode = int(permissions, 8)
            
            # Set permissions
            os.chmod(target_path, mode)
            logger.debug(f"Set permissions {permissions} on: {path}")
            
            return True
            
        except ValueError as e:
            logger.error(f"Invalid permission format '{permissions}': {e}")
            return False
        except OSError as e:
            logger.error(f"Failed to set permissions on {path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error setting permissions on {path}: {e}")
            return False
    
    def download_files(self, files: List[FileSpec]) -> DownloadResult:
        """Download files from remote sources.
        
        Args:
            files: List of file specifications to download
            
        Returns:
            DownloadResult with download status and details
        """
        downloaded_files = []
        failed_files = []
        errors = []
        
        logger.info(f"Starting download of {len(files)} files")
        
        for file_spec in files:
            try:
                success = self._download_single_file(file_spec)
                if success:
                    downloaded_files.append(file_spec.destination_path)
                    logger.debug(f"Successfully downloaded: {file_spec.url} -> {file_spec.destination_path}")
                else:
                    failed_files.append(file_spec.destination_path)
                    errors.append(f"Failed to download {file_spec.url}")
                    
            except Exception as e:
                failed_files.append(file_spec.destination_path)
                error_msg = f"Error downloading {file_spec.url}: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
        
        success = len(failed_files) == 0
        logger.info(f"Download completed: {len(downloaded_files)} successful, {len(failed_files)} failed")
        
        return DownloadResult(
            success=success,
            downloaded_files=downloaded_files,
            failed_files=failed_files,
            errors=errors
        )
    
    def _download_single_file(self, file_spec: FileSpec) -> bool:
        """Download a single file with retry logic and integrity verification.
        
        Args:
            file_spec: File specification to download
            
        Returns:
            True if download was successful
        """
        destination_path = Path(file_spec.destination_path)
        
        # Create parent directories if they don't exist
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Attempt download with retries
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Downloading {file_spec.url} (attempt {attempt + 1}/{self.max_retries})")
                
                # Download the file
                urllib.request.urlretrieve(file_spec.url, destination_path)
                self._created_paths.append(str(destination_path))
                
                # Verify checksum if provided
                if file_spec.checksum:
                    if not self._verify_checksum(destination_path, file_spec.checksum):
                        logger.warning(f"Checksum verification failed for {file_spec.url}")
                        destination_path.unlink(missing_ok=True)  # Remove corrupted file
                        if attempt < self.max_retries - 1:
                            time.sleep(self.retry_delay)
                            continue
                        return False
                
                # Set executable permissions if required
                if file_spec.executable:
                    self.set_permissions(str(destination_path), '755')
                
                return True
                
            except urllib.error.URLError as e:
                logger.warning(f"Network error downloading {file_spec.url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
                
            except Exception as e:
                logger.warning(f"Error downloading {file_spec.url}: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                return False
        
        return False
    
    def _verify_checksum(self, file_path: Path, expected_checksum: str) -> bool:
        """Verify file integrity using checksum.
        
        Args:
            file_path: Path to the downloaded file
            expected_checksum: Expected checksum (SHA256 hex string)
            
        Returns:
            True if checksum matches
        """
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_checksum = sha256_hash.hexdigest()
            return actual_checksum.lower() == expected_checksum.lower()
            
        except Exception as e:
            logger.error(f"Error verifying checksum for {file_path}: {e}")
            return False
    
    def rollback_operations(self) -> bool:
        """Rollback all file operations performed by this manager instance.
        
        Returns:
            True if rollback was successful
        """
        logger.info(f"Rolling back {len(self._created_paths)} file operations")
        rollback_errors = []
        
        # Remove files and directories in reverse order of creation
        for path_str in reversed(self._created_paths):
            try:
                path = Path(path_str)
                if path.exists():
                    if path.is_file():
                        path.unlink()
                        logger.debug(f"Removed file: {path}")
                    elif path.is_dir():
                        # Only remove directory if it's empty
                        try:
                            path.rmdir()
                            logger.debug(f"Removed empty directory: {path}")
                        except OSError:
                            # Directory not empty, skip removal
                            logger.debug(f"Skipped non-empty directory: {path}")
                            
            except Exception as e:
                error_msg = f"Failed to remove {path_str}: {e}"
                rollback_errors.append(error_msg)
                logger.error(error_msg)
        
        # Clear the tracking list
        self._created_paths.clear()
        
        if rollback_errors:
            logger.warning(f"Rollback completed with {len(rollback_errors)} errors")
            return False
        else:
            logger.info("Rollback completed successfully")
            return True
    
    def cleanup_partial_operations(self, target_directory: str) -> bool:
        """Clean up partial file operations in a target directory.
        
        Args:
            target_directory: Directory to clean up
            
        Returns:
            True if cleanup was successful
        """
        try:
            target_path = Path(target_directory)
            
            if not target_path.exists():
                logger.debug(f"Target directory does not exist: {target_directory}")
                return True
            
            logger.info(f"Cleaning up partial operations in: {target_directory}")
            
            # Remove all files and subdirectories
            for item in target_path.iterdir():
                if item.is_file():
                    item.unlink()
                    logger.debug(f"Removed file: {item}")
                elif item.is_dir():
                    shutil.rmtree(item)
                    logger.debug(f"Removed directory: {item}")
            
            logger.info(f"Cleanup completed for: {target_directory}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup {target_directory}: {e}")
            return False
    
    def validate_file_operations(self, files: List[FileSpec]) -> Dict[str, bool]:
        """Validate that file operations completed successfully.
        
        Args:
            files: List of file specifications to validate
            
        Returns:
            Dictionary mapping file paths to validation results
        """
        validation_results = {}
        
        logger.info(f"Validating {len(files)} file operations")
        
        for file_spec in files:
            destination_path = Path(file_spec.destination_path)
            
            # Check if file exists
            if not destination_path.exists():
                validation_results[file_spec.destination_path] = False
                logger.error(f"File does not exist: {file_spec.destination_path}")
                continue
            
            # Verify checksum if provided
            if file_spec.checksum:
                if not self._verify_checksum(destination_path, file_spec.checksum):
                    validation_results[file_spec.destination_path] = False
                    logger.error(f"Checksum validation failed: {file_spec.destination_path}")
                    continue
            
            # Check executable permissions if required
            if file_spec.executable:
                file_stat = destination_path.stat()
                if not (file_stat.st_mode & stat.S_IXUSR):
                    validation_results[file_spec.destination_path] = False
                    logger.error(f"File is not executable: {file_spec.destination_path}")
                    continue
            
            validation_results[file_spec.destination_path] = True
            logger.debug(f"File validation passed: {file_spec.destination_path}")
        
        successful_validations = sum(1 for result in validation_results.values() if result)
        logger.info(f"Validation completed: {successful_validations}/{len(files)} files passed")
        
        return validation_results
    
    def get_created_paths(self) -> List[str]:
        """Get list of paths created by this manager instance.
        
        Returns:
            List of created file and directory paths
        """
        return self._created_paths.copy()
    
    def clear_tracking(self) -> None:
        """Clear the tracking of created paths."""
        self._created_paths.clear()