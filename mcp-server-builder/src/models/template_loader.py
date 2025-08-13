"""Template loading and parsing utilities for the MCP Server Builder."""

import json
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .base import ServerTemplate, TemplateFile, ServerLanguage, ServerFramework
from .validation import TemplateValidator, TemplateValidationError, validate_template_file_paths


class TemplateLoadError(Exception):
    """Exception raised when template loading fails."""
    pass


class TemplateLoader:
    """Loads and parses server templates from various sources."""
    
    def __init__(self):
        self.validator = TemplateValidator()
    
    def load_from_file(self, file_path: Union[str, Path]) -> ServerTemplate:
        """
        Load a template from a JSON or YAML file.
        
        Args:
            file_path: Path to the template file
            
        Returns:
            ServerTemplate instance
            
        Raises:
            TemplateLoadError: If loading or parsing fails
            TemplateValidationError: If validation fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise TemplateLoadError(f"Template file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix.lower() in ['.yaml', '.yml']:
                    template_data = yaml.safe_load(f)
                elif file_path.suffix.lower() == '.json':
                    template_data = json.load(f)
                else:
                    raise TemplateLoadError(f"Unsupported file format: {file_path.suffix}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise TemplateLoadError(f"Failed to parse template file: {e}")
        except Exception as e:
            raise TemplateLoadError(f"Failed to read template file: {e}")
        
        return self.load_from_dict(template_data)
    
    def load_from_dict(self, template_data: Dict[str, Any]) -> ServerTemplate:
        """
        Load a template from a dictionary.
        
        Args:
            template_data: Dictionary containing template data
            
        Returns:
            ServerTemplate instance
            
        Raises:
            TemplateValidationError: If validation fails
            TemplateLoadError: If parsing fails
        """
        # Validate the template data
        self.validator.validate_and_raise(template_data)
        
        try:
            # Parse template files
            files = []
            for file_data in template_data.get('files', []):
                files.append(TemplateFile(
                    path=file_data['path'],
                    url=file_data['url'],
                    checksum=file_data.get('checksum'),
                    executable=file_data.get('executable', False)
                ))
            
            # Validate file paths
            path_errors = validate_template_file_paths(files)
            if path_errors:
                raise TemplateValidationError(
                    "Template file path validation failed",
                    path_errors
                )
            
            # Create ServerTemplate instance
            template = ServerTemplate(
                id=template_data['id'],
                name=template_data['name'],
                description=template_data['description'],
                language=ServerLanguage(template_data['language']),
                framework=ServerFramework(template_data['framework']),
                files=files,
                dependencies=template_data.get('dependencies', []),
                build_commands=template_data.get('build_commands', []),
                configuration_schema=template_data.get('configuration_schema', {})
            )
            
            return template
            
        except (ValueError, KeyError) as e:
            raise TemplateLoadError(f"Failed to parse template data: {e}")
    
    def load_from_directory(self, directory_path: Union[str, Path]) -> List[ServerTemplate]:
        """
        Load all templates from a directory.
        
        Args:
            directory_path: Path to directory containing template files
            
        Returns:
            List of ServerTemplate instances
            
        Raises:
            TemplateLoadError: If directory access fails
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            raise TemplateLoadError(f"Template directory not found: {directory_path}")
        
        if not directory_path.is_dir():
            raise TemplateLoadError(f"Path is not a directory: {directory_path}")
        
        templates = []
        errors = []
        
        # Look for template files
        for file_path in directory_path.glob("*.json"):
            try:
                template = self.load_from_file(file_path)
                templates.append(template)
            except (TemplateLoadError, TemplateValidationError) as e:
                errors.append(f"Failed to load {file_path.name}: {e}")
        
        for file_path in directory_path.glob("*.yaml"):
            try:
                template = self.load_from_file(file_path)
                templates.append(template)
            except (TemplateLoadError, TemplateValidationError) as e:
                errors.append(f"Failed to load {file_path.name}: {e}")
        
        for file_path in directory_path.glob("*.yml"):
            try:
                template = self.load_from_file(file_path)
                templates.append(template)
            except (TemplateLoadError, TemplateValidationError) as e:
                errors.append(f"Failed to load {file_path.name}: {e}")
        
        if errors:
            error_msg = f"Failed to load {len(errors)} templates:\n" + "\n".join(errors)
            raise TemplateLoadError(error_msg)
        
        return templates
    
    def save_to_file(self, template: ServerTemplate, file_path: Union[str, Path], 
                     format: str = 'json') -> None:
        """
        Save a template to a file.
        
        Args:
            template: ServerTemplate to save
            file_path: Path where to save the template
            format: File format ('json' or 'yaml')
            
        Raises:
            TemplateLoadError: If saving fails
        """
        file_path = Path(file_path)
        
        # Convert template to dictionary
        template_dict = {
            "id": template.id,
            "name": template.name,
            "description": template.description,
            "language": template.language.value,
            "framework": template.framework.value,
            "files": [
                {
                    "path": f.path,
                    "url": f.url,
                    "checksum": f.checksum,
                    "executable": f.executable
                }
                for f in template.files
            ],
            "dependencies": template.dependencies,
            "build_commands": template.build_commands,
            "configuration_schema": template.configuration_schema
        }
        
        try:
            # Create parent directory if it doesn't exist
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if format.lower() == 'yaml':
                    yaml.dump(template_dict, f, default_flow_style=False, indent=2)
                elif format.lower() == 'json':
                    json.dump(template_dict, f, indent=2, ensure_ascii=False)
                else:
                    raise TemplateLoadError(f"Unsupported format: {format}")
                    
        except Exception as e:
            raise TemplateLoadError(f"Failed to save template: {e}")


def create_template_from_minimal_data(
    template_id: str,
    name: str,
    description: str,
    language: ServerLanguage,
    framework: ServerFramework,
    files: List[Dict[str, Any]] = None,
    dependencies: List[str] = None,
    build_commands: List[str] = None,
    configuration_schema: Dict[str, Any] = None
) -> ServerTemplate:
    """
    Create a ServerTemplate from minimal data with defaults.
    
    Args:
        template_id: Unique template identifier
        name: Template name
        description: Template description
        language: Server language
        framework: Server framework
        files: List of file specifications (optional)
        dependencies: List of dependencies (optional)
        build_commands: List of build commands (optional)
        configuration_schema: Configuration schema (optional)
        
    Returns:
        ServerTemplate instance
    """
    template_files = []
    if files:
        for file_data in files:
            template_files.append(TemplateFile(
                path=file_data['path'],
                url=file_data['url'],
                checksum=file_data.get('checksum'),
                executable=file_data.get('executable', False)
            ))
    
    return ServerTemplate(
        id=template_id,
        name=name,
        description=description,
        language=language,
        framework=framework,
        files=template_files,
        dependencies=dependencies or [],
        build_commands=build_commands or [],
        configuration_schema=configuration_schema or {}
    )