# Troubleshooting Guide

## Common Issues and Solutions

### Project Creation Issues

#### Issue: "Template not found" error

**Symptoms:**
```
Template 'my-template' not found
```

**Causes:**
- Incorrect template ID
- Template not properly registered
- Template files missing

**Solutions:**
1. List available templates:
   ```python
   from mcp_server_builder.managers.template_engine import TemplateEngineImpl
   
   engine = TemplateEngineImpl()
   templates = engine.list_templates()
   for template in templates:
       print(f"ID: {template.id}, Name: {template.name}")
   ```

2. Check template directory structure:
   ```bash
   ls -la mcp-server-builder/src/templates/
   ```

3. Verify template configuration files are valid JSON/YAML

#### Issue: "Permission denied" during directory creation

**Symptoms:**
```
Permission denied: '/path/to/output/directory'
```

**Causes:**
- Insufficient permissions on output directory
- Directory owned by different user
- Read-only file system

**Solutions:**
1. Check directory permissions:
   ```bash
   ls -la /path/to/output/
   ```

2. Create directory with proper permissions:
   ```bash
   mkdir -p /path/to/output/my-project
   chmod 755 /path/to/output/my-project
   ```

3. Use a different output directory:
   ```python
   config = {
       'output_directory': os.path.expanduser('~/mcp-projects')
   }
   ```

#### Issue: "Disk space insufficient" error

**Symptoms:**
```
No space left on device
```

**Solutions:**
1. Check available disk space:
   ```bash
   df -h
   ```

2. Clean up temporary files:
   ```bash
   rm -rf /tmp/mcp-builder-*
   ```

3. Use a different output directory with more space

### File Download Issues

#### Issue: Network timeouts during file download

**Symptoms:**
```
Connection timeout: https://example.com/template-file.py
```

**Causes:**
- Network connectivity issues
- Server unavailable
- Firewall blocking requests

**Solutions:**
1. Test network connectivity:
   ```bash
   curl -I https://example.com/template-file.py
   ```

2. Configure proxy if needed:
   ```python
   import os
   os.environ['HTTP_PROXY'] = 'http://proxy.company.com:8080'
   os.environ['HTTPS_PROXY'] = 'https://proxy.company.com:8080'
   ```

3. Use alternative template sources or local templates

#### Issue: Checksum verification failures

**Symptoms:**
```
Checksum mismatch for file: expected abc123, got def456
```

**Causes:**
- File corrupted during download
- Template definition has incorrect checksum
- Network interference

**Solutions:**
1. Retry the download:
   ```python
   # The system automatically retries, but you can force a retry
   manager.cleanup_project(project_id)
   result = manager.create_project(name, template, config)
   ```

2. Verify template checksum manually:
   ```bash
   curl -o temp-file.py https://example.com/template-file.py
   sha256sum temp-file.py
   ```

3. Update template definition with correct checksum

### Dependency Installation Issues

#### Issue: Package not found

**Symptoms:**
```
Package 'unknown-package' not found
```

**Causes:**
- Package name typo
- Package not available in current registry
- Wrong package manager detected

**Solutions:**
1. Verify package name:
   ```bash
   pip search package-name
   npm search package-name
   ```

2. Check package manager detection:
   ```python
   from mcp_server_builder.managers.dependency_manager import DependencyManagerImpl
   
   dep_manager = DependencyManagerImpl()
   detected = dep_manager.detect_package_manager('/path/to/project')
   print(f"Detected package manager: {detected}")
   ```

3. Manually specify correct dependencies in config:
   ```python
   config = {
       'additional_dependencies': ['correct-package-name>=1.0.0']
   }
   ```

#### Issue: Version conflicts

**Symptoms:**
```
Dependency conflict: package-a requires package-b>=2.0, but package-c requires package-b<2.0
```

**Solutions:**
1. Review dependency tree:
   ```bash
   pip show package-name
   pip list --outdated
   ```

2. Use compatible versions:
   ```python
   config = {
       'additional_dependencies': [
           'package-a>=1.0,<2.0',
           'package-b>=1.5,<2.0'
       ]
   }
   ```

