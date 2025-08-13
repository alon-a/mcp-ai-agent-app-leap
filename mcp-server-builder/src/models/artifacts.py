"""Artifact management models for the MCP Server Builder."""

import os
import hashlib
import json
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from enum import Enum


class ArtifactType(Enum):
    """Types of build artifacts."""
    EXECUTABLE = "executable"
    LIBRARY = "library"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    SOURCE_MAP = "source_map"
    PACKAGE = "package"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


class ArtifactStatus(Enum):
    """Status of artifact validation."""
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    CORRUPTED = "corrupted"
    UNKNOWN = "unknown"


@dataclass
class ArtifactInfo:
    """Information about a build artifact."""
    path: str
    relative_path: str
    size: int
    checksum: str
    artifact_type: ArtifactType
    status: ArtifactStatus
    created_time: float
    metadata: Dict[str, Any]


@dataclass
class ArtifactCollection:
    """Collection of build artifacts."""
    project_path: str
    build_tool: str
    artifacts: List[ArtifactInfo]
    total_size: int
    collection_time: float
    validation_results: Dict[str, Any]


@dataclass
class ArtifactValidationResult:
    """Result of artifact validation."""
    artifact_path: str
    is_valid: bool
    validation_checks: Dict[str, bool]
    errors: List[str]
    warnings: List[str]


@dataclass
class PackagingResult:
    """Result of artifact packaging."""
    success: bool
    package_path: Optional[str]
    packaged_artifacts: List[str]
    package_size: int
    errors: List[str]


@dataclass
class ArtifactReport:
    """Comprehensive report of build artifacts."""
    project_path: str
    build_tool: str
    build_success: bool
    total_artifacts: int
    valid_artifacts: int
    invalid_artifacts: int
    missing_artifacts: int
    total_size: int
    artifacts: List[ArtifactInfo]
    validation_summary: Dict[str, int]
    packaging_info: Optional[PackagingResult]
    report_time: float
    errors: List[str]
    warnings: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary for serialization."""
        return asdict(self)
    
    def to_json(self) -> str:
        """Convert report to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)
    
    def save_to_file(self, file_path: str) -> bool:
        """Save report to a JSON file."""
        try:
            with open(file_path, 'w') as f:
                f.write(self.to_json())
            return True
        except Exception:
            return False


