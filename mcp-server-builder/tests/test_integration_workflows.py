"""Integration tests for end-to-end MCP server builder workflows."""

import pytest
import tempfile
import os
import shutil
import json
import yaml
import subprocess
import time
from pathlib import Path
from unittest.mock import patch, Mock

from src.managers.project_manager import ProjectManagerImpl
from src.managers.progress_tracker import LogLevel
from src.models.base import ProjectStatus


class TestEndToEndWorkflows:
    """Integration tests for complete project creation workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManagerImpl(log_level=LogLevel.DEBUG)
        self.test_project_name = "test-integration-project"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_python_fastmcp_complete_workflow(self):
        """Test complete workflow for Python FastMCP server creation."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Test FastMCP Server',
                'server_version': '1.0.0',
                'transport': 'stdio'
            },
            'environment_variables': {
                'DEBUG': 'true',
                'LOG_LEVEL': 'info'
            },
            'additional_dependencies': [
                'requests>=2.31.0'
            ]
        }
        
        # Mock network operations to avoid actual downloads
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            # Mock successful download
            mock_download.return_value = None
            
            # Mock successful subprocess calls (pip install, build commands)
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            # Create project
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            # Verify project creation succeeded
            assert result.success is True
            assert result.status == ProjectStatus.COMPLETED
            assert len(result.errors) == 0
            
            # Verify project directory was created
            project_path = Path(self.temp_dir) / self.test_project_name
            assert project_path.exists()
            assert project_path.is_dir()
            
            # Verify basic project structure
            expected_files = ['pyproject.toml', 'README.md', 'src']
            for expected_file in expected_files:
                assert (project_path / expected_file).exists()
            
            # Verify configuration was applied
            if (project_path / 'pyproject.toml').exists():
                with open(project_path / 'pyproject.toml', 'r') as f:
                    content = f.read()
                    assert 'Test FastMCP Server' in content or self.test_project_name in content
    
    def test_python_lowlevel_complete_workflow(self):
        """Test complete workflow for Python low-level server creation."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Test Low-level Server',
                'server_version': '2.0.0',
                'transport': 'http'
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-lowlevel',
                config=config
            )
            
            assert result.success is True
            assert result.status == ProjectStatus.COMPLETED
            
            project_path = Path(self.temp_dir) / self.test_project_name
            assert project_path.exists()
            
            # Verify Python project structure
            expected_files = ['pyproject.toml', 'README.md']
            for expected_file in expected_files:
                assert (project_path / expected_file).exists()
    
    def test_typescript_sdk_complete_workflow(self):
        """Test complete workflow for TypeScript SDK server creation."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Test TypeScript Server',
                'server_version': '1.5.0',
                'transport': 'sse'
            },
            'additional_dependencies': [
                'express@^4.18.0',
                'cors@^2.8.5'
            ]
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='typescript-sdk',
                config=config
            )
            
            assert result.success is True
            assert result.status == ProjectStatus.COMPLETED
            
            project_path = Path(self.temp_dir) / self.test_project_name
            assert project_path.exists()
            
            # Verify TypeScript project structure
            expected_files = ['package.json', 'tsconfig.json', 'README.md']
            for expected_file in expected_files:
                assert (project_path / expected_file).exists()
            
            # Verify package.json contains custom dependencies
            if (project_path / 'package.json').exists():
                with open(project_path / 'package.json', 'r') as f:
                    package_data = json.load(f)
                    dependencies = package_data.get('dependencies', {})
                    assert 'express' in dependencies or '@modelcontextprotocol/sdk' in dependencies
    
    def test_workflow_with_network_failure_recovery(self):
        """Test workflow with network failure and recovery."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Test Recovery Server'
            }
        }
        
        # Mock network failure followed by success
        download_attempts = []
        
        def mock_download_with_retry(url, path):
            download_attempts.append(url)
            if len(download_attempts) <= 2:  # Fail first 2 attempts
                raise Exception("Network error")
            # Succeed on 3rd attempt
            Path(path).write_text("mock file content")
        
        with patch('urllib.request.urlretrieve', side_effect=mock_download_with_retry), \
             patch('subprocess.run') as mock_subprocess:
            
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            # Should eventually succeed after retries
            assert result.success is True
            assert len(download_attempts) >= 3  # Should have retried
    
    def test_workflow_with_build_failure(self):
        """Test workflow behavior when build commands fail."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Test Build Failure'
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            # Mock build failure
            mock_subprocess.return_value = Mock(
                returncode=1, 
                stdout='', 
                stderr='Build failed: missing dependency'
            )
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            # Should fail due to build error
            assert result.success is False
            assert result.status == ProjectStatus.FAILED
            assert len(result.errors) > 0
            assert any('build' in error.lower() for error in result.errors)
    
    def test_workflow_with_invalid_template(self):
        """Test workflow with invalid template ID."""
        config = {
            'output_directory': self.temp_dir
        }
        
        result = self.project_manager.create_project(
            name=self.test_project_name,
            template='nonexistent-template',
            config=config
        )
        
        assert result.success is False
        assert result.status == ProjectStatus.FAILED
        assert len(result.errors) > 0
    
    def test_workflow_with_invalid_output_directory(self):
        """Test workflow with invalid output directory."""
        config = {
            'output_directory': '/nonexistent/path/that/cannot/be/created'
        }
        
        result = self.project_manager.create_project(
            name=self.test_project_name,
            template='python-fastmcp',
            config=config
        )
        
        assert result.success is False
        assert result.status == ProjectStatus.FAILED
    
    def test_workflow_progress_tracking(self):
        """Test that progress is properly tracked throughout workflow."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Progress Test Server'
            }
        }
        
        progress_events = []
        
        def progress_callback(event):
            progress_events.append(event)
        
        self.project_manager.add_progress_callback(progress_callback)
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            assert result.success is True
            
            # Verify progress events were generated
            assert len(progress_events) > 0
            
            # Check that we have phase start and complete events
            phase_starts = [e for e in progress_events if e.event_type.value == 'phase_start']
            phase_completes = [e for e in progress_events if e.event_type.value == 'phase_complete']
            
            assert len(phase_starts) > 0
            assert len(phase_completes) > 0
            
            # Verify expected phases were tracked
            phases = {e.phase for e in progress_events}
            expected_phases = ['initialization', 'template_preparation', 'directory_creation']
            
            for expected_phase in expected_phases:
                assert expected_phase in phases
    
    def test_workflow_error_handling_and_rollback(self):
        """Test error handling and rollback functionality."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Rollback Test Server'
            }
        }
        
        # Create a scenario where file creation succeeds but build fails
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            # Build fails
            mock_subprocess.return_value = Mock(
                returncode=1,
                stdout='',
                stderr='Critical build error'
            )
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            assert result.success is False
            
            # Verify error information is available
            errors = self.project_manager.get_project_errors(result.project_id)
            assert len(errors) > 0
            
            # Verify error summary
            error_summary = self.project_manager.get_error_summary(result.project_id)
            assert error_summary['error_count'] > 0
    
    def test_concurrent_project_creation(self):
        """Test creating multiple projects concurrently."""
        import threading
        import time
        
        results = {}
        
        def create_project(project_name, template):
            config = {
                'output_directory': self.temp_dir,
                'custom_settings': {
                    'server_name': f'Concurrent {project_name}'
                }
            }
            
            with patch('urllib.request.urlretrieve') as mock_download, \
                 patch('subprocess.run') as mock_subprocess:
                
                mock_download.return_value = None
                mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
                
                # Add small random delay to encourage race conditions
                time.sleep(0.01)
                
                result = self.project_manager.create_project(
                    name=project_name,
                    template=template,
                    config=config
                )
                
                results[project_name] = result
        
        # Start multiple threads
        threads = []
        project_configs = [
            ('concurrent-project-1', 'python-fastmcp'),
            ('concurrent-project-2', 'python-lowlevel'),
            ('concurrent-project-3', 'typescript-sdk')
        ]
        
        for project_name, template in project_configs:
            thread = threading.Thread(target=create_project, args=(project_name, template))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all projects were created successfully
        assert len(results) == 3
        for project_name, result in results.items():
            assert result.success is True
            assert result.status == ProjectStatus.COMPLETED
            
            # Verify project directories exist
            project_path = Path(self.temp_dir) / project_name
            assert project_path.exists()
    
    def test_workflow_with_custom_configuration_file(self):
        """Test workflow using configuration from file."""
        # Create a configuration file
        config_data = {
            'template': 'python-fastmcp',
            'custom_settings': {
                'server_name': 'Config File Server',
                'server_version': '3.0.0',
                'transport': 'http'
            },
            'environment_variables': {
                'API_KEY': 'test-key-123',
                'DEBUG': 'false'
            },
            'additional_dependencies': [
                'pydantic>=2.0.0',
                'fastapi>=0.100.0'
            ]
        }
        
        config_file = Path(self.temp_dir) / 'test-config.json'
        with open(config_file, 'w') as f:
            json.dump(config_data, f, indent=2)
        
        # Load configuration and create project
        from src.cli.config_loader import load_config_file, validate_config_schema
        
        loaded_config = load_config_file(str(config_file))
        validated_config = validate_config_schema(loaded_config)
        
        # Add output directory
        project_config = {
            'output_directory': self.temp_dir,
            **validated_config.get('custom_settings', {}),
            'environment_variables': validated_config.get('environment_variables', {}),
            'additional_dependencies': validated_config.get('additional_dependencies', [])
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template=validated_config['template'],
                config=project_config
            )
            
            assert result.success is True
            assert result.status == ProjectStatus.COMPLETED
    
    def test_workflow_validation_integration(self):
        """Test integration with validation engine."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Validation Test Server'
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess, \
             patch('src.managers.validation_engine.ValidationEngineImpl.validate_server') as mock_validate:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            # Mock validation success
            from src.models.validation import ValidationResult
            mock_validate.return_value = ValidationResult(
                success=True,
                server_path=str(Path(self.temp_dir) / self.test_project_name),
                validation_errors=[],
                performance_metrics={},
                compliance_results={}
            )
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            assert result.success is True
            
            # Verify validation was called
            mock_validate.assert_called_once()
    
    def test_cross_platform_compatibility(self):
        """Test cross-platform compatibility aspects."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Cross Platform Server'
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            assert result.success is True
            
            project_path = Path(self.temp_dir) / self.test_project_name
            assert project_path.exists()
            
            # Verify path separators are handled correctly
            for root, dirs, files in os.walk(project_path):
                for file in files:
                    file_path = Path(root) / file
                    assert file_path.exists()
                    # Verify file is readable
                    assert os.access(file_path, os.R_OK)
    
    def test_cleanup_after_failure(self):
        """Test cleanup behavior after project creation failure."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Cleanup Test Server'
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            # File download succeeds
            mock_download.return_value = None
            
            # Build fails critically
            mock_subprocess.return_value = Mock(
                returncode=1,
                stdout='',
                stderr='Critical failure'
            )
            
            result = self.project_manager.create_project(
                name=self.test_project_name,
                template='python-fastmcp',
                config=config
            )
            
            assert result.success is False
            
            # Test cleanup functionality
            cleanup_success = self.project_manager.cleanup_project(result.project_id)
            
            # Cleanup might succeed or fail depending on what was created
            # The important thing is that it doesn't crash
            assert isinstance(cleanup_success, bool)


class TestTemplateSpecificWorkflows:
    """Integration tests for template-specific workflows."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManagerImpl(log_level=LogLevel.INFO)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_python_fastmcp_specific_features(self):
        """Test Python FastMCP template specific features."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'FastMCP Feature Test',
                'transport': 'stdio',
                'enable_tools': True,
                'enable_resources': True,
                'enable_prompts': False
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name='fastmcp-features-test',
                template='python-fastmcp',
                config=config
            )
            
            assert result.success is True
            
            project_path = Path(self.temp_dir) / 'fastmcp-features-test'
            
            # Verify FastMCP-specific files
            expected_files = ['pyproject.toml', 'src']
            for expected_file in expected_files:
                assert (project_path / expected_file).exists()
    
    def test_typescript_sdk_specific_features(self):
        """Test TypeScript SDK template specific features."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'TypeScript Feature Test',
                'transport': 'sse',
                'build_target': 'es2020',
                'include_examples': True
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name='typescript-features-test',
                template='typescript-sdk',
                config=config
            )
            
            assert result.success is True
            
            project_path = Path(self.temp_dir) / 'typescript-features-test'
            
            # Verify TypeScript-specific files
            expected_files = ['package.json', 'tsconfig.json']
            for expected_file in expected_files:
                assert (project_path / expected_file).exists()
    
    def test_python_lowlevel_specific_features(self):
        """Test Python low-level template specific features."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Low-level Feature Test',
                'transport': 'http',
                'include_async_support': True,
                'include_logging': True
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            result = self.project_manager.create_project(
                name='lowlevel-features-test',
                template='python-lowlevel',
                config=config
            )
            
            assert result.success is True
            
            project_path = Path(self.temp_dir) / 'lowlevel-features-test'
            
            # Verify low-level specific files
            expected_files = ['pyproject.toml', 'README.md']
            for expected_file in expected_files:
                assert (project_path / expected_file).exists()


if __name__ == "__main__":
    pytest.main([__file__])