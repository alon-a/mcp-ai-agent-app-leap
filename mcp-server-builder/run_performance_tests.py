#!/usr/bin/env python3
"""
Performance test runner for MCP Server Builder.

This script runs performance and stress tests with proper monitoring
and reporting of system resources.
"""

import sys
import os
import time
import psutil
import subprocess
import json
from pathlib import Path
from datetime import datetime


class PerformanceTestRunner:
    """Runner for performance tests with system monitoring."""
    
    def __init__(self):
        self.start_time = None
        self.results = {}
        self.system_info = self._get_system_info()
    
    def _get_system_info(self):
        """Get system information for test context."""
        return {
            'cpu_count': psutil.cpu_count(),
            'cpu_count_logical': psutil.cpu_count(logical=True),
            'memory_total_gb': psutil.virtual_memory().total / (1024**3),
            'python_version': sys.version,
            'platform': sys.platform,
            'timestamp': datetime.now().isoformat()
        }
    
    def run_test_suite(self, test_file, test_name=None):
        """Run a specific test suite with monitoring."""
        print(f"\n{'='*60}")
        print(f"Running performance tests: {test_file}")
        if test_name:
            print(f"Specific test: {test_name}")
        print(f"{'='*60}")
        
        # Build pytest command
        cmd = [
            sys.executable, '-m', 'pytest',
            test_file,
            '-v',
            '-s',  # Show print output
            '--tb=short',
            '--disable-warnings'
        ]
        
        if test_name:
            cmd.extend(['-k', test_name])
        
        # Monitor system resources during test
        process = psutil.Process()
        start_memory = process.memory_info().rss
        start_time = time.time()
        
        try:
            # Run the tests
            result = subprocess.run(
                cmd,
                capture_output=False,  # Let output go to console
                text=True,
                cwd=Path(__file__).parent
            )
            
            end_time = time.time()
            end_memory = process.memory_info().rss
            
            # Record results
            test_results = {
                'exit_code': result.returncode,
                'duration_seconds': end_time - start_time,
                'memory_start_mb': start_memory / (1024 * 1024),
                'memory_end_mb': end_memory / (1024 * 1024),
                'memory_delta_mb': (end_memory - start_memory) / (1024 * 1024),
                'success': result.returncode == 0
            }
            
            self.results[f"{test_file}:{test_name or 'all'}"] = test_results
            
            print(f"\nTest Results for {test_file}:")
            print(f"  Exit Code: {test_results['exit_code']}")
            print(f"  Duration: {test_results['duration_seconds']:.2f}s")
            print(f"  Memory Delta: {test_results['memory_delta_mb']:.2f}MB")
            print(f"  Success: {test_results['success']}")
            
            return test_results['success']
            
        except Exception as e:
            print(f"Error running tests: {e}")
            return False
    
    def run_all_performance_tests(self):
        """Run all performance test suites."""
        test_suites = [
            ('tests/test_performance_stress.py::TestPerformanceBenchmarks', 'Performance Benchmarks'),
            ('tests/test_performance_stress.py::TestStressTesting', 'Stress Tests'),
            ('tests/test_performance_stress.py::TestResourceMonitoring', 'Resource Monitoring'),
        ]
        
        print(f"System Information:")
        for key, value in self.system_info.items():
            print(f"  {key}: {value}")
        
        all_passed = True
        
        for test_suite, description in test_suites:
            print(f"\n{'='*60}")
            print(f"Running {description}")
            print(f"{'='*60}")
            
            success = self.run_test_suite(test_suite)
            if not success:
                all_passed = False
                print(f"❌ {description} FAILED")
            else:
                print(f"✅ {description} PASSED")
        
        return all_passed
    
    def generate_report(self, output_file='performance_report.json'):
        """Generate a performance test report."""
        report = {
            'system_info': self.system_info,
            'test_results': self.results,
            'summary': {
                'total_tests': len(self.results),
                'passed_tests': sum(1 for r in self.results.values() if r['success']),
                'failed_tests': sum(1 for r in self.results.values() if not r['success']),
                'total_duration': sum(r['duration_seconds'] for r in self.results.values()),
                'total_memory_delta': sum(r['memory_delta_mb'] for r in self.results.values())
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\nPerformance report saved to: {output_file}")
        return report


def main():
    """Main entry point for performance test runner."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run MCP Server Builder performance tests')
    parser.add_argument('--test', help='Specific test to run')
    parser.add_argument('--suite', help='Specific test suite to run')
    parser.add_argument('--report', default='performance_report.json', 
                       help='Output file for performance report')
    parser.add_argument('--quick', action='store_true', 
                       help='Run only quick performance tests')
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner()
    
    if args.test:
        # Run specific test
        success = runner.run_test_suite('tests/test_performance_stress.py', args.test)
    elif args.suite:
        # Run specific suite
        success = runner.run_test_suite(f'tests/test_performance_stress.py::{args.suite}')
    elif args.quick:
        # Run only quick tests
        quick_tests = [
            'test_template_engine_performance',
            'test_progress_tracking_performance',
            'test_error_handling_performance'
        ]
        success = True
        for test in quick_tests:
            if not runner.run_test_suite('tests/test_performance_stress.py', test):
                success = False
    else:
        # Run all performance tests
        success = runner.run_all_performance_tests()
    
    # Generate report
    report = runner.generate_report(args.report)
    
    # Print summary
    print(f"\n{'='*60}")
    print("PERFORMANCE TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed_tests']}")
    print(f"Failed: {report['summary']['failed_tests']}")
    print(f"Total Duration: {report['summary']['total_duration']:.2f}s")
    print(f"Total Memory Delta: {report['summary']['total_memory_delta']:.2f}MB")
    
    if success:
        print("🎉 All performance tests PASSED!")
        sys.exit(0)
    else:
        print("❌ Some performance tests FAILED!")
        sys.exit(1)


if __name__ == '__main__':
    main()