class ArtifactDetector:
    """Detects and classifies build artifacts."""
    
    # File extensions mapped to artifact types
    ARTIFACT_TYPE_MAPPING = {
        # Executables
        '.exe': ArtifactType.EXECUTABLE,
        '.bin': ArtifactType.EXECUTABLE,
        '.app': ArtifactType.EXECUTABLE,
        
        # Libraries
        '.dll': ArtifactType.LIBRARY,
        '.so': ArtifactType.LIBRARY,
        '.dylib': ArtifactType.LIBRARY,
        '.lib': ArtifactType.LIBRARY,
        '.a': ArtifactType.LIBRARY,
        '.jar': ArtifactType.LIBRARY,
        '.wasm': ArtifactType.LIBRARY,
        
        # Packages
        '.whl': ArtifactType.PACKAGE,
        '.tar.gz': ArtifactType.PACKAGE,
        '.tgz': ArtifactType.PACKAGE,
        '.zip': ArtifactType.PACKAGE,
        '.deb': ArtifactType.PACKAGE,
        '.rpm': ArtifactType.PACKAGE,
        '.msi': ArtifactType.PACKAGE,
        
        # Configuration
        '.json': ArtifactType.CONFIGURATION,
        '.yaml': ArtifactType.CONFIGURATION,
        '.yml': ArtifactType.CONFIGURATION,
        '.toml': ArtifactType.CONFIGURATION,
        '.ini': ArtifactType.CONFIGURATION,
        '.conf': ArtifactType.CONFIGURATION,
        
        # Documentation
        '.md': ArtifactType.DOCUMENTATION,
        '.txt': ArtifactType.DOCUMENTATION,
        '.html': ArtifactType.DOCUMENTATION,
        '.pdf': ArtifactType.DOCUMENTATION,
        
        # Source maps
        '.map': ArtifactType.SOURCE_MAP,
        '.js.map': ArtifactType.SOURCE_MAP,
        '.css.map': ArtifactType.SOURCE_MAP,
    }
    
    # Build tool specific artifact patterns
    BUILD_TOOL_PATTERNS = {
        'npm scripts': {
            'common_files': ['package.json', 'index.js', 'index.d.ts'],
            'directories': ['dist', 'build', 'lib'],
            'extensions': ['.js', '.ts', '.d.ts', '.css', '.html']
        },
        'tsc': {
            'common_files': ['index.d.ts', 'tsconfig.tsbuildinfo'],
            'directories': ['dist', 'build', 'lib'],
            'extensions': ['.js', '.d.ts', '.js.map']
        },
        'webpack': {
            'common_files': ['bundle.js', 'main.js', 'vendor.js'],
            'directories': ['dist', 'build'],
            'extensions': ['.js', '.css', '.html', '.map']
        },
        'vite': {
            'common_files': ['index.html', 'main.js'],
            'directories': ['dist'],
            'extensions': ['.js', '.css', '.html', '.map']
        },
        'setuptools': {
            'common_files': ['setup.py', 'MANIFEST.in'],
            'directories': ['build', 'dist', 'egg-info'],
            'extensions': ['.whl', '.tar.gz', '.egg']
        },
        'poetry build': {
            'common_files': ['pyproject.toml'],
            'directories': ['dist'],
            'extensions': ['.whl', '.tar.gz']
        },
        'cargo build': {
            'common_files': ['Cargo.toml', 'Cargo.lock'],
            'directories': ['target/release', 'target/debug'],
            'extensions': ['.exe', '.bin', '.rlib', '.so', '.dll']
        },
        'go build': {
            'common_files': ['go.mod', 'go.sum'],
            'directories': ['.'],
            'extensions': ['.exe', '.bin']
        }
    }
    
    @classmethod
    def detect_artifact_type(cls, file_path: str) -> ArtifactType:
        """Detect the type of an artifact based on its file extension."""
        path = Path(file_path)
        
        # Check for compound extensions first
        if path.suffix == '.gz' and path.stem.endswith('.tar'):
            return cls.ARTIFACT_TYPE_MAPPING.get('.tar.gz', ArtifactType.UNKNOWN)
        
        # Check for .js.map, .css.map etc.
        if path.suffix == '.map':
            return ArtifactType.SOURCE_MAP
        
        # Check single extension
        extension = path.suffix.lower()
        return cls.ARTIFACT_TYPE_MAPPING.get(extension, ArtifactType.UNKNOWN)
    
    @classmethod
    def is_likely_artifact(cls, file_path: str, build_tool: str) -> bool:
        """Determine if a file is likely to be a build artifact."""
        path = Path(file_path)
        
        # Get build tool patterns
        patterns = cls.BUILD_TOOL_PATTERNS.get(build_tool, {})
        
        # Check if it's a common artifact file first
        common_files = patterns.get('common_files', [])
        if path.name in common_files:
            return True
        
        # Check if file is in common artifact directories
        artifact_dirs = patterns.get('directories', [])
        for artifact_dir in artifact_dirs:
            if artifact_dir != '.' and artifact_dir in str(path):
                return True
        
        # For files in artifact directories, check extensions
        in_artifact_dir = any(artifact_dir != '.' and artifact_dir in str(path) 
                             for artifact_dir in artifact_dirs)
        if in_artifact_dir:
            expected_extensions = patterns.get('extensions', [])
            if path.suffix.lower() in expected_extensions:
                return True
        
        # Check if it matches general artifact patterns (but not source files)
        artifact_type = cls.detect_artifact_type(file_path)
        if artifact_type != ArtifactType.UNKNOWN:
            # Exclude source files that might be in src directories
            if 'src' in str(path).lower() and artifact_type == ArtifactType.UNKNOWN:
                return False
            return True
        
        return False
    
    @classmethod
    def get_expected_artifacts(cls, build_tool: str, project_path: str) -> Set[str]:
        """Get set of expected artifact patterns for a build tool."""
        patterns = cls.BUILD_TOOL_PATTERNS.get(build_tool, {})
        expected = set()
        
        # Add common files
        expected.update(patterns.get('common_files', []))
        
        # Add directory patterns
        for directory in patterns.get('directories', []):
            expected.add(f"{directory}/*")
        
        return expected