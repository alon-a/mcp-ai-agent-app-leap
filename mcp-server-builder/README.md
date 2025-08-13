# MCP Server Builder

An automated tool for creating Model Context Protocol (MCP) server projects from templates.

## Overview

The MCP Server Builder automates the entire process of creating MCP server projects, including:

- Project structure creation
- Template-based file generation
- Dependency management
- Build system execution
- Server validation

## Features

- **Multiple Language Support**: Python, TypeScript, Go, Rust, Java
- **Framework Templates**: FastMCP, TypeScript SDK, low-level implementations
- **Automated Setup**: Complete project scaffolding with dependencies
- **Build Integration**: Automatic compilation and artifact generation
- **Validation**: MCP protocol compliance testing

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Create a new MCP server project
mcp-builder create my-server --template python-fastmcp

# List available templates
mcp-builder templates

# Validate an existing server
mcp-builder validate ./my-server
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/

# Type checking
mypy src/
```

## Architecture

The MCP Server Builder follows a modular architecture with these core components:

- **ProjectManager**: Orchestrates the build process
- **TemplateEngine**: Manages server templates
- **FileManager**: Handles file operations
- **DependencyManager**: Manages package installation
- **BuildSystem**: Executes build commands
- **ValidationEngine**: Tests server functionality

## License

MIT License