3. Create virtual environment for isolation:
   ```bash
   python -m venv mcp-server-env
   source mcp-server-env/bin/activate  # Linux/Mac
   # or
   mcp-server-env\Scripts\activate  # Windows
   ```

### Build Issues

#### Issue: Build command not found

**Symptoms:**
```
Command 'npm' not found
Command 'cargo' not found
```

**Causes:**
- Build tool not installed
- Build tool not in PATH
- Wrong build system detected

**Solutions:**
1. Install required build tools:
   ```bash
   # Node.js/npm
   curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
   sudo apt-get install -y nodejs
   
   # Rust/cargo
   curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
   
   # Python build tools
   pip install build setuptools wheel
   ```

2. Check PATH configuration:
   ```bash
   echo $PATH
   which npm
   which cargo
   ```

3. Manually specify build commands:
   ```python
   # Override template build commands if needed
   template = engine.get_template('my-template')
   template.build_commands = ['/usr/local/bin/npm install', '/usr/local/bin/npm run build']
   ```

#### Issue: Compilation errors

**Symptoms:**
```
Error: Cannot find module 'missing-dependency'
SyntaxError: invalid syntax
```

**Solutions:**
1. Check build logs for specific errors:
   ```python
   result = manager.create_project(name, template, config)
   if not result.success:
       print("Build logs:")
       # Build logs are included in the result
       for log in result.build_logs:
           print(log)
   ```

2. Verify all dependencies are installed:
   ```bash
   cd /path/to/project
   npm list  # for Node.js
   pip list  # for Python
   ```

3. Clean and rebuild:
   ```bash
   cd /path/to/project
   rm -rf node_modules package-lock.json  # Node.js
   rm -rf __pycache__ *.pyc  # Python
   # Then retry build
   ```

### Validation Issues

#### Issue: Server fails to start

**Symptoms:**
```
Server startup validation failed
Process exited with code 1
```

**Causes:**
- Missing dependencies
- Configuration errors
- Port conflicts
- Permission issues

**Solutions:**
1. Check server logs:
   ```bash
   cd /path/to/project
   python server.py  # or appropriate start command
   ```

2. Verify configuration:
   ```python
   # Check generated configuration files
   import json
   with open('/path/to/project/config.json') as f:
       config = json.load(f)
       print(json.dumps(config, indent=2))
   ```

3. Test with minimal configuration:
   ```python
   # Create project with minimal settings
   config = {
       'custom_settings': {
           'server_name': 'Test Server',
           'transport_type': 'stdio'
       }
   }
   ```

#### Issue: MCP protocol validation fails

**Symptoms:**
```
MCP protocol validation failed
Missing required capabilities
```

**Solutions:**
1. Check MCP protocol version compatibility:
   ```python
   from mcp_server_builder.managers.validation_engine import MCPValidationEngine
   
   validator = MCPValidationEngine()
   result = validator.run_comprehensive_tests('/path/to/project')
   print(f"Protocol version: {result.get('protocol_version')}")
   print(f"Supported capabilities: {result.get('capabilities')}")
   ```

2. Update template to latest MCP specification:
   ```bash
   # Check for template updates
   git pull origin main  # if using git-based templates
   ```

3. Manually implement missing capabilities:
   ```python
   # Add required MCP methods to your server implementation
   # See MCP specification for details
   ```

## Debugging Techniques

### Enable Debug Logging

```python
from mcp_server_builder.managers.project_manager import ProjectManagerImpl
from mcp_server_builder.managers.progress_tracker import LogLevel

# Enable debug logging
manager = ProjectManagerImpl(
    log_level=LogLevel.DEBUG,
    log_file='mcp-builder-debug.log'
)
```

### Inspect Project State

```python
# Get detailed project information
details = manager.get_project_details(project_id)
print(json.dumps(details, indent=2, default=str))

# Get all progress events
events = manager.get_project_events(project_id)
for event in events:
    print(f"{event.timestamp}: {event.event_type.value} - {event.message}")
```

