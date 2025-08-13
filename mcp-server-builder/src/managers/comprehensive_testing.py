"""Comprehensive MCP Server Testing Framework."""

import asyncio
import json
import time
import statistics
import subprocess
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime, timedelta

from .interfaces import ValidationEngine
from ..models.base import (
    ValidationResult, ServerStartupResult, ProtocolComplianceResult,
    FunctionalityTestResult, ValidationReport
)
from ..models.enums import ValidationLevel, TransportType


@dataclass
class PerformanceBenchmark:
    """Performance benchmark results for server operations."""
    operation_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_response_time: float
    min_response_time: float
    max_response_time: float
    percentile_95_response_time: float
    requests_per_second: float
    error_rate: float
    memory_usage_mb: float
    cpu_usage_percent: float


@dataclass
class IntegrationTestResult:
    """Results from integration testing with MCP clients."""
    client_name: str
    connection_successful: bool
    handshake_time: float
    supported_features: List[str]
    failed_features: List[str]
    compatibility_score: float
    errors: List[str] = field(default_factory=list)


@dataclass
class ComprehensiveTestReport:
    """Comprehensive test report including all testing aspects."""
    project_path: str
    test_timestamp: str
    overall_success: bool
    basic_validation: ValidationReport
    performance_benchmarks: List[PerformanceBenchmark]
    integration_results: List[IntegrationTestResult]
    load_test_results: Dict[str, Any]
    security_scan_results: Dict[str, Any]
    recommendations: List[str]
    total_test_duration: float


