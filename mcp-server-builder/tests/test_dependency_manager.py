"""Tests for dependency manager functionality."""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.managers.dependency_manager import DependencyManagerImpl
from src.models.enums import PackageManager


class TestDependencyManager:
    """Test cases for DependencyManager implementation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dependency_manager = DependencyManagerImpl()
    
    def test_detect_npm_project(self):
        """Test detection of npm project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.NPM.value
    
    def test_detect_yarn_project(self):
        """Test detection of yarn project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json and yarn.lock
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            yarn_lock = Path(temp_dir) / "yarn.lock"
            yarn_lock.write_text("# yarn lockfile")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.YARN.value
    
    def test_detect_pnpm_project(self):
        """Test detection of pnpm project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json and pnpm-lock.yaml
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            pnpm_lock = Path(temp_dir) / "pnpm-lock.yaml"
            pnpm_lock.write_text("lockfileVersion: 5.4")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.PNPM.value
    
    def test_detect_pip_project(self):
        """Test detection of pip project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("requests==2.28.0")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.PIP.value
    
    def test_detect_poetry_project(self):
        """Test detection of poetry project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml with poetry section
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text("""
[tool.poetry]
name = "test-project"
version = "0.1.0"
""")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.POETRY.value
    
    def test_detect_cargo_project(self):
        """Test detection of cargo project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create Cargo.toml
            cargo_toml = Path(temp_dir) / "Cargo.toml"
            cargo_toml.write_text("""
[package]
name = "test-project"
version = "0.1.0"
""")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.CARGO.value
    
    def test_detect_go_mod_project(self):
        """Test detection of go mod project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create go.mod
            go_mod = Path(temp_dir) / "go.mod"
            go_mod.write_text("module test-project\n\ngo 1.19")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.GO_MOD.value
    
    def test_detect_maven_project(self):
        """Test detection of maven project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pom.xml
            pom_xml = Path(temp_dir) / "pom.xml"
            pom_xml.write_text("""
<project>
    <groupId>com.example</groupId>
    <artifactId>test-project</artifactId>
    <version>1.0.0</version>
