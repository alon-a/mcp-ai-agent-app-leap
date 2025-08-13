"""Performance and stress tests for MCP server builder."""

import pytest
import tempfile
import os
import shutil
import time
import threading
import psutil
import gc
from pathlib import Path
from unittest.mock import patch, Mock
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

from src.managers.project_manager import ProjectManagerImpl
from src.managers.progress_tracker import LogLevel
from src.managers.template_engine import TemplateEngineImpl
from src.managers.file_manager import FileManagerImpl


class PerformanceMonitor:
    """Helper class to monitor performance metrics."""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.start_memory = None
        self.end_memory = None
        self.peak_memory = None
        self.process = psutil.Process()
    
    def start(self):
        """Start monitoring."""
        gc.collect()  # Clean up before measuring
        self.start_time = time.time()
        self.start_memory = self.process.memory_info().rss
        self.peak_memory = self.start_memory
    
    def update_peak_memory(self):
        """Update peak memory usage."""
        current_memory = self.process.memory_info().rss
        if current_memory > self.peak_memory:
            self.peak_memory = current_memory
    
    def stop(self):
        """Stop monitoring and return metrics."""
        self.end_time = time.time()
        self.end_memory = self.process.memory_info().rss
        
        return {
            'duration_seconds': self.end_time - self.start_time,
            'start_memory_mb': self.start_memory / (1024 * 1024),
            'end_memory_mb': self.end_memory / (1024 * 1024),
            'peak_memory_mb': self.peak_memory / (1024 * 1024),
            'memory_delta_mb': (self.end_memory - self.start_memory) / (1024 * 1024)
        }


