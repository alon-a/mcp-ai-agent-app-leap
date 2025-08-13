"""Tests for template validation functionality."""

import pytest
from src.models.validation import (
    TemplateValidator,
    TemplateValidationError,
    validate_configuration_schema,
    validate_template_file_paths,
    TEMPLATE_SCHEMA
)
from src.models.base import TemplateFile, ServerTemplate, ServerLanguage, ServerFramework


class TestTemplateValidator:
    """Test cases for TemplateValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TemplateValidator()
        
        self.valid_template_data = {
            "id": "test-template",
            "name": "Test Template",
            "description": "A test template for validation",
            "language": "python",
            "framework": "fastmcp",
            "files": [
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py",
                    "checksum": "a" * 64,
                    "executable": False
                }
            ],
            "dependencies": ["fastmcp>=0.1.0"],
            "build_commands": ["pip install -e ."],
            "configuration_schema": {
                "type": "object",
                "properties": {
                    "server_name": {"type": "string"}
                }
            }
        }
    
    def test_validate_valid_template_dict(self):
        """Test validation of a valid template dictionary."""
        errors = self.validator.validate_template_dict(self.valid_template_data)
        assert errors == []
    
    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing."""
        invalid_data = self.valid_template_data.copy()
        del invalid_data["id"]
        
        errors = self.validator.validate_template_dict(invalid_data)
        assert len(errors) > 0
        assert any("id" in error for error in errors)
    
    def test_validate_invalid_language(self):
        """Test validation fails with invalid language."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["language"] = "invalid-language"
        
        errors = self.validator.validate_template_dict(invalid_data)
        assert len(errors) > 0
        assert any("language" in error for error in errors)
    
    def test_validate_invalid_framework(self):
        """Test validation fails with invalid framework."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["framework"] = "invalid-framework"
        
        errors = self.validator.validate_template_dict(invalid_data)
        assert len(errors) > 0
        assert any("framework" in error for error in errors)
    
    def test_validate_invalid_id_format(self):
        """Test validation fails with invalid ID format."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["id"] = "Invalid ID with spaces"
        
        errors = self.validator.validate_template_dict(invalid_data)
        assert len(errors) > 0
        assert any("id" in error for error in errors)
    
    def test_validate_invalid_checksum(self):
        """Test validation fails with invalid checksum format."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["files"][0]["checksum"] = "invalid-checksum"
        
        errors = self.validator.validate_template_dict(invalid_data)
        assert len(errors) > 0
        assert any("checksum" in error for error in errors)
    
    def test_validate_empty_files_array(self):
        """Test validation fails with empty files array."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["files"] = []
        
        errors = self.validator.validate_template_dict(invalid_data)
        assert len(errors) > 0
        assert any("files" in error for error in errors)
    
    def test_validate_template_object(self):
        """Test validation of ServerTemplate object."""
        template = ServerTemplate(
            id="test-template",
            name="Test Template",
            description="A test template",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                TemplateFile(
                    path="main.py",
                    url="https://example.com/main.py",
                    checksum="a" * 64,
                    executable=False
                )
            ],
            dependencies=["fastmcp>=0.1.0"],
            build_commands=["pip install -e ."],
            configuration_schema={}
        )
        
        errors = self.validator.validate_template(template)
        assert errors == []
    
    def test_validate_and_raise_valid(self):
        """Test validate_and_raise doesn't raise for valid data."""
        try:
            self.validator.validate_and_raise(self.valid_template_data)
        except TemplateValidationError:
            pytest.fail("validate_and_raise raised exception for valid data")
    
    def test_validate_and_raise_invalid(self):
        """Test validate_and_raise raises for invalid data."""
        invalid_data = self.valid_template_data.copy()
        del invalid_data["id"]
        
        with pytest.raises(TemplateValidationError) as exc_info:
            self.validator.validate_and_raise(invalid_data)
        
        assert len(exc_info.value.errors) > 0


class TestConfigurationSchemaValidation:
    """Test cases for configuration schema validation."""
    
    def test_validate_valid_schema(self):
        """Test validation of a valid JSON schema."""
        valid_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "port": {"type": "integer", "minimum": 1, "maximum": 65535}
            },
            "required": ["name"]
        }
        
        errors = validate_configuration_schema(valid_schema)
        assert errors == []
    
    def test_validate_invalid_schema(self):
        """Test validation fails for invalid JSON schema."""
        invalid_schema = {
            "type": "invalid-type"
        }
        
        errors = validate_configuration_schema(invalid_schema)
        assert len(errors) > 0
    
    def test_validate_empty_schema(self):
        """Test validation of empty schema."""
        empty_schema = {}
        
        errors = validate_configuration_schema(empty_schema)
        assert errors == []


class TestTemplateFilePathValidation:
    """Test cases for template file path validation."""
    
    def test_validate_valid_paths(self):
        """Test validation of valid file paths."""
        files = [
            TemplateFile("src/main.py", "https://example.com/main.py"),
            TemplateFile("config/settings.json", "https://example.com/settings.json"),
            TemplateFile("README.md", "https://example.com/readme.md")
        ]
        
        errors = validate_template_file_paths(files)
        assert errors == []
    
    def test_validate_absolute_path(self):
        """Test validation fails for absolute paths."""
        files = [
            TemplateFile("/absolute/path.py", "https://example.com/path.py")
        ]
        
        errors = validate_template_file_paths(files)
        assert len(errors) > 0
        assert any("absolute" in error.lower() for error in errors)
    
    def test_validate_parent_traversal(self):
        """Test validation fails for parent directory traversal."""
        files = [
            TemplateFile("../parent/file.py", "https://example.com/file.py")
        ]
        
        errors = validate_template_file_paths(files)
        assert len(errors) > 0
        assert any("traversal" in error.lower() for error in errors)
    
    def test_validate_empty_path_component(self):
        """Test validation fails for empty path components."""
        files = [
            TemplateFile("src//empty.py", "https://example.com/empty.py")
        ]
        
        errors = validate_template_file_paths(files)
        assert len(errors) > 0
        assert any("empty" in error.lower() for error in errors)
    
    def test_validate_reserved_names(self):
        """Test validation fails for Windows reserved names."""
        files = [
            TemplateFile("CON.py", "https://example.com/con.py"),
            TemplateFile("src/PRN.txt", "https://example.com/prn.txt")
        ]
        
        errors = validate_template_file_paths(files)
        assert len(errors) > 0
        assert any("reserved" in error.lower() for error in errors)