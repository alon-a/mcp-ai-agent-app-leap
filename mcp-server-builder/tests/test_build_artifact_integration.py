"""Integration tests for complete build artifact management workflow."""

import os
import tempfile
import shutil
import json
from unittest.mock import patch

import pytest

from src.managers.build_system import BuildSystemManager


class TestBuildArtifactIntegration:
    """Test complete build artifact management integration."""
    
    @pytest.fixture
    def temp_project(self):
        """Create a temporary project with build artifacts."""
        temp_dir = tempfile.mkdtemp()
        
        # Create npm project structure
        project_files = {
            "package.json": json.dumps({
                "name": "test-mcp-server",
                "version": "1.0.0",
                "scripts": {"build": "echo 'Building...'"},
                "main": "dist/index.js"
            }),
            "package-lock.json": json.dumps({"lockfileVersion": 2}),
            "src/index.ts": "export default function mcpServer() { console.log('MCP Server'); }",
            "dist/index.js": "function mcpServer() { console.log('MCP Server'); } module.exports = mcpServer;",
            "dist/index.d.ts": "export default function mcpServer(): void;",
            "dist/index.js.map": '{"version":3,"sources":["../src/index.ts"]}',
            "dist/package.json": json.dumps({"name": "test-mcp-server", "main": "index.js"}),
        }
        
        for file_path, content in project_files.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
        
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def build_manager(self):
        """Create a build system manager."""
        return BuildSystemManager()
    
    def test_complete_build_artifact_workflow(self, build_manager, temp_project):
        """Test the complete build artifact management workflow."""
        # Mock successful command execution
        with patch.object(build_manager, '_execute_single_command') as mock_exec:
            mock_exec.return_value = {
                "success": True,
                "logs": ["Build completed successfully", "Generated 4 artifacts"],
                "errors": []
            }
            
            # Step 1: Execute build with artifact collection
            print(f"\n=== Step 1: Execute Build ===")
            build_result = build_manager.execute_build(temp_project, ["npm run build"])
            
            # Verify build result
            assert build_result.success
            assert build_result.build_tool == "npm scripts"
            assert len(build_result.artifacts) > 0
            assert build_result.artifact_report is not None
            
            print(f"Build successful: {build_result.success}")
            print(f"Build tool: {build_result.build_tool}")
            print(f"Artifacts found: {len(build_result.artifacts)}")
            print(f"Execution time: {build_result.execution_time:.2f}s")
            
            # Step 2: Verify artifact detection and validation
            print(f"\n=== Step 2: Artifact Validation ===")
            artifact_report = build_manager.validate_build_artifacts(temp_project)
            
            assert artifact_report.total_artifacts > 0
            assert artifact_report.valid_artifacts > 0
            assert artifact_report.build_tool == "npm scripts"
            
            print(f"Total artifacts: {artifact_report.total_artifacts}")
            print(f"Valid artifacts: {artifact_report.valid_artifacts}")
            print(f"Invalid artifacts: {artifact_report.invalid_artifacts}")
            print(f"Total size: {artifact_report.total_size} bytes")
            
            # Step 3: Package artifacts
            print(f"\n=== Step 3: Package Artifacts ===")
            package_path = os.path.join(temp_project, "build-artifacts.zip")
            packaging_success = build_manager.package_build_artifacts(
                temp_project, package_path, "zip"
            )
            
            assert packaging_success
            assert os.path.exists(package_path)
            package_size = os.path.getsize(package_path)
            
            print(f"Packaging successful: {packaging_success}")
            print(f"Package path: {package_path}")
            print(f"Package size: {package_size} bytes")
            
            # Step 4: Generate build summary
            print(f"\n=== Step 4: Build Summary ===")
            build_summary = build_manager.generate_build_summary(temp_project)
            
            assert build_summary["build_system"] == "npm scripts"
            assert build_summary["artifacts"]["total"] > 0
            assert len(build_summary["build_history"]) > 0
            
            print(f"Build system: {build_summary['build_system']}")
            print(f"Total artifacts: {build_summary['artifacts']['total']}")
            print(f"Valid artifacts: {build_summary['artifacts']['valid']}")
            print(f"Build history entries: {len(build_summary['build_history'])}")
            print(f"Recommendations: {len(build_summary['recommendations'])}")
            
            # Step 5: Export comprehensive report
            print(f"\n=== Step 5: Export Report ===")
            report_path = os.path.join(temp_project, "comprehensive-build-report.json")
            export_success = build_manager.export_build_report(
                temp_project, report_path, include_artifacts=True
            )
            
            assert export_success
            assert os.path.exists(report_path)
            
            # Verify report content
            with open(report_path, 'r') as f:
                report_data = json.load(f)
            
            assert "project_path" in report_data
            assert "build_system" in report_data
            assert "artifacts" in report_data
            assert "detailed_artifacts" in report_data
            assert "recommendations" in report_data
            
            print(f"Report export successful: {export_success}")
            print(f"Report path: {report_path}")
            print(f"Report contains {len(report_data.get('detailed_artifacts', []))} detailed artifacts")
            
            # Step 6: Verify persistent storage
            print(f"\n=== Step 6: Verify Storage ===")
            
            # Check build result storage
            build_result_path = os.path.join(temp_project, "build-result.json")
            assert os.path.exists(build_result_path)
            
            # Check artifact report storage
            artifact_report_path = os.path.join(temp_project, "build-artifacts-report.json")
            assert os.path.exists(artifact_report_path)
            
            # Load and verify stored build result
            loaded_result = build_manager.load_build_result(build_result_path)
            assert loaded_result is not None
            assert loaded_result.success == build_result.success
            assert loaded_result.build_tool == build_result.build_tool
            
            print(f"Build result stored: {os.path.exists(build_result_path)}")
            print(f"Artifact report stored: {os.path.exists(artifact_report_path)}")
            print(f"Build result loaded successfully: {loaded_result is not None}")
            
            # Step 7: Verify build history
            print(f"\n=== Step 7: Build History ===")
            build_history = build_manager.get_build_history(temp_project)
            
            assert len(build_history) > 0
            assert build_history[0]["success"] is True
            assert "build_tool" in build_history[0]
            assert "artifacts_count" in build_history[0]
            
            print(f"Build history entries: {len(build_history)}")
            print(f"Last build successful: {build_history[0]['success']}")
            print(f"Last build tool: {build_history[0].get('build_tool', 'unknown')}")
            print(f"Last build artifacts: {build_history[0].get('artifacts_count', 0)}")
            
            print(f"\n=== Workflow Complete ===")
            print("✅ Build execution with artifact collection")
            print("✅ Artifact detection and validation")
            print("✅ Artifact packaging")
            print("✅ Build summary generation")
            print("✅ Comprehensive report export")
            print("✅ Persistent storage")
            print("✅ Build history tracking")
    
    def test_build_artifact_error_handling(self, build_manager, temp_project):
        """Test error handling in build artifact management."""
        # Mock failed command execution
        with patch.object(build_manager, '_execute_single_command') as mock_exec:
            mock_exec.return_value = {
                "success": False,
                "logs": ["Build started"],
                "errors": ["Build failed: compilation error"]
            }
            
            # Execute build
            build_result = build_manager.execute_build(temp_project, ["npm run build"])
            
            # Verify error handling
            assert not build_result.success
            assert len(build_result.errors) > 0
            assert "Build failed" in build_result.errors[0]
            
            # Build summary should still work
            build_summary = build_manager.generate_build_summary(temp_project)
            assert build_summary["build_system"] == "npm scripts"
            
            # Should have recommendations for failed build
            assert len(build_summary["recommendations"]) > 0
    
    def test_artifact_management_without_build_system(self, build_manager):
        """Test artifact management when no build system is detected."""
        temp_dir = tempfile.mkdtemp()
        try:
            # Empty directory with no build system indicators
            
            # Generate build summary
            build_summary = build_manager.generate_build_summary(temp_dir)
            
            assert build_summary["build_system"] is None
            assert build_summary["artifacts"]["total"] == 0
            assert "No build system detected" in build_summary["recommendations"][0]
            
            # Export report should still work
            report_path = os.path.join(temp_dir, "report.json")
            export_success = build_manager.export_build_report(temp_dir, report_path)
            
            assert export_success
            assert os.path.exists(report_path)
            
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])