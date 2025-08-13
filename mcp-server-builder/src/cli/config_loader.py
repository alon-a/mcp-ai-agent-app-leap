"""Configuration file loading utilities."""

import json
import yaml
from pathlib import Path
from typing import Dict, Any


def load_config_file(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from JSON or YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
        
    Raises:
        ValueError: If file format is not supported or invalid
        FileNotFoundError: If file doesn't exist
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Determine file format by extension
        if config_file.suffix.lower() == '.json':
            return json.loads(content)
        elif config_file.suffix.lower() in ('.yaml', '.yml'):
            return yaml.safe_load(content) or {}
        else:
            # Try to auto-detect format
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                try:
                    return yaml.safe_load(content) or {}
                except yaml.YAMLError:
                    raise ValueError(f"Unsupported configuration file format: {config_file.suffix}")
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in configuration file: {e}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Error reading configuration file: {e}")


def get_config_schema() -> Dict[str, Any]:
    """
    Get the JSON schema for configuration validation.
    
    Returns:
        JSON schema dictionary
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "MCP Server Builder Configuration",
        "type": "object",
        "properties": {
            "template": {
                "type": "string",
                "description": "Template ID to use for server creation",
                "examples": ["python-fastmcp", "python-lowlevel", "typescript-sdk"]
            },
            "custom_settings": {
                "type": "object",
                "description": "Template-specific configuration settings",
                "additionalProperties": True
            },
            "environment_variables": {
                "type": "object",
                "description": "Environment variables for the server",
                "patternProperties": {
                    "^[A-Z_][A-Z0-9_]*$": {
                        "type": ["string", "number", "boolean"]
                    }
                },
                "additionalProperties": False
            },
            "additional_dependencies": {
                "type": "array",
                "description": "Additional package dependencies",
                "items": {
                    "type": "string",
                    "pattern": "^[a-zA-Z0-9_-]+([><=!~]+[0-9.]+.*)?$"
                }
            }
        },
        "additionalProperties": False
    }


def validate_config_schema(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate configuration against JSON schema.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated and normalized configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    try:
        import jsonschema
        
        # Get schema and validate
        schema = get_config_schema()
        jsonschema.validate(config, schema)
        
        # Additional custom validation
        validated_config = {}
        
        # Copy valid keys
        for key in ['template', 'custom_settings', 'environment_variables', 'additional_dependencies']:
            if key in config:
                validated_config[key] = config[key]
        
        # Normalize environment variables to strings
        if 'environment_variables' in validated_config:
            env_vars = validated_config['environment_variables']
            for key, value in env_vars.items():
                env_vars[key] = str(value)
        
        return validated_config
        
    except ImportError:
        # Fallback to basic validation if jsonschema not available
        return _validate_config_basic(config)
    except jsonschema.ValidationError as e:
        raise ValueError(f"Configuration validation error: {e.message}")
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")


def _validate_config_basic(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Basic configuration validation without jsonschema.
    
    Args:
        config: Configuration dictionary to validate
        
    Returns:
        Validated configuration
        
    Raises:
        ValueError: If configuration is invalid
    """
    # Define expected schema
    expected_keys = {
        'template': str,
        'custom_settings': dict,
        'environment_variables': dict,
        'additional_dependencies': list
    }
    
    validated_config = {}
    
    for key, expected_type in expected_keys.items():
        if key in config:
            value = config[key]
            if not isinstance(value, expected_type):
                raise ValueError(f"Configuration key '{key}' must be of type {expected_type.__name__}, got {type(value).__name__}")
            validated_config[key] = value
    
    # Validate additional_dependencies items are strings
    if 'additional_dependencies' in validated_config:
        deps = validated_config['additional_dependencies']
        for i, dep in enumerate(deps):
            if not isinstance(dep, str):
                raise ValueError(f"Dependency at index {i} must be a string, got {type(dep).__name__}")
    
    # Validate environment_variables values are strings
    if 'environment_variables' in validated_config:
        env_vars = validated_config['environment_variables']
        for key, value in env_vars.items():
            if not isinstance(key, str):
                raise ValueError(f"Environment variable key must be a string, got {type(key).__name__}")
            if not isinstance(value, (str, int, float, bool)):
                raise ValueError(f"Environment variable '{key}' value must be a string, number, or boolean")
            # Convert to string
            env_vars[key] = str(value)
    
    return validated_config


def create_example_config() -> Dict[str, Any]:
    """
    Create an example configuration dictionary.
    
    Returns:
        Example configuration
    """
    return {
        "template": "python-fastmcp",
        "custom_settings": {
            "server_name": "My MCP Server",
            "server_version": "1.0.0",
            "transport": "stdio"
        },
        "environment_variables": {
            "DEBUG": "false",
            "LOG_LEVEL": "info"
        },
        "additional_dependencies": [
            "requests>=2.31.0",
            "pydantic>=2.0.0"
        ]
    }


def save_config_file(config: Dict[str, Any], output_path: str, format_type: str = 'json') -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration dictionary to save
        output_path: Path where to save the configuration
        format_type: File format ('json' or 'yaml')
        
    Raises:
        ValueError: If format is not supported
    """
    output_file = Path(output_path)
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            if format_type.lower() == 'json':
                json.dump(config, f, indent=2, ensure_ascii=False)
            elif format_type.lower() in ('yaml', 'yml'):
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            else:
                raise ValueError(f"Unsupported format: {format_type}")
    
    except Exception as e:
        raise ValueError(f"Error saving configuration file: {e}")