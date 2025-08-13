"""Tests for artifact management functionality."""

import os
import tempfile
import shutil
import json
import zipfile
import tarfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.managers.artifact_manager import ArtifactManager
from src.models.artifacts import (
    ArtifactType, ArtifactStatus, ArtifactInfo, ArtifactDetector
)


class TestArtifactDetector:
    """Test artifact detection functionality."""
    
    def test_detect_artifact_type_executable(self):
        """Test detection of executable artifacts."""
        assert ArtifactDetector.detect_artifact_type("server.exe") == ArtifactType.EXECUTABLE
        assert ArtifactDetector.detect_artifact_type("app.bin") == ArtifactType.EXECUTABLE
        assert ArtifactDetector.detect_artifact_type("program") == ArtifactType.UNKNOWN
    
    def test_detect_artifact_type_library(self):
        """Test detection of library artifacts."""
        assert ArtifactDetector.detect_artifact_type("lib.dll") == ArtifactType.LIBRARY
        assert ArtifactDetector.detect_artifact_type("lib.so") == ArtifactType.LIBRARY
        assert ArtifactDetector.detect_artifact_type("lib.dylib") == ArtifactType.LIBRARY
        assert ArtifactDetector.detect_artifact_type("app.jar") == ArtifactType.LIBRARY
    
    def test_detect_artifact_type_package(self):
        """Test detection of package artifacts."""
        assert ArtifactDetector.detect_artifact_type("package.whl") == ArtifactType.PACKAGE
        assert ArtifactDetector.detect_artifact_type("archive.tar.gz") == ArtifactType.PACKAGE
        assert ArtifactDetector.detect_artifact_type("bundle.zip") == ArtifactType.PACKAGE
    
    def test_detect_artifact_type_configuration(self):
        """Test detection of configuration artifacts."""
        assert ArtifactDetector.detect_artifact_type("config.json") == ArtifactType.CONFIGURATION
        assert ArtifactDetector.detect_artifact_type("settings.yaml") == ArtifactType.CONFIGURATION
        assert ArtifactDetector.detect_artifact_type("app.toml") == ArtifactType.CONFIGURATION
    
    def test_detect_artifact_type_source_map(self):
        """Test detection of source map artifacts."""
        assert ArtifactDetector.detect_artifact_type("app.js.map") == ArtifactType.SOURCE_MAP
        assert ArtifactDetector.detect_artifact_type("style.css.map") == ArtifactType.SOURCE_MAP
        assert ArtifactDetector.detect_artifact_type("bundle.map") == ArtifactType.SOURCE_MAP
    
    def test_is_likely_artifact_npm_scripts(self):
        """Test artifact likelihood detection for npm scripts."""
        assert ArtifactDetector.is_likely_artifact("dist/index.js", "npm scripts")
        assert ArtifactDetector.is_likely_artifact("build/bundle.js", "npm scripts")
        assert ArtifactDetector.is_likely_artifact("package.json", "npm scripts")
        # Source files should not be considered artifacts
        assert not ArtifactDetector.is_likely_artifact("src/main.ts", "npm scripts")
    
    def test_is_likely_artifact_python_setuptools(self):
        """Test artifact likelihood detection for Python setuptools."""
        assert ArtifactDetector.is_likely_artifact("dist/package.whl", "setuptools")
        assert ArtifactDetector.is_likely_artifact("build/lib/module.py", "setuptools")
        assert not ArtifactDetector.is_likely_artifact("src/main.py", "setuptools")
    
    def test_get_expected_artifacts(self):
        """Test getting expected artifacts for build tools."""
        npm_expected = ArtifactDetector.get_expected_artifacts("npm scripts", "/project")
        assert "package.json" in npm_expected
        assert "dist/*" in npm_expected
        
        python_expected = ArtifactDetector.get_expected_artifacts("setuptools", "/project")
        assert "setup.py" in python_expected
        assert "dist/*" in python_expected


