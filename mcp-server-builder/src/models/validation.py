"""Template validation utilities for the MCP Server Builder."""

import json
import jsonschema
from typing import Dict, Any, List, Optional
from pathlib import Path
from .base import ServerTemplate, TemplateFile, ServerLanguage, ServerFramework


# JSON Schema for ServerTemplate validation
TEMPLATE_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {
            "type": "string",
            "pattern": "^[a-z0-9-]+$",
            "minLength": 1,
            "maxLength": 50
        },
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 100
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "maxLength": 500
        },
        "language": {
            "type": "string",
            "enum": [lang.value for lang in ServerLanguage]
        },
        "framework": {
            "type": "string",
            "enum": [framework.value for framework in ServerFramework]
        },
        "files": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "minLength": 1
                    },
                    "url": {
                        "type": "string",
                        "format": "uri"
                    },
                    "checksum": {
                        "type": ["string", "null"],
                        "pattern": "^[a-fA-F0-9]{64}$"
                    },
                    "executable": {
                        "type": "boolean"
                    }
                },
                "required": ["path", "url"],
                "additionalProperties": False
            },
            "minItems": 1
        },
        "dependencies": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1
            }
        },
        "build_commands": {
            "type": "array",
            "items": {
                "type": "string",
                "minLength": 1
            }
        },
        "configuration_schema": {
            "type": "object"
        }
    },
    "required": ["id", "name", "description", "language", "framework", "files", "dependencies", "build_commands"],
    "additionalProperties": False
}


class TemplateValidationError(Exception):
    """Exception raised when template validation fails."""
    
    def __init__(self, message: str, errors: List[str] = None):
        super().__init__(message)
        self.errors = errors or []


class TemplateValidator:
    """Validates server templates against JSON schema."""
    
    def __init__(self):
        self.validator = jsonschema.Draft7Validator(TEMPLATE_SCHEMA)
    
    def validate_template_dict(self, template_data: Dict[str, Any]) -> List[str]:
        """
        Validate a template dictionary against the schema.
        
        Args:
            template_data: Dictionary containing template data
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        for error in self.validator.iter_errors(template_data):
            error_path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"Validation error at {error_path}: {error.message}")
        
        return errors
    
    def validate_template(self, template: ServerTemplate) -> List[str]:
        """
        Validate a ServerTemplate object.
        
        Args:
            template: ServerTemplate instance to validate
            
        Returns:
            List of validation error messages (empty if valid)
        """
        # Convert template to dictionary for validation
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
        
        return self.validate_template_dict(template_dict)
    
    def validate_and_raise(self, template_data: Dict[str, Any]) -> None:
        """
        Validate template data and raise exception if invalid.
        
        Args:
            template_data: Dictionary containing template data
            
        Raises:
            TemplateValidationError: If validation fails
        """
        errors = self.validate_template_dict(template_data)
        if errors:
            raise TemplateValidationError(
                f"Template validation failed with {len(errors)} errors",
                errors
            )


def validate_configuration_schema(schema: Dict[str, Any]) -> List[str]:
    """
    Validate that a configuration schema is a valid JSON schema.
    
    Args:
        schema: Configuration schema to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    try:
        # Try to create a validator with the schema
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        errors.append(f"Invalid JSON schema: {e.message}")
    except Exception as e:
        errors.append(f"Schema validation error: {str(e)}")
    
    return errors


def validate_template_file_paths(files: List[TemplateFile]) -> List[str]:
    """
    Validate that template file paths are safe and don't contain dangerous patterns.
    
    Args:
        files: List of template files to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    for file in files:
        # Check for absolute paths using string operations for cross-platform compatibility
        if file.path.startswith('/') or (len(file.path) > 1 and file.path[1] == ':'):
            errors.append(f"File path '{file.path}' must be relative")
        
        # Check for parent directory traversal
        if ".." in file.path:
            errors.append(f"File path '{file.path}' contains parent directory traversal")
        
        # Check for empty path components (double slashes)
        if "//" in file.path or "\\\\" in file.path:
            errors.append(f"File path '{file.path}' contains empty path components")
        
        # Check for reserved names on Windows
        path = Path(file.path)
        reserved_names = {"CON", "PRN", "AUX", "NUL", "COM1", "COM2", "COM3", "COM4", 
                         "COM5", "COM6", "COM7", "COM8", "COM9", "LPT1", "LPT2", 
                         "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9"}
        
        for part in path.parts:
            if part.upper().split('.')[0] in reserved_names:
                errors.append(f"File path '{file.path}' contains reserved name '{part}'")
    
    return errors