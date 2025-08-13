"""Tests for FileManager implementation."""

import os
import tempfile
import shutil
import hashlib
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import pytest

from src.managers.file_manager import FileManagerImpl
from src.models.base import FileSpec, DownloadResult


class TestFileManagerImpl:
    """Test cases for FileManagerImpl."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.file_manager = FileManagerImpl(max_retries=2, retry_delay=0.1)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_create_directory_structure_simple(self):
        """Test creating a simple directory structure."""
        structure = {
            "src": {},
            "tests": {},
            "docs": {}
        }
        
        result = self.file_manager.create_directory_structure(self.temp_dir, structure)
        
        assert result is True
        assert (Path(self.temp_dir) / "src").exists()
        assert (Path(self.temp_dir) / "tests").exists()
        assert (Path(self.temp_dir) / "docs").exists()
    
    def test_create_directory_structure_nested(self):
        """Test creating a nested directory structure."""
        structure = {
            "src": {
                "models": {},
                "managers": {
                    "interfaces": {}
                },
                "utils": {}
            },
            "tests": {
                "unit": {},
                "integration": {}
            }
        }
        
        result = self.file_manager.create_directory_structure(self.temp_dir, structure)
        
        assert result is True
        assert (Path(self.temp_dir) / "src" / "models").exists()
        assert (Path(self.temp_dir) / "src" / "managers" / "interfaces").exists()
        assert (Path(self.temp_dir) / "src" / "utils").exists()
        assert (Path(self.temp_dir) / "tests" / "unit").exists()
        assert (Path(self.temp_dir) / "tests" / "integration").exists()
    
    def test_create_directory_structure_existing_dirs(self):
        """Test creating directory structure when some directories already exist."""
        # Create some directories first
        existing_dir = Path(self.temp_dir) / "src"
        existing_dir.mkdir()
        
        structure = {
            "src": {
                "models": {}
            },
            "tests": {}
        }
        
        result = self.file_manager.create_directory_structure(self.temp_dir, structure)
        
        assert result is True
        assert (Path(self.temp_dir) / "src" / "models").exists()
        assert (Path(self.temp_dir) / "tests").exists()
    
    def test_set_permissions_file(self):
        """Test setting permissions on a file."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test content")
        
        result = self.file_manager.set_permissions(str(test_file), "644")
        
        assert result is True
        # Check that permissions were set (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            file_stat = test_file.stat()
            assert oct(file_stat.st_mode)[-3:] == "644"
    
    def test_set_permissions_directory(self):
        """Test setting permissions on a directory."""
        test_dir = Path(self.temp_dir) / "test_dir"
        test_dir.mkdir()
        
        result = self.file_manager.set_permissions(str(test_dir), "755")
        
        assert result is True
        # Check that permissions were set (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            dir_stat = test_dir.stat()
            assert oct(dir_stat.st_mode)[-3:] == "755"
    
    def test_set_permissions_nonexistent_path(self):
        """Test setting permissions on a non-existent path."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent.txt"
        
        result = self.file_manager.set_permissions(str(nonexistent_path), "644")
        
        assert result is False
    
    def test_set_permissions_invalid_format(self):
        """Test setting permissions with invalid format."""
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test content")
        
        result = self.file_manager.set_permissions(str(test_file), "invalid")
        
        assert result is False
    
    @patch('urllib.request.urlretrieve')
    def test_download_files_success(self, mock_urlretrieve):
        """Test successful file download."""
        mock_urlretrieve.return_value = None
        
        files = [
            FileSpec(
                url="https://example.com/file1.txt",
                destination_path=str(Path(self.temp_dir) / "file1.txt")
            ),
            FileSpec(
                url="https://example.com/file2.txt",
                destination_path=str(Path(self.temp_dir) / "file2.txt")
            )
        ]
        
        result = self.file_manager.download_files(files)
        
        assert result.success is True
        assert len(result.downloaded_files) == 2
        assert len(result.failed_files) == 0
        assert len(result.errors) == 0
        assert mock_urlretrieve.call_count == 2
    
    @patch('urllib.request.urlretrieve')
    def test_download_files_with_checksum(self, mock_urlretrieve):
        """Test file download with checksum verification."""
        # Create a test file with known content and checksum
        test_content = b"test file content"
        expected_checksum = hashlib.sha256(test_content).hexdigest()
        
        def mock_download(url, path):
            Path(path).write_bytes(test_content)
        
        mock_urlretrieve.side_effect = mock_download
        
        files = [
            FileSpec(
                url="https://example.com/file1.txt",
                destination_path=str(Path(self.temp_dir) / "file1.txt"),
                checksum=expected_checksum
            )
        ]
        
        result = self.file_manager.download_files(files)
        
        assert result.success is True
        assert len(result.downloaded_files) == 1
        assert len(result.failed_files) == 0
    
    @patch('urllib.request.urlretrieve')
    def test_download_files_checksum_mismatch(self, mock_urlretrieve):
        """Test file download with checksum mismatch."""
        # Create a test file with different content than expected checksum
        test_content = b"test file content"
        wrong_checksum = "wrong_checksum_value"
        
        def mock_download(url, path):
            Path(path).write_bytes(test_content)
        
        mock_urlretrieve.side_effect = mock_download
        
        files = [
            FileSpec(
                url="https://example.com/file1.txt",
                destination_path=str(Path(self.temp_dir) / "file1.txt"),
                checksum=wrong_checksum
            )
        ]
        
        result = self.file_manager.download_files(files)
        
        assert result.success is False
        assert len(result.downloaded_files) == 0
        assert len(result.failed_files) == 1
    
    @patch('urllib.request.urlretrieve')
    def test_download_files_with_executable(self, mock_urlretrieve):
        """Test file download with executable permissions."""
        mock_urlretrieve.return_value = None
        
        files = [
            FileSpec(
                url="https://example.com/script.sh",
                destination_path=str(Path(self.temp_dir) / "script.sh"),
                executable=True
            )
        ]
        
        result = self.file_manager.download_files(files)
        
        assert result.success is True
        # Check executable permissions (on Unix-like systems)
        if os.name != 'nt':  # Skip on Windows
            script_path = Path(self.temp_dir) / "script.sh"
            file_stat = script_path.stat()
            assert file_stat.st_mode & 0o111  # Check if any execute bit is set
    
    @patch('urllib.request.urlretrieve')
    def test_download_files_network_error_with_retry(self, mock_urlretrieve):
        """Test file download with network error and retry logic."""
        import urllib.error
        
        # First call fails, second call succeeds
        mock_urlretrieve.side_effect = [
            urllib.error.URLError("Network error"),
            None
        ]
        
        files = [
            FileSpec(
                url="https://example.com/file1.txt",
                destination_path=str(Path(self.temp_dir) / "file1.txt")
            )
        ]
        
        result = self.file_manager.download_files(files)
        
        assert result.success is True
        assert len(result.downloaded_files) == 1
        assert mock_urlretrieve.call_count == 2
    
    @patch('urllib.request.urlretrieve')
    def test_download_files_permanent_failure(self, mock_urlretrieve):
        """Test file download with permanent failure."""
        import urllib.error
        
        mock_urlretrieve.side_effect = urllib.error.URLError("Permanent error")
        
        files = [
            FileSpec(
                url="https://example.com/file1.txt",
                destination_path=str(Path(self.temp_dir) / "file1.txt")
            )
        ]
        
        result = self.file_manager.download_files(files)
        
        assert result.success is False
        assert len(result.downloaded_files) == 0
        assert len(result.failed_files) == 1
        assert len(result.errors) == 1
        assert mock_urlretrieve.call_count == 2  # max_retries = 2
    
    def test_rollback_operations(self):
        """Test rollback of file operations."""
        # Create some files and directories
        structure = {"src": {"models": {}}}
        self.file_manager.create_directory_structure(self.temp_dir, structure)
        
        # Create a test file
        test_file = Path(self.temp_dir) / "test.txt"
        test_file.write_text("test")
        self.file_manager._created_paths.append(str(test_file))
        
        # Verify files exist
        assert (Path(self.temp_dir) / "src").exists()
        assert test_file.exists()
        
        # Rollback operations
        result = self.file_manager.rollback_operations()
        
        assert result is True
        assert not test_file.exists()
        # Directories might still exist if they're not empty
    
    def test_cleanup_partial_operations(self):
        """Test cleanup of partial operations."""
        # Create some test files and directories
        test_dir = Path(self.temp_dir) / "partial_project"
        test_dir.mkdir()
        
        (test_dir / "file1.txt").write_text("content1")
        (test_dir / "subdir").mkdir()
        (test_dir / "subdir" / "file2.txt").write_text("content2")
        
        # Verify files exist
        assert test_dir.exists()
        assert (test_dir / "file1.txt").exists()
        assert (test_dir / "subdir" / "file2.txt").exists()
        
        # Cleanup
        result = self.file_manager.cleanup_partial_operations(str(test_dir))
        
        assert result is True
        assert test_dir.exists()  # Directory itself remains
        assert not (test_dir / "file1.txt").exists()
        assert not (test_dir / "subdir").exists()
    
    def test_validate_file_operations_success(self):
        """Test validation of successful file operations."""
        # Create test files
        test_file1 = Path(self.temp_dir) / "file1.txt"
        test_file2 = Path(self.temp_dir) / "file2.txt"
        
        test_content1 = b"content1"
        test_content2 = b"content2"
        
        test_file1.write_bytes(test_content1)
        test_file2.write_bytes(test_content2)
        
        # Make file2 executable
        if os.name != 'nt':  # Skip on Windows
            os.chmod(test_file2, 0o755)
        
        files = [
            FileSpec(
                url="https://example.com/file1.txt",
                destination_path=str(test_file1),
                checksum=hashlib.sha256(test_content1).hexdigest()
            ),
            FileSpec(
                url="https://example.com/file2.txt",
                destination_path=str(test_file2),
                executable=True
            )
        ]
        
        result = self.file_manager.validate_file_operations(files)
        
        assert len(result) == 2
        assert result[str(test_file1)] is True
        if os.name != 'nt':  # Skip executable check on Windows
            assert result[str(test_file2)] is True
    
    def test_validate_file_operations_missing_file(self):
        """Test validation with missing file."""
        files = [
            FileSpec(
                url="https://example.com/missing.txt",
                destination_path=str(Path(self.temp_dir) / "missing.txt")
            )
        ]
        
        result = self.file_manager.validate_file_operations(files)
        
        assert len(result) == 1
        assert result[str(Path(self.temp_dir) / "missing.txt")] is False
    
    def test_get_created_paths(self):
        """Test getting list of created paths."""
        structure = {"src": {}}
        self.file_manager.create_directory_structure(self.temp_dir, structure)
        
        created_paths = self.file_manager.get_created_paths()
        
        assert len(created_paths) > 0
        assert any("src" in path for path in created_paths)
    
    def test_clear_tracking(self):
        """Test clearing path tracking."""
        structure = {"src": {}}
        self.file_manager.create_directory_structure(self.temp_dir, structure)
        
        assert len(self.file_manager.get_created_paths()) > 0
        
        self.file_manager.clear_tracking()
        
        assert len(self.file_manager.get_created_paths()) == 0