class TestArtifactManager:
    """Test artifact manager functionality."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project directory with sample artifacts."""
        temp_dir = tempfile.mkdtemp()
        
        # Create project structure
        dist_dir = os.path.join(temp_dir, "dist")
        os.makedirs(dist_dir)
        
        # Create sample artifacts
        artifacts = {
            "dist/index.js": "console.log('Hello World');",
            "dist/style.css": "body { margin: 0; }",
            "dist/index.html": "<html><body>Test</body></html>",
            "package.json": json.dumps({"name": "test-project", "version": "1.0.0"}),
        }
        
        for file_path, content in artifacts.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        yield temp_dir
        
        # Cleanup
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def artifact_manager(self):
        """Create an artifact manager instance."""
        return ArtifactManager()
    
    def test_detect_and_collect_artifacts(self, artifact_manager, temp_project):
        """Test artifact detection and collection."""
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm scripts"
        )
        
        assert collection.project_path == temp_project
        assert collection.build_tool == "npm scripts"
        assert len(collection.artifacts) > 0
        assert collection.total_size > 0
        
        # Check that we found expected artifacts
        artifact_paths = [a.relative_path for a in collection.artifacts]
        assert any("index.js" in path for path in artifact_paths)
        assert any("package.json" in path for path in artifact_paths)
    
    def test_validate_artifacts(self, artifact_manager, temp_project):
        """Test artifact validation."""
        # First collect artifacts
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        
        # Then validate them
        validation_results = artifact_manager.validate_artifacts(collection.artifacts)
        
        assert len(validation_results) == len(collection.artifacts)
        
        # All artifacts should be valid since they exist and have correct checksums
        valid_results = [r for r in validation_results if r.is_valid]
        assert len(valid_results) > 0
    
    def test_package_artifacts_zip(self, artifact_manager, temp_project):
        """Test packaging artifacts as ZIP."""
        # Collect artifacts
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        
        # Package as ZIP
        output_path = os.path.join(temp_project, "artifacts.zip")
        result = artifact_manager.package_artifacts(
            collection.artifacts, output_path, "zip"
        )
        
        assert result.success
        assert result.package_path == output_path
        assert os.path.exists(output_path)
        assert result.package_size > 0
        
        # Verify ZIP contents
        with zipfile.ZipFile(output_path, 'r') as zip_file:
            zip_contents = zip_file.namelist()
            assert len(zip_contents) > 0
    
    def test_package_artifacts_tar_gz(self, artifact_manager, temp_project):
        """Test packaging artifacts as TAR.GZ."""
        # Collect artifacts
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        
        # Package as TAR.GZ
        output_path = os.path.join(temp_project, "artifacts.tar.gz")
        result = artifact_manager.package_artifacts(
            collection.artifacts, output_path, "tar.gz"
        )
        
        assert result.success
        assert result.package_path == output_path
        assert os.path.exists(output_path)
        assert result.package_size > 0
        
        # Verify TAR contents
        with tarfile.open(output_path, 'r:gz') as tar_file:
            tar_contents = tar_file.getnames()
            assert len(tar_contents) > 0
    
    def test_generate_artifact_report(self, artifact_manager, temp_project):
        """Test artifact report generation."""
        # Collect artifacts
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        
        # Validate artifacts
        validation_results = artifact_manager.validate_artifacts(collection.artifacts)
        
        # Generate report
        report = artifact_manager.generate_artifact_report(
            collection, validation_results
        )
        
        assert report.project_path == temp_project
        assert report.build_tool == "npm-scripts"
        assert report.total_artifacts > 0
        assert report.valid_artifacts >= 0
        assert report.total_size > 0
        assert len(report.artifacts) > 0
        
        # Test report serialization
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "project_path" in report_dict
        
        report_json = report.to_json()
        assert isinstance(report_json, str)
        parsed = json.loads(report_json)
        assert parsed["project_path"] == temp_project
    
    def test_save_artifact_report(self, artifact_manager, temp_project):
        """Test saving artifact report to file."""
        # Create a simple report
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        report = artifact_manager.generate_artifact_report(collection)
        
        # Save report
        report_path = os.path.join(temp_project, "artifact_report.json")
        success = artifact_manager.save_artifact_report(report, report_path)
        
        assert success
        assert os.path.exists(report_path)
        
        # Verify report contents
        with open(report_path, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report["project_path"] == temp_project
        assert saved_report["build_tool"] == "npm-scripts"
    
    def test_artifact_validation_missing_file(self, artifact_manager):
        """Test validation of missing artifacts."""
        # Create artifact info for non-existent file
        artifact = ArtifactInfo(
            path="/nonexistent/file.js",
            relative_path="file.js",
            size=100,
            checksum="abc123",
            artifact_type=ArtifactType.UNKNOWN,
            status=ArtifactStatus.UNKNOWN,
            created_time=0.0,
            metadata={}
        )
        
        validation_results = artifact_manager.validate_artifacts([artifact])
        
        assert len(validation_results) == 1
        result = validation_results[0]
        assert not result.is_valid
        assert "does not exist" in " ".join(result.errors).lower()
    
    def test_artifact_size_limits(self, artifact_manager, temp_project):
        """Test artifact size limit enforcement."""
        # Create a large file
        large_file_path = os.path.join(temp_project, "large_file.bin")
        with open(large_file_path, 'wb') as f:
            f.write(b'0' * (artifact_manager.max_single_file_size + 1))
        
        # Try to collect artifacts
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        
        # Large file should be skipped
        large_file_artifacts = [
            a for a in collection.artifacts 
            if "large_file.bin" in a.path
        ]
        assert len(large_file_artifacts) == 0
    
    def test_configuration_validation(self, artifact_manager, temp_project):
        """Test validation of configuration files."""
        # Create valid and invalid JSON files
        valid_json_path = os.path.join(temp_project, "valid.json")
        invalid_json_path = os.path.join(temp_project, "invalid.json")
        
        with open(valid_json_path, 'w') as f:
            json.dump({"test": "value"}, f)
        
        with open(invalid_json_path, 'w') as f:
            f.write('{"invalid": json}')
        
        # Create artifact info
        valid_artifact = artifact_manager._create_artifact_info(valid_json_path, temp_project)
        invalid_artifact = artifact_manager._create_artifact_info(invalid_json_path, temp_project)
        
        # Validate
        valid_result = artifact_manager._validate_single_artifact(valid_artifact)
        invalid_result = artifact_manager._validate_single_artifact(invalid_artifact)
        
        assert valid_result.is_valid
        assert not invalid_result.is_valid
        assert any("Invalid JSON" in error for error in invalid_result.errors)
    
    def test_package_validation(self, artifact_manager, temp_project):
        """Test validation of package files."""
        # Create a valid ZIP file
        zip_path = os.path.join(temp_project, "test.zip")
        with zipfile.ZipFile(zip_path, 'w') as zip_file:
            zip_file.writestr("test.txt", "test content")
        
        # Create artifact info
        artifact = artifact_manager._create_artifact_info(zip_path, temp_project)
        
        # Validate
        result = artifact_manager._validate_single_artifact(artifact)
        
        assert result.is_valid
        assert result.validation_checks.get("valid_zip", False)
    
    def test_unsupported_package_format(self, artifact_manager, temp_project):
        """Test handling of unsupported package formats."""
        collection = artifact_manager.detect_and_collect_artifacts(
            temp_project, "npm-scripts"
        )
        
        output_path = os.path.join(temp_project, "artifacts.rar")
        result = artifact_manager.package_artifacts(
            collection.artifacts, output_path, "rar"
        )
        
        assert not result.success
        assert "Unsupported package format" in " ".join(result.errors)
    
    def test_empty_artifact_collection(self, artifact_manager):
        """Test handling of empty artifact collections."""
        temp_dir = tempfile.mkdtemp()
        try:
            collection = artifact_manager.detect_and_collect_artifacts(
                temp_dir, "npm-scripts"
            )
            
            assert collection.project_path == temp_dir
            assert len(collection.artifacts) == 0
            assert collection.total_size == 0
            
            # Generate report for empty collection
            report = artifact_manager.generate_artifact_report(collection)
            assert report.total_artifacts == 0
            assert not report.build_success  # No artifacts means build didn't succeed
            
        finally:
            shutil.rmtree(temp_dir)


class TestArtifactIntegration:
    """Integration tests for artifact management."""
    
    def test_full_artifact_workflow(self):
        """Test complete artifact management workflow."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create a realistic project structure
            project_files = {
                "package.json": json.dumps({
                    "name": "test-mcp-server",
                    "version": "1.0.0",
                    "scripts": {"build": "tsc"}
                }),
                "dist/index.js": "exports.default = function() { return 'MCP Server'; };",
                "dist/index.d.ts": "export default function(): string;",
                "dist/package.json": json.dumps({"name": "test-mcp-server", "main": "index.js"}),
                "README.md": "# Test MCP Server\n\nA test server.",
            }
            
            for file_path, content in project_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            # Initialize artifact manager
            manager = ArtifactManager()
            
            # Step 1: Detect and collect artifacts
            collection = manager.detect_and_collect_artifacts(temp_dir, "npm-scripts")
            assert len(collection.artifacts) > 0
            
            # Step 2: Validate artifacts
            validation_results = manager.validate_artifacts(collection.artifacts)
            valid_count = sum(1 for r in validation_results if r.is_valid)
            assert valid_count > 0
            
            # Step 3: Package artifacts
            package_path = os.path.join(temp_dir, "mcp-server-artifacts.zip")
            packaging_result = manager.package_artifacts(
                collection.artifacts, package_path, "zip"
            )
            assert packaging_result.success
            assert os.path.exists(package_path)
            
            # Step 4: Generate comprehensive report
            report = manager.generate_artifact_report(
                collection, validation_results, packaging_result
            )
            assert report.build_success
            assert report.total_artifacts > 0
            assert report.packaging_info is not None
            
            # Step 5: Save report
            report_path = os.path.join(temp_dir, "artifact_report.json")
            success = manager.save_artifact_report(report, report_path)
            assert success
            assert os.path.exists(report_path)
            
            # Verify report contents
            with open(report_path, 'r') as f:
                saved_report = json.load(f)
            
            assert saved_report["build_success"]
            assert saved_report["total_artifacts"] > 0
            assert saved_report["packaging_info"]["success"]
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__])