</project>
""")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.MAVEN.value
    
    def test_detect_gradle_project(self):
        """Test detection of gradle project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create build.gradle
            build_gradle = Path(temp_dir) / "build.gradle"
            build_gradle.write_text("plugins { id 'java' }")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.GRADLE.value
    
    def test_detect_multiple_package_managers(self):
        """Test detection of multiple package managers in one project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files for multiple package managers
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("requests==2.28.0")
            
            result = self.dependency_manager.detect_multiple_package_managers(temp_dir)
            assert PackageManager.NPM.value in result
            assert PackageManager.PIP.value in result
            assert len(result) == 2
    
    def test_no_package_manager_detected(self):
        """Test when no package manager is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Empty directory
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result is None
    
    def test_nonexistent_directory(self):
        """Test detection with nonexistent directory."""
        result = self.dependency_manager.detect_package_manager("/nonexistent/path")
        assert result is None
    
    def test_priority_selection_poetry_over_pip(self):
        """Test that poetry is selected over pip when both are present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create both poetry and pip files
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text("""
[tool.poetry]
name = "test-project"
version = "0.1.0"
""")
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("requests==2.28.0")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.POETRY.value
    
    def test_priority_selection_yarn_over_npm(self):
        """Test that yarn is selected over npm when both are present."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json and yarn.lock
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            yarn_lock = Path(temp_dir) / "yarn.lock"
            yarn_lock.write_text("# yarn lockfile")
            
            result = self.dependency_manager.detect_package_manager(temp_dir)
            assert result == PackageManager.YARN.value
    
    @patch('subprocess.run')
    def test_check_version_compatibility_success(self, mock_run):
        """Test successful version compatibility check."""
        mock_run.return_value = MagicMock(returncode=0, stdout="8.19.2")
        
        result = self.dependency_manager.check_version_compatibility("/test/path", "npm")
        
        assert result["compatible"] is True
        assert result["installed"] is True
        assert result["version"] == "8.19.2"
        assert result["error"] is None
    
    @patch('subprocess.run')
    def test_check_version_compatibility_command_not_found(self, mock_run):
        """Test version compatibility check when command is not found."""
        mock_run.side_effect = FileNotFoundError()
        
        result = self.dependency_manager.check_version_compatibility("/test/path", "npm")
        
        assert result["compatible"] is False
        assert result["installed"] is False
        assert result["version"] is None
        assert "not installed" in result["error"]
    
    @patch('subprocess.run')
    def test_check_version_compatibility_old_version(self, mock_run):
        """Test version compatibility check with old version."""
        mock_run.return_value = MagicMock(returncode=0, stdout="5.0.0")
        
        result = self.dependency_manager.check_version_compatibility("/test/path", "npm")
        
        assert result["compatible"] is False
        assert result["installed"] is True
        assert result["version"] == "5.0.0"
        assert "below minimum" in result["error"]
    
    def test_check_version_compatibility_unsupported_manager(self):
        """Test version compatibility check with unsupported package manager."""
        result = self.dependency_manager.check_version_compatibility("/test/path", "unsupported")
        
        assert result["compatible"] is False
        assert result["installed"] is False
        assert "Unsupported package manager" in result["error"]
    
    def test_validate_poetry_pyproject_toml(self):
        """Test validation of poetry pyproject.toml file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml with poetry section
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text("""
[tool.poetry]
name = "test-project"
version = "0.1.0"
""")
            
            result = self.dependency_manager._validate_package_manager_file(
                PackageManager.POETRY, pyproject
            )
            assert result is True
    
    def test_validate_non_poetry_pyproject_toml(self):
        """Test validation of non-poetry pyproject.toml file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create pyproject.toml without poetry section
            pyproject = Path(temp_dir) / "pyproject.toml"
            pyproject.write_text("""
[build-system]
requires = ["setuptools"]
""")
            
            result = self.dependency_manager._validate_package_manager_file(
                PackageManager.POETRY, pyproject
            )
            assert result is False
    
    def test_extract_version_number_patterns(self):
        """Test version number extraction from various formats."""
        test_cases = [
            ("8.19.2", "8.19.2"),
            ("v1.22.19", "1.22.19"),
            ("npm 8.19.2", "8.19.2"),
            ("yarn 1.22", "1.22"),
            ("poetry version 1.2.2", "1.2.2"),
            ("invalid output", None)
        ]
        
        for output, expected in test_cases:
            result = self.dependency_manager._extract_version_number(output)
            assert result == expected   
 
    # Tests for task 4.2 - dependency installation
    
    @patch('subprocess.run')
    def test_install_dependencies_success(self, mock_run):
        """Test successful dependency installation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock successful installation
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = self.dependency_manager.install_dependencies(temp_dir, ["express", "lodash"])
            
            assert result.success is True
            assert len(result.installed_packages) == 2
            assert "express" in result.installed_packages
            assert "lodash" in result.installed_packages
            assert len(result.failed_packages) == 0
    
    @patch('subprocess.run')
    def test_install_dependencies_partial_failure(self, mock_run):
        """Test dependency installation with partial failures."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock mixed success/failure
            def mock_run_side_effect(*args, **kwargs):
                if "express" in args[0]:
                    return MagicMock(returncode=0, stdout="", stderr="")
                else:
                    return MagicMock(returncode=1, stdout="", stderr="Package not found")
            
            mock_run.side_effect = mock_run_side_effect
            
            result = self.dependency_manager.install_dependencies(temp_dir, ["express", "nonexistent"])
            
            assert result.success is False
            assert len(result.installed_packages) == 1
            assert "express" in result.installed_packages
            assert len(result.failed_packages) == 1
            assert "nonexistent" in result.failed_packages
    
    def test_install_dependencies_no_package_manager(self):
        """Test installation when no package manager is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Empty directory with no package manager files
            result = self.dependency_manager.install_dependencies(temp_dir, ["express"])
            
            assert result.success is False
            assert len(result.installed_packages) == 0
            assert len(result.failed_packages) == 1
            assert "No package manager detected" in result.errors[0]
    
    def test_install_dependencies_nonexistent_path(self):
        """Test installation with nonexistent project path."""
        result = self.dependency_manager.install_dependencies("/nonexistent/path", ["express"])
        
        assert result.success is False
        assert len(result.installed_packages) == 0
        assert len(result.failed_packages) == 1
        assert "does not exist" in result.errors[0]
    
    @patch('subprocess.run')
    def test_install_dependencies_with_custom_sources(self, mock_run):
        """Test installation with custom package sources."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock successful installation
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            result = self.dependency_manager.install_dependencies_with_manager(
                temp_dir, "npm", ["express"], ["https://custom-registry.com"]
            )
            
            assert result.success is True
            assert len(result.installed_packages) == 1
            # Verify custom registry was used in command
            assert mock_run.call_count >= 1
            # Check the install command (should be the last call)
            install_call = mock_run.call_args_list[-1]
            call_args = install_call[0][0]
            assert "--registry" in call_args
            assert "https://custom-registry.com" in call_args
    
    def test_install_dependencies_unsupported_manager(self):
        """Test installation with unsupported package manager."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.dependency_manager.install_dependencies_with_manager(
                temp_dir, "unsupported", ["express"]
            )
            
            assert result.success is False
            assert "Unsupported package manager" in result.errors[0]
    
    def test_build_install_command_npm(self):
        """Test building install command for npm."""
        cmd = self.dependency_manager._build_install_command(
            PackageManager.NPM, "express", ["https://registry.npmjs.org"]
        )
        
        expected = ["npm", "install", "express", "--registry", "https://registry.npmjs.org"]
        assert cmd == expected
    
    def test_build_install_command_pip(self):
        """Test building install command for pip."""
        cmd = self.dependency_manager._build_install_command(
            PackageManager.PIP, "requests", ["https://pypi.org/simple"]
        )
        
        expected = ["pip", "install", "requests", "-i", "https://pypi.org/simple"]
        assert cmd == expected
    
    def test_build_install_command_poetry(self):
        """Test building install command for poetry."""
        cmd = self.dependency_manager._build_install_command(
            PackageManager.POETRY, "requests", ["https://pypi.org/simple"]
        )
        
        expected = ["poetry", "add", "requests", "--source", "https://pypi.org/simple"]
        assert cmd == expected
    
    def test_build_install_command_cargo(self):
        """Test building install command for cargo."""
        cmd = self.dependency_manager._build_install_command(
            PackageManager.CARGO, "serde"
        )
        
        expected = ["cargo", "add", "serde"]
        assert cmd == expected
    
    @patch('subprocess.run')
    def test_resolve_dependency_conflicts_npm(self, mock_run):
        """Test dependency conflict resolution for npm."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock audit output with vulnerabilities
            audit_output = json.dumps({
                "vulnerabilities": {
                    "lodash": {
                        "severity": "high",
                        "title": "Prototype Pollution"
                    }
                }
            })
            mock_run.return_value = MagicMock(returncode=0, stdout=audit_output, stderr="")
            
            result = self.dependency_manager.resolve_dependency_conflicts(temp_dir)
            
            assert result["success"] is True
            assert len(result["conflicts"]) == 1
            assert result["conflicts"][0]["package"] == "lodash"
            assert result["conflicts"][0]["type"] == "security"
            assert result["conflicts"][0]["severity"] == "high"
    
    @patch('subprocess.run')
    def test_resolve_dependency_conflicts_pip(self, mock_run):
        """Test dependency conflict resolution for pip."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("requests==2.28.0")
            
            # Mock pip check output with conflicts
            mock_run.return_value = MagicMock(
                returncode=1, 
                stdout="requests 2.28.0 has requirement urllib3>=1.21.1, but you have urllib3 1.20.0",
                stderr=""
            )
            
            result = self.dependency_manager.resolve_dependency_conflicts(temp_dir)
            
            assert result["success"] is True
            assert len(result["conflicts"]) == 1
            assert result["conflicts"][0]["type"] == "dependency"
            assert result["conflicts"][0]["severity"] == "error"
    
    def test_suggest_conflict_resolutions(self):
        """Test conflict resolution suggestions."""
        conflicts = [
            {
                "package": "lodash",
                "type": "security",
                "severity": "high",
                "description": "Prototype Pollution"
            },
            {
                "package": "requests",
                "type": "dependency",
                "severity": "error",
                "description": "Version conflict"
            }
        ]
        
        resolutions = self.dependency_manager._suggest_conflict_resolutions(conflicts)
        
        assert len(resolutions) == 2
        assert resolutions[0]["action"] == "update"
        assert "npm update lodash" in resolutions[0]["command"]
        assert resolutions[1]["action"] == "resolve_version"
    
    def test_parse_npm_audit_output_json(self):
        """Test parsing npm audit JSON output."""
        audit_output = json.dumps({
            "vulnerabilities": {
                "lodash": {
                    "severity": "high",
                    "title": "Prototype Pollution"
                },
                "minimist": {
                    "severity": "low",
                    "title": "Prototype Pollution"
                }
            }
        })
        
        conflicts = self.dependency_manager._parse_npm_audit_output(audit_output)
        
        assert len(conflicts) == 2
        assert conflicts[0]["package"] == "lodash"
        assert conflicts[0]["severity"] == "high"
        assert conflicts[1]["package"] == "minimist"
        assert conflicts[1]["severity"] == "low"
    
    def test_parse_npm_audit_output_text(self):
        """Test parsing npm audit text output."""
        audit_output = """
        found 2 vulnerabilities (1 low, 1 high)
        High severity vulnerability in lodash
        Low severity vulnerability in minimist
        """
        
        conflicts = self.dependency_manager._parse_npm_audit_output(audit_output)
        
        assert len(conflicts) == 2
        assert all("vulnerability" in conflict["description"].lower() for conflict in conflicts)
    
    # Tests for enhanced task 4.2 functionality
    
    def test_configure_npm_registries(self):
        """Test npm registry configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_sources = ["https://custom-registry.com"]
            registry_config = {
                "scoped_registries": {
                    "mycompany": "https://npm.mycompany.com"
                },
                "auth_tokens": {
                    "https://custom-registry.com": "token123"
                }
            }
            
            self.dependency_manager._configure_npm_registries(
                temp_dir, custom_sources, registry_config
            )
            
            npmrc_path = Path(temp_dir) / ".npmrc"
            assert npmrc_path.exists()
            
            content = npmrc_path.read_text()
            assert "registry=https://custom-registry.com" in content
            assert "@mycompany:registry=https://npm.mycompany.com" in content
            assert "_authToken=token123" in content
    
    def test_configure_pip_registries(self):
        """Test pip registry configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_sources = ["https://pypi.mycompany.com/simple", "https://pypi.org/simple"]
            registry_config = {
                "trusted_hosts": ["pypi.mycompany.com", "pypi.org"]
            }
            
            self.dependency_manager._configure_pip_registries(
                temp_dir, custom_sources, registry_config
            )
            
            pip_conf_path = Path(temp_dir) / "pip.conf"
            assert pip_conf_path.exists()
            
            content = pip_conf_path.read_text()
            assert "index-url = https://pypi.mycompany.com/simple" in content
            assert "extra-index-url = https://pypi.org/simple" in content
            assert "trusted-host = pypi.mycompany.com pypi.org" in content
    
    @patch('toml.load')
    @patch('toml.dump')
    def test_configure_poetry_registries(self, mock_dump, mock_load):
        """Test poetry registry configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Mock existing pyproject.toml
            mock_load.return_value = {"tool": {"poetry": {}}}
            
            custom_sources = ["https://pypi.mycompany.com/simple"]
            
            self.dependency_manager._configure_poetry_registries(
                temp_dir, custom_sources, None
            )
            
            # Verify toml.dump was called with correct structure
            mock_dump.assert_called_once()
            call_args = mock_dump.call_args[0][0]
            
            assert "tool" in call_args
            assert "poetry" in call_args["tool"]
            assert "source" in call_args["tool"]["poetry"]
            assert len(call_args["tool"]["poetry"]["source"]) == 1
            assert call_args["tool"]["poetry"]["source"][0]["url"] == "https://pypi.mycompany.com/simple"
            assert call_args["tool"]["poetry"]["source"][0]["default"] is True
    
    def test_configure_go_registries(self):
        """Test Go module registry configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_sources = ["https://goproxy.mycompany.com", "direct"]
            registry_config = {
                "sumdb": "sum.golang.org",
                "private_modules": ["github.com/mycompany/*"]
            }
            
            self.dependency_manager._configure_go_registries(
                temp_dir, custom_sources, registry_config
            )
            
            env_path = Path(temp_dir) / ".env"
            assert env_path.exists()
            
            content = env_path.read_text()
            assert "GOPROXY=https://goproxy.mycompany.com,direct" in content
            assert "GOSUMDB=sum.golang.org" in content
            assert "GOPRIVATE=github.com/mycompany/*" in content
    
    @patch('subprocess.run')
    def test_install_with_conflict_resolution_auto_success(self, mock_run):
        """Test automatic conflict resolution with successful resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock initial failure, then successful audit, then successful retry
            def mock_run_side_effect(*args, **kwargs):
                if "install" in args[0]:
                    if mock_run.call_count <= 1:
                        # First install attempt fails
                        return MagicMock(returncode=1, stdout="", stderr="Conflict detected")
                    else:
                        # Retry after resolution succeeds
                        return MagicMock(returncode=0, stdout="", stderr="")
                elif "audit" in args[0]:
                    # Audit returns conflicts
                    audit_output = json.dumps({
                        "vulnerabilities": {
                            "lodash": {"severity": "high", "title": "Prototype Pollution"}
                        }
                    })
                    return MagicMock(returncode=0, stdout=audit_output, stderr="")
                elif "update" in args[0]:
                    # Update command succeeds
                    return MagicMock(returncode=0, stdout="", stderr="")
                else:
                    return MagicMock(returncode=0, stdout="", stderr="")
            
            mock_run.side_effect = mock_run_side_effect
            
            result = self.dependency_manager.install_with_conflict_resolution(
                temp_dir, ["express"], "auto"
            )
            
            assert result.success is True
            assert len(result.installed_packages) == 1
            assert "express" in result.installed_packages
    
    @patch('subprocess.run')
    def test_install_with_conflict_resolution_strict_mode(self, mock_run):
        """Test strict mode conflict resolution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock initial failure and audit with conflicts
            def mock_run_side_effect(*args, **kwargs):
                if "install" in args[0]:
                    return MagicMock(returncode=1, stdout="", stderr="Conflict detected")
                elif "audit" in args[0]:
                    audit_output = json.dumps({
                        "vulnerabilities": {
                            "lodash": {"severity": "high", "title": "Prototype Pollution"}
                        }
                    })
                    return MagicMock(returncode=0, stdout=audit_output, stderr="")
                else:
                    return MagicMock(returncode=0, stdout="", stderr="")
            
            mock_run.side_effect = mock_run_side_effect
            
            result = self.dependency_manager.install_with_conflict_resolution(
                temp_dir, ["express"], "strict"
            )
            
            assert result.success is False
            assert "Strict mode" in result.errors[0]
            assert "conflicts detected" in result.errors[0]
    
    @patch('subprocess.run')
    def test_apply_automatic_resolutions(self, mock_run):
        """Test applying automatic conflict resolutions."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock successful resolution commands
            mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")
            
            resolutions = [
                {
                    "package": "lodash",
                    "action": "update",
                    "command": "npm update lodash",
                    "priority": "high"
                }
            ]
            
            result = self.dependency_manager._apply_automatic_resolutions(temp_dir, resolutions)
            
            assert result["success"] is True
            assert len(result["applied_resolutions"]) == 1
            assert result["applied_resolutions"][0]["package"] == "lodash"
            assert result["applied_resolutions"][0]["success"] is True
    
    # Tests for task 4.3 - dependency verification and validation
    
    def test_verify_installation_success(self):
        """Test successful dependency verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json with dependencies
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "express": "^4.18.0",
                    "lodash": "^4.17.21"
                }
            }))
            
            # Create mock node_modules structure
            node_modules = Path(temp_dir) / "node_modules"
            node_modules.mkdir()
            
            # Create express package
            express_dir = node_modules / "express"
            express_dir.mkdir()
            express_package_json = express_dir / "package.json"
            express_package_json.write_text(json.dumps({
                "name": "express",
                "version": "4.18.2"
            }))
            
            # Create lodash package
            lodash_dir = node_modules / "lodash"
            lodash_dir.mkdir()
            lodash_package_json = lodash_dir / "package.json"
            lodash_package_json.write_text(json.dumps({
                "name": "lodash",
                "version": "4.17.21"
            }))
            
            result = self.dependency_manager.verify_installation(temp_dir)
            
            assert result.success is True
            assert len(result.verified_packages) == 2
            assert "express" in result.verified_packages
            assert "lodash" in result.verified_packages
            assert len(result.missing_packages) == 0
    
    def test_verify_installation_missing_packages(self):
        """Test verification with missing packages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json with dependencies
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "express": "^4.18.0",
                    "missing-package": "^1.0.0"
                }
            }))
            
            # Create partial node_modules structure (missing one package)
            node_modules = Path(temp_dir) / "node_modules"
            node_modules.mkdir()
            
            express_dir = node_modules / "express"
            express_dir.mkdir()
            express_package_json = express_dir / "package.json"
            express_package_json.write_text(json.dumps({
                "name": "express",
                "version": "4.18.2"
            }))
            
            result = self.dependency_manager.verify_installation(temp_dir)
            
            assert result.success is False
            assert len(result.verified_packages) == 1
            assert "express" in result.verified_packages
            assert len(result.missing_packages) == 1
            assert "missing-package" in result.missing_packages
    
    def test_verify_installation_no_package_manager(self):
        """Test verification when no package manager is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Empty directory with no package manager files
            result = self.dependency_manager.verify_installation(temp_dir)
            
            assert result.success is False
            assert len(result.verified_packages) == 0
            assert len(result.missing_packages) == 0
            assert "No package manager detected" in result.errors[0]
    
    def test_verify_installation_nonexistent_path(self):
        """Test verification with nonexistent project path."""
        result = self.dependency_manager.verify_installation("/nonexistent/path")
        
        assert result.success is False
        assert "does not exist" in result.errors[0]
    
    @patch('subprocess.run')
    def test_verify_python_dependency_success(self, mock_run):
        """Test successful Python dependency verification."""
        # Mock pip show output
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="Name: requests\nVersion: 2.28.0\nSummary: Python HTTP library"
        )
        
        result = self.dependency_manager._verify_python_dependency(
            "/test/path", "requests", ">=2.0.0"
        )
        
        assert result["installed"] is True
        assert result["version"] == "2.28.0"
        assert result["version_compatible"] is True
        assert result["error"] is None
    
    @patch('subprocess.run')
    def test_verify_python_dependency_not_installed(self, mock_run):
        """Test Python dependency verification when package is not installed."""
        # Mock pip show failure
        mock_run.return_value = MagicMock(returncode=1, stdout="", stderr="Package not found")
        
        result = self.dependency_manager._verify_python_dependency(
            "/test/path", "nonexistent", None
        )
        
        assert result["installed"] is False
        assert result["version"] is None
        assert "not installed" in result["error"]
    
    def test_verify_npm_dependency_success(self):
        """Test successful npm dependency verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create node_modules structure
            node_modules = Path(temp_dir) / "node_modules" / "express"
            node_modules.mkdir(parents=True)
            
            package_json = node_modules / "package.json"
            package_json.write_text(json.dumps({
                "name": "express",
                "version": "4.18.2"
            }))
            
            result = self.dependency_manager._verify_npm_dependency(
                temp_dir, "express", "^4.18.0"
            )
            
            assert result["installed"] is True
            assert result["version"] == "4.18.2"
            assert result["version_compatible"] is True
            assert result["error"] is None
    
    def test_verify_npm_dependency_missing(self):
        """Test npm dependency verification when package is missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.dependency_manager._verify_npm_dependency(
                temp_dir, "missing-package", None
            )
            
            assert result["installed"] is False
            assert result["version"] is None
            assert "not found in node_modules" in result["error"]
    
    def test_check_version_compatibility_string(self):
        """Test version compatibility checking."""
        test_cases = [
            ("1.2.3", "^1.2.0", True),
            ("1.2.3", "^1.3.0", False),
            ("2.0.0", "^1.2.0", False),
            ("1.2.3", "~1.2.0", True),
            ("1.3.0", "~1.2.0", False),
            ("1.2.3", ">=1.0.0", True),
            ("0.9.0", ">=1.0.0", False),
            ("1.2.3", "1.2.3", True),
            ("1.2.4", "1.2.3", False)
        ]
        
        for installed, expected, should_match in test_cases:
            result = self.dependency_manager._check_version_compatibility_string(installed, expected)
            assert result == should_match, f"Failed for {installed} vs {expected}"
    
    def test_get_expected_dependencies_npm(self):
        """Test getting expected dependencies from package.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "express": "^4.18.0",
                    "lodash": "^4.17.21"
                },
                "devDependencies": {
                    "jest": "^29.0.0"
                }
            }))
            
            result = self.dependency_manager._get_expected_dependencies(
                temp_dir, PackageManager.NPM
            )
            
            assert len(result) == 3
            assert result["express"] == "^4.18.0"
            assert result["lodash"] == "^4.17.21"
            assert result["jest"] == "^29.0.0"
    
    def test_get_expected_dependencies_pip(self):
        """Test getting expected dependencies from requirements.txt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("""
