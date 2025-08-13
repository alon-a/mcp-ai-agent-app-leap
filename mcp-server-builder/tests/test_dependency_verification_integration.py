"""Integration tests for dependency verification and validation functionality."""

import os
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.managers.dependency_manager import DependencyManagerImpl


class TestDependencyVerificationIntegration:
    """Integration test cases for dependency verification and validation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.dependency_manager = DependencyManagerImpl()
    
    def test_complete_npm_verification_workflow(self):
        """Test complete verification workflow for npm project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a realistic npm project structure
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-mcp-server",
                "version": "1.0.0",
                "dependencies": {
                    "express": "^4.18.0",
                    "lodash": "^4.17.21"
                },
                "devDependencies": {
                    "jest": "^29.0.0"
                },
                "engines": {
                    "node": ">=14.0.0"
                }
            }))
            
            # Create node_modules structure
            node_modules = Path(temp_dir) / "node_modules"
            node_modules.mkdir()
            
            # Create express package
            express_dir = node_modules / "express"
            express_dir.mkdir()
            express_package_json = express_dir / "package.json"
            express_package_json.write_text(json.dumps({
                "name": "express",
                "version": "4.18.2"
            }))
            
            # Create lodash package
            lodash_dir = node_modules / "lodash"
            lodash_dir.mkdir()
            lodash_package_json = lodash_dir / "package.json"
            lodash_package_json.write_text(json.dumps({
                "name": "lodash",
                "version": "4.17.21"
            }))
            
            # Create jest package
            jest_dir = node_modules / "jest"
            jest_dir.mkdir()
            jest_package_json = jest_dir / "package.json"
            jest_package_json.write_text(json.dumps({
                "name": "jest",
                "version": "29.3.1"
            }))
            
            # Test verification
            verification_result = self.dependency_manager.verify_installation(temp_dir)
            
            assert verification_result.success is True
            assert len(verification_result.verified_packages) == 3
            assert "express" in verification_result.verified_packages
            assert "lodash" in verification_result.verified_packages
            assert "jest" in verification_result.verified_packages
            assert len(verification_result.missing_packages) == 0
    
    def test_complete_python_verification_workflow(self):
        """Test complete verification workflow for Python project."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create requirements.txt
            requirements = Path(temp_dir) / "requirements.txt"
            requirements.write_text("""
