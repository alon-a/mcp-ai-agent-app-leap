# Configuration Examples

This directory contains example configuration files for different MCP server setups.

## Available Examples

### Basic Python Server (`basic-python.json`)
A minimal Python FastMCP server configuration with:
- Standard FastMCP template
- Basic logging configuration
- No additional dependencies

Usage:
```bash
mcp-builder create my-server --config examples/configs/basic-python.json
```

### Advanced Python Server (`advanced-python.yaml`)
A comprehensive Python server configuration with:
- HTTP transport instead of STDIO
- Authentication enabled
- Database integration
- Additional web framework dependencies
- Debug logging enabled

Usage:
```bash
mcp-builder create my-advanced-server --config examples/configs/advanced-python.yaml
```

### TypeScript Server (`typescript-server.json`)
A TypeScript MCP server configuration with:
- Official TypeScript SDK
- ES2020 build target
- Source maps enabled
- Additional utility libraries

Usage:
```bash
mcp-builder create my-ts-server --config examples/configs/typescript-server.json
```

## Configuration Schema

All configuration files support the following structure:

```json
{
  "template": "template-id",
  "custom_settings": {
    "key": "value"
  },
  "environment_variables": {
    "ENV_VAR": "value"
  },
  "additional_dependencies": [
    "package>=version"
  ]
}
```

### Fields

- **template**: The template ID to use (see `mcp-builder templates` for available options)
- **custom_settings**: Template-specific configuration options
- **environment_variables**: Environment variables to set for the server
- **additional_dependencies**: Extra packages to install beyond template defaults

## Generating Custom Configurations

You can generate a configuration file for any template:

```bash
# Generate JSON config for Python FastMCP
mcp-builder config generate --template python-fastmcp --output my-config.json

# Generate YAML config for TypeScript SDK
mcp-builder config generate --template typescript-sdk --format yaml --output my-config.yaml
```

## Validating Configurations

Validate your configuration files before using them:

```bash
mcp-builder config validate my-config.json
```

This will check:
- File format and syntax
- Schema compliance
- Template availability
- Dependency format validation