"""Tests for template loading functionality."""

import json
import yaml
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from src.models.template_loader import (
    TemplateLoader,
    TemplateLoadError,
    create_template_from_minimal_data
)
from src.models.validation import TemplateValidationError
from src.models.base import ServerLanguage, ServerFramework, TemplateFile


class TestTemplateLoader:
    """Test cases for TemplateLoader class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.loader = TemplateLoader()
        
        self.valid_template_data = {
            "id": "test-template",
            "name": "Test Template",
            "description": "A test template for loading",
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
    
    def test_load_from_dict_valid(self):
        """Test loading template from valid dictionary."""
        template = self.loader.load_from_dict(self.valid_template_data)
        
        assert template.id == "test-template"
        assert template.name == "Test Template"
        assert template.language == ServerLanguage.PYTHON
        assert template.framework == ServerFramework.FASTMCP
        assert len(template.files) == 1
        assert template.files[0].path == "main.py"
        assert template.dependencies == ["fastmcp>=0.1.0"]
        assert template.build_commands == ["pip install -e ."]
    
    def test_load_from_dict_invalid(self):
        """Test loading fails with invalid dictionary."""
        invalid_data = self.valid_template_data.copy()
        del invalid_data["id"]
        
        with pytest.raises(TemplateValidationError):
            self.loader.load_from_dict(invalid_data)
    
    def test_load_from_dict_invalid_language(self):
        """Test loading fails with invalid language."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["language"] = "invalid-language"
        
        with pytest.raises(TemplateValidationError):
            self.loader.load_from_dict(invalid_data)
    
    def test_load_from_dict_unsafe_path(self):
        """Test loading fails with unsafe file paths."""
        invalid_data = self.valid_template_data.copy()
        invalid_data["files"][0]["path"] = "../unsafe/path.py"
        
        with pytest.raises(TemplateValidationError):
            self.loader.load_from_dict(invalid_data)
    
    def test_load_from_json_file(self):
        """Test loading template from JSON file."""
        with TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "template.json"
            
            with open(template_file, 'w') as f:
                json.dump(self.valid_template_data, f)
            
            template = self.loader.load_from_file(template_file)
            assert template.id == "test-template"
            assert template.name == "Test Template"
    
    def test_load_from_yaml_file(self):
        """Test loading template from YAML file."""
        with TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "template.yaml"
            
            with open(template_file, 'w') as f:
                yaml.dump(self.valid_template_data, f)
            
            template = self.loader.load_from_file(template_file)
            assert template.id == "test-template"
            assert template.name == "Test Template"
    
    def test_load_from_yml_file(self):
        """Test loading template from .yml file."""
        with TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "template.yml"
            
            with open(template_file, 'w') as f:
                yaml.dump(self.valid_template_data, f)
            
            template = self.loader.load_from_file(template_file)
            assert template.id == "test-template"
            assert template.name == "Test Template"
    
    def test_load_from_nonexistent_file(self):
        """Test loading fails for nonexistent file."""
        with pytest.raises(TemplateLoadError) as exc_info:
            self.loader.load_from_file("nonexistent.json")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_from_unsupported_format(self):
        """Test loading fails for unsupported file format."""
        with TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "template.txt"
            template_file.write_text("invalid content")
            
            with pytest.raises(TemplateLoadError) as exc_info:
                self.loader.load_from_file(template_file)
            
            assert "unsupported" in str(exc_info.value).lower()
    
    def test_load_from_invalid_json(self):
        """Test loading fails for invalid JSON."""
        with TemporaryDirectory() as temp_dir:
            template_file = Path(temp_dir) / "template.json"
            template_file.write_text("invalid json content")
            
            with pytest.raises(TemplateLoadError) as exc_info:
                self.loader.load_from_file(template_file)
            
            assert "parse" in str(exc_info.value).lower()
    
    def test_load_from_directory(self):
        """Test loading all templates from directory."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create multiple template files
            template1_data = self.valid_template_data.copy()
            template1_data["id"] = "template-1"
            
            template2_data = self.valid_template_data.copy()
            template2_data["id"] = "template-2"
            
            with open(temp_path / "template1.json", 'w') as f:
                json.dump(template1_data, f)
            
            with open(temp_path / "template2.yaml", 'w') as f:
                yaml.dump(template2_data, f)
            
            templates = self.loader.load_from_directory(temp_path)
            
            assert len(templates) == 2
            template_ids = {t.id for t in templates}
            assert template_ids == {"template-1", "template-2"}
    
    def test_load_from_nonexistent_directory(self):
        """Test loading fails for nonexistent directory."""
        with pytest.raises(TemplateLoadError) as exc_info:
            self.loader.load_from_directory("nonexistent_directory")
        
        assert "not found" in str(exc_info.value).lower()
    
    def test_load_from_file_not_directory(self):
        """Test loading fails when path is not a directory."""
        with TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "not_a_directory.txt"
            file_path.write_text("content")
            
            with pytest.raises(TemplateLoadError) as exc_info:
                self.loader.load_from_directory(file_path)
            
            assert "not a directory" in str(exc_info.value).lower()
    
    def test_save_to_json_file(self):
        """Test saving template to JSON file."""
        template = self.loader.load_from_dict(self.valid_template_data)
        
        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "output.json"
            
            self.loader.save_to_file(template, output_file, format='json')
            
            assert output_file.exists()
            
            # Load back and verify
            loaded_template = self.loader.load_from_file(output_file)
            assert loaded_template.id == template.id
            assert loaded_template.name == template.name
    
    def test_save_to_yaml_file(self):
        """Test saving template to YAML file."""
        template = self.loader.load_from_dict(self.valid_template_data)
        
        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "output.yaml"
            
            self.loader.save_to_file(template, output_file, format='yaml')
            
            assert output_file.exists()
            
            # Load back and verify
            loaded_template = self.loader.load_from_file(output_file)
            assert loaded_template.id == template.id
            assert loaded_template.name == template.name
    
    def test_save_unsupported_format(self):
        """Test saving fails for unsupported format."""
        template = self.loader.load_from_dict(self.valid_template_data)
        
        with TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "output.txt"
            
            with pytest.raises(TemplateLoadError) as exc_info:
                self.loader.save_to_file(template, output_file, format='txt')
            
            assert "unsupported" in str(exc_info.value).lower()


class TestCreateTemplateFromMinimalData:
    """Test cases for create_template_from_minimal_data function."""
    
    def test_create_minimal_template(self):
        """Test creating template with minimal data."""
        template = create_template_from_minimal_data(
            template_id="minimal-template",
            name="Minimal Template",
            description="A minimal template",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP
        )
        
        assert template.id == "minimal-template"
        assert template.name == "Minimal Template"
        assert template.language == ServerLanguage.PYTHON
        assert template.framework == ServerFramework.FASTMCP
        assert template.files == []
        assert template.dependencies == []
        assert template.build_commands == []
        assert template.configuration_schema == {}
    
    def test_create_template_with_files(self):
        """Test creating template with file specifications."""
        files = [
            {
                "path": "main.py",
                "url": "https://example.com/main.py",
                "executable": True
            }
        ]
        
        template = create_template_from_minimal_data(
            template_id="template-with-files",
            name="Template with Files",
            description="A template with files",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=files
        )
        
        assert len(template.files) == 1
        assert template.files[0].path == "main.py"
        assert template.files[0].url == "https://example.com/main.py"
        assert template.files[0].executable is True
    
    def test_create_template_with_all_options(self):
        """Test creating template with all optional parameters."""
        files = [{"path": "main.py", "url": "https://example.com/main.py"}]
        dependencies = ["fastmcp>=0.1.0"]
        build_commands = ["pip install -e ."]
        config_schema = {"type": "object"}
        
        template = create_template_from_minimal_data(
            template_id="full-template",
            name="Full Template",
            description="A complete template",
            language=ServerLanguage.TYPESCRIPT,
            framework=ServerFramework.TYPESCRIPT_SDK,
            files=files,
            dependencies=dependencies,
            build_commands=build_commands,
            configuration_schema=config_schema
        )
        
        assert template.language == ServerLanguage.TYPESCRIPT
        assert template.framework == ServerFramework.TYPESCRIPT_SDK
        assert template.dependencies == dependencies
        assert template.build_commands == build_commands
        assert template.configuration_schema == config_schema