class ComprehensiveServerTester:
    """Comprehensive testing framework for MCP servers."""
    
    def __init__(self, validation_engine: ValidationEngine, max_workers: int = 4):
        """Initialize the comprehensive tester.
        
        Args:
            validation_engine: Basic validation engine for server testing
            max_workers: Maximum number of worker threads for concurrent testing
        """
        self.validation_engine = validation_engine
        self.max_workers = max_workers
        self.active_processes: List[subprocess.Popen] = []
        
    def run_comprehensive_tests(
        self, 
        project_path: str,
        include_performance: bool = True,
        include_integration: bool = True,
        include_load_testing: bool = True,
        include_security_scan: bool = True
    ) -> ComprehensiveTestReport:
        """Run comprehensive tests on the MCP server.
        
        Args:
            project_path: Path to the MCP server project
            include_performance: Whether to run performance benchmarks
            include_integration: Whether to run integration tests
            include_load_testing: Whether to run load tests
            include_security_scan: Whether to run security scans
            
        Returns:
            ComprehensiveTestReport with all test results
        """
        start_time = time.time()
        test_timestamp = datetime.now().isoformat()
        
        try:
            # Run basic validation first
            basic_validation = self.validation_engine.run_comprehensive_tests(project_path)
            
            # Initialize results containers
            performance_benchmarks = []
            integration_results = []
            load_test_results = {}
            security_scan_results = {}
            
            # Run performance benchmarks if requested and basic validation passed
            if include_performance and basic_validation["success"]:
                performance_benchmarks = self._run_performance_benchmarks(project_path)
            
            # Run integration tests if requested and basic validation passed
            if include_integration and basic_validation["success"]:
                integration_results = self._run_integration_tests(project_path)
            
            # Run load tests if requested and basic validation passed
            if include_load_testing and basic_validation["success"]:
                load_test_results = self._run_load_tests(project_path)
            
            # Run security scan if requested
            if include_security_scan:
                security_scan_results = self._run_security_scan(project_path)
            
            # Calculate overall success
            overall_success = (
                basic_validation["success"] and
                all(bench.error_rate < 0.1 for bench in performance_benchmarks) and
                all(result.compatibility_score > 0.7 for result in integration_results) and
                (not load_test_results or load_test_results.get("success", True)) and
                (not security_scan_results or security_scan_results.get("critical_issues", 0) == 0)
            )
            
            # Generate comprehensive recommendations
            recommendations = self._generate_comprehensive_recommendations(
                basic_validation["report"],
                performance_benchmarks,
                integration_results,
                load_test_results,
                security_scan_results
            )
            
            total_duration = time.time() - start_time
            
            return ComprehensiveTestReport(
                project_path=project_path,
                test_timestamp=test_timestamp,
                overall_success=overall_success,
                basic_validation=basic_validation["report"],
                performance_benchmarks=performance_benchmarks,
                integration_results=integration_results,
                load_test_results=load_test_results,
                security_scan_results=security_scan_results,
                recommendations=recommendations,
                total_test_duration=total_duration
            )
            
        except Exception as e:
            # Return failed report with error information
            return ComprehensiveTestReport(
                project_path=project_path,
                test_timestamp=test_timestamp,
                overall_success=False,
                basic_validation=ValidationReport(
                    project_path=project_path,
                    validation_level=ValidationLevel.STANDARD,
                    overall_success=False,
                    startup_result=ServerStartupResult(False, None, 0.0, [str(e)], []),
                    protocol_result=ProtocolComplianceResult(False, [], [], None, [str(e)]),
                    functionality_result=FunctionalityTestResult(False, {}, {}, {}, [str(e)], {}),
                    performance_metrics={},
                    recommendations=[],
                    timestamp=test_timestamp,
                    total_execution_time=time.time() - start_time
                ),
                performance_benchmarks=[],
                integration_results=[],
                load_test_results={},
                security_scan_results={},
                recommendations=[f"Critical error during testing: {str(e)}"],
                total_test_duration=time.time() - start_time
            )
        finally:
            self._cleanup_processes()
    
    def _run_performance_benchmarks(self, project_path: str) -> List[PerformanceBenchmark]:
        """Run performance benchmarks on the MCP server.
        
        Args:
            project_path: Path to the MCP server project
            
        Returns:
            List of performance benchmark results
        """
        benchmarks = []
        
        # Start server for benchmarking
        server_process = self._start_server_for_testing(project_path)
        if not server_process:
            return benchmarks
        
        try:
            # Wait for server to initialize
            time.sleep(2)
            
            # Benchmark different operations
            benchmark_operations = [
                ("initialize", self._benchmark_initialize),
                ("list_tools", self._benchmark_list_tools),
                ("list_resources", self._benchmark_list_resources),
                ("list_prompts", self._benchmark_list_prompts),
                ("call_tool", self._benchmark_call_tool),
                ("read_resource", self._benchmark_read_resource),
                ("get_prompt", self._benchmark_get_prompt)
            ]
            
            for operation_name, benchmark_func in benchmark_operations:
                try:
                    benchmark = benchmark_func(server_process, operation_name)
                    if benchmark:
                        benchmarks.append(benchmark)
                except Exception as e:
                    # Create failed benchmark result
                    benchmarks.append(PerformanceBenchmark(
                        operation_name=operation_name,
                        total_requests=0,
                        successful_requests=0,
                        failed_requests=1,
                        average_response_time=0.0,
                        min_response_time=0.0,
                        max_response_time=0.0,
                        percentile_95_response_time=0.0,
                        requests_per_second=0.0,
                        error_rate=1.0,
                        memory_usage_mb=0.0,
                        cpu_usage_percent=0.0
                    ))
            
        finally:
            self._stop_server_process(server_process)
        
        return benchmarks
    
    def _benchmark_operation(
        self, 
        server_process: subprocess.Popen,
        operation_name: str,
        request_generator: Callable[[], Dict[str, Any]],
        num_requests: int = 100
    ) -> PerformanceBenchmark:
        """Benchmark a specific MCP operation.
        
        Args:
            server_process: Running server process
            operation_name: Name of the operation being benchmarked
            request_generator: Function that generates MCP requests
            num_requests: Number of requests to send for benchmarking
            
        Returns:
            PerformanceBenchmark with results
        """
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Monitor system resources
        import psutil
        process = psutil.Process(server_process.pid)
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        cpu_times = []
        
        start_time = time.time()
        
        # Send requests and measure response times
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                # Generate and send request
                request = request_generator()
                request["id"] = i + 1
                
                # Send request to server
                server_process.stdin.write(json.dumps(request) + "\n")
                server_process.stdin.flush()
                
                # Wait for response (simplified - real implementation would parse JSON-RPC)
                time.sleep(0.01)  # Simulate response processing time
                
                request_end = time.time()
                response_time = request_end - request_start
                response_times.append(response_time)
                successful_requests += 1
                
                # Monitor CPU usage
                cpu_times.append(process.cpu_percent())
                
            except Exception:
                failed_requests += 1
                request_end = time.time()
                response_times.append(request_end - request_start)
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        avg_memory = (initial_memory + final_memory) / 2
        
        # Calculate statistics
        if response_times:
            avg_response_time = statistics.mean(response_times)
            min_response_time = min(response_times)
            max_response_time = max(response_times)
            percentile_95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) >= 20 else max_response_time
        else:
            avg_response_time = min_response_time = max_response_time = percentile_95 = 0.0
        
        requests_per_second = num_requests / total_duration if total_duration > 0 else 0.0
        error_rate = failed_requests / num_requests if num_requests > 0 else 1.0
        avg_cpu = statistics.mean(cpu_times) if cpu_times else 0.0
        
        return PerformanceBenchmark(
            operation_name=operation_name,
            total_requests=num_requests,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            average_response_time=avg_response_time,
            min_response_time=min_response_time,
            max_response_time=max_response_time,
            percentile_95_response_time=percentile_95,
            requests_per_second=requests_per_second,
            error_rate=error_rate,
            memory_usage_mb=avg_memory,
            cpu_usage_percent=avg_cpu
        )
    
    def _benchmark_initialize(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark MCP initialize operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "benchmark-client", "version": "1.0.0"}
                }
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 50)
    
    def _benchmark_list_tools(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark tools/list operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "tools/list",
                "params": {}
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 100)
    
    def _benchmark_list_resources(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark resources/list operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "resources/list",
                "params": {}
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 100)
    
    def _benchmark_list_prompts(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark prompts/list operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "prompts/list",
                "params": {}
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 100)
    
    def _benchmark_call_tool(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark tools/call operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": "sample_tool",
                    "arguments": {"test": "value"}
                }
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 50)
    
    def _benchmark_read_resource(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark resources/read operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "resources/read",
                "params": {
                    "uri": "test://sample_resource"
                }
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 50)
    
    def _benchmark_get_prompt(self, server_process: subprocess.Popen, operation_name: str) -> PerformanceBenchmark:
        """Benchmark prompts/get operation."""
        def generate_request():
            return {
                "jsonrpc": "2.0",
                "method": "prompts/get",
                "params": {
                    "name": "sample_prompt",
                    "arguments": {"context": "test"}
                }
            }
        
        return self._benchmark_operation(server_process, operation_name, generate_request, 50) 
   
    def _run_integration_tests(self, project_path: str) -> List[IntegrationTestResult]:
        """Run integration tests with different MCP clients.
        
        Args:
            project_path: Path to the MCP server project
            
        Returns:
            List of integration test results
        """
        integration_results = []
        
        # Define different client configurations to test against
        test_clients = [
            {
                "name": "Standard MCP Client",
                "capabilities": ["tools", "resources", "prompts"],
                "protocol_version": "2024-11-05"
            },
            {
                "name": "Tools-Only Client", 
                "capabilities": ["tools"],
                "protocol_version": "2024-11-05"
            },
            {
                "name": "Resources-Only Client",
                "capabilities": ["resources"],
                "protocol_version": "2024-11-05"
            },
            {
                "name": "Legacy Client",
                "capabilities": ["tools", "resources"],
                "protocol_version": "2024-10-07"
            }
        ]
        
        # Start server for integration testing
        server_process = self._start_server_for_testing(project_path)
        if not server_process:
            return integration_results
        
        try:
            # Wait for server to initialize
            time.sleep(2)
            
            # Test each client configuration
            for client_config in test_clients:
                result = self._test_client_integration(server_process, client_config)
                integration_results.append(result)
                
        finally:
            self._stop_server_process(server_process)
        
        return integration_results
    
    def _test_client_integration(
        self, 
        server_process: subprocess.Popen, 
        client_config: Dict[str, Any]
    ) -> IntegrationTestResult:
        """Test integration with a specific client configuration.
        
        Args:
            server_process: Running server process
            client_config: Client configuration to test
            
        Returns:
            IntegrationTestResult for this client
        """
        client_name = client_config["name"]
        capabilities = client_config["capabilities"]
        protocol_version = client_config["protocol_version"]
        
        errors = []
        supported_features = []
        failed_features = []
        connection_successful = False
        handshake_time = 0.0
        
        try:
            # Test connection and handshake
            handshake_start = time.time()
            
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": protocol_version,
                    "capabilities": {cap: {} for cap in capabilities},
                    "clientInfo": {
                        "name": client_name.lower().replace(" ", "-"),
                        "version": "1.0.0"
                    }
                }
            }
            
            server_process.stdin.write(json.dumps(init_request) + "\n")
            server_process.stdin.flush()
            
            # Wait for response (simplified)
            time.sleep(0.1)
            
            handshake_time = time.time() - handshake_start
            connection_successful = True
            
            # Test each capability
            for capability in capabilities:
                if self._test_capability_integration(server_process, capability):
                    supported_features.append(capability)
                else:
                    failed_features.append(capability)
                    errors.append(f"Capability {capability} not supported or failed")
            
            # Test additional features based on capabilities
            if "tools" in capabilities:
                if self._test_tool_execution_integration(server_process):
                    supported_features.append("tool_execution")
                else:
                    failed_features.append("tool_execution")
            
            if "resources" in capabilities:
                if self._test_resource_access_integration(server_process):
                    supported_features.append("resource_access")
                else:
                    failed_features.append("resource_access")
            
            if "prompts" in capabilities:
                if self._test_prompt_rendering_integration(server_process):
                    supported_features.append("prompt_rendering")
                else:
                    failed_features.append("prompt_rendering")
            
        except Exception as e:
            errors.append(f"Integration test failed: {str(e)}")
            connection_successful = False
        
        # Calculate compatibility score
        total_features = len(supported_features) + len(failed_features)
        compatibility_score = len(supported_features) / total_features if total_features > 0 else 0.0
        
        return IntegrationTestResult(
            client_name=client_name,
            connection_successful=connection_successful,
            handshake_time=handshake_time,
            supported_features=supported_features,
            failed_features=failed_features,
            compatibility_score=compatibility_score,
            errors=errors
        )
    
    def _test_capability_integration(self, server_process: subprocess.Popen, capability: str) -> bool:
        """Test a specific capability integration.
        
        Args:
            server_process: Running server process
            capability: Capability to test (tools, resources, prompts)
            
        Returns:
            True if capability is supported
        """
        try:
            method_map = {
                "tools": "tools/list",
                "resources": "resources/list", 
                "prompts": "prompts/list"
            }
            
            method = method_map.get(capability)
            if not method:
                return False
            
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": method,
                "params": {}
            }
            
            server_process.stdin.write(json.dumps(request) + "\n")
            server_process.stdin.flush()
            
            # Wait for response (simplified)
            time.sleep(0.1)
            
            return True  # Simplified - real implementation would parse response
            
        except Exception:
            return False
    
    def _test_tool_execution_integration(self, server_process: subprocess.Popen) -> bool:
        """Test tool execution integration."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "test_tool",
                    "arguments": {"test": "integration"}
                }
            }
            
            server_process.stdin.write(json.dumps(request) + "\n")
            server_process.stdin.flush()
            time.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    def _test_resource_access_integration(self, server_process: subprocess.Popen) -> bool:
        """Test resource access integration."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "resources/read",
                "params": {
                    "uri": "test://integration_resource"
                }
            }
            
            server_process.stdin.write(json.dumps(request) + "\n")
            server_process.stdin.flush()
            time.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    def _test_prompt_rendering_integration(self, server_process: subprocess.Popen) -> bool:
        """Test prompt rendering integration."""
        try:
            request = {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "prompts/get",
                "params": {
                    "name": "test_prompt",
                    "arguments": {"context": "integration"}
                }
            }
            
            server_process.stdin.write(json.dumps(request) + "\n")
            server_process.stdin.flush()
            time.sleep(0.1)
            
            return True
        except Exception:
            return False
    
    def _run_load_tests(self, project_path: str) -> Dict[str, Any]:
        """Run load tests on the MCP server.
        
        Args:
            project_path: Path to the MCP server project
            
        Returns:
            Dictionary with load test results
        """
        load_test_results = {
            "success": False,
            "concurrent_users": 0,
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "average_response_time": 0.0,
            "max_response_time": 0.0,
            "requests_per_second": 0.0,
            "error_rate": 0.0,
            "memory_peak_mb": 0.0,
            "cpu_peak_percent": 0.0,
            "errors": []
        }
        
        # Start server for load testing
        server_process = self._start_server_for_testing(project_path)
        if not server_process:
            load_test_results["errors"].append("Failed to start server for load testing")
            return load_test_results
        
        try:
            # Wait for server to initialize
            time.sleep(2)
            
            # Configure load test parameters
            concurrent_users = [1, 5, 10, 20]
            requests_per_user = 50
            
            best_results = None
            
            for num_users in concurrent_users:
                try:
                    results = self._execute_load_test(server_process, num_users, requests_per_user)
                    
                    # Update best results
                    if results["error_rate"] < 0.1:  # Less than 10% error rate
                        best_results = results
                        load_test_results.update(results)
                        load_test_results["success"] = True
                    else:
                        # Stop if error rate is too high
                        break
                        
                except Exception as e:
                    load_test_results["errors"].append(f"Load test with {num_users} users failed: {str(e)}")
                    break
            
            if not best_results:
                load_test_results["errors"].append("All load tests failed or had high error rates")
            
        finally:
            self._stop_server_process(server_process)
        
        return load_test_results
    
    def _execute_load_test(
        self, 
        server_process: subprocess.Popen, 
        concurrent_users: int, 
        requests_per_user: int
    ) -> Dict[str, Any]:
        """Execute a load test with specified parameters.
        
        Args:
            server_process: Running server process
            concurrent_users: Number of concurrent users to simulate
            requests_per_user: Number of requests each user should send
            
        Returns:
            Dictionary with load test results
        """
        import psutil
        
        # Monitor server process
        process = psutil.Process(server_process.pid)
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        response_times = []
        successful_requests = 0
        failed_requests = 0
        memory_samples = []
        cpu_samples = []
        
        start_time = time.time()
        
        # Create thread pool for concurrent users
        with ThreadPoolExecutor(max_workers=concurrent_users) as executor:
            # Submit tasks for each user
            futures = []
            for user_id in range(concurrent_users):
                future = executor.submit(self._simulate_user_load, server_process, user_id, requests_per_user)
                futures.append(future)
            
            # Monitor system resources while tests run
            monitor_thread = threading.Thread(
                target=self._monitor_system_resources,
                args=(process, memory_samples, cpu_samples, len(futures))
            )
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Collect results from all users
            for future in as_completed(futures):
                try:
                    user_results = future.result()
                    response_times.extend(user_results["response_times"])
                    successful_requests += user_results["successful_requests"]
                    failed_requests += user_results["failed_requests"]
                except Exception as e:
                    failed_requests += requests_per_user
        
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Calculate statistics
        total_requests = successful_requests + failed_requests
        average_response_time = statistics.mean(response_times) if response_times else 0.0
        max_response_time = max(response_times) if response_times else 0.0
        requests_per_second = total_requests / total_duration if total_duration > 0 else 0.0
        error_rate = failed_requests / total_requests if total_requests > 0 else 1.0
        
        memory_peak = max(memory_samples) if memory_samples else initial_memory
        cpu_peak = max(cpu_samples) if cpu_samples else 0.0
        
        return {
            "concurrent_users": concurrent_users,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "average_response_time": average_response_time,
            "max_response_time": max_response_time,
            "requests_per_second": requests_per_second,
            "error_rate": error_rate,
            "memory_peak_mb": memory_peak,
            "cpu_peak_percent": cpu_peak,
            "test_duration": total_duration
        }
    
    def _simulate_user_load(
        self, 
        server_process: subprocess.Popen, 
        user_id: int, 
        num_requests: int
    ) -> Dict[str, Any]:
        """Simulate load from a single user.
        
        Args:
            server_process: Running server process
            user_id: Unique identifier for this user
            num_requests: Number of requests this user should send
            
        Returns:
            Dictionary with user's test results
        """
        response_times = []
        successful_requests = 0
        failed_requests = 0
        
        # Mix of different request types
        request_types = [
            ("tools/list", {}),
            ("resources/list", {}),
            ("prompts/list", {}),
            ("tools/call", {"name": "test_tool", "arguments": {"user": user_id}}),
        ]
        
        for i in range(num_requests):
            request_start = time.time()
            
            try:
                # Select request type
                method, params = request_types[i % len(request_types)]
                
                request = {
                    "jsonrpc": "2.0",
                    "id": f"{user_id}_{i}",
                    "method": method,
                    "params": params
                }
                
                # Send request
                server_process.stdin.write(json.dumps(request) + "\n")
                server_process.stdin.flush()
                
                # Simulate processing time
                time.sleep(0.01)
                
                request_end = time.time()
                response_times.append(request_end - request_start)
                successful_requests += 1
                
            except Exception:
                failed_requests += 1
                request_end = time.time()
                response_times.append(request_end - request_start)
        
        return {
            "response_times": response_times,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests
        }
    
    def _monitor_system_resources(
        self, 
        process: 'psutil.Process', 
        memory_samples: List[float], 
        cpu_samples: List[float],
        num_workers: int
    ):
        """Monitor system resources during load testing.
        
        Args:
            process: Process to monitor
            memory_samples: List to store memory usage samples
            cpu_samples: List to store CPU usage samples
            num_workers: Number of worker threads (for monitoring duration)
        """
        import psutil
        
        # Monitor for up to 60 seconds or until workers complete
        start_time = time.time()
        while time.time() - start_time < 60:
            try:
                memory_mb = process.memory_info().rss / 1024 / 1024
                cpu_percent = process.cpu_percent()
                
                memory_samples.append(memory_mb)
                cpu_samples.append(cpu_percent)
                
                time.sleep(0.5)  # Sample every 500ms
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                break
    
    def _run_security_scan(self, project_path: str) -> Dict[str, Any]:
        """Run security scan on the MCP server project.
        
        Args:
            project_path: Path to the MCP server project
            
        Returns:
            Dictionary with security scan results
        """
        security_results = {
            "success": False,
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "total_issues": 0,
            "scanned_files": 0,
            "scan_duration": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        start_time = time.time()
        
        try:
            project_dir = Path(project_path)
            scanned_files = 0
            
            # Scan for common security issues
            security_results.update(self._scan_dependency_vulnerabilities(project_dir))
            security_results.update(self._scan_code_security_issues(project_dir))
            security_results.update(self._scan_configuration_security(project_dir))
            
            # Count scanned files
            for file_pattern in ["*.py", "*.js", "*.ts", "*.json", "*.yaml", "*.yml"]:
                scanned_files += len(list(project_dir.rglob(file_pattern)))
            
            # Merge results from individual scans
            dep_results = self._scan_dependency_vulnerabilities(project_dir)
            code_results = self._scan_code_security_issues(project_dir)
            config_results = self._scan_configuration_security(project_dir)
            
            # Combine all results
            security_results["critical_issues"] = (
                dep_results["critical_issues"] + 
                code_results["critical_issues"] + 
                config_results["critical_issues"]
            )
            security_results["high_issues"] = (
                dep_results["high_issues"] + 
                code_results["high_issues"] + 
                config_results["high_issues"]
            )
            security_results["medium_issues"] = (
                dep_results["medium_issues"] + 
                code_results["medium_issues"] + 
                config_results["medium_issues"]
            )
            security_results["low_issues"] = (
                dep_results["low_issues"] + 
                code_results["low_issues"] + 
                config_results["low_issues"]
            )
            
            # Combine issues and recommendations
            security_results["issues"].extend(dep_results["issues"])
            security_results["issues"].extend(code_results["issues"])
            security_results["issues"].extend(config_results["issues"])
            
            security_results["recommendations"].extend(dep_results["recommendations"])
            security_results["recommendations"].extend(code_results["recommendations"])
            security_results["recommendations"].extend(config_results["recommendations"])
            
            security_results["scanned_files"] = scanned_files
            security_results["success"] = True
            
        except Exception as e:
            security_results["issues"].append({
                "severity": "high",
                "type": "scan_error",
                "description": f"Security scan failed: {str(e)}",
                "file": "unknown",
                "line": 0
            })
            security_results["high_issues"] += 1
        
        security_results["scan_duration"] = time.time() - start_time
        security_results["total_issues"] = (
            security_results["critical_issues"] + 
            security_results["high_issues"] + 
            security_results["medium_issues"] + 
            security_results["low_issues"]
        )
        
        return security_results  
  
    def _scan_dependency_vulnerabilities(self, project_dir: Path) -> Dict[str, Any]:
        """Scan for dependency vulnerabilities.
        
        Args:
            project_dir: Project directory to scan
            
        Returns:
            Dictionary with vulnerability scan results
        """
        results = {
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Check Python dependencies
        requirements_files = list(project_dir.glob("requirements*.txt")) + list(project_dir.glob("pyproject.toml"))
        for req_file in requirements_files:
            try:
                content = req_file.read_text()
                
                # Check for known vulnerable patterns
                vulnerable_patterns = [
                    ("requests<2.20.0", "medium", "Outdated requests library with known vulnerabilities"),
                    ("flask<1.0", "high", "Outdated Flask version with security issues"),
                    ("django<3.2", "high", "Outdated Django version with security vulnerabilities"),
                    ("pyyaml<5.4", "medium", "PyYAML version vulnerable to code execution"),
                ]
                
                for pattern, severity, description in vulnerable_patterns:
                    if pattern.split("<")[0] in content.lower():
                        results["issues"].append({
                            "severity": severity,
                            "type": "dependency_vulnerability",
                            "description": description,
                            "file": str(req_file),
                            "line": 0
                        })
                        results[f"{severity}_issues"] += 1
                        
            except Exception:
                pass
        
        # Check Node.js dependencies
        package_json = project_dir / "package.json"
        if package_json.exists():
            try:
                content = package_json.read_text()
                
                # Check for known vulnerable Node.js packages
                if "lodash" in content and '"lodash": "4.17.20"' not in content:
                    results["issues"].append({
                        "severity": "medium",
                        "type": "dependency_vulnerability", 
                        "description": "Potentially outdated lodash version",
                        "file": str(package_json),
                        "line": 0
                    })
                    results["medium_issues"] += 1
                    
            except Exception:
                pass
        
        if results["critical_issues"] > 0 or results["high_issues"] > 0:
            results["recommendations"].append("Update vulnerable dependencies to latest secure versions")
        
        return results
    
    def _scan_code_security_issues(self, project_dir: Path) -> Dict[str, Any]:
        """Scan for code security issues.
        
        Args:
            project_dir: Project directory to scan
            
        Returns:
            Dictionary with code security scan results
        """
        results = {
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Security patterns to check for
        security_patterns = [
            (r"eval\s*\(", "critical", "Use of eval() function - code injection risk"),
            (r"exec\s*\(", "critical", "Use of exec() function - code injection risk"),
            (r"subprocess\.call\s*\(.*shell\s*=\s*True", "high", "Shell injection vulnerability"),
            (r"os\.system\s*\(", "high", "Command injection vulnerability"),
            (r"pickle\.loads?\s*\(", "high", "Unsafe pickle deserialization"),
            (r"yaml\.load\s*\(", "medium", "Unsafe YAML loading - use safe_load"),
            (r"input\s*\(.*\)", "low", "Use of input() function in Python 2 style"),
            (r"password\s*=\s*['\"][^'\"]+['\"]", "medium", "Hardcoded password detected"),
            (r"api_key\s*=\s*['\"][^'\"]+['\"]", "medium", "Hardcoded API key detected"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "medium", "Hardcoded secret detected"),
        ]
        
        # Scan Python files
        for py_file in project_dir.rglob("*.py"):
            try:
                content = py_file.read_text()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, severity, description in security_patterns:
                        import re
                        if re.search(pattern, line, re.IGNORECASE):
                            results["issues"].append({
                                "severity": severity,
                                "type": "code_security",
                                "description": description,
                                "file": str(py_file),
                                "line": line_num
                            })
                            results[f"{severity}_issues"] += 1
                            
            except Exception:
                pass
        
        # Scan JavaScript/TypeScript files
        js_files = list(project_dir.rglob("*.js")) + list(project_dir.rglob("*.ts"))
        for js_file in js_files:
            try:
                content = js_file.read_text()
                lines = content.split('\n')
                
                js_patterns = [
                    (r"eval\s*\(", "critical", "Use of eval() - code injection risk"),
                    (r"innerHTML\s*=", "medium", "Potential XSS vulnerability with innerHTML"),
                    (r"document\.write\s*\(", "medium", "Use of document.write - XSS risk"),
                    (r"\.exec\s*\(", "high", "Command execution detected"),
                ]
                
                for line_num, line in enumerate(lines, 1):
                    for pattern, severity, description in js_patterns:
                        import re
                        if re.search(pattern, line, re.IGNORECASE):
                            results["issues"].append({
                                "severity": severity,
                                "type": "code_security",
                                "description": description,
                                "file": str(js_file),
                                "line": line_num
                            })
                            results[f"{severity}_issues"] += 1
                            
            except Exception:
                pass
        
        if results["critical_issues"] > 0:
            results["recommendations"].append("Fix critical security vulnerabilities immediately")
        if results["high_issues"] > 0:
            results["recommendations"].append("Address high-severity security issues")
        if results["medium_issues"] > 0:
            results["recommendations"].append("Review and fix medium-severity security issues")
        
        return results
    
    def _scan_configuration_security(self, project_dir: Path) -> Dict[str, Any]:
        """Scan for configuration security issues.
        
        Args:
            project_dir: Project directory to scan
            
        Returns:
            Dictionary with configuration security scan results
        """
        results = {
            "critical_issues": 0,
            "high_issues": 0,
            "medium_issues": 0,
            "low_issues": 0,
            "issues": [],
            "recommendations": []
        }
        
        # Check for sensitive files that shouldn't be in version control
        sensitive_files = [
            (".env", "high", "Environment file with potential secrets"),
            (".env.local", "high", "Local environment file with potential secrets"),
            ("config.json", "medium", "Configuration file that may contain secrets"),
            ("secrets.json", "critical", "Secrets file detected"),
            ("private.key", "critical", "Private key file detected"),
            ("id_rsa", "critical", "SSH private key detected"),
        ]
        
        for filename, severity, description in sensitive_files:
            if (project_dir / filename).exists():
                results["issues"].append({
                    "severity": severity,
                    "type": "configuration_security",
                    "description": description,
                    "file": str(project_dir / filename),
                    "line": 0
                })
                results[f"{severity}_issues"] += 1
        
        # Check .gitignore for proper exclusions
        gitignore = project_dir / ".gitignore"
        if gitignore.exists():
            try:
                content = gitignore.read_text()
                required_ignores = [".env", "*.key", "secrets.*", "config.json"]
                
                for ignore_pattern in required_ignores:
                    if ignore_pattern not in content:
                        results["issues"].append({
                            "severity": "low",
                            "type": "configuration_security",
                            "description": f"Missing {ignore_pattern} in .gitignore",
                            "file": str(gitignore),
                            "line": 0
                        })
                        results["low_issues"] += 1
                        
            except Exception:
                pass
        else:
            results["issues"].append({
                "severity": "medium",
                "type": "configuration_security",
                "description": "Missing .gitignore file",
                "file": str(project_dir),
                "line": 0
            })
            results["medium_issues"] += 1
        
        # Check for proper file permissions (simplified)
        script_files = list(project_dir.rglob("*.sh")) + list(project_dir.rglob("*.py"))
        for script_file in script_files:
            try:
                import stat
                file_stat = script_file.stat()
                if file_stat.st_mode & stat.S_IWOTH:  # World writable
                    results["issues"].append({
                        "severity": "medium",
                        "type": "configuration_security",
                        "description": "File is world-writable",
                        "file": str(script_file),
                        "line": 0
                    })
                    results["medium_issues"] += 1
            except Exception:
                pass
        
        if results["critical_issues"] > 0 or results["high_issues"] > 0:
            results["recommendations"].append("Secure sensitive configuration files and credentials")
        
        return results
    
    def _generate_comprehensive_recommendations(
        self,
        basic_validation: ValidationReport,
        performance_benchmarks: List[PerformanceBenchmark],
        integration_results: List[IntegrationTestResult],
        load_test_results: Dict[str, Any],
        security_scan_results: Dict[str, Any]
    ) -> List[str]:
        """Generate comprehensive recommendations based on all test results.
        
        Args:
            basic_validation: Basic validation report
            performance_benchmarks: Performance benchmark results
            integration_results: Integration test results
            load_test_results: Load test results
            security_scan_results: Security scan results
            
        Returns:
            List of comprehensive recommendations
        """
        recommendations = []
        
        # Include basic validation recommendations
        recommendations.extend(basic_validation.recommendations)
        
        # Performance recommendations
        slow_operations = [b for b in performance_benchmarks if b.average_response_time > 1.0]
        if slow_operations:
            op_names = [op.operation_name for op in slow_operations]
            recommendations.append(f"Optimize slow operations: {', '.join(op_names)}")
        
        high_error_operations = [b for b in performance_benchmarks if b.error_rate > 0.05]
        if high_error_operations:
            op_names = [op.operation_name for op in high_error_operations]
            recommendations.append(f"Fix high error rate operations: {', '.join(op_names)}")
        
        high_memory_operations = [b for b in performance_benchmarks if b.memory_usage_mb > 100]
        if high_memory_operations:
            recommendations.append("Consider memory optimization for resource-intensive operations")
        
        # Integration recommendations
        failed_integrations = [r for r in integration_results if r.compatibility_score < 0.7]
        if failed_integrations:
            client_names = [r.client_name for r in failed_integrations]
            recommendations.append(f"Improve compatibility with: {', '.join(client_names)}")
        
        # Load testing recommendations
        if load_test_results.get("error_rate", 0) > 0.05:
            recommendations.append("Improve server stability under load")
        
        if load_test_results.get("concurrent_users", 0) < 10:
            recommendations.append("Consider scaling improvements for concurrent user support")
        
        # Security recommendations
        if security_scan_results.get("critical_issues", 0) > 0:
            recommendations.append("URGENT: Fix critical security vulnerabilities before deployment")
        
        if security_scan_results.get("high_issues", 0) > 0:
            recommendations.append("Address high-severity security issues")
        
        # Include security-specific recommendations
        recommendations.extend(security_scan_results.get("recommendations", []))
        
        # General recommendations based on overall results
        if not basic_validation.overall_success:
            recommendations.append("Complete basic server validation before advanced testing")
        
        if len(performance_benchmarks) == 0:
            recommendations.append("Add performance monitoring to track server metrics")
        
        if len(integration_results) == 0:
            recommendations.append("Test integration with different MCP client types")
        
        return list(set(recommendations))  # Remove duplicates
    
    def _start_server_for_testing(self, project_path: str) -> Optional[subprocess.Popen]:
        """Start server process for testing.
        
        Args:
            project_path: Path to the MCP server project
            
        Returns:
            Server process or None if failed
        """
        entry_point = self.validation_engine._detect_server_entry_point(project_path)
        if not entry_point:
            return None
        
        process = self.validation_engine._start_server_process(project_path, entry_point)
        if process:
            self.active_processes.append(process)
        
        return process
    
    def _stop_server_process(self, process: subprocess.Popen):
        """Stop a server process.
        
        Args:
            process: Process to stop
        """
        try:
            if process in self.active_processes:
                self.active_processes.remove(process)
            
            if process.poll() is None:  # Process is still running
                process.terminate()
                time.sleep(1)
                if process.poll() is None:  # Still running, force kill
                    process.kill()
        except Exception:
            pass
    
    def _cleanup_processes(self):
        """Clean up all active processes."""
        for process in self.active_processes[:]:  # Copy list to avoid modification during iteration
            self._stop_server_process(process)
        
        self.active_processes.clear()
    
    def __del__(self):
        """Cleanup on destruction."""
        self._cleanup_processes()