### Manual Validation Steps

```python
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = '/path/to/project'

# Step-by-step validation
print("1. Testing server startup...")
startup_ok = validator.validate_server_startup(project_path)
print(f"   Result: {'✅' if startup_ok else '❌'}")

print("2. Testing MCP protocol compliance...")
protocol_ok = validator.validate_mcp_protocol(project_path)
print(f"   Result: {'✅' if protocol_ok else '❌'}")

print("3. Testing functionality...")
functionality = validator.validate_functionality(project_path)
for func_type, result in functionality.items():
    print(f"   {func_type}: {'✅' if result else '❌'}")
```

### Environment Diagnostics

```python
import sys
import os
import subprocess

def diagnose_environment():
    """Diagnose the current environment for common issues."""
    
    print("=== Environment Diagnostics ===")
    
    # Python version
    print(f"Python version: {sys.version}")
    
    # Available disk space
    import shutil
    total, used, free = shutil.disk_usage('/')
    print(f"Disk space: {free // (2**30)} GB free of {total // (2**30)} GB total")
    
    # Network connectivity
    try:
        import urllib.request
        urllib.request.urlopen('https://pypi.org', timeout=5)
        print("Network connectivity: ✅")
    except:
        print("Network connectivity: ❌")
    
    # Package managers
    managers = ['pip', 'npm', 'cargo', 'go']
    for manager in managers:
        try:
            result = subprocess.run([manager, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print(f"{manager}: ✅ {version}")
            else:
                print(f"{manager}: ❌ Not working")
        except:
            print(f"{manager}: ❌ Not found")
    
    # Permissions
    test_dir = '/tmp/mcp-test'
    try:
        os.makedirs(test_dir, exist_ok=True)
        with open(f'{test_dir}/test.txt', 'w') as f:
            f.write('test')
        os.remove(f'{test_dir}/test.txt')
        os.rmdir(test_dir)
        print("File system permissions: ✅")
    except:
        print("File system permissions: ❌")

# Run diagnostics
diagnose_environment()
```

## Performance Issues

### Slow Project Creation

**Symptoms:**
- Project creation takes unusually long
- Progress appears stuck

**Solutions:**
1. Check network speed for file downloads
2. Use local templates when possible
3. Reduce logging verbosity:
   ```python
   manager = ProjectManagerImpl(log_level=LogLevel.WARNING)
   ```

### Memory Usage Issues

**Symptoms:**
- Out of memory errors
- System becomes unresponsive

**Solutions:**
1. Monitor memory usage:
   ```python
   import psutil
   process = psutil.Process()
   print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.1f} MB")
   ```

2. Process projects sequentially instead of concurrently
3. Clean up completed projects promptly:
   ```python
   if result.status == ProjectStatus.COMPLETED:
       manager.cleanup_project(result.project_id)
   ```

## Getting Help

### Log Analysis

When reporting issues, include relevant log information:

```python
# Enable comprehensive logging
manager = ProjectManagerImpl(
    log_level=LogLevel.DEBUG,
    log_file='mcp-builder-debug.log'
)

# After issue occurs, check the log file
with open('mcp-builder-debug.log') as f:
    print(f.read())
```

### System Information

Include system information when reporting issues:

```python
import platform
import sys

print(f"OS: {platform.system()} {platform.release()}")
print(f"Python: {sys.version}")
print(f"Architecture: {platform.machine()}")
```

### Issue Reporting Template

When reporting issues, please include:

1. **Environment Information:**
   - Operating system and version
   - Python version
   - MCP Server Builder version

2. **Steps to Reproduce:**
   - Exact commands or code used
   - Configuration parameters
   - Template used

3. **Expected vs Actual Behavior:**
   - What you expected to happen
   - What actually happened

4. **Error Messages:**
   - Complete error messages
   - Stack traces
   - Log files (with debug logging enabled)

5. **Additional Context:**
   - Network environment (proxy, firewall)
   - File system type and permissions
   - Any custom modifications made