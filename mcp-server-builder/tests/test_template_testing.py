"""Tests for template testing utilities."""

import pytest
from src.models.template_testing import (
    TemplateTestResult,
    TemplateSchemaValidator,
    ParameterSubstitutionTester,
    TemplateCustomizationTester,
    run_comprehensive_template_tests
)
from src.models.template_loader import create_template_from_minimal_data
from src.models.base import ServerLanguage, ServerFramework, TemplateFile, ServerTemplate


class TestTemplateTestResult:
    """Test cases for TemplateTestResult class."""
    
    def test_initialization(self):
        """Test TemplateTestResult initialization."""
        result = TemplateTestResult()
        
        assert result.passed is True
        assert result.errors == []
        assert result.warnings == []
        assert result.test_results == {}
    
    def test_add_error(self):
        """Test adding error messages."""
        result = TemplateTestResult()
        result.add_error("Test error")
        
        assert result.passed is False
        assert "Test error" in result.errors
    
    def test_add_warning(self):
        """Test adding warning messages."""
        result = TemplateTestResult()
        result.add_warning("Test warning")
        
        assert result.passed is True  # Warnings don't affect pass status
        assert "Test warning" in result.warnings
    
    def test_add_test_result_pass(self):
        """Test adding passing test result."""
        result = TemplateTestResult()
        result.add_test_result("test_name", True)
        
        assert result.passed is True
        assert result.test_results["test_name"] is True
    
    def test_add_test_result_fail(self):
        """Test adding failing test result."""
        result = TemplateTestResult()
        result.add_test_result("test_name", False, "Test failed")
        
        assert result.passed is False
        assert result.test_results["test_name"] is False
        assert "test_name: Test failed" in result.errors


class TestTemplateSchemaValidator:
    """Test cases for TemplateSchemaValidator class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = TemplateSchemaValidator()
        
        self.valid_template = create_template_from_minimal_data(
            template_id="test-template",
            name="Test Template",
            description="A test template",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py"
                }
            ],
            dependencies=["fastmcp>=0.1.0"],
            build_commands=["pip install -e ."],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "default": "Test Server"}
                }
            }
        )
    
    def test_validate_valid_template(self):
        """Test validation of a valid template."""
        result = self.validator.validate_template_compliance(self.valid_template)
        
        assert result.passed is True
        assert len(result.errors) == 0
        assert "schema_validation" in result.test_results
        assert result.test_results["schema_validation"] is True
    
    def test_validate_template_with_invalid_url(self):
        """Test validation of template with invalid URL."""
        invalid_template = create_template_from_minimal_data(
            template_id="invalid-template",
            name="Invalid Template",
            description="Template with invalid URL",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "not-a-valid-url"
                }
            ]
        )
        
        result = self.validator.validate_template_compliance(invalid_template)
        
        assert result.passed is False
        assert any("Invalid URL format" in error for error in result.errors)
        assert result.test_results.get("url_validation") is False
    
    def test_validate_template_with_unsafe_path(self):
        """Test validation of template with unsafe file path."""
        unsafe_template = ServerTemplate(
            id="unsafe-template",
            name="Unsafe Template",
            description="Template with unsafe path",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                TemplateFile(
                    path="../unsafe/path.py",
                    url="https://example.com/unsafe.py"
                )
            ],
            dependencies=[],
            build_commands=[],
            configuration_schema={}
        )
        
        result = self.validator.validate_template_compliance(unsafe_template)
        
        assert result.passed is False
        assert any("File path validation" in error for error in result.errors)
    
    def test_validate_template_with_dangerous_build_command(self):
        """Test validation of template with dangerous build command."""
        dangerous_template = create_template_from_minimal_data(
            template_id="dangerous-template",
            name="Dangerous Template",
            description="Template with dangerous command",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py"
                }
            ],
            build_commands=["rm -rf /"]
        )
        
        result = self.validator.validate_template_compliance(dangerous_template)
        
        assert result.passed is False
        assert any("Invalid build command" in error for error in result.errors)
    
    def test_validate_template_no_dependencies(self):
        """Test validation of template with no dependencies."""
        no_deps_template = create_template_from_minimal_data(
            template_id="no-deps-template",
            name="No Dependencies Template",
            description="Template without dependencies",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py"
                }
            ]
        )
        
        result = self.validator.validate_template_compliance(no_deps_template)
        
        # Should pass but with warning
        assert result.passed is True
        assert any("no dependencies specified" in warning for warning in result.warnings)


class TestParameterSubstitutionTester:
    """Test cases for ParameterSubstitutionTester class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tester = ParameterSubstitutionTester()
        
        self.template = create_template_from_minimal_data(
            template_id="substitution-template",
            name="Substitution Template",
            description="Template for testing substitution",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "{{server_name}}.py",
                    "url": "https://example.com/{{server_name}}.py"
                }
            ],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "default": "default_server"}
                }
            }
        )
    
    def test_parameter_substitution_valid_configs(self):
        """Test parameter substitution with valid configurations."""
        test_configs = [
            {"server_name": "test_server"},
            {"server_name": "another_server"},
            {}  # Empty config to test defaults
        ]
        
        result = self.tester.test_parameter_substitution(self.template, test_configs)
        
        assert result.passed is True
        assert len(result.test_results) >= len(test_configs)
        
        # Check that all substitution tests passed
        for i in range(len(test_configs)):
            test_name = f"substitution_test_{i + 1}"
            assert result.test_results.get(test_name) is True
    
    def test_parameter_substitution_empty_config_list(self):
        """Test parameter substitution with empty config list."""
        result = self.tester.test_parameter_substitution(self.template, [])
        
        assert result.passed is True
        assert len(result.test_results) == 0


