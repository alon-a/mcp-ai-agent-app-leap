"""Tests for build system management."""

import os
import json
import tempfile
import subprocess
import pytest
from pathlib import Path
from unittest.mock import patch, mock_open

from src.managers.build_system import BuildSystemManager, BuildConfig
from src.models.enums import BuildTool


class TestBuildSystemManager:
    """Test cases for BuildSystemManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.build_manager = BuildSystemManager()
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_detect_npm_scripts(self):
        """Test detection of npm scripts build system."""
        # Create package.json with build script
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "webpack --mode=production"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        
        # Create package-lock.json
        Path(package_lock_path).touch()
        
        result = self.build_manager._detect_npm_scripts(self.temp_dir)
        assert result is True
    
    def test_detect_npm_scripts_no_build_script(self):
        """Test npm detection fails when no build script exists."""
        package_json = {
            "name": "test-project",
            "scripts": {
                "start": "node index.js"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        
        result = self.build_manager._detect_npm_scripts(self.temp_dir)
        assert result is False
    
    def test_detect_npm_scripts_with_yarn(self):
        """Test detection of npm scripts with yarn.lock."""
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "webpack --mode=production"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        yarn_lock_path = os.path.join(self.temp_dir, "yarn.lock")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(yarn_lock_path).touch()
        
        result = self.build_manager._detect_npm_scripts(self.temp_dir)
        assert result is True
    
    def test_detect_npm_scripts_with_pnpm(self):
        """Test detection of npm scripts with pnpm-lock.yaml."""
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "webpack --mode=production"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        pnpm_lock_path = os.path.join(self.temp_dir, "pnpm-lock.yaml")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(pnpm_lock_path).touch()
        
        result = self.build_manager._detect_npm_scripts(self.temp_dir)
        assert result is True
    
    def test_detect_typescript(self):
        """Test detection of TypeScript compiler."""
        # Create tsconfig.json without bundler configs
        Path(os.path.join(self.temp_dir, "tsconfig.json")).touch()
        
        result = self.build_manager._detect_typescript(self.temp_dir)
        assert result is True
    
    def test_detect_typescript_with_bundler(self):
        """Test TypeScript detection fails when bundler is present."""
        # Create tsconfig.json and webpack config
        Path(os.path.join(self.temp_dir, "tsconfig.json")).touch()
        Path(os.path.join(self.temp_dir, "webpack.config.js")).touch()
        
        result = self.build_manager._detect_typescript(self.temp_dir)
        assert result is False
    
    def test_detect_webpack(self):
        """Test detection of Webpack build system."""
        Path(os.path.join(self.temp_dir, "webpack.config.js")).touch()
        
        result = self.build_manager._detect_webpack(self.temp_dir)
        assert result is True
    
    def test_detect_vite(self):
        """Test detection of Vite build system."""
        Path(os.path.join(self.temp_dir, "vite.config.ts")).touch()
        
        result = self.build_manager._detect_vite(self.temp_dir)
        assert result is True
    
    def test_detect_setuptools(self):
        """Test detection of Python setuptools."""
        Path(os.path.join(self.temp_dir, "setup.py")).touch()
        
        result = self.build_manager._detect_setuptools(self.temp_dir)
        assert result is True
    
    def test_detect_setuptools_pyproject(self):
        """Test detection of setuptools via pyproject.toml."""
        Path(os.path.join(self.temp_dir, "pyproject.toml")).touch()
        
        result = self.build_manager._detect_setuptools(self.temp_dir)
        assert result is True
    
    def test_detect_poetry(self):
        """Test detection of Poetry build system."""
        # Create pyproject.toml with poetry configuration
        pyproject_content = """
