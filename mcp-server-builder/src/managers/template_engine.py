"""Template engine implementation for MCP Server Builder."""

import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from ..models.base import ServerTemplate, TemplateResult, ServerLanguage, ServerFramework
from ..models.template_loader import TemplateLoader, TemplateLoadError, create_template_from_minimal_data
from ..models.validation import TemplateValidationError
from .interfaces import TemplateEngine


class TemplateEngineImpl(TemplateEngine):
    """Implementation of the TemplateEngine interface."""
    
    def __init__(self, template_directory: Optional[str] = None):
        """
        Initialize the template engine.
        
        Args:
            template_directory: Optional path to directory containing custom templates
        """
        self.loader = TemplateLoader()
        self.template_directory = template_directory
        self._templates: Dict[str, ServerTemplate] = {}
        self._load_built_in_templates()
        
        if template_directory:
            self._load_custom_templates()
    
    def _load_built_in_templates(self) -> None:
        """Load built-in templates."""
        # Python FastMCP Template
        python_fastmcp = create_template_from_minimal_data(
            template_id="python-fastmcp",
            name="Python FastMCP Server",
            description="High-level Python MCP server using the FastMCP framework with decorators",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/examples/fastmcp/main.py",
                    "executable": False
                },
                {
                    "path": "pyproject.toml",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/examples/fastmcp/pyproject.toml",
                    "executable": False
                },
                {
                    "path": "README.md",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/examples/fastmcp/README.md",
                    "executable": False
                }
            ],
            dependencies=["fastmcp>=0.1.0", "pydantic>=2.0.0"],
            build_commands=["pip install -e ."],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of the MCP server",
                        "default": "My FastMCP Server"
                    },
                    "server_version": {
                        "type": "string",
                        "description": "Version of the server",
                        "default": "1.0.0"
                    },
                    "transport": {
                        "type": "string",
                        "enum": ["stdio", "http", "sse"],
                        "description": "Transport protocol to use",
                        "default": "stdio"
                    }
                },
                "required": ["server_name"]
            }
        )
        
        # Python Low-level SDK Template
        python_lowlevel = create_template_from_minimal_data(
            template_id="python-lowlevel",
            name="Python Low-level MCP Server",
            description="Low-level Python MCP server using direct protocol implementation",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.LOW_LEVEL,
            files=[
                {
                    "path": "server.py",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/examples/lowlevel/server.py",
                    "executable": False
                },
                {
                    "path": "pyproject.toml",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/examples/lowlevel/pyproject.toml",
                    "executable": False
                },
                {
                    "path": "README.md",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/python-sdk/main/examples/lowlevel/README.md",
                    "executable": False
                }
            ],
            dependencies=["mcp>=1.0.0", "pydantic>=2.0.0"],
            build_commands=["pip install -e ."],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of the MCP server",
                        "default": "My Low-level Server"
                    },
                    "server_version": {
                        "type": "string",
                        "description": "Version of the server",
                        "default": "1.0.0"
                    },
                    "transport": {
                        "type": "string",
                        "enum": ["stdio", "http", "sse"],
                        "description": "Transport protocol to use",
                        "default": "stdio"
                    }
                },
                "required": ["server_name"]
            }
        )
        
        # TypeScript SDK Template
        typescript_sdk = create_template_from_minimal_data(
            template_id="typescript-sdk",
            name="TypeScript MCP Server",
            description="TypeScript MCP server using the official TypeScript SDK",
            language=ServerLanguage.TYPESCRIPT,
            framework=ServerFramework.TYPESCRIPT_SDK,
            files=[
                {
                    "path": "src/index.ts",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/examples/basic/src/index.ts",
                    "executable": False
                },
                {
                    "path": "package.json",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/examples/basic/package.json",
                    "executable": False
                },
                {
                    "path": "tsconfig.json",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/examples/basic/tsconfig.json",
                    "executable": False
                },
                {
                    "path": "README.md",
                    "url": "https://raw.githubusercontent.com/modelcontextprotocol/typescript-sdk/main/examples/basic/README.md",
                    "executable": False
                }
            ],
            dependencies=["@modelcontextprotocol/sdk", "typescript", "@types/node"],
            build_commands=["npm install", "npm run build"],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of the MCP server",
                        "default": "My TypeScript Server"
                    },
                    "server_version": {
                        "type": "string",
                        "description": "Version of the server",
                        "default": "1.0.0"
                    },
                    "transport": {
                        "type": "string",
                        "enum": ["stdio", "http", "sse"],
                        "description": "Transport protocol to use",
                        "default": "stdio"
                    }
                },
                "required": ["server_name"]
            }
        )
        
        # Store built-in templates
        self._templates[python_fastmcp.id] = python_fastmcp
        self._templates[python_lowlevel.id] = python_lowlevel
        self._templates[typescript_sdk.id] = typescript_sdk
    
    def _load_custom_templates(self) -> None:
        """Load custom templates from the template directory."""
        if not self.template_directory:
            return
        
        try:
            custom_templates = self.loader.load_from_directory(self.template_directory)
            for template in custom_templates:
                self._templates[template.id] = template
        except TemplateLoadError:
            # Silently ignore custom template loading errors
            # Built-in templates will still be available
            pass
    
    def list_templates(self) -> List[ServerTemplate]:
        """List all available server templates."""
        return list(self._templates.values())
    
    def get_template(self, template_id: str) -> Optional[ServerTemplate]:
        """Get a specific template by ID."""
        return self._templates.get(template_id)
    
    def apply_template(self, template: ServerTemplate, config: Dict[str, Any]) -> TemplateResult:
        """Apply a template with given configuration."""
        try:
            # Validate configuration against template schema
            validation_errors = self._validate_configuration(template, config)
            if validation_errors:
                return TemplateResult(
                    success=False,
                    generated_files=[],
                    applied_config={},
                    errors=validation_errors
                )
            
            # Apply parameter substitution to template files
            generated_files = []
            applied_config = self._merge_with_defaults(template, config)
            
            for template_file in template.files:
                # Apply parameter substitution to file path
                substituted_path = self._substitute_parameters(template_file.path, applied_config)
                generated_files.append(substituted_path)
            
            return TemplateResult(
                success=True,
                generated_files=generated_files,
                applied_config=applied_config,
                errors=[]
            )
            
        except Exception as e:
            return TemplateResult(
                success=False,
                generated_files=[],
                applied_config={},
                errors=[f"Template application failed: {str(e)}"]
            )
    
    def _validate_configuration(self, template: ServerTemplate, config: Dict[str, Any]) -> List[str]:
        """Validate configuration against template schema."""
        errors = []
        
        if not template.configuration_schema:
            return errors
        
        try:
            import jsonschema
            jsonschema.validate(config, template.configuration_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Configuration validation error: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Template schema error: {e.message}")
        except ImportError:
            # If jsonschema is not available, skip validation
            pass
        
        return errors
    
    def _merge_with_defaults(self, template: ServerTemplate, config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge user configuration with template defaults."""
        merged_config = {}
        
        # Extract defaults from schema
        if template.configuration_schema and "properties" in template.configuration_schema:
            for prop_name, prop_schema in template.configuration_schema["properties"].items():
                if "default" in prop_schema:
                    merged_config[prop_name] = prop_schema["default"]
        
        # Override with user-provided values
        merged_config.update(config)
        
        return merged_config
    
    def _substitute_parameters(self, text: str, config: Dict[str, Any]) -> str:
        """Substitute template parameters in text."""
        # Replace {{parameter}} patterns with values from config
        def replace_param(match):
            param_name = match.group(1).strip()
            return str(config.get(param_name, match.group(0)))
        
        return re.sub(r'{{([^}]+)}}', replace_param, text)
    
    def add_template(self, template: ServerTemplate) -> bool:
        """
        Add a new template to the engine.
        
        Args:
            template: ServerTemplate to add
            
        Returns:
            True if template was added successfully
        """
        try:
            # Validate the template
            from ..models.validation import TemplateValidator
            validator = TemplateValidator()
            errors = validator.validate_template(template)
            
            if errors:
                return False
            
            self._templates[template.id] = template
            return True
            
        except Exception:
            return False
    
    def remove_template(self, template_id: str) -> bool:
        """
        Remove a template from the engine.
        
        Args:
            template_id: ID of template to remove
            
        Returns:
            True if template was removed successfully
        """
        if template_id in self._templates:
            del self._templates[template_id]
            return True
        return False
    
    def get_templates_by_language(self, language: ServerLanguage) -> List[ServerTemplate]:
        """
        Get all templates for a specific language.
        
        Args:
            language: Server language to filter by
            
        Returns:
            List of templates for the specified language
        """
        return [template for template in self._templates.values() 
                if template.language == language]
    
    def get_templates_by_framework(self, framework: ServerFramework) -> List[ServerTemplate]:
        """
        Get all templates for a specific framework.
        
        Args:
            framework: Server framework to filter by
            
        Returns:
            List of templates for the specified framework
        """
        return [template for template in self._templates.values() 
                if template.framework == framework]
    
    def reload_templates(self) -> None:
        """Reload all templates (built-in and custom)."""
        self._templates.clear()
        self._load_built_in_templates()
        if self.template_directory:
            self._load_custom_templates()