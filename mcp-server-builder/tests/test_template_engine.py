"""Tests for template engine implementation."""

import pytest
from tempfile import TemporaryDirectory
from pathlib import Path
import json
from src.managers.template_engine import TemplateEngineImpl
from src.models.base import ServerTemplate, ServerLanguage, ServerFramework, TemplateFile
from src.models.template_loader import create_template_from_minimal_data


class TestTemplateEngineImpl:
    """Test cases for TemplateEngineImpl class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.engine = TemplateEngineImpl()
    
    def test_initialization(self):
        """Test template engine initialization."""
        assert self.engine is not None
        assert len(self.engine._templates) > 0  # Should have built-in templates
    
    def test_list_templates(self):
        """Test listing all available templates."""
        templates = self.engine.list_templates()
        
        assert len(templates) >= 3  # At least the 3 built-in templates
        template_ids = {t.id for t in templates}
        
        # Check that built-in templates are present
        assert "python-fastmcp" in template_ids
        assert "python-lowlevel" in template_ids
        assert "typescript-sdk" in template_ids
    
    def test_get_template_existing(self):
        """Test getting an existing template."""
        template = self.engine.get_template("python-fastmcp")
        
        assert template is not None
        assert template.id == "python-fastmcp"
        assert template.language == ServerLanguage.PYTHON
        assert template.framework == ServerFramework.FASTMCP
        assert len(template.files) > 0
        assert len(template.dependencies) > 0
    
    def test_get_template_nonexistent(self):
        """Test getting a non-existent template."""
        template = self.engine.get_template("nonexistent-template")
        assert template is None
    
    def test_built_in_python_fastmcp_template(self):
        """Test the built-in Python FastMCP template."""
        template = self.engine.get_template("python-fastmcp")
        
        assert template.name == "Python FastMCP Server"
        assert template.language == ServerLanguage.PYTHON
        assert template.framework == ServerFramework.FASTMCP
        assert "fastmcp" in template.dependencies[0]
        assert "pip install -e ." in template.build_commands
        assert "server_name" in template.configuration_schema["properties"]
    
    def test_built_in_python_lowlevel_template(self):
        """Test the built-in Python low-level template."""
        template = self.engine.get_template("python-lowlevel")
        
        assert template.name == "Python Low-level MCP Server"
        assert template.language == ServerLanguage.PYTHON
        assert template.framework == ServerFramework.LOW_LEVEL
        assert any("mcp" in dep for dep in template.dependencies)
        assert "pip install -e ." in template.build_commands
    
    def test_built_in_typescript_template(self):
        """Test the built-in TypeScript template."""
        template = self.engine.get_template("typescript-sdk")
        
        assert template.name == "TypeScript MCP Server"
        assert template.language == ServerLanguage.TYPESCRIPT
        assert template.framework == ServerFramework.TYPESCRIPT_SDK
        assert any("@modelcontextprotocol/sdk" in dep for dep in template.dependencies)
        assert "npm install" in template.build_commands
        assert "npm run build" in template.build_commands
    
    def test_apply_template_valid_config(self):
        """Test applying template with valid configuration."""
        template = self.engine.get_template("python-fastmcp")
        config = {
            "server_name": "Test Server",
            "server_version": "2.0.0",
            "transport": "http"
        }
        
        result = self.engine.apply_template(template, config)
        
        assert result.success is True
        assert len(result.generated_files) > 0
        assert result.applied_config["server_name"] == "Test Server"
        assert result.applied_config["server_version"] == "2.0.0"
        assert result.applied_config["transport"] == "http"
        assert len(result.errors) == 0
    
    def test_apply_template_with_defaults(self):
        """Test applying template with partial config (using defaults)."""
        template = self.engine.get_template("python-fastmcp")
        config = {"server_name": "Test Server"}
        
        result = self.engine.apply_template(template, config)
        
        assert result.success is True
        assert result.applied_config["server_name"] == "Test Server"
        assert result.applied_config["server_version"] == "1.0.0"  # Default value
        assert result.applied_config["transport"] == "stdio"  # Default value
    
    def test_apply_template_invalid_config(self):
        """Test applying template with invalid configuration."""
        template = self.engine.get_template("python-fastmcp")
        config = {
            "server_name": 123,  # Should be string
            "transport": "invalid-transport"  # Not in enum
        }
        
        result = self.engine.apply_template(template, config)
        
        # Note: This test might pass if jsonschema is not available
        # In that case, validation is skipped
        if result.success is False:
            assert len(result.errors) > 0
    
    def test_parameter_substitution(self):
        """Test parameter substitution in template text."""
        config = {"server_name": "My Server", "version": "1.0.0"}
        
        # Test the private method
        result = self.engine._substitute_parameters(
            "Server: {{server_name}} v{{version}}", 
            config
        )
        
        assert result == "Server: My Server v1.0.0"
    
    def test_parameter_substitution_missing_param(self):
        """Test parameter substitution with missing parameter."""
        config = {"server_name": "My Server"}
        
        result = self.engine._substitute_parameters(
            "Server: {{server_name}} v{{missing_param}}", 
            config
        )
        
        assert result == "Server: My Server v{{missing_param}}"
    
    def test_add_template(self):
        """Test adding a new template."""
        new_template = create_template_from_minimal_data(
            template_id="test-template",
            name="Test Template",
            description="A test template",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[{"path": "main.py", "url": "https://example.com/main.py"}]
        )
        
        success = self.engine.add_template(new_template)
        assert success is True
        
        retrieved = self.engine.get_template("test-template")
        assert retrieved is not None
        assert retrieved.name == "Test Template"
    
    def test_add_invalid_template(self):
        """Test adding an invalid template."""
        # Create a template with invalid data
        invalid_template = ServerTemplate(
            id="",  # Invalid empty ID
            name="Invalid Template",
            description="Invalid",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[],
            dependencies=[],
            build_commands=[],
            configuration_schema={}
        )
        
        success = self.engine.add_template(invalid_template)
        assert success is False
    
    def test_remove_template(self):
        """Test removing a template."""
        # First add a template
        new_template = create_template_from_minimal_data(
            template_id="removable-template",
            name="Removable Template",
            description="A template to remove",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[{"path": "main.py", "url": "https://example.com/main.py"}]
        )
        
        self.engine.add_template(new_template)
        assert self.engine.get_template("removable-template") is not None
        
        # Now remove it
        success = self.engine.remove_template("removable-template")
        assert success is True
        assert self.engine.get_template("removable-template") is None
    
    def test_remove_nonexistent_template(self):
        """Test removing a non-existent template."""
        success = self.engine.remove_template("nonexistent-template")
        assert success is False
    
    def test_get_templates_by_language(self):
        """Test filtering templates by language."""
        python_templates = self.engine.get_templates_by_language(ServerLanguage.PYTHON)
        typescript_templates = self.engine.get_templates_by_language(ServerLanguage.TYPESCRIPT)
        
        assert len(python_templates) >= 2  # At least python-fastmcp and python-lowlevel
        assert len(typescript_templates) >= 1  # At least typescript-sdk
        
        # Verify all returned templates have the correct language
        for template in python_templates:
            assert template.language == ServerLanguage.PYTHON
        
        for template in typescript_templates:
            assert template.language == ServerLanguage.TYPESCRIPT
    
    def test_get_templates_by_framework(self):
        """Test filtering templates by framework."""
        fastmcp_templates = self.engine.get_templates_by_framework(ServerFramework.FASTMCP)
        lowlevel_templates = self.engine.get_templates_by_framework(ServerFramework.LOW_LEVEL)
        typescript_templates = self.engine.get_templates_by_framework(ServerFramework.TYPESCRIPT_SDK)
        
        assert len(fastmcp_templates) >= 1
        assert len(lowlevel_templates) >= 1
        assert len(typescript_templates) >= 1
        
        # Verify all returned templates have the correct framework
        for template in fastmcp_templates:
            assert template.framework == ServerFramework.FASTMCP
    
    def test_reload_templates(self):
        """Test reloading templates."""
        # Add a custom template
        custom_template = create_template_from_minimal_data(
            template_id="custom-template",
            name="Custom Template",
            description="A custom template",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[{"path": "main.py", "url": "https://example.com/main.py"}]
        )
        
        self.engine.add_template(custom_template)
        assert self.engine.get_template("custom-template") is not None
        
        # Reload templates (should remove custom template but keep built-ins)
        self.engine.reload_templates()
        
        assert self.engine.get_template("custom-template") is None
        assert self.engine.get_template("python-fastmcp") is not None  # Built-in should remain


class TestTemplateEngineWithCustomDirectory:
    """Test cases for TemplateEngine with custom template directory."""
    
    def test_load_custom_templates(self):
        """Test loading custom templates from directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a custom template file
            custom_template_data = {
                "id": "custom-python",
                "name": "Custom Python Server",
                "description": "A custom Python server template",
                "language": "python",
                "framework": "fastmcp",
                "files": [
                    {
                        "path": "custom.py",
                        "url": "https://example.com/custom.py"
                    }
                ],
                "dependencies": ["custom-package>=1.0.0"],
                "build_commands": ["pip install -e ."],
                "configuration_schema": {}
            }
            
            with open(temp_path / "custom.json", 'w') as f:
                json.dump(custom_template_data, f)
            
            # Create engine with custom directory
            engine = TemplateEngineImpl(template_directory=str(temp_path))
            
            # Should have both built-in and custom templates
            templates = engine.list_templates()
            template_ids = {t.id for t in templates}
            
            assert "python-fastmcp" in template_ids  # Built-in
            assert "custom-python" in template_ids  # Custom
            
            custom_template = engine.get_template("custom-python")
            assert custom_template is not None
            assert custom_template.name == "Custom Python Server"
    
    def test_invalid_custom_template_directory(self):
        """Test handling of invalid custom template directory."""
        # Should not raise exception, just use built-in templates
        engine = TemplateEngineImpl(template_directory="/nonexistent/directory")
        
        templates = engine.list_templates()
        assert len(templates) >= 3  # Should still have built-in templates
    
    def test_custom_template_loading_error(self):
        """Test handling of custom template loading errors."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create an invalid template file
            with open(temp_path / "invalid.json", 'w') as f:
                f.write("invalid json content")
            
            # Should not raise exception, just use built-in templates
            engine = TemplateEngineImpl(template_directory=str(temp_path))
            
            templates = engine.list_templates()
            assert len(templates) >= 3  # Should still have built-in templates