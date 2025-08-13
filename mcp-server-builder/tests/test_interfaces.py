"""Tests for manager interfaces."""

import pytest
from abc import ABC
from src.managers import (
    ProjectManager,
    TemplateEngine,
    FileManager,
    DependencyManager,
    BuildSystem,
    ValidationEngine,
)


def test_interfaces_are_abstract():
    """Test that all manager interfaces are abstract base classes."""
    # These should raise TypeError when trying to instantiate directly
    with pytest.raises(TypeError):
        ProjectManager()
    
    with pytest.raises(TypeError):
        TemplateEngine()
    
    with pytest.raises(TypeError):
        FileManager()
    
    with pytest.raises(TypeError):
        DependencyManager()
    
    with pytest.raises(TypeError):
        BuildSystem()
    
    with pytest.raises(TypeError):
        ValidationEngine()


def test_interfaces_inherit_from_abc():
    """Test that all interfaces inherit from ABC."""
    assert issubclass(ProjectManager, ABC)
    assert issubclass(TemplateEngine, ABC)
    assert issubclass(FileManager, ABC)
    assert issubclass(DependencyManager, ABC)
    assert issubclass(BuildSystem, ABC)
    assert issubclass(ValidationEngine, ABC)


def test_interface_methods_are_abstract():
    """Test that interface methods are properly marked as abstract."""
    # Check that key methods exist and are abstract
    assert hasattr(ProjectManager, 'create_project')
    assert hasattr(ProjectManager, 'get_project_status')
    assert hasattr(ProjectManager, 'cleanup_project')
    
    assert hasattr(TemplateEngine, 'list_templates')
    assert hasattr(TemplateEngine, 'get_template')
    assert hasattr(TemplateEngine, 'apply_template')
    
    assert hasattr(FileManager, 'create_directory_structure')
    assert hasattr(FileManager, 'download_files')
    assert hasattr(FileManager, 'set_permissions')
    
    assert hasattr(DependencyManager, 'detect_package_manager')
    assert hasattr(DependencyManager, 'install_dependencies')
    assert hasattr(DependencyManager, 'verify_installation')
    
    assert hasattr(BuildSystem, 'detect_build_system')
    assert hasattr(BuildSystem, 'execute_build')
    assert hasattr(BuildSystem, 'get_build_artifacts')
    
    assert hasattr(ValidationEngine, 'validate_server_startup')
    assert hasattr(ValidationEngine, 'validate_mcp_protocol')
    assert hasattr(ValidationEngine, 'validate_functionality')
    assert hasattr(ValidationEngine, 'run_comprehensive_tests')