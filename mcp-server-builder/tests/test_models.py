"""Tests for data models."""

import pytest
from src.models import (
    ServerLanguage,
    ServerFramework,
    ProjectStatus,
    ServerTemplate,
    ProjectConfig,
    BuildResult,
    TemplateFile,
    PackageManager,
    BuildTool,
)


def test_server_template_creation():
    """Test ServerTemplate data model creation."""
    template_file = TemplateFile(
        path="main.py",
        url="https://example.com/main.py",
        checksum="abc123",
        executable=False
    )
    
    template = ServerTemplate(
        id="python-fastmcp",
        name="Python FastMCP Server",
        description="A FastMCP-based Python server",
        language=ServerLanguage.PYTHON,
        framework=ServerFramework.FASTMCP,
        files=[template_file],
        dependencies=["fastmcp>=0.1.0"],
        build_commands=["pip install -e ."],
        configuration_schema={"name": {"type": "string", "required": True}}
    )
    
    assert template.id == "python-fastmcp"
    assert template.language == ServerLanguage.PYTHON
    assert template.framework == ServerFramework.FASTMCP
    assert len(template.files) == 1
    assert template.files[0].path == "main.py"


def test_project_config_creation():
    """Test ProjectConfig data model creation."""
    config = ProjectConfig(
        name="my-server",
        template_id="python-fastmcp",
        output_directory="./output",
        custom_settings={"port": 8080},
        environment_variables={"DEBUG": "true"},
        additional_dependencies=["requests"]
    )
    
    assert config.name == "my-server"
    assert config.template_id == "python-fastmcp"
    assert config.custom_settings["port"] == 8080
    assert "DEBUG" in config.environment_variables


def test_build_result_creation():
    """Test BuildResult data model creation."""
    result = BuildResult(
        success=True,
        project_path="./my-server",
        artifacts=["dist/my-server-0.1.0.tar.gz"],
        logs=["Building project...", "Build completed"],
        errors=[],
        execution_time=45.2
    )
    
    assert result.success is True
    assert result.project_path == "./my-server"
    assert len(result.artifacts) == 1
    assert result.execution_time == 45.2


def test_enums():
    """Test enum values."""
    assert PackageManager.NPM.value == "npm"
    assert PackageManager.PIP.value == "pip"
    assert BuildTool.WEBPACK.value == "webpack"
    assert BuildTool.CARGO_BUILD.value == "cargo build"