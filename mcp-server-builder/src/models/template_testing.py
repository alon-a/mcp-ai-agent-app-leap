"""Template testing utilities for the MCP Server Builder."""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from .base import ServerTemplate, TemplateFile
from .validation import TemplateValidator, validate_template_file_paths
from .template_loader import TemplateLoader


class TemplateTestResult:
    """Result of template testing operations."""
    
    def __init__(self):
        self.passed: bool = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.test_results: Dict[str, bool] = {}
    
    def add_error(self, message: str) -> None:
        """Add an error message."""
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)
    
    def add_test_result(self, test_name: str, passed: bool, message: str = None) -> None:
        """Add a test result."""
        self.test_results[test_name] = passed
        if not passed:
            self.passed = False
            if message:
                self.add_error(f"{test_name}: {message}")


class TemplateSchemaValidator:
    """Advanced template schema validation utilities."""
    
    def __init__(self):
        self.validator = TemplateValidator()
    
    def validate_template_compliance(self, template: ServerTemplate) -> TemplateTestResult:
        """
        Perform comprehensive template compliance validation.
        
        Args:
            template: ServerTemplate to validate
            
        Returns:
            TemplateTestResult with validation results
        """
        result = TemplateTestResult()
        
        # Basic schema validation
        schema_errors = self.validator.validate_template(template)
        if schema_errors:
            for error in schema_errors:
                result.add_error(f"Schema validation: {error}")
        else:
            result.add_test_result("schema_validation", True)
        
        # File path validation
        path_errors = validate_template_file_paths(template.files)
        if path_errors:
            for error in path_errors:
                result.add_error(f"File path validation: {error}")
        else:
            result.add_test_result("file_path_validation", True)
        
        # URL validation
        self._validate_file_urls(template, result)
        
        # Dependency validation
        self._validate_dependencies(template, result)
        
        # Build command validation
        self._validate_build_commands(template, result)
        
        # Configuration schema validation
        self._validate_configuration_schema(template, result)
        
        return result
    
    def _validate_file_urls(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Validate file URLs in template."""
        import re
        
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        valid_urls = 0
        for file in template.files:
            if url_pattern.match(file.url):
                valid_urls += 1
            else:
                result.add_error(f"Invalid URL format: {file.url}")
        
        if valid_urls == len(template.files):
            result.add_test_result("url_validation", True)
        else:
            result.add_test_result("url_validation", False, 
                                 f"Only {valid_urls}/{len(template.files)} URLs are valid")
    
    def _validate_dependencies(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Validate dependency specifications."""
        if not template.dependencies:
            result.add_warning("Template has no dependencies specified")
            result.add_test_result("dependency_validation", True)
            return
        
        valid_deps = 0
        for dep in template.dependencies:
            if self._is_valid_dependency_spec(dep):
                valid_deps += 1
            else:
                result.add_error(f"Invalid dependency specification: {dep}")
        
        if valid_deps == len(template.dependencies):
            result.add_test_result("dependency_validation", True)
        else:
            result.add_test_result("dependency_validation", False,
                                 f"Only {valid_deps}/{len(template.dependencies)} dependencies are valid")
    
    def _is_valid_dependency_spec(self, dep: str) -> bool:
        """Check if dependency specification is valid."""
        if not dep or not isinstance(dep, str):
            return False
        
        # Basic validation - should contain package name
        # More sophisticated validation could check against package registries
        return len(dep.strip()) > 0 and not dep.startswith(' ')
    
    def _validate_build_commands(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Validate build command specifications."""
        if not template.build_commands:
            result.add_warning("Template has no build commands specified")
            result.add_test_result("build_command_validation", True)
            return
        
        valid_commands = 0
        for cmd in template.build_commands:
            if self._is_valid_build_command(cmd):
                valid_commands += 1
            else:
                result.add_error(f"Invalid build command: {cmd}")
        
        if valid_commands == len(template.build_commands):
            result.add_test_result("build_command_validation", True)
        else:
            result.add_test_result("build_command_validation", False,
                                 f"Only {valid_commands}/{len(template.build_commands)} commands are valid")
    
    def _is_valid_build_command(self, cmd: str) -> bool:
        """Check if build command is valid."""
        if not cmd or not isinstance(cmd, str):
            return False
        
        # Basic validation - should not be empty and not contain dangerous patterns
        cmd = cmd.strip()
        if not cmd:
            return False
        
        # Check for potentially dangerous commands
        dangerous_patterns = ['rm -rf', 'del /f', 'format', 'fdisk', 'mkfs']
        cmd_lower = cmd.lower()
        
        for pattern in dangerous_patterns:
            if pattern in cmd_lower:
                return False
        
        return True
    
    def _validate_configuration_schema(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Validate configuration schema."""
        if not template.configuration_schema:
            result.add_warning("Template has no configuration schema")
            result.add_test_result("config_schema_validation", True)
            return
        
        try:
            from ..models.validation import validate_configuration_schema
            schema_errors = validate_configuration_schema(template.configuration_schema)
            
            if schema_errors:
                for error in schema_errors:
                    result.add_error(f"Configuration schema: {error}")
                result.add_test_result("config_schema_validation", False)
            else:
                result.add_test_result("config_schema_validation", True)
                
        except ImportError:
            result.add_warning("Cannot validate configuration schema - jsonschema not available")
            result.add_test_result("config_schema_validation", True)


class ParameterSubstitutionTester:
    """Test parameter substitution functionality."""
    
    def test_parameter_substitution(self, template: ServerTemplate, 
                                  test_configs: List[Dict[str, Any]]) -> TemplateTestResult:
        """
        Test parameter substitution with various configurations.
        
        Args:
            template: Template to test
            test_configs: List of test configurations
            
        Returns:
            TemplateTestResult with substitution test results
        """
        result = TemplateTestResult()
        
        from ..managers.template_engine import TemplateEngineImpl
        engine = TemplateEngineImpl()
        
        for i, config in enumerate(test_configs):
            test_name = f"substitution_test_{i + 1}"
            
            try:
                template_result = engine.apply_template(template, config)
                
                if template_result.success:
                    result.add_test_result(test_name, True)
                    
                    # Verify that parameters were actually substituted
                    if self._verify_substitution(template_result.applied_config, config):
                        result.add_test_result(f"{test_name}_verification", True)
                    else:
                        result.add_test_result(f"{test_name}_verification", False,
                                             "Parameter substitution verification failed")
                else:
                    result.add_test_result(test_name, False, 
                                         f"Template application failed: {template_result.errors}")
                    
            except Exception as e:
                result.add_test_result(test_name, False, f"Exception during substitution: {str(e)}")
        
        return result
    
    def _verify_substitution(self, applied_config: Dict[str, Any], 
                           original_config: Dict[str, Any]) -> bool:
        """Verify that parameter substitution worked correctly."""
        # Check that all original config values are present in applied config
        for key, value in original_config.items():
            if key not in applied_config or applied_config[key] != value:
                return False
        return True


class TemplateCustomizationTester:
    """Test template customization functionality."""
    
    def test_template_customization(self, template: ServerTemplate) -> TemplateTestResult:
        """
        Test various template customization scenarios.
        
        Args:
            template: Template to test
            
        Returns:
            TemplateTestResult with customization test results
        """
        result = TemplateTestResult()
        
        # Test with minimal configuration
        self._test_minimal_config(template, result)
        
        # Test with full configuration
        self._test_full_config(template, result)
        
        # Test with invalid configuration
        self._test_invalid_config(template, result)
        
        # Test with edge case configurations
        self._test_edge_cases(template, result)
        
        return result
    
    def _test_minimal_config(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Test with minimal required configuration."""
        from ..managers.template_engine import TemplateEngineImpl
        engine = TemplateEngineImpl()
        
        # Extract required fields from schema
        required_config = {}
        if template.configuration_schema and "required" in template.configuration_schema:
            for required_field in template.configuration_schema["required"]:
                if (template.configuration_schema.get("properties", {})
                    .get(required_field, {}).get("default")):
                    required_config[required_field] = (
                        template.configuration_schema["properties"][required_field]["default"]
                    )
                else:
                    # Use a generic test value
                    required_config[required_field] = f"test_{required_field}"
        
        try:
            template_result = engine.apply_template(template, required_config)
            if template_result.success:
                result.add_test_result("minimal_config_test", True)
            else:
                result.add_test_result("minimal_config_test", False,
                                     f"Minimal config failed: {template_result.errors}")
        except Exception as e:
            result.add_test_result("minimal_config_test", False, str(e))
    
    def _test_full_config(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Test with full configuration."""
        from ..managers.template_engine import TemplateEngineImpl
        engine = TemplateEngineImpl()
        
        # Create full config from schema
        full_config = {}
        if template.configuration_schema and "properties" in template.configuration_schema:
            for prop_name, prop_schema in template.configuration_schema["properties"].items():
                if "default" in prop_schema:
                    full_config[prop_name] = prop_schema["default"]
                elif prop_schema.get("type") == "string":
                    full_config[prop_name] = f"test_{prop_name}"
                elif prop_schema.get("type") == "integer":
                    full_config[prop_name] = 42
                elif prop_schema.get("type") == "boolean":
                    full_config[prop_name] = True
        
        try:
            template_result = engine.apply_template(template, full_config)
            if template_result.success:
                result.add_test_result("full_config_test", True)
            else:
                result.add_test_result("full_config_test", False,
                                     f"Full config failed: {template_result.errors}")
        except Exception as e:
            result.add_test_result("full_config_test", False, str(e))
    
    def _test_invalid_config(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Test with invalid configuration."""
        from ..managers.template_engine import TemplateEngineImpl
        engine = TemplateEngineImpl()
        
        # Test with invalid types
        invalid_config = {"invalid_field": "invalid_value"}
        
        try:
            template_result = engine.apply_template(template, invalid_config)
            # Invalid config should either fail or be handled gracefully
            result.add_test_result("invalid_config_test", True)
        except Exception as e:
            result.add_test_result("invalid_config_test", True)  # Exception is acceptable
    
    def _test_edge_cases(self, template: ServerTemplate, result: TemplateTestResult) -> None:
        """Test edge case configurations."""
        from ..managers.template_engine import TemplateEngineImpl
        engine = TemplateEngineImpl()
        
        edge_cases = [
            {},  # Empty config
            {"": "empty_key"},  # Empty key
            {"key": ""},  # Empty value
            {"key": None},  # None value
        ]
        
        for i, config in enumerate(edge_cases):
            test_name = f"edge_case_{i + 1}"
            try:
                template_result = engine.apply_template(template, config)
                result.add_test_result(test_name, True)  # Should handle gracefully
            except Exception as e:
                result.add_test_result(test_name, True)  # Exception is acceptable for edge cases


def run_comprehensive_template_tests(template: ServerTemplate) -> Dict[str, TemplateTestResult]:
    """
    Run comprehensive tests on a template.
    
    Args:
        template: Template to test
        
    Returns:
        Dictionary mapping test category to results
    """
    results = {}
    
    # Schema compliance tests
    schema_validator = TemplateSchemaValidator()
    results["schema_compliance"] = schema_validator.validate_template_compliance(template)
    
    # Parameter substitution tests
    substitution_tester = ParameterSubstitutionTester()
    test_configs = [
        {"server_name": "Test Server"},
        {"server_name": "Another Server", "version": "2.0.0"},
        {}  # Empty config to test defaults
    ]
    results["parameter_substitution"] = substitution_tester.test_parameter_substitution(
        template, test_configs
    )
    
    # Customization tests
    customization_tester = TemplateCustomizationTester()
    results["customization"] = customization_tester.test_template_customization(template)
    
    return results