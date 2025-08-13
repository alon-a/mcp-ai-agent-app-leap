"""Tests for build system artifact management integration."""

import os
import tempfile
import shutil
import json
from unittest.mock import patch, MagicMock

import pytest

from src.managers.build_system import BuildSystemManager
from src.models.artifacts import ArtifactReport


class TestBuildSystemArtifacts:
    """Test build system artifact management integration."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with build artifacts."""
        temp_dir = tempfile.mkdtemp()
        
        # Create npm project structure
        project_files = {
            "package.json": json.dumps({
                "name": "test-mcp-server",
                "version": "1.0.0",
                "scripts": {"build": "echo 'Building...'"},
                "main": "dist/index.js"
            }),
            "package-lock.json": json.dumps({"lockfileVersion": 2}),  # Add lock file
            "dist/index.js": "console.log('MCP Server');",
            "dist/index.d.ts": "export default function(): void;",
            "dist/package.json": json.dumps({"name": "test-mcp-server"}),
        }
        
        for file_path, content in project_files.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def build_manager(self):
        """Create a build system manager."""
        return BuildSystemManager()
    
    def test_get_build_artifacts(self, build_manager, temp_project):
        """Test getting build artifacts from a project."""
        artifacts = build_manager.get_build_artifacts(temp_project)
        
        assert isinstance(artifacts, list)
        assert len(artifacts) > 0
        
        # Check that we found expected artifacts
        artifact_names = [os.path.basename(path) for path in artifacts]
        assert "index.js" in artifact_names
        assert "package.json" in artifact_names
    
    def test_get_build_artifacts_no_build_system(self, build_manager):
        """Test getting artifacts when no build system is detected."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Empty directory with no build system indicators
            artifacts = build_manager.get_build_artifacts(temp_dir)
            assert artifacts == []
        finally:
            shutil.rmtree(temp_dir)
    
    def test_validate_build_artifacts(self, build_manager, temp_project):
        """Test validating build artifacts."""
        report = build_manager.validate_build_artifacts(temp_project)
        
        assert isinstance(report, ArtifactReport)
        assert report.project_path == temp_project
        assert report.build_tool == "npm scripts"
        assert report.total_artifacts > 0
        assert report.valid_artifacts > 0
        
        # Should have found some valid artifacts
        assert report.build_success or report.valid_artifacts > 0
    
    def test_validate_build_artifacts_no_build_system(self, build_manager):
        """Test validating artifacts when no build system is detected."""
        temp_dir = tempfile.mkdtemp()
        try:
            report = build_manager.validate_build_artifacts(temp_dir)
            
            assert isinstance(report, ArtifactReport)
            assert report.project_path == temp_dir
            assert report.build_tool == "unknown"
            assert report.total_artifacts == 0
            assert not report.build_success
        finally:
            shutil.rmtree(temp_dir)
    
    def test_package_build_artifacts_zip(self, build_manager, temp_project):
        """Test packaging build artifacts as ZIP."""
        output_path = os.path.join(temp_project, "artifacts.zip")
        success = build_manager.package_build_artifacts(
            temp_project, output_path, "zip"
        )
        
        assert success
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_package_build_artifacts_tar_gz(self, build_manager, temp_project):
        """Test packaging build artifacts as TAR.GZ."""
        output_path = os.path.join(temp_project, "artifacts.tar.gz")
        success = build_manager.package_build_artifacts(
            temp_project, output_path, "tar.gz"
        )
        
        assert success
        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0
    
    def test_package_build_artifacts_no_build_system(self, build_manager):
        """Test packaging when no build system is detected."""
        temp_dir = tempfile.mkdtemp()
        try:
            output_path = os.path.join(temp_dir, "artifacts.zip")
            success = build_manager.package_build_artifacts(
                temp_dir, output_path, "zip"
            )
            
            assert not success
            assert not os.path.exists(output_path)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_package_build_artifacts_no_artifacts(self, build_manager):
        """Test packaging when no artifacts are found."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create package.json but no dist directory
            package_json = os.path.join(temp_dir, "package.json")
            with open(package_json, 'w') as f:
                json.dump({"name": "test", "scripts": {"build": "echo"}}, f)
            
            output_path = os.path.join(temp_dir, "artifacts.zip")
            success = build_manager.package_build_artifacts(
                temp_dir, output_path, "zip"
            )
            
            assert not success
            assert not os.path.exists(output_path)
        finally:
            shutil.rmtree(temp_dir)
    
    def test_build_execution_with_artifact_collection(self, build_manager, temp_project):
        """Test that build execution properly collects artifacts."""
        # Mock successful command execution
        with patch.object(build_manager, '_execute_single_command') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "logs": ["Build completed successfully"],
                "errors": []
            }
            
            # Execute build
            result = build_manager.execute_build(temp_project, ["npm run build"])
            
            assert result.success
            assert len(result.artifacts) > 0
            
            # Check that artifacts were collected from dist directory
            assert any("index.js" in artifact for artifact in result.artifacts)
    
    def test_python_project_artifacts(self, build_manager):
        """Test artifact detection for Python projects."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create Python project structure
            project_files = {
                "pyproject.toml": """