class TestPerformanceBenchmarks:
    """Performance benchmark tests."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManagerImpl(log_level=LogLevel.ERROR)  # Reduce logging overhead
        self.monitor = PerformanceMonitor()
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_single_project_creation_performance(self):
        """Benchmark single project creation performance."""
        config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Performance Test Server'
            }
        }
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            self.monitor.start()
            
            result = self.project_manager.create_project(
                name='performance-test-project',
                template='python-fastmcp',
                config=config
            )
            
            metrics = self.monitor.stop()
            
            assert result.success is True
            
            # Performance assertions
            assert metrics['duration_seconds'] < 30.0  # Should complete within 30 seconds
            assert metrics['memory_delta_mb'] < 100.0  # Should not use more than 100MB additional memory
            
            print(f"Single project creation metrics: {metrics}")
    
    def test_template_engine_performance(self):
        """Benchmark template engine operations."""
        engine = TemplateEngineImpl()
        
        self.monitor.start()
        
        # Benchmark template listing
        for _ in range(100):
            templates = engine.list_templates()
            assert len(templates) > 0
            self.monitor.update_peak_memory()
        
        # Benchmark template retrieval
        for _ in range(100):
            template = engine.get_template('python-fastmcp')
            assert template is not None
            self.monitor.update_peak_memory()
        
        # Benchmark template application
        template = engine.get_template('python-fastmcp')
        config = {'server_name': 'Perf Test', 'server_version': '1.0.0'}
        
        for _ in range(50):
            result = engine.apply_template(template, config)
            assert result.success is True
            self.monitor.update_peak_memory()
        
        metrics = self.monitor.stop()
        
        # Performance assertions
        assert metrics['duration_seconds'] < 10.0  # Should complete within 10 seconds
        assert metrics['memory_delta_mb'] < 50.0  # Should not leak significant memory
        
        print(f"Template engine performance metrics: {metrics}")
    
    def test_file_manager_performance(self):
        """Benchmark file manager operations."""
        file_manager = FileManagerImpl()
        
        # Create test directory structure
        large_structure = {}
        for i in range(10):
            large_structure[f'dir_{i}'] = {}
            for j in range(10):
                large_structure[f'dir_{i}'][f'subdir_{j}'] = {}
        
        self.monitor.start()
        
        # Benchmark directory creation
        for iteration in range(5):
            test_dir = Path(self.temp_dir) / f'perf_test_{iteration}'
            success = file_manager.create_directory_structure(str(test_dir), large_structure)
            assert success is True
            self.monitor.update_peak_memory()
        
        metrics = self.monitor.stop()
        
        # Performance assertions
        assert metrics['duration_seconds'] < 5.0  # Should complete within 5 seconds
        assert metrics['memory_delta_mb'] < 20.0  # Should not use excessive memory
        
        print(f"File manager performance metrics: {metrics}")
    
    def test_progress_tracking_performance(self):
        """Benchmark progress tracking overhead."""
        from src.managers.progress_tracker import ProgressTracker
        
        tracker = ProgressTracker(log_level=LogLevel.ERROR)
        project_id = 'perf-test-project'
        
        self.monitor.start()
        
        # Simulate intensive progress tracking
        for phase_num in range(10):
            phase_name = f'phase_{phase_num}'
            tracker.start_phase(project_id, phase_name, f'Starting {phase_name}')
            
            for progress in range(0, 101, 10):
                tracker.update_progress(project_id, progress, f'Progress {progress}%')
                self.monitor.update_peak_memory()
            
            tracker.complete_phase(project_id, f'Completed {phase_name}')
        
        metrics = self.monitor.stop()
        
        # Verify events were tracked
        events = tracker.get_project_events(project_id)
        assert len(events) > 100  # Should have many events
        
        # Performance assertions
        assert metrics['duration_seconds'] < 2.0  # Should be very fast
        assert metrics['memory_delta_mb'] < 10.0  # Should have minimal memory overhead
        
        print(f"Progress tracking performance metrics: {metrics}")
    
    def test_error_handling_performance(self):
        """Benchmark error handling performance."""
        from src.managers.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        
        error_handler = ErrorHandler()
        project_id = 'perf-test-project'
        
        self.monitor.start()
        
        # Generate many errors
        for i in range(1000):
            error_handler.handle_error(
                project_id=project_id,
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f'Performance test error {i}',
                phase='performance_test'
            )
            
            if i % 100 == 0:
                self.monitor.update_peak_memory()
        
        metrics = self.monitor.stop()
        
        # Verify errors were stored
        errors = error_handler.get_project_errors(project_id)
        assert len(errors) == 1000
        
        # Performance assertions
        assert metrics['duration_seconds'] < 5.0  # Should handle 1000 errors quickly
        assert metrics['memory_delta_mb'] < 50.0  # Should not use excessive memory
        
        print(f"Error handling performance metrics: {metrics}")


class TestStressTesting:
    """Stress tests for system limits and concurrent operations."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_manager = ProjectManagerImpl(log_level=LogLevel.ERROR)
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_concurrent_project_creation_stress(self):
        """Stress test concurrent project creation."""
        num_projects = 10
        results = {}
        errors = []
        
        def create_project(project_index):
            """Create a single project."""
            project_name = f'stress-test-project-{project_index}'
            config = {
                'output_directory': self.temp_dir,
                'custom_settings': {
                    'server_name': f'Stress Test Server {project_index}'
                }
            }
            
            with patch('urllib.request.urlretrieve') as mock_download, \
                 patch('subprocess.run') as mock_subprocess:
                
                mock_download.return_value = None
                mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
                
                try:
                    start_time = time.time()
                    result = self.project_manager.create_project(
                        name=project_name,
                        template='python-fastmcp',
                        config=config
                    )
                    end_time = time.time()
                    
                    return {
                        'project_index': project_index,
                        'success': result.success,
                        'duration': end_time - start_time,
                        'status': result.status,
                        'error_count': len(result.errors)
                    }
                except Exception as e:
                    return {
                        'project_index': project_index,
                        'success': False,
                        'error': str(e),
                        'duration': 0
                    }
        
        # Use ThreadPoolExecutor for concurrent execution
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_project, i) for i in range(num_projects)]
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results[result['project_index']] = result
                except Exception as e:
                    errors.append(str(e))
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Analyze results
        successful_projects = [r for r in results.values() if r.get('success', False)]
        failed_projects = [r for r in results.values() if not r.get('success', False)]
        
        durations = [r['duration'] for r in successful_projects if 'duration' in r]
        
        print(f"Concurrent stress test results:")
        print(f"  Total duration: {total_duration:.2f}s")
        print(f"  Successful projects: {len(successful_projects)}/{num_projects}")
        print(f"  Failed projects: {len(failed_projects)}")
        print(f"  Average project duration: {statistics.mean(durations):.2f}s" if durations else "N/A")
        print(f"  Max project duration: {max(durations):.2f}s" if durations else "N/A")
        print(f"  Errors: {len(errors)}")
        
        # Stress test assertions
        assert len(successful_projects) >= num_projects * 0.8  # At least 80% should succeed
        assert total_duration < 60.0  # Should complete within 60 seconds
        if durations:
            assert max(durations) < 30.0  # No single project should take more than 30 seconds
    
    def test_memory_stress_large_projects(self):
        """Stress test memory usage with large project configurations."""
        monitor = PerformanceMonitor()
        
        # Create a large configuration
        large_config = {
            'output_directory': self.temp_dir,
            'custom_settings': {
                'server_name': 'Large Config Test Server',
                'server_version': '1.0.0'
            },
            'environment_variables': {f'VAR_{i}': f'value_{i}' for i in range(100)},
            'additional_dependencies': [f'package-{i}>=1.0.0' for i in range(50)]
        }
        
        monitor.start()
        
        with patch('urllib.request.urlretrieve') as mock_download, \
             patch('subprocess.run') as mock_subprocess:
            
            mock_download.return_value = None
            mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
            
            # Create multiple projects with large configurations
            for i in range(5):
                project_name = f'large-config-project-{i}'
                
                result = self.project_manager.create_project(
                    name=project_name,
                    template='python-fastmcp',
                    config=large_config
                )
                
                assert result.success is True
                monitor.update_peak_memory()
                
                # Force garbage collection between projects
                gc.collect()
        
        metrics = monitor.stop()
        
        print(f"Memory stress test metrics: {metrics}")
        
        # Memory stress assertions
        assert metrics['peak_memory_mb'] < 500.0  # Should not exceed 500MB peak memory
        assert metrics['memory_delta_mb'] < 200.0  # Should not leak more than 200MB
    
    def test_template_engine_stress(self):
        """Stress test template engine with many operations."""
        engine = TemplateEngineImpl()
        monitor = PerformanceMonitor()
        
        monitor.start()
        
        # Stress test template operations
        for iteration in range(100):
            # List templates
            templates = engine.list_templates()
            assert len(templates) > 0
            
            # Get each template multiple times
            for template in templates:
                retrieved = engine.get_template(template.id)
                assert retrieved is not None
                
                # Apply template with different configurations
                for config_variant in range(3):
                    config = {
                        'server_name': f'Stress Test {iteration}-{config_variant}',
                        'server_version': f'{iteration}.{config_variant}.0'
                    }
                    
                    result = engine.apply_template(retrieved, config)
                    assert result.success is True
            
            if iteration % 10 == 0:
                monitor.update_peak_memory()
                gc.collect()  # Periodic cleanup
        
        metrics = monitor.stop()
        
        print(f"Template engine stress test metrics: {metrics}")
        
        # Stress test assertions
        assert metrics['duration_seconds'] < 60.0  # Should complete within 60 seconds
        assert metrics['memory_delta_mb'] < 100.0  # Should not leak significant memory
    
    def test_file_system_stress(self):
        """Stress test file system operations."""
        file_manager = FileManagerImpl()
        monitor = PerformanceMonitor()
        
        monitor.start()
        
        # Create many directory structures
        for iteration in range(20):
            test_dir = Path(self.temp_dir) / f'stress_test_{iteration}'
            
            # Create nested structure
            structure = {}
            for i in range(5):
                structure[f'level1_{i}'] = {}
                for j in range(5):
                    structure[f'level1_{i}'][f'level2_{j}'] = {}
                    for k in range(3):
                        structure[f'level1_{i}'][f'level2_{j}'][f'level3_{k}'] = {}
            
            success = file_manager.create_directory_structure(str(test_dir), structure)
            assert success is True
            
            if iteration % 5 == 0:
                monitor.update_peak_memory()
        
        metrics = monitor.stop()
        
        print(f"File system stress test metrics: {metrics}")
        
        # Verify all directories were created
        total_dirs = 0
        for root, dirs, files in os.walk(self.temp_dir):
            total_dirs += len(dirs)
        
        print(f"Total directories created: {total_dirs}")
        
        # Stress test assertions
        assert metrics['duration_seconds'] < 30.0  # Should complete within 30 seconds
        assert total_dirs > 1000  # Should have created many directories
    
    def test_error_handling_stress(self):
        """Stress test error handling with many errors."""
        from src.managers.error_handler import ErrorHandler, ErrorCategory, ErrorSeverity
        
        error_handler = ErrorHandler()
        monitor = PerformanceMonitor()
        
        categories = list(ErrorCategory)
        severities = list(ErrorSeverity)
        
        monitor.start()
        
        # Generate many errors across multiple projects
        for project_num in range(10):
            project_id = f'stress-project-{project_num}'
            
            for error_num in range(100):
                category = categories[error_num % len(categories)]
                severity = severities[error_num % len(severities)]
                
                error_handler.handle_error(
                    project_id=project_id,
                    category=category,
                    severity=severity,
                    message=f'Stress test error {error_num}',
                    phase=f'phase_{error_num % 5}',
                    details={'error_number': error_num, 'project_number': project_num}
                )
            
            if project_num % 2 == 0:
                monitor.update_peak_memory()
        
        metrics = monitor.stop()
        
        # Verify error storage
        total_errors = 0
        for project_num in range(10):
            project_id = f'stress-project-{project_num}'
            errors = error_handler.get_project_errors(project_id)
            total_errors += len(errors)
            
            # Test error summary performance
            summary = error_handler.get_error_summary(project_id)
            assert summary['error_count'] == 100
        
        print(f"Error handling stress test metrics: {metrics}")
        print(f"Total errors stored: {total_errors}")
        
        # Stress test assertions
        assert total_errors == 1000  # Should have stored all errors
        assert metrics['duration_seconds'] < 10.0  # Should handle errors quickly
        assert metrics['memory_delta_mb'] < 100.0  # Should not use excessive memory
    
    def test_progress_tracking_stress(self):
        """Stress test progress tracking with intensive updates."""
        from src.managers.progress_tracker import ProgressTracker
        
        tracker = ProgressTracker(log_level=LogLevel.ERROR)
        monitor = PerformanceMonitor()
        
        monitor.start()
        
        # Simulate many projects with intensive progress tracking
        for project_num in range(20):
            project_id = f'stress-project-{project_num}'
            
            for phase_num in range(5):
                phase_name = f'phase_{phase_num}'
                tracker.start_phase(project_id, phase_name, f'Starting {phase_name}')
                
                # Many progress updates
                for progress in range(0, 101, 2):  # 50 updates per phase
                    tracker.update_progress(
                        project_id, 
                        progress, 
                        f'Progress {progress}%',
                        {'current_step': progress, 'phase': phase_name}
                    )
                
                tracker.complete_phase(project_id, f'Completed {phase_name}')
            
            if project_num % 5 == 0:
                monitor.update_peak_memory()
        
        metrics = monitor.stop()
        
        # Verify tracking worked
        total_events = 0
        for project_num in range(20):
            project_id = f'stress-project-{project_num}'
            events = tracker.get_project_events(project_id)
            total_events += len(events)
            
            # Test summary performance
            summary = tracker.get_project_summary(project_id)
            assert summary['project_id'] == project_id
        
        print(f"Progress tracking stress test metrics: {metrics}")
        print(f"Total events tracked: {total_events}")
        
        # Stress test assertions
        assert total_events > 2000  # Should have tracked many events (20 projects * 5 phases * 52 events per phase)
        assert metrics['duration_seconds'] < 15.0  # Should handle intensive tracking quickly
        assert metrics['memory_delta_mb'] < 150.0  # Should not use excessive memory


