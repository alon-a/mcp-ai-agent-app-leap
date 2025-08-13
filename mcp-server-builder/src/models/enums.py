"""Enums and constants for the MCP Server Builder."""

from enum import Enum


class PackageManager(Enum):
    """Supported package managers."""
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    PIP = "pip"
    POETRY = "poetry"
    PIPENV = "pipenv"
    CARGO = "cargo"
    GO_MOD = "go mod"
    MAVEN = "maven"
    GRADLE = "gradle"


class BuildTool(Enum):
    """Supported build tools."""
    NPM_SCRIPTS = "npm scripts"
    WEBPACK = "webpack"
    VITE = "vite"
    TSC = "tsc"
    PYTHON_SETUPTOOLS = "setuptools"
    POETRY_BUILD = "poetry build"
    CARGO_BUILD = "cargo build"
    GO_BUILD = "go build"
    MAVEN_BUILD = "maven"
    GRADLE_BUILD = "gradle"


class TransportType(Enum):
    """MCP transport types."""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"
    WEBSOCKET = "websocket"


class ValidationLevel(Enum):
    """Validation levels for MCP servers."""
    BASIC = "basic"
    STANDARD = "standard"
    COMPREHENSIVE = "comprehensive"