[build-system]
requires = ["setuptools", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "test-mcp-server"
version = "1.0.0"
""",
                "dist/test_mcp_server-1.0.0-py3-none-any.whl": "fake wheel content",
                "dist/test_mcp_server-1.0.0.tar.gz": "fake source distribution",
            }
            
            for file_path, content in project_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            # Get artifacts
            artifacts = build_manager.get_build_artifacts(temp_dir)
            
            assert len(artifacts) > 0
            artifact_names = [os.path.basename(path) for path in artifacts]
            assert any(".whl" in name for name in artifact_names)
            assert any(".tar.gz" in name for name in artifact_names)
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_typescript_project_artifacts(self, build_manager):
        """Test artifact detection for TypeScript projects."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create TypeScript project structure
            project_files = {
                "tsconfig.json": json.dumps({
                    "compilerOptions": {
                        "outDir": "dist",
                        "declaration": True
                    }
                }),
                "dist/index.js": "exports.default = function() {};",
                "dist/index.d.ts": "export default function(): void;",
                "dist/index.js.map": '{"version":3,"sources":["../src/index.ts"]}',
            }
            
            for file_path, content in project_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            # Get artifacts
            artifacts = build_manager.get_build_artifacts(temp_dir)
            
            assert len(artifacts) > 0
            artifact_names = [os.path.basename(path) for path in artifacts]
            assert "index.js" in artifact_names
            assert "index.d.ts" in artifact_names
            assert "index.js.map" in artifact_names
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_cargo_project_artifacts(self, build_manager):
        """Test artifact detection for Rust/Cargo projects."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Create Cargo project structure
            project_files = {
                "Cargo.toml": """
[package]
name = "test-mcp-server"
version = "1.0.0"
edition = "2021"
""",
                "target/release/test-mcp-server.exe": "fake executable",
                "target/release/deps/libtest_mcp_server.rlib": "fake library",
            }
            
            for file_path, content in project_files.items():
                full_path = os.path.join(temp_dir, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w') as f:
                    f.write(content)
            
            # Get artifacts
            artifacts = build_manager.get_build_artifacts(temp_dir)
            
            assert len(artifacts) > 0
            artifact_names = [os.path.basename(path) for path in artifacts]
            assert any(".exe" in name or "test-mcp-server" in name for name in artifact_names)
            
        finally:
            shutil.rmtree(temp_dir)
    
    def test_artifact_report_integration(self, build_manager, temp_project):
        """Test integration between build system and artifact reporting."""
        # Validate artifacts and get report
        report = build_manager.validate_build_artifacts(temp_project)
        
        # Verify report structure
        assert hasattr(report, 'project_path')
        assert hasattr(report, 'build_tool')
        assert hasattr(report, 'total_artifacts')
        assert hasattr(report, 'valid_artifacts')
        assert hasattr(report, 'artifacts')
        assert hasattr(report, 'validation_summary')
        
        # Verify report content
        assert report.project_path == temp_project
        assert report.build_tool in ["npm scripts", "tsc", "webpack", "vite"]
        assert report.total_artifacts > 0
        
        # Test report serialization
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "artifacts" in report_dict
        
        report_json = report.to_json()
        assert isinstance(report_json, str)
        parsed_report = json.loads(report_json)
        assert parsed_report["project_path"] == temp_project
    
    def test_build_result_storage(self, build_manager, temp_project):
        """Test storing and loading build results."""
        # Mock successful command execution
        with patch.object(build_manager, '_execute_single_command') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "logs": ["Build completed successfully"],
                "errors": []
            }
            
            # Execute build
            result = build_manager.execute_build(temp_project, ["npm run build"])
            
            assert result.success
            assert result.build_tool is not None
            assert result.artifact_report is not None
            
            # Check that build result was stored
            storage_path = os.path.join(temp_project, "build-result.json")
            assert os.path.exists(storage_path)
            
            # Load and verify stored result
            loaded_result = build_manager.load_build_result(storage_path)
            assert loaded_result is not None
            assert loaded_result.success == result.success
            assert loaded_result.project_path == result.project_path
            assert loaded_result.build_tool == result.build_tool
    
    def test_build_history(self, build_manager, temp_project):
        """Test build history tracking."""
        # Mock successful command execution
        with patch.object(build_manager, '_execute_single_command') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "logs": ["Build completed successfully"],
                "errors": []
            }
            
            # Execute build
            build_manager.execute_build(temp_project, ["npm run build"])
            
            # Get build history
            history = build_manager.get_build_history(temp_project)
            
            assert len(history) > 0
            assert history[0]["success"] is True
            assert "build_tool" in history[0]
            assert "artifacts_count" in history[0]
            assert "execution_time" in history[0]
    
    def test_build_summary_generation(self, build_manager, temp_project):
        """Test comprehensive build summary generation."""
        # Generate build summary
        summary = build_manager.generate_build_summary(temp_project)
        
        assert isinstance(summary, dict)
        assert "project_path" in summary
        assert "build_system" in summary
        assert "artifacts" in summary
        assert "recommendations" in summary
        
        assert summary["project_path"] == temp_project
        assert summary["build_system"] in ["npm scripts", "tsc", "webpack", "vite"]
        assert isinstance(summary["artifacts"], dict)
        assert isinstance(summary["recommendations"], list)
    
    def test_build_report_export(self, build_manager, temp_project):
        """Test exporting comprehensive build reports."""
        output_path = os.path.join(temp_project, "build-report.json")
        
        # Export build report
        success = build_manager.export_build_report(
            temp_project, output_path, include_artifacts=True
        )
        
        assert success
        assert os.path.exists(output_path)
        
        # Verify report content
        with open(output_path, 'r') as f:
            report_data = json.load(f)
        
        assert "project_path" in report_data
        assert "build_system" in report_data
        assert "artifacts" in report_data
        assert "detailed_artifacts" in report_data
        assert report_data["project_path"] == temp_project
    
    def test_enhanced_build_result_with_artifacts(self, build_manager, temp_project):
        """Test enhanced build result with comprehensive artifact information."""
        # Mock successful command execution
        with patch.object(build_manager, '_execute_single_command') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "logs": ["Build completed successfully"],
                "errors": []
            }
            
            # Execute build
            result = build_manager.execute_build(temp_project, ["npm run build"])
            
            # Verify enhanced build result
            assert result.success
            assert result.build_tool is not None
            assert result.artifact_report is not None
            
            # Check artifact report structure
            artifact_report = result.artifact_report
            assert "total_artifacts" in artifact_report
            assert "valid_artifacts" in artifact_report
            assert "total_size" in artifact_report
            assert "validation_summary" in artifact_report
            
            # Check that detailed artifact report was saved
            report_path = os.path.join(temp_project, "build-artifacts-report.json")
            assert os.path.exists(report_path)


if __name__ == "__main__":
    pytest.main([__file__])