class TestTemplateCustomizationTester:
    """Test cases for TemplateCustomizationTester class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.tester = TemplateCustomizationTester()
        
        self.template = create_template_from_minimal_data(
            template_id="customization-template",
            name="Customization Template",
            description="Template for testing customization",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py"
                }
            ],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "default": "default_server"
                    },
                    "port": {
                        "type": "integer",
                        "default": 8080
                    },
                    "debug": {
                        "type": "boolean",
                        "default": False
                    }
                },
                "required": ["server_name"]
            }
        )
    
    def test_template_customization(self):
        """Test template customization functionality."""
        result = self.tester.test_template_customization(self.template)
        
        assert result.passed is True
        
        # Check that all customization tests are present
        expected_tests = [
            "minimal_config_test",
            "full_config_test",
            "invalid_config_test"
        ]
        
        for test_name in expected_tests:
            assert test_name in result.test_results
        
        # Check for edge case tests
        edge_case_tests = [name for name in result.test_results.keys() 
                          if name.startswith("edge_case_")]
        assert len(edge_case_tests) > 0
    
    def test_template_customization_no_schema(self):
        """Test customization of template without configuration schema."""
        no_schema_template = create_template_from_minimal_data(
            template_id="no-schema-template",
            name="No Schema Template",
            description="Template without configuration schema",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py"
                }
            ]
        )
        
        result = self.tester.test_template_customization(no_schema_template)
        
        # Should still pass, just with limited testing
        assert result.passed is True


class TestComprehensiveTemplateTesting:
    """Test cases for comprehensive template testing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.template = create_template_from_minimal_data(
            template_id="comprehensive-template",
            name="Comprehensive Template",
            description="Template for comprehensive testing",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[
                {
                    "path": "main.py",
                    "url": "https://example.com/main.py"
                }
            ],
            dependencies=["fastmcp>=0.1.0"],
            build_commands=["pip install -e ."],
            configuration_schema={
                "type": "object",
                "properties": {
                    "server_name": {"type": "string", "default": "test_server"}
                }
            }
        )
    
    def test_run_comprehensive_template_tests(self):
        """Test running comprehensive template tests."""
        results = run_comprehensive_template_tests(self.template)
        
        # Check that all test categories are present
        expected_categories = [
            "schema_compliance",
            "parameter_substitution",
            "customization"
        ]
        
        for category in expected_categories:
            assert category in results
            assert isinstance(results[category], TemplateTestResult)
        
        # Check that at least some tests passed
        for category, result in results.items():
            assert len(result.test_results) > 0
    
    def test_comprehensive_tests_with_invalid_template(self):
        """Test comprehensive testing with invalid template."""
        invalid_template = ServerTemplate(
            id="",  # Invalid empty ID
            name="Invalid Template",
            description="Invalid template",
            language=ServerLanguage.PYTHON,
            framework=ServerFramework.FASTMCP,
            files=[],  # Empty files list
            dependencies=[],
            build_commands=[],
            configuration_schema={}
        )
        
        results = run_comprehensive_template_tests(invalid_template)
        
        # Should still run all tests, but schema compliance should fail
        assert "schema_compliance" in results
        assert results["schema_compliance"].passed is False
        
        # Other tests might still run
        assert "parameter_substitution" in results
        assert "customization" in results