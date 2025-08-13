"""Input validation utilities for CLI."""

import re
import os
from pathlib import Path
from typing import Optional


def validate_project_name(name: str) -> Optional[str]:
    """
    Validate project name.
    
    Args:
        name: Project name to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not name:
        return "Project name cannot be empty"
    
    if len(name) < 2:
        return "Project name must be at least 2 characters long"
    
    if len(name) > 50:
        return "Project name must be 50 characters or less"
    
    # Check for valid identifier pattern (letters, numbers, hyphens, underscores)
    if not re.match(r'^[a-zA-Z][a-zA-Z0-9_-]*$', name):
        return "Project name must start with a letter and contain only letters, numbers, hyphens, and underscores"
    
    # Check for reserved names
    reserved_names = {
        'con', 'prn', 'aux', 'nul', 'com1', 'com2', 'com3', 'com4', 'com5',
        'com6', 'com7', 'com8', 'com9', 'lpt1', 'lpt2', 'lpt3', 'lpt4',
        'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    
    if name.lower() in reserved_names:
        return f"'{name}' is a reserved name and cannot be used"
    
    return None


def validate_output_directory(path: str) -> Optional[str]:
    """
    Validate output directory path.
    
    Args:
        path: Directory path to validate
        
    Returns:
        Error message if invalid, None if valid
    """
    if not path:
        return "Output directory cannot be empty"
    
    try:
        # Convert to Path object for validation
        dir_path = Path(path)
        
        # Check if path is absolute and exists
        if dir_path.is_absolute():
            if not dir_path.exists():
                return f"Directory '{path}' does not exist"
            if not dir_path.is_dir():
                return f"'{path}' is not a directory"
        
        # Check for invalid characters (Windows-specific)
        invalid_chars = '<>:"|?*'
        if any(char in str(dir_path) for char in invalid_chars):
            return f"Directory path contains invalid characters: {invalid_chars}"
        
        # Check if we can write to the directory (if it exists)
        if dir_path.exists() and not os.access(dir_path, os.W_OK):
            return f"No write permission for directory '{path}'"
        
        return None
        
    except (OSError, ValueError) as e:
        return f"Invalid directory path: {e}"


def validate_template_id(template_id: str, available_templates: list) -> Optional[str]:
    """
    Validate template ID against available templates.
    
    Args:
        template_id: Template ID to validate
        available_templates: List of available template IDs
        
    Returns:
        Error message if invalid, None if valid
    """
    if not template_id:
        return "Template ID cannot be empty"
    
    if template_id not in available_templates:
        return f"Template '{template_id}' not found. Available templates: {', '.join(available_templates)}"
    
    return None


def validate_config_file(config_path: str) -> Optional[str]:
    """
    Validate configuration file path and format.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Error message if invalid, None if valid
    """
    if not config_path:
        return "Configuration file path cannot be empty"
    
    config_file = Path(config_path)
    
    if not config_file.exists():
        return f"Configuration file '{config_path}' does not exist"
    
    if not config_file.is_file():
        return f"'{config_path}' is not a file"
    
    # Check file extension
    valid_extensions = {'.json', '.yaml', '.yml'}
    if config_file.suffix.lower() not in valid_extensions:
        return f"Configuration file must have one of these extensions: {', '.join(valid_extensions)}"
    
    # Check if file is readable
    if not os.access(config_file, os.R_OK):
        return f"No read permission for configuration file '{config_path}'"
    
    return None


def validate_verbosity_level(level: int) -> Optional[str]:
    """
    Validate verbosity level.
    
    Args:
        level: Verbosity level (0-3)
        
    Returns:
        Error message if invalid, None if valid
    """
    if level < 0:
        return "Verbosity level cannot be negative"
    
    if level > 3:
        return "Maximum verbosity level is 3 (-vvv)"
    
    return None