[tool.poetry]
name = "test-project"
version = "0.1.0"
"""
        
        pyproject_path = os.path.join(self.temp_dir, "pyproject.toml")
        with open(pyproject_path, 'w') as f:
            f.write(pyproject_content)
        
        # Mock the tomli import at the module level
        with patch('builtins.__import__') as mock_import:
            def side_effect(name, *args, **kwargs):
                if name == 'tomli':
                    mock_tomli = type('MockTomli', (), {})()
                    mock_tomli.load = lambda f: {
                        "tool": {
                            "poetry": {
                                "name": "test-project"
                            }
                        }
                    }
                    return mock_tomli
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            result = self.build_manager._detect_poetry(self.temp_dir)
            assert result is True
    
    def test_detect_poetry_fallback(self):
        """Test Poetry detection fallback to poetry.lock."""
        # Create pyproject.toml without poetry section
        Path(os.path.join(self.temp_dir, "pyproject.toml")).touch()
        Path(os.path.join(self.temp_dir, "poetry.lock")).touch()
        
        # Mock tomli to raise ImportError
        with patch('builtins.__import__') as mock_import:
            def side_effect(name, *args, **kwargs):
                if name == 'tomli':
                    raise ImportError("No module named 'tomli'")
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = side_effect
            result = self.build_manager._detect_poetry(self.temp_dir)
            assert result is True
    
    def test_detect_cargo(self):
        """Test detection of Cargo build system."""
        Path(os.path.join(self.temp_dir, "Cargo.toml")).touch()
        
        result = self.build_manager._detect_cargo(self.temp_dir)
        assert result is True
    
    def test_detect_go(self):
        """Test detection of Go modules."""
        Path(os.path.join(self.temp_dir, "go.mod")).touch()
        
        result = self.build_manager._detect_go(self.temp_dir)
        assert result is True
    
    def test_detect_maven(self):
        """Test detection of Maven build system."""
        Path(os.path.join(self.temp_dir, "pom.xml")).touch()
        
        result = self.build_manager._detect_maven(self.temp_dir)
        assert result is True
    
    def test_detect_gradle(self):
        """Test detection of Gradle build system."""
        Path(os.path.join(self.temp_dir, "build.gradle")).touch()
        
        result = self.build_manager._detect_gradle(self.temp_dir)
        assert result is True
    
    def test_detect_build_system_npm(self):
        """Test overall build system detection for npm project."""
        # Create npm project structure
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "webpack --mode=production"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        result = self.build_manager.detect_build_system(self.temp_dir)
        assert result == BuildTool.NPM_SCRIPTS.value
    
    def test_detect_build_system_none(self):
        """Test build system detection when no build system is found."""
        result = self.build_manager.detect_build_system(self.temp_dir)
        assert result is None
    
    def test_detect_build_system_nonexistent_path(self):
        """Test build system detection with nonexistent path."""
        result = self.build_manager.detect_build_system("/nonexistent/path")
        assert result is None
    
    def test_get_build_config(self):
        """Test getting build configuration for a project."""
        # Create npm project
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "webpack --mode=production"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        config = self.build_manager.get_build_config(self.temp_dir)
        
        assert config is not None
        assert config.build_tool == BuildTool.NPM_SCRIPTS
        assert config.commands == ["npm run build"]
        assert config.working_directory == self.temp_dir
        assert "NODE_ENV" in config.environment
        assert config.environment["NODE_ENV"] == "production"
    
    def test_get_build_config_custom_commands(self):
        """Test getting build configuration with custom commands."""
        # Create npm project
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "webpack --mode=production"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        custom_commands = ["npm run custom-build", "npm run test"]
        config = self.build_manager.get_build_config(self.temp_dir, custom_commands)
        
        assert config is not None
        assert config.commands == custom_commands
    
    def test_get_build_config_no_build_system(self):
        """Test getting build configuration when no build system is detected."""
        config = self.build_manager.get_build_config(self.temp_dir)
        assert config is None
    
    def test_customize_build_config(self):
        """Test customizing build configuration."""
        base_config = BuildConfig(
            build_tool=BuildTool.NPM_SCRIPTS,
            commands=["npm run build"],
            environment={"NODE_ENV": "production"},
            working_directory=self.temp_dir
        )
        
        customizations = {
            "commands": ["npm run custom-build"],
            "environment": {"CUSTOM_VAR": "value"},
            "timeout": 600,
            "output_directory": "/custom/output"
        }
        
        customized = self.build_manager.customize_build_config(base_config, customizations)
        
        assert customized.commands == ["npm run custom-build"]
        assert customized.environment["NODE_ENV"] == "production"
        assert customized.environment["CUSTOM_VAR"] == "value"
        assert customized.timeout == 600
        assert customized.output_directory == "/custom/output"
    
    def test_get_build_environment_node(self):
        """Test getting build environment for Node.js projects."""
        env = self.build_manager._get_build_environment(BuildTool.NPM_SCRIPTS, self.temp_dir)
        assert "NODE_ENV" in env
        assert env["NODE_ENV"] == "production"
    
    def test_get_build_environment_cargo(self):
        """Test getting build environment for Cargo projects."""
        env = self.build_manager._get_build_environment(BuildTool.CARGO_BUILD, self.temp_dir)
        assert "CARGO_TARGET_DIR" in env
        assert env["CARGO_TARGET_DIR"] == os.path.join(self.temp_dir, "target")
    
    def test_get_build_environment_python(self):
        """Test getting build environment for Python projects."""
        env = self.build_manager._get_build_environment(BuildTool.PYTHON_SETUPTOOLS, self.temp_dir)
        assert "PYTHONPATH" in env
        assert env["PYTHONPATH"] == self.temp_dir
    
    def test_get_output_directory(self):
        """Test getting output directory for different build tools."""
        # Test npm
        output_dir = self.build_manager._get_output_directory(BuildTool.NPM_SCRIPTS, self.temp_dir)
        assert output_dir == os.path.join(self.temp_dir, "dist")
        
        # Test cargo
        output_dir = self.build_manager._get_output_directory(BuildTool.CARGO_BUILD, self.temp_dir)
        assert output_dir == os.path.join(self.temp_dir, "target/release")
        
        # Test python
        output_dir = self.build_manager._get_output_directory(BuildTool.PYTHON_SETUPTOOLS, self.temp_dir)
        assert output_dir == os.path.join(self.temp_dir, "build")
    
    def test_execute_build_nonexistent_path(self):
        """Test execute_build with nonexistent project path."""
        result = self.build_manager.execute_build("/nonexistent/path", ["echo test"])
        
        assert result.success is False
        assert "Project path does not exist" in result.errors[0]
        assert result.execution_time == 0.0
    
    def test_execute_build_no_commands(self):
        """Test execute_build with empty command list."""
        result = self.build_manager.execute_build(self.temp_dir, [])
        
        assert result.success is False
        assert "No build commands provided" in result.errors[0]
        assert result.execution_time == 0.0
    
    def test_execute_build_no_build_system(self):
        """Test execute_build when no build system is detected."""
        result = self.build_manager.execute_build(self.temp_dir, ["echo test"])
        
        assert result.success is False
        assert "Could not determine build configuration" in result.errors[0]
    
    @patch('subprocess.Popen')
    def test_execute_build_success(self, mock_popen):
        """Test successful build execution."""
        
        # Set up npm project
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "echo 'Building project'"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        # Create output directory
        output_dir = os.path.join(self.temp_dir, "dist")
        os.makedirs(output_dir)
        Path(os.path.join(output_dir, "bundle.js")).touch()
        
        # Mock subprocess
        mock_process = mock_popen.return_value
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = ["Building project\n", ""]
        mock_process.stderr.readline.side_effect = [""]
        mock_process.wait.return_value = None
        
        result = self.build_manager.execute_build(self.temp_dir, ["npm run build"])
        
        assert result.success is True
        assert result.project_path == self.temp_dir
        assert len(result.artifacts) == 1
        assert "bundle.js" in result.artifacts[0]
        assert result.execution_time >= 0
    
    @patch('subprocess.Popen')
    def test_execute_build_command_failure(self, mock_popen):
        """Test build execution with command failure."""
        
        # Set up npm project
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "exit 1"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        # Mock subprocess failure
        mock_process = mock_popen.return_value
        mock_process.returncode = 1
        mock_process.stdout.readline.side_effect = [""]
        mock_process.stderr.readline.side_effect = ["Build failed\n", ""]
        mock_process.wait.return_value = None
        
        result = self.build_manager.execute_build(self.temp_dir, ["npm run build"])
        
        assert result.success is False
        assert any("Command failed with exit code 1" in error for error in result.errors)
        assert result.execution_time >= 0
    
    @patch('subprocess.Popen')
    def test_execute_build_timeout(self, mock_popen):
        """Test build execution with timeout."""
        # Set up npm project
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "sleep 10"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        # Mock subprocess timeout
        mock_process = mock_popen.return_value
        mock_process.wait.side_effect = subprocess.TimeoutExpired("cmd", 1)
        mock_process.kill.return_value = None
        mock_process.stdout.readline.side_effect = [""]
        mock_process.stderr.readline.side_effect = [""]
        
        # Use short timeout for test
        build_manager = BuildSystemManager()
        config = build_manager.get_build_config(self.temp_dir)
        config.timeout = 1
        
        result = build_manager._execute_build_with_config(config)
        
        assert result.success is False
        assert any("timed out" in error for error in result.errors)
    
    @patch('subprocess.Popen')
    def test_execute_build_command_not_found(self, mock_popen):
        """Test build execution with command not found."""
        # Set up npm project
        package_json = {
            "name": "test-project",
            "scripts": {
                "build": "nonexistent-command"
            }
        }
        
        package_json_path = os.path.join(self.temp_dir, "package.json")
        package_lock_path = os.path.join(self.temp_dir, "package-lock.json")
        
        with open(package_json_path, 'w') as f:
            json.dump(package_json, f)
        Path(package_lock_path).touch()
        
        # Mock FileNotFoundError
        mock_popen.side_effect = FileNotFoundError("Command not found")
        
        result = self.build_manager.execute_build(self.temp_dir, ["nonexistent-command"])
        
        assert result.success is False
        assert any("Command not found" in error for error in result.errors)
    
    def test_collect_build_artifacts(self):
        """Test collecting build artifacts from output directory."""
        # Create output directory with artifacts
        output_dir = os.path.join(self.temp_dir, "dist")
        os.makedirs(output_dir)
        
        # Create some artifact files
        Path(os.path.join(output_dir, "bundle.js")).touch()
        Path(os.path.join(output_dir, "bundle.css")).touch()
        
        # Create subdirectory with more artifacts
        sub_dir = os.path.join(output_dir, "assets")
        os.makedirs(sub_dir)
        Path(os.path.join(sub_dir, "image.png")).touch()
        
        artifacts = self.build_manager._collect_build_artifacts(output_dir)
        
        assert len(artifacts) == 3
        assert "bundle.js" in artifacts
        assert "bundle.css" in artifacts
        assert os.path.join("assets", "image.png") in artifacts
    
    def test_collect_build_artifacts_nonexistent_dir(self):
        """Test collecting artifacts from nonexistent directory."""
        artifacts = self.build_manager._collect_build_artifacts("/nonexistent/dir")
        assert artifacts == []
    
    def test_get_build_artifacts_not_implemented(self):
        """Test that get_build_artifacts raises NotImplementedError."""
        with pytest.raises(NotImplementedError):
            self.build_manager.get_build_artifacts(self.temp_dir)