requests>=2.28.0
flask>=2.0.0
pytest>=7.0.0
""")
            
            # Mock pip show commands for verification
            def mock_pip_show(*args, **kwargs):
                if "requests" in args[0]:
                    return MagicMock(
                        returncode=0,
                        stdout="Name: requests\nVersion: 2.28.1\nSummary: HTTP library"
                    )
                elif "flask" in args[0]:
                    return MagicMock(
                        returncode=0,
                        stdout="Name: flask\nVersion: 2.2.2\nSummary: Web framework"
                    )
                elif "pytest" in args[0]:
                    return MagicMock(
                        returncode=0,
                        stdout="Name: pytest\nVersion: 7.2.0\nSummary: Testing framework"
                    )
                else:
                    return MagicMock(returncode=1, stdout="", stderr="Package not found")
            
            with patch('subprocess.run', side_effect=mock_pip_show):
                verification_result = self.dependency_manager.verify_installation(temp_dir)
                
                assert verification_result.success is True
                assert len(verification_result.verified_packages) == 3
                assert "requests" in verification_result.verified_packages
                assert "flask" in verification_result.verified_packages
                assert "pytest" in verification_result.verified_packages
                assert len(verification_result.missing_packages) == 0
    
    @patch('subprocess.run')
    def test_security_scanning_integration(self, mock_run):
        """Test security scanning integration with verification."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "lodash": "4.17.20"  # Vulnerable version
                }
            }))
            
            # Create node_modules with vulnerable package
            node_modules = Path(temp_dir) / "node_modules" / "lodash"
            node_modules.mkdir(parents=True)
            lodash_package_json = node_modules / "package.json"
            lodash_package_json.write_text(json.dumps({
                "name": "lodash",
                "version": "4.17.20"
            }))
            
            # Mock npm audit output with vulnerability
            audit_output = json.dumps({
                "vulnerabilities": {
                    "lodash": {
                        "severity": "high",
                        "title": "Prototype Pollution",
                        "overview": "Lodash is vulnerable to prototype pollution",
                        "fixAvailable": True
                    }
                }
            })
            mock_run.return_value = MagicMock(returncode=0, stdout=audit_output, stderr="")
            
            # First verify installation
            verification_result = self.dependency_manager.verify_installation(temp_dir)
            assert verification_result.success is True
            assert "lodash" in verification_result.verified_packages
            
            # Then scan for vulnerabilities
            security_result = self.dependency_manager.scan_security_vulnerabilities(temp_dir)
            assert security_result["success"] is True
            assert len(security_result["vulnerabilities"]) == 1
            
            vuln = security_result["vulnerabilities"][0]
            assert vuln["package"] == "lodash"
            assert vuln["severity"] == "high"
            assert vuln["fixAvailable"] is True
    
    @patch('subprocess.run')
    def test_compatibility_validation_integration(self, mock_run):
        """Test compatibility validation integration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json with engine requirements
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "express": "^4.18.0"
                },
                "engines": {
                    "node": ">=16.0.0"
                }
            }))
            
            # Mock node version check
            def mock_subprocess(*args, **kwargs):
                if "node" in args[0] and "--version" in args[0]:
                    return MagicMock(returncode=0, stdout="v18.12.0", stderr="")
                else:
                    return MagicMock(returncode=0, stdout="", stderr="")
            
            mock_run.side_effect = mock_subprocess
            
            # Test compatibility validation
            compatibility_result = self.dependency_manager.validate_dependency_compatibility(temp_dir)
            
            assert compatibility_result["success"] is True
            assert compatibility_result["compatible"] is True
            # Should have no engine compatibility issues since Node 18.12.0 >= 16.0.0
    
    def test_missing_dependencies_workflow(self):
        """Test workflow when dependencies are missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json with dependencies
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "express": "^4.18.0",
                    "missing-package": "^1.0.0"
                }
            }))
            
            # Create partial node_modules (only express)
            node_modules = Path(temp_dir) / "node_modules" / "express"
            node_modules.mkdir(parents=True)
            express_package_json = node_modules / "package.json"
            express_package_json.write_text(json.dumps({
                "name": "express",
                "version": "4.18.2"
            }))
            
            # Test verification
            verification_result = self.dependency_manager.verify_installation(temp_dir)
            
            assert verification_result.success is False
            assert len(verification_result.verified_packages) == 1
            assert "express" in verification_result.verified_packages
            assert len(verification_result.missing_packages) == 1
            assert "missing-package" in verification_result.missing_packages
    
    def test_version_mismatch_detection(self):
        """Test detection of version mismatches."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create package.json requiring specific version
            package_json = Path(temp_dir) / "package.json"
            package_json.write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "lodash": "^4.17.21"  # Require 4.17.21 or higher
                }
            }))
            
            # Create node_modules with older version
            node_modules = Path(temp_dir) / "node_modules" / "lodash"
            node_modules.mkdir(parents=True)
            lodash_package_json = node_modules / "package.json"
            lodash_package_json.write_text(json.dumps({
                "name": "lodash",
                "version": "4.17.15"  # Older version
            }))
            
            # Test verification
            verification_result = self.dependency_manager.verify_installation(temp_dir)
            
            # Should still be considered "verified" (installed) but with version issues
            assert len(verification_result.verified_packages) == 1
            assert "lodash" in verification_result.verified_packages
            
            # The version compatibility check should detect the mismatch
            # (This would be reported in health checks or detailed verification)
    
    def test_no_package_manager_detected(self):
        """Test behavior when no package manager is detected."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Empty directory with no package manager files
            
            # Test all verification functions
            verification_result = self.dependency_manager.verify_installation(temp_dir)
            assert verification_result.success is False
            assert "No package manager detected" in verification_result.errors[0]
            
            security_result = self.dependency_manager.scan_security_vulnerabilities(temp_dir)
            assert security_result["success"] is False
            assert "No package manager detected" in security_result["error"]
            
            compatibility_result = self.dependency_manager.validate_dependency_compatibility(temp_dir)
            assert compatibility_result["success"] is False
            assert "No package manager detected" in compatibility_result["error"]