requests==2.28.0
flask>=2.0.0
# This is a comment
pytest>=7.0.0
""")
            
            result = self.dependency_manager._get_expected_dependencies(
                temp_dir, PackageManager.PIP
            )
            
            assert len(result) == 3
            assert result["requests"] == "==2.28.0"
            assert result["flask"] == ">=2.0.0"
            assert result["pytest"] == ">=7.0.0"
    
    @patch('subprocess.run')
    def test_scan_security_vulnerabilities_npm(self, mock_run):
        """Test security vulnerability scanning for npm."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            # Mock npm audit output
            audit_output = json.dumps({
                "vulnerabilities": {
                    "lodash": {
                        "severity": "high",
                        "title": "Prototype Pollution",
                        "overview": "Lodash is vulnerable to prototype pollution",
                        "cwe": ["CWE-1321"],
                        "cvss": {"score": 7.5},
                        "range": ">=1.0.0 <4.17.21",
                        "fixAvailable": True
                    }
                }
            })
            mock_run.return_value = MagicMock(returncode=0, stdout=audit_output, stderr="")
            
            result = self.dependency_manager.scan_security_vulnerabilities(temp_dir)
            
            assert result["success"] is True
            assert len(result["vulnerabilities"]) == 1
            vuln = result["vulnerabilities"][0]
            assert vuln["package"] == "lodash"
            assert vuln["severity"] == "high"
            assert vuln["title"] == "Prototype Pollution"
            assert vuln["fixAvailable"] is True
    
    @patch('subprocess.run')
    def test_scan_security_vulnerabilities_python(self, mock_run):
        """Test security vulnerability scanning for Python."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("requests==2.25.0")
            
            # Mock safety output
            safety_output = json.dumps([{
                "package": "requests",
                "installed_version": "2.25.0",
                "vulnerability_id": "CVE-2021-33503",
                "advisory": "Requests is vulnerable to ReDoS",
                "vulnerable_spec": "<2.25.1"
            }])
            mock_run.return_value = MagicMock(returncode=0, stdout=safety_output, stderr="")
            
            result = self.dependency_manager.scan_security_vulnerabilities(temp_dir)
            
            assert result["success"] is True
            assert len(result["vulnerabilities"]) == 1
            vuln = result["vulnerabilities"][0]
            assert vuln["package"] == "requests"
            assert vuln["severity"] == "high"  # CVE- prefix maps to high
            assert vuln["installed_version"] == "2.25.0"
    
    def test_scan_security_vulnerabilities_no_package_manager(self):
        """Test vulnerability scanning when no package manager is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.dependency_manager.scan_security_vulnerabilities(temp_dir)
            
            assert result["success"] is False
            assert "No package manager detected" in result["error"]
    
    @patch('subprocess.run')
    def test_validate_dependency_compatibility_success(self, mock_run):
        """Test successful dependency compatibility validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "engines": {
                    "node": ">=14.0.0"
                }
            }))
            
            # Mock successful npm ls and node version
            mock_run.side_effect = [
                MagicMock(returncode=0, stdout="", stderr=""),  # npm ls
                MagicMock(returncode=0, stdout="v16.14.0", stderr="")  # node --version
            ]
            
            result = self.dependency_manager.validate_dependency_compatibility(temp_dir)
            
            assert result["success"] is True
            assert result["compatible"] is True
            assert len(result["issues"]) == 0
    
    def test_validate_dependency_compatibility_no_package_manager(self):
        """Test compatibility validation when no package manager is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = self.dependency_manager.validate_dependency_compatibility(temp_dir)
            
            assert result["success"] is False
            assert result["compatible"] is False
            assert "No package manager detected" in result["error"]
    
    def test_check_platform_compatibility(self):
        """Test platform compatibility checking."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json with platform restrictions
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "os": ["linux", "darwin"],
                "cpu": ["x64", "arm64"]
            }))
            
            issues = self.dependency_manager._check_platform_compatibility(
                temp_dir, PackageManager.NPM
            )
            
            # This test will vary based on the actual platform running the test
            # We just verify the method runs without error
            assert isinstance(issues, list)
    
    @patch('subprocess.run')
    def test_check_npm_peer_dependencies(self, mock_run):
        """Test checking for missing npm peer dependencies."""
        # Mock npm ls output with peer dependency warnings
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="",
            stderr="npm WARN peer dep missing: react@>=16.0.0, required by react-router@6.0.0"
        )
        
        issues = self.dependency_manager._check_npm_peer_dependencies("/test/path")
        
        assert len(issues) == 1
        assert "Missing peer dependency" in issues[0]
        assert "react@>=16.0.0" in issues[0]
    
    @patch('subprocess.run')
    def test_check_python_dependency_conflicts(self, mock_run):
        """Test checking for Python dependency conflicts."""
        # Mock pip check output with conflicts
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="requests 2.28.0 has requirement urllib3>=1.21.1, but you have urllib3 1.20.0"
        )
        
        issues = self.dependency_manager._check_python_dependency_conflicts("/test/path")
        
        assert len(issues) == 1
        assert "Dependency conflict" in issues[0]
        assert "urllib3" in issues[0]
    
    @patch('subprocess.run')
    def test_check_outdated_dependencies_npm(self, mock_run):
        """Test checking for outdated npm dependencies."""
        # Mock npm outdated output
        outdated_output = json.dumps({
            "lodash": {
                "current": "4.17.20",
                "latest": "4.17.21"
            }
        })
        mock_run.return_value = MagicMock(returncode=0, stdout=outdated_output, stderr="")
        
        issues = self.dependency_manager._check_outdated_dependencies(
            "/test/path", PackageManager.NPM
        )
        
        assert len(issues) == 1
        assert "Outdated package lodash" in issues[0]
        assert "4.17.20 -> 4.17.21" in issues[0]
    
    @patch('subprocess.run')
    def test_check_outdated_dependencies_pip(self, mock_run):
        """Test checking for outdated pip dependencies."""
        # Mock pip list --outdated output
        outdated_output = json.dumps([{
            "name": "requests",
            "version": "2.27.0",
            "latest_version": "2.28.0"
        }])
        mock_run.return_value = MagicMock(returncode=0, stdout=outdated_output, stderr="")
        
        issues = self.dependency_manager._check_outdated_dependencies(
            "/test/path", PackageManager.PIP
        )
        
        assert len(issues) == 1
        assert "Outdated package requests" in issues[0]
        assert "2.27.0 -> 2.28.0" in issues[0]
    
    def test_map_safety_severity(self):
        """Test mapping safety vulnerability IDs to severity levels."""
        test_cases = [
            ("CVE-2021-33503", "high"),
            ("GHSA-abcd-1234", "medium"),
            ("UNKNOWN-123", "unknown")
        ]
        
        for vuln_id, expected_severity in test_cases:
            result = self.dependency_manager._map_safety_severity(vuln_id)
            assert result == expected_severity
    
    def test_perform_dependency_health_checks(self):
        """Test performing comprehensive dependency health checks."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text('{"name": "test-project"}')
            
            result = self.dependency_manager._perform_dependency_health_checks(
                temp_dir, PackageManager.NPM
            )
            
            assert "errors" in result
            assert "warnings" in result
            assert isinstance(result["errors"], list)
            assert isinstance(result["warnings"], list)