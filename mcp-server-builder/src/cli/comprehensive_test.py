"""CLI command for comprehensive MCP server testing."""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any

from ..managers.validation_engine import MCPValidationEngine
from ..managers.comprehensive_testing import ComprehensiveServerTester
from ..models.enums import ValidationLevel


def create_comprehensive_test_parser(subparsers):
    """Create the comprehensive test command parser.
    
    Args:
        subparsers: Argparse subparsers object
    """
    parser = subparsers.add_parser(
        'comprehensive-test',
        help='Run comprehensive tests on an MCP server project',
        description='Execute comprehensive testing including performance benchmarks, '
                   'integration tests, load testing, and security scans on an MCP server.'
    )
    
    parser.add_argument(
        'project_path',
        help='Path to the MCP server project directory'
    )
    
    parser.add_argument(
        '--skip-performance',
        action='store_true',
        help='Skip performance benchmarking tests'
    )
    
    parser.add_argument(
        '--skip-integration',
        action='store_true',
        help='Skip integration tests with different MCP clients'
    )
    
    parser.add_argument(
        '--skip-load-testing',
        action='store_true',
        help='Skip load testing'
    )
    
    parser.add_argument(
        '--skip-security',
        action='store_true',
        help='Skip security scanning'
    )
    
    parser.add_argument(
        '--validation-level',
        choices=['basic', 'standard', 'comprehensive'],
        default='standard',
        help='Level of validation to perform (default: standard)'
    )
    
    parser.add_argument(
        '--max-workers',
        type=int,
        default=4,
        help='Maximum number of worker threads for concurrent testing (default: 4)'
    )
    
    parser.add_argument(
        '--timeout',
        type=int,
        default=30,
        help='Timeout for validation operations in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--output-format',
        choices=['text', 'json'],
        default='text',
        help='Output format for test results (default: text)'
    )
    
    parser.add_argument(
        '--output-file',
        help='File to write test results to (default: stdout)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.set_defaults(func=run_comprehensive_test)


def run_comprehensive_test(args):
    """Run comprehensive testing on an MCP server project.
    
    Args:
        args: Parsed command line arguments
    """
    try:
        # Validate project path
        project_path = Path(args.project_path)
        if not project_path.exists():
            print(f"Error: Project path '{project_path}' does not exist", file=sys.stderr)
            return 1
        
        if not project_path.is_dir():
            print(f"Error: Project path '{project_path}' is not a directory", file=sys.stderr)
            return 1
        
        # Convert validation level
        validation_level_map = {
            'basic': ValidationLevel.BASIC,
            'standard': ValidationLevel.STANDARD,
            'comprehensive': ValidationLevel.COMPREHENSIVE
        }
        validation_level = validation_level_map[args.validation_level]
        
        if args.verbose:
            print(f"Starting comprehensive testing for: {project_path}")
            print(f"Validation level: {args.validation_level}")
            print(f"Max workers: {args.max_workers}")
            print(f"Timeout: {args.timeout}s")
            print()
        
        # Initialize testing components
        validation_engine = MCPValidationEngine(
            timeout=args.timeout,
            validation_level=validation_level
        )
        
        comprehensive_tester = ComprehensiveServerTester(
            validation_engine=validation_engine,
            max_workers=args.max_workers
        )
        
        # Run comprehensive tests
        if args.verbose:
            print("Running comprehensive tests...")
        
        test_report = comprehensive_tester.run_comprehensive_tests(
            project_path=str(project_path),
            include_performance=not args.skip_performance,
            include_integration=not args.skip_integration,
            include_load_testing=not args.skip_load_testing,
            include_security_scan=not args.skip_security
        )
        
        # Format and output results
        if args.output_format == 'json':
            output = format_json_output(test_report)
        else:
            output = format_text_output(test_report, verbose=args.verbose)
        
        # Write output
        if args.output_file:
            with open(args.output_file, 'w') as f:
                f.write(output)
            if args.verbose:
                print(f"Results written to: {args.output_file}")
        else:
            print(output)
        
        # Return appropriate exit code
        return 0 if test_report.overall_success else 1
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Error during comprehensive testing: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


def format_text_output(test_report, verbose: bool = False) -> str:
    """Format test report as human-readable text.
    
    Args:
        test_report: ComprehensiveTestReport to format
        verbose: Whether to include verbose details
        
    Returns:
        Formatted text output
    """
    lines = []
    
    # Header
    lines.append("=" * 60)
    lines.append("MCP Server Comprehensive Test Report")
    lines.append("=" * 60)
    lines.append(f"Project: {test_report.project_path}")
    lines.append(f"Test Time: {test_report.test_timestamp}")
    lines.append(f"Duration: {test_report.total_test_duration:.2f}s")
    lines.append(f"Overall Success: {'PASS' if test_report.overall_success else 'FAIL'}")
    lines.append("")
    
    # Basic Validation Summary
    lines.append("Basic Validation:")
    lines.append(f"  Status: {'PASS' if test_report.basic_validation.overall_success else 'FAIL'}")
    lines.append(f"  Startup: {'PASS' if test_report.basic_validation.startup_result.success else 'FAIL'}")
    lines.append(f"  Protocol: {'PASS' if test_report.basic_validation.protocol_result.success else 'FAIL'}")
    lines.append(f"  Functionality: {'PASS' if test_report.basic_validation.functionality_result.success else 'FAIL'}")
    lines.append("")
    
    # Performance Benchmarks
    if test_report.performance_benchmarks:
        lines.append("Performance Benchmarks:")
        for benchmark in test_report.performance_benchmarks:
            status = "PASS" if benchmark.error_rate < 0.1 else "FAIL"
            lines.append(f"  {status} {benchmark.operation_name}:")
            lines.append(f"    Requests: {benchmark.successful_requests}/{benchmark.total_requests}")
            lines.append(f"    Avg Response: {benchmark.average_response_time:.3f}s")
            lines.append(f"    RPS: {benchmark.requests_per_second:.1f}")
            lines.append(f"    Error Rate: {benchmark.error_rate:.1%}")
            if verbose:
                lines.append(f"    Memory: {benchmark.memory_usage_mb:.1f}MB")
                lines.append(f"    CPU: {benchmark.cpu_usage_percent:.1f}%")
        lines.append("")
    
    # Integration Tests
    if test_report.integration_results:
        lines.append("Integration Tests:")
        for integration in test_report.integration_results:
            status = "PASS" if integration.compatibility_score > 0.7 else "FAIL"
            lines.append(f"  {status} {integration.client_name}:")
            lines.append(f"    Connection: {'PASS' if integration.connection_successful else 'FAIL'}")
            lines.append(f"    Compatibility: {integration.compatibility_score:.1%}")
            lines.append(f"    Supported: {len(integration.supported_features)} features")
            if integration.failed_features:
                lines.append(f"    Failed: {', '.join(integration.failed_features)}")
        lines.append("")
    
    # Load Testing
    if test_report.load_test_results:
        lines.append("Load Testing:")
        load_results = test_report.load_test_results
        status = "PASS" if load_results.get("success", False) else "FAIL"
        lines.append(f"  {status} Status: {'PASS' if load_results.get('success', False) else 'FAIL'}")
        if load_results.get("concurrent_users"):
            lines.append(f"    Max Users: {load_results['concurrent_users']}")
            lines.append(f"    Total Requests: {load_results.get('total_requests', 0)}")
            lines.append(f"    Error Rate: {load_results.get('error_rate', 0):.1%}")
            lines.append(f"    RPS: {load_results.get('requests_per_second', 0):.1f}")
        lines.append("")
    
    # Security Scan
    if test_report.security_scan_results:
        lines.append("Security Scan:")
        security = test_report.security_scan_results
        status = "PASS" if security.get("critical_issues", 0) == 0 else "FAIL"
        lines.append(f"  {status} Status: {'SECURE' if security.get('critical_issues', 0) == 0 else 'VULNERABLE'}")
        lines.append(f"    Critical: {security.get('critical_issues', 0)}")
        lines.append(f"    High: {security.get('high_issues', 0)}")
        lines.append(f"    Medium: {security.get('medium_issues', 0)}")
        lines.append(f"    Low: {security.get('low_issues', 0)}")
        lines.append(f"    Files Scanned: {security.get('scanned_files', 0)}")
        lines.append("")
    
    # Recommendations
    if test_report.recommendations:
        lines.append("Recommendations:")
        for i, recommendation in enumerate(test_report.recommendations, 1):
            lines.append(f"  {i}. {recommendation}")
        lines.append("")
    
    # Detailed errors (if verbose and there are failures)
    if verbose and not test_report.overall_success:
        lines.append("Detailed Issues:")
        
        if not test_report.basic_validation.overall_success:
            if test_report.basic_validation.startup_result.errors:
                lines.append("  Startup Errors:")
                for error in test_report.basic_validation.startup_result.errors:
                    lines.append(f"    - {error}")
            
            if test_report.basic_validation.protocol_result.errors:
                lines.append("  Protocol Errors:")
                for error in test_report.basic_validation.protocol_result.errors:
                    lines.append(f"    - {error}")
            
            if test_report.basic_validation.functionality_result.errors:
                lines.append("  Functionality Errors:")
                for error in test_report.basic_validation.functionality_result.errors:
                    lines.append(f"    - {error}")
        
        if test_report.security_scan_results.get("issues"):
            lines.append("  Security Issues:")
            for issue in test_report.security_scan_results["issues"][:10]:  # Limit to first 10
                lines.append(f"    - {issue['severity'].upper()}: {issue['description']}")
                if issue.get('file') and issue.get('line'):
                    lines.append(f"      File: {issue['file']}:{issue['line']}")
        
        lines.append("")
    
    return "\n".join(lines)


def format_json_output(test_report) -> str:
    """Format test report as JSON.
    
    Args:
        test_report: ComprehensiveTestReport to format
        
    Returns:
        JSON formatted output
    """
    # Convert the test report to a dictionary for JSON serialization
    report_dict = {
        "project_path": test_report.project_path,
        "test_timestamp": test_report.test_timestamp,
        "overall_success": test_report.overall_success,
        "total_test_duration": test_report.total_test_duration,
        "basic_validation": {
            "overall_success": test_report.basic_validation.overall_success,
            "startup_success": test_report.basic_validation.startup_result.success,
            "protocol_success": test_report.basic_validation.protocol_result.success,
            "functionality_success": test_report.basic_validation.functionality_result.success,
            "startup_time": test_report.basic_validation.startup_result.startup_time,
            "supported_capabilities": test_report.basic_validation.protocol_result.supported_capabilities,
            "missing_capabilities": test_report.basic_validation.protocol_result.missing_capabilities,
            "tested_tools": test_report.basic_validation.functionality_result.tested_tools,
            "tested_resources": test_report.basic_validation.functionality_result.tested_resources,
            "tested_prompts": test_report.basic_validation.functionality_result.tested_prompts,
        },
        "performance_benchmarks": [
            {
                "operation_name": b.operation_name,
                "total_requests": b.total_requests,
                "successful_requests": b.successful_requests,
                "failed_requests": b.failed_requests,
                "average_response_time": b.average_response_time,
                "min_response_time": b.min_response_time,
                "max_response_time": b.max_response_time,
                "percentile_95_response_time": b.percentile_95_response_time,
                "requests_per_second": b.requests_per_second,
                "error_rate": b.error_rate,
                "memory_usage_mb": b.memory_usage_mb,
                "cpu_usage_percent": b.cpu_usage_percent
            }
            for b in test_report.performance_benchmarks
        ],
        "integration_results": [
            {
                "client_name": r.client_name,
                "connection_successful": r.connection_successful,
                "handshake_time": r.handshake_time,
                "supported_features": r.supported_features,
                "failed_features": r.failed_features,
                "compatibility_score": r.compatibility_score,
                "errors": r.errors
            }
            for r in test_report.integration_results
        ],
        "load_test_results": test_report.load_test_results,
        "security_scan_results": test_report.security_scan_results,
        "recommendations": test_report.recommendations
    }
    
    return json.dumps(report_dict, indent=2)


if __name__ == "__main__":
    # For testing the CLI directly
    parser = argparse.ArgumentParser(description="MCP Server Comprehensive Testing")
    create_comprehensive_test_parser(parser.add_subparsers(dest='command'))
    
    args = parser.parse_args()
    if hasattr(args, 'func'):
        sys.exit(args.func(args))
    else:
        parser.print_help()
        sys.exit(1)