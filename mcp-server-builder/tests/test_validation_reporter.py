"""Tests for validation reporting functionality."""

import json
import tempfile
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch

from src.managers.validation_reporter import ValidationReporter
from src.models.base import (
    ValidationReport, ServerStartupResult, ProtocolComplianceResult,
    FunctionalityTestResult
)
from src.models.enums import ValidationLevel


@pytest.fixture
def temp_reports_dir():
    """Create a temporary directory for test reports."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def sample_validation_report():
    """Create a sample validation report for testing."""
    startup_result = ServerStartupResult(
        success=True,
        process_id=12345,
        startup_time=2.5,
        errors=[],
        logs=["Server started successfully"]
    )
    
    protocol_result = ProtocolComplianceResult(
        success=True,
        supported_capabilities=["initialize", "tools/list", "resources/list"],
        missing_capabilities=[],
        protocol_version="2024-11-05",
        errors=[]
    )
    
    functionality_result = FunctionalityTestResult(
        success=True,
        tested_tools={"sample_tool": True},
        tested_resources={"sample_resource": True},
        tested_prompts={},
        errors=[],
        performance_metrics={"tools_response_time": 0.1, "resources_response_time": 0.2}
    )
    
    return ValidationReport(
        project_path="/test/project",
        validation_level=ValidationLevel.STANDARD,
        overall_success=True,
        startup_result=startup_result,
        protocol_result=protocol_result,
        functionality_result=functionality_result,
        performance_metrics={"startup_time": 2.5, "total_capabilities": 3},
        recommendations=[],
        timestamp=datetime.now().isoformat(),
        total_execution_time=5.0
    )


@pytest.fixture
def failed_validation_report():
    """Create a failed validation report for testing."""
    startup_result = ServerStartupResult(
        success=False,
        process_id=None,
        startup_time=0.0,
        errors=["ImportError: No module named 'mcp'"],
        logs=[]
    )
    
    protocol_result = ProtocolComplianceResult(
        success=False,
        supported_capabilities=["initialize"],
        missing_capabilities=["tools/list", "resources/list"],
        protocol_version=None,
        errors=["Protocol initialization failed"]
    )
    
    functionality_result = FunctionalityTestResult(
        success=False,
        tested_tools={},
        tested_resources={},
        tested_prompts={},
        errors=["No capabilities found"],
        performance_metrics={}
    )
    
    return ValidationReport(
        project_path="/test/failed_project",
        validation_level=ValidationLevel.STANDARD,
        overall_success=False,
        startup_result=startup_result,
        protocol_result=protocol_result,
        functionality_result=functionality_result,
        performance_metrics={"startup_time": 0.0},
        recommendations=["Fix server startup issues"],
        timestamp=datetime.now().isoformat(),
        total_execution_time=1.0
    )


class TestValidationReporter:
    """Test cases for ValidationReporter."""
    
    def test_initialization(self, temp_reports_dir):
        """Test reporter initialization."""
        reporter = ValidationReporter(temp_reports_dir)
        
        assert reporter.reports_directory == Path(temp_reports_dir)
        assert (Path(temp_reports_dir) / "detailed").exists()
        assert (Path(temp_reports_dir) / "summaries").exists()
        assert (Path(temp_reports_dir) / "diagnostics").exists()
    
    def test_generate_detailed_report(self, temp_reports_dir, sample_validation_report):
        """Test detailed report generation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        detailed_report = reporter.generate_detailed_report(sample_validation_report)
        
        assert "metadata" in detailed_report
        assert "executive_summary" in detailed_report
        assert "detailed_results" in detailed_report
        assert "performance_analysis" in detailed_report
        assert "actionable_recommendations" in detailed_report
        assert "next_steps" in detailed_report
        
        # Check metadata
        metadata = detailed_report["metadata"]
        assert metadata["project_path"] == "/test/project"
        assert metadata["overall_success"] is True
        assert metadata["validation_level"] == "standard"
        
        # Check executive summary
        summary = detailed_report["executive_summary"]
        assert summary["status"] == "PASS"
        assert "confidence_level" in summary
        assert "readiness_assessment" in summary
    
    def test_generate_detailed_report_with_diagnostics(self, temp_reports_dir, failed_validation_report):
        """Test detailed report generation with diagnostics."""
        reporter = ValidationReporter(temp_reports_dir)
        
        detailed_report = reporter.generate_detailed_report(failed_validation_report, include_diagnostics=True)
        
        assert "diagnostics" in detailed_report
        diagnostics = detailed_report["diagnostics"]
        assert "environment_info" in diagnostics
        assert "project_analysis" in diagnostics
        assert "error_analysis" in diagnostics
        assert "troubleshooting_guide" in diagnostics
    
    def test_generate_summary_report(self, temp_reports_dir, sample_validation_report):
        """Test summary report generation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        summary_report = reporter.generate_summary_report(sample_validation_report)
        
        assert summary_report["project"] == "/test/project"
        assert summary_report["overall_success"] is True
        assert summary_report["validation_level"] == "standard"
        assert "results_summary" in summary_report
        assert "error_count" in summary_report
        assert "performance_score" in summary_report
        
        results_summary = summary_report["results_summary"]
        assert results_summary["startup"] is True
        assert results_summary["protocol"] is True
        assert results_summary["functionality"] is True
    
    def test_save_detailed_report(self, temp_reports_dir, sample_validation_report):
        """Test saving detailed report to disk."""
        reporter = ValidationReporter(temp_reports_dir)
        
        report_path = reporter.save_report(sample_validation_report, "detailed")
        
        assert Path(report_path).exists()
        assert "detailed" in report_path
        
        # Verify report content
        with open(report_path) as f:
            saved_report = json.load(f)
        
        assert saved_report["metadata"]["project_path"] == "/test/project"
        assert saved_report["metadata"]["overall_success"] is True
    
    def test_save_summary_report(self, temp_reports_dir, sample_validation_report):
        """Test saving summary report to disk."""
        reporter = ValidationReporter(temp_reports_dir)
        
        report_path = reporter.save_report(sample_validation_report, "summary")
        
        assert Path(report_path).exists()
        assert "summary" in report_path
        
        # Verify report content
        with open(report_path) as f:
            saved_report = json.load(f)
        
        assert saved_report["project"] == "/test/project"
        assert saved_report["overall_success"] is True
    
    def test_save_diagnostics_report(self, temp_reports_dir, failed_validation_report):
        """Test saving diagnostics report to disk."""
        reporter = ValidationReporter(temp_reports_dir)
        
        report_path = reporter.save_report(failed_validation_report, "diagnostics")
        
        assert Path(report_path).exists()
        assert "diagnostics" in report_path
    
    def test_validation_history_tracking(self, temp_reports_dir, sample_validation_report):
        """Test validation history tracking."""
        reporter = ValidationReporter(temp_reports_dir)
        
        # Save a report to create history entry
        reporter.save_report(sample_validation_report, "detailed")
        
        # Get history
        history = reporter.get_validation_history()
        
        assert len(history) == 1
        assert history[0]["project_path"] == "/test/project"
        assert history[0]["overall_success"] is True
    
    def test_validation_history_filtering(self, temp_reports_dir, sample_validation_report, failed_validation_report):
        """Test validation history filtering by project."""
        reporter = ValidationReporter(temp_reports_dir)
        
        # Save reports for different projects
        reporter.save_report(sample_validation_report, "detailed")
        reporter.save_report(failed_validation_report, "detailed")
        
        # Get history for specific project
        history = reporter.get_validation_history("/test/project")
        
        assert len(history) == 1
        assert history[0]["project_path"] == "/test/project"
        
        # Get all history
        all_history = reporter.get_validation_history()
        assert len(all_history) == 2
    
    def test_validation_history_limit(self, temp_reports_dir, sample_validation_report):
        """Test validation history limit."""
        reporter = ValidationReporter(temp_reports_dir)
        
        # Save multiple reports
        for i in range(5):
            reporter.save_report(sample_validation_report, "detailed")
        
        # Get limited history
        history = reporter.get_validation_history(limit=3)
        
        assert len(history) == 3
    
    def test_trend_analysis_insufficient_data(self, temp_reports_dir):
        """Test trend analysis with insufficient data."""
        reporter = ValidationReporter(temp_reports_dir)
        
        trend_analysis = reporter.generate_trend_analysis("/test/project")
        
        assert "message" in trend_analysis
        assert "Insufficient data" in trend_analysis["message"]
        assert trend_analysis["data_points"] == 0
    
    def test_trend_analysis_with_data(self, temp_reports_dir, sample_validation_report, failed_validation_report):
        """Test trend analysis with sufficient data."""
        reporter = ValidationReporter(temp_reports_dir)
        
        # Save multiple reports to create trend data
        reporter.save_report(sample_validation_report, "detailed")
        reporter.save_report(failed_validation_report, "detailed")
        
        # Modify project path to match for trend analysis
        failed_validation_report.project_path = "/test/project"
        reporter.save_report(failed_validation_report, "detailed")
        
        trend_analysis = reporter.generate_trend_analysis("/test/project")
        
        assert "total_validations" in trend_analysis
        assert "success_rate" in trend_analysis
        assert "trends" in trend_analysis
        assert "latest_vs_previous" in trend_analysis
        assert "recommendations" in trend_analysis
    
    def test_actionable_recommendations_generation(self, temp_reports_dir, failed_validation_report):
        """Test actionable recommendations generation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        detailed_report = reporter.generate_detailed_report(failed_validation_report)
        recommendations = detailed_report["actionable_recommendations"]
        
        assert len(recommendations) > 0
        
        # Check recommendation structure
        for rec in recommendations:
            assert "priority" in rec
            assert "category" in rec
            assert "issue" in rec
            assert "impact" in rec
            assert "action_steps" in rec
            assert "estimated_effort" in rec
            
            assert rec["priority"] in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
            assert isinstance(rec["action_steps"], list)
            assert len(rec["action_steps"]) > 0
    
    def test_next_steps_generation_success(self, temp_reports_dir, sample_validation_report):
        """Test next steps generation for successful validation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        detailed_report = reporter.generate_detailed_report(sample_validation_report)
        next_steps = detailed_report["next_steps"]
        
        assert len(next_steps) > 0
        assert any("ready for deployment" in step.lower() for step in next_steps)
    
    def test_next_steps_generation_failure(self, temp_reports_dir, failed_validation_report):
        """Test next steps generation for failed validation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        detailed_report = reporter.generate_detailed_report(failed_validation_report)
        next_steps = detailed_report["next_steps"]
        
        assert len(next_steps) > 0
        assert any("validation failed" in step.lower() for step in next_steps)
        assert any("fix" in step.lower() for step in next_steps)
    
    def test_performance_analysis(self, temp_reports_dir, sample_validation_report):
        """Test performance analysis generation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        detailed_report = reporter.generate_detailed_report(sample_validation_report)
        performance_analysis = detailed_report["performance_analysis"]
        
        assert "overall_score" in performance_analysis
        assert "metrics" in performance_analysis
        assert "benchmarks" in performance_analysis
        
        assert isinstance(performance_analysis["overall_score"], (int, float))
        assert 0 <= performance_analysis["overall_score"] <= 100
    
    def test_error_handling_invalid_report_type(self, temp_reports_dir, sample_validation_report):
        """Test error handling for invalid report type."""
        reporter = ValidationReporter(temp_reports_dir)
        
        with pytest.raises(ValueError, match="Unknown report type"):
            reporter.save_report(sample_validation_report, "invalid_type")
    
    def test_report_id_generation(self, temp_reports_dir, sample_validation_report):
        """Test report ID generation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        report_id = reporter._generate_report_id(sample_validation_report)
        
        assert isinstance(report_id, str)
        assert len(report_id) > 0
        assert "project" in report_id.lower()  # Should contain project name
    
    def test_confidence_level_calculation(self, temp_reports_dir, sample_validation_report, failed_validation_report):
        """Test confidence level calculation."""
        reporter = ValidationReporter(temp_reports_dir)
        
        # Test high confidence (successful validation)
        confidence_high = reporter._calculate_confidence_level(sample_validation_report)
        assert confidence_high == "HIGH"
        
        # Test low confidence (failed validation)
        confidence_low = reporter._calculate_confidence_level(failed_validation_report)
        assert confidence_low == "LOW"
    
    def test_deployment_readiness_assessment(self, temp_reports_dir, sample_validation_report, failed_validation_report):
        """Test deployment readiness assessment."""
        reporter = ValidationReporter(temp_reports_dir)
        
        # Test ready deployment
        readiness_ready = reporter._assess_deployment_readiness(sample_validation_report)
        assert readiness_ready == "READY"
        
        # Test not ready deployment
        readiness_not_ready = reporter._assess_deployment_readiness(failed_validation_report)
        assert readiness_not_ready == "NOT_READY"


if __name__ == "__main__":
    pytest.main([__file__])