class TestResourceMonitoring:
    """Tests for monitoring resource usage during operations."""
    
    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""
        project_manager = ProjectManagerImpl(log_level=LogLevel.ERROR)
        temp_dir = tempfile.mkdtemp()
        
        try:
            initial_memory = psutil.Process().memory_info().rss
            memory_samples = []
            
            config = {
                'output_directory': temp_dir,
                'custom_settings': {'server_name': 'Leak Test Server'}
            }
            
            with patch('urllib.request.urlretrieve') as mock_download, \
                 patch('subprocess.run') as mock_subprocess:
                
                mock_download.return_value = None
                mock_subprocess.return_value = Mock(returncode=0, stdout='', stderr='')
                
                # Perform repeated operations
                for i in range(10):
                    project_name = f'leak-test-{i}'
                    
                    result = project_manager.create_project(
                        name=project_name,
                        template='python-fastmcp',
                        config=config
                    )
                    
                    assert result.success is True
                    
                    # Clean up project to simulate normal usage
                    project_manager.cleanup_project(result.project_id)
                    
                    # Force garbage collection
                    gc.collect()
                    
                    # Sample memory usage
                    current_memory = psutil.Process().memory_info().rss
                    memory_samples.append(current_memory)
            
            final_memory = memory_samples[-1]
            memory_growth = (final_memory - initial_memory) / (1024 * 1024)  # MB
            
            print(f"Memory leak test:")
            print(f"  Initial memory: {initial_memory / (1024 * 1024):.2f} MB")
            print(f"  Final memory: {final_memory / (1024 * 1024):.2f} MB")
            print(f"  Memory growth: {memory_growth:.2f} MB")
            
            # Memory leak assertion
            assert memory_growth < 50.0  # Should not grow by more than 50MB
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    def test_cpu_usage_monitoring(self):
        """Test CPU usage during intensive operations."""
        import psutil
        
        process = psutil.Process()
        cpu_samples = []
        
        # Monitor CPU usage during template operations
        engine = TemplateEngineImpl()
        
        start_time = time.time()
        
        for i in range(100):
            # CPU-intensive template operations
            templates = engine.list_templates()
            
            for template in templates:
                retrieved = engine.get_template(template.id)
                config = {'server_name': f'CPU Test {i}', 'server_version': '1.0.0'}
                result = engine.apply_template(retrieved, config)
                assert result.success is True
            
            # Sample CPU usage
            if i % 10 == 0:
                cpu_percent = process.cpu_percent()
                cpu_samples.append(cpu_percent)
        
        end_time = time.time()
        duration = end_time - start_time
        
        if cpu_samples:
            avg_cpu = statistics.mean(cpu_samples)
            max_cpu = max(cpu_samples)
            
            print(f"CPU usage monitoring:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Average CPU: {avg_cpu:.2f}%")
            print(f"  Max CPU: {max_cpu:.2f}%")
            
            # CPU usage should be reasonable
            assert avg_cpu < 80.0  # Average CPU should not exceed 80%
    
    def test_disk_usage_monitoring(self):
        """Test disk usage during file operations."""
        temp_dir = tempfile.mkdtemp()
        
        try:
            initial_disk_usage = shutil.disk_usage(temp_dir).used
            
            file_manager = FileManagerImpl()
            
            # Create many directory structures
            for i in range(50):
                test_dir = Path(temp_dir) / f'disk_test_{i}'
                
                # Large nested structure
                structure = {}
                for j in range(10):
                    structure[f'dir_{j}'] = {}
                    for k in range(10):
                        structure[f'dir_{j}'][f'subdir_{k}'] = {}
                
                success = file_manager.create_directory_structure(str(test_dir), structure)
                assert success is True
            
            final_disk_usage = shutil.disk_usage(temp_dir).used
            disk_usage_mb = (final_disk_usage - initial_disk_usage) / (1024 * 1024)
            
            print(f"Disk usage monitoring:")
            print(f"  Disk usage: {disk_usage_mb:.2f} MB")
            
            # Disk usage should be reasonable for directory creation
            assert disk_usage_mb < 100.0  # Should not use more than 100MB for directories
            
        finally:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Run with specific markers for performance tests
    pytest.main([__file__, "-v", "-s"])  # -s to see print output