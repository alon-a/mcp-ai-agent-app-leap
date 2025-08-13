"""Main CLI entry point for MCP Server Builder."""

import argparse
import sys
import os
import json
from typing import Dict, Any, Optional, List
from pathlib import Path

from .comprehensive_test import create_comprehensive_test_parser
from .interactive import InteractiveMode
from .validators import validate_project_name, validate_output_directory, validate_template_id, validate_config_file, validate_verbosity_level
from .output import OutputFormatter, ProgressIndicator, create_summary_report, format_duration
from ..managers.project_manager import ProjectManagerImpl
from ..managers.template_engine import TemplateEngineImpl
from ..models.base import ProjectConfig


def add_common_arguments(parser):
    """Add common arguments to a parser."""
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (use -v, -vv, or -vvv)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )


def create_main_parser():
    """Create the main argument parser with comprehensive options."""
    parser = argparse.ArgumentParser(
        prog='mcp-server-builder',
        description='MCP Server Builder - Automated MCP server project generator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create my-server --template python-fastmcp
  %(prog)s create my-server --interactive
  %(prog)s templates --detailed
  %(prog)s validate ./my-server-project
  %(prog)s create my-server --config config.json

For more information, visit: https://github.com/modelcontextprotocol/server-builder
        """
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (use -v, -vv, or -vvv)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress all output except errors'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(
        dest='command',
        help='Available commands',
        metavar='COMMAND',
        required=True
    )
    
    # Create command
    create_parser = subparsers.add_parser(
        'create',
        help='Create a new MCP server project',
        description='Create a new MCP server project from a template',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create my-server --template python-fastmcp
  %(prog)s create my-server --interactive
  %(prog)s create my-server --template typescript-sdk --output ./projects/
        """
    )
    add_common_arguments(create_parser)
    create_parser.add_argument(
        'name',
        help='Project name (must be valid identifier)',
        type=str
    )
    create_parser.add_argument(
        '--template', '-t',
        help='Template to use for the server (use "templates" command to list available)',
        type=str
    )
    create_parser.add_argument(
        '--output', '-o',
        help='Output directory (default: current directory)',
        type=str,
        default='.'
    )
    create_parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Use interactive mode for template selection and configuration'
    )
    create_parser.add_argument(
        '--config', '-c',
        help='Path to configuration file (JSON or YAML)',
        type=str
    )
    create_parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Overwrite existing project directory if it exists'
    )
    create_parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be created without actually creating it'
    )
    create_parser.set_defaults(func=create_project)
    
    # Templates command
    templates_parser = subparsers.add_parser(
        'templates',
        help='List available server templates',
        description='List and describe available MCP server templates'
    )
    add_common_arguments(templates_parser)
    templates_parser.add_argument(
        '--detailed', '-d',
        action='store_true',
        help='Show detailed information about each template'
    )
    templates_parser.add_argument(
        '--language', '-l',
        help='Filter templates by programming language',
        choices=['python', 'typescript', 'javascript', 'go', 'rust']
    )
    templates_parser.add_argument(
        '--framework', '-f',
        help='Filter templates by framework',
        choices=['fastmcp', 'sdk', 'low-level']
    )
    templates_parser.set_defaults(func=list_templates)
    
    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate an MCP server project',
        description='Validate that an MCP server project is correctly configured and functional'
    )
    validate_parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (use -v, -vv, or -vvv)'
    )
    validate_parser.add_argument(
        'path',
        help='Path to MCP server project directory',
        type=str
    )
    validate_parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to automatically fix common issues'
    )
    validate_parser.add_argument(
        '--report',
        help='Save validation report to file',
        type=str
    )
    validate_parser.set_defaults(func=validate_project)
    
    # Info command
    info_parser = subparsers.add_parser(
        'info',
        help='Show information about a template or project',
        description='Display detailed information about a template or existing project'
    )
    info_parser.add_argument(
        'target',
        help='Template ID or project path',
        type=str
    )
    info_parser.set_defaults(func=show_info)
    
    # Config command
    config_parser = subparsers.add_parser(
        'config',
        help='Generate or validate configuration files',
        description='Generate example configuration files or validate existing ones'
    )
    config_subparsers = config_parser.add_subparsers(
        dest='config_action',
        help='Configuration actions',
        required=True
    )
    
    # Generate config subcommand
    generate_config_parser = config_subparsers.add_parser(
        'generate',
        help='Generate example configuration file'
    )
    generate_config_parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (use -v, -vv, or -vvv)'
    )
    generate_config_parser.add_argument(
        '--output', '-o',
        help='Output file path (default: mcp-config.json)',
        default='mcp-config.json'
    )
    generate_config_parser.add_argument(
        '--format', '-f',
        help='Configuration file format',
        choices=['json', 'yaml'],
        default='json'
    )
    generate_config_parser.add_argument(
        '--template', '-t',
        help='Generate config for specific template'
    )
    generate_config_parser.set_defaults(func=generate_config)
    
    # Validate config subcommand
    validate_config_parser = config_subparsers.add_parser(
        'validate',
        help='Validate configuration file'
    )
    validate_config_parser.add_argument(
        '--verbose', '-v',
        action='count',
        default=0,
        help='Increase verbosity (use -v, -vv, or -vvv)'
    )
    validate_config_parser.add_argument(
        'config_file',
        help='Path to configuration file to validate'
    )
    validate_config_parser.set_defaults(func=validate_config)
    
    # Comprehensive test command
    create_comprehensive_test_parser(subparsers)
    
    return parser


def create_project(args):
    """Create a new MCP server project."""
    from .config_loader import load_config_file
    import time
    
    # Initialize output formatter
    formatter = OutputFormatter(verbosity=getattr(args, 'verbose', 0))
    start_time = time.time()
    
    # Validate project name
    name_error = validate_project_name(args.name)
    if name_error:
        formatter.error(f"Invalid project name: {name_error}")
        return 1
    
    # Validate output directory
    output_error = validate_output_directory(args.output)
    if output_error:
        formatter.error(f"Invalid output directory: {output_error}")
        return 1
    
    # Check if project directory already exists
    project_path = Path(args.output) / args.name
    if project_path.exists() and not args.force:
        formatter.error(f"Project directory '{project_path}' already exists. Use --force to overwrite.")
        return 1
    
    try:
        # Initialize managers
        formatter.verbose("Initializing template engine and project manager", 2)
        template_engine = TemplateEngineImpl()
        project_manager = ProjectManagerImpl()
        
        # Load configuration from file if provided
        config_data = {}
        if args.config:
            config_error = validate_config_file(args.config)
            if config_error:
                formatter.error(config_error)
                return 1
            
            formatter.verbose(f"Loading configuration from: {args.config}")
            config_data = load_config_file(args.config)
            formatter.debug(f"Loaded config: {config_data}")
        
        # Use interactive mode or command line arguments
        if args.interactive:
            formatter.info("Starting interactive mode")
            interactive = InteractiveMode(template_engine)
            config = interactive.run(args.name, args.output)
        else:
            # Validate template if provided
            if args.template:
                available_templates = [t.id for t in template_engine.list_templates()]
                template_error = validate_template_id(args.template, available_templates)
                if template_error:
                    formatter.error(template_error)
                    return 1
            
            # Create config from command line arguments
            config = ProjectConfig(
                name=args.name,
                template_id=args.template or config_data.get('template', 'python-fastmcp'),
                output_directory=args.output,
                custom_settings=config_data.get('custom_settings', {}),
                environment_variables=config_data.get('environment_variables', {}),
                additional_dependencies=config_data.get('additional_dependencies', [])
            )
        
        # Get template for display
        template = template_engine.get_template(config.template_id)
        
        # Dry run mode
        if args.dry_run:
            formatter.header("Dry Run Mode", "Showing what would be created")
            
            dry_run_data = {
                "Project Name": config.name,
                "Template": template.name,
                "Location": str(project_path),
                "Files to Create": len(template.files),
                "Dependencies": len(template.dependencies + config.additional_dependencies)
            }
            
            create_summary_report("Project Preview", dry_run_data, formatter)
            return 0
        
        # Create the project with progress indication
        formatter.header(f"Creating MCP Server Project: {args.name}")
        
        # Show project configuration
        config_data = {
            "Template": template.name,
            "Output Directory": config.output_directory,
            "Custom Settings": config.custom_settings,
            "Environment Variables": config.environment_variables,
            "Additional Dependencies": config.additional_dependencies
        }
        
        formatter.section("Project Configuration")
        for key, value in config_data.items():
            if isinstance(value, dict) and value:
                formatter.key_value(key, f"{len(value)} items")
                for k, v in list(value.items())[:3]:
                    formatter.key_value(k, v, indent=1)
                if len(value) > 3:
                    formatter.list_item(f"... and {len(value) - 3} more", indent=1)
            elif isinstance(value, list) and value:
                formatter.key_value(key, f"{len(value)} items")
                for item in value[:3]:
                    formatter.list_item(str(item), indent=1)
                if len(value) > 3:
                    formatter.list_item(f"... and {len(value) - 3} more", indent=1)
            elif value:
                formatter.key_value(key, value)
        
        # Create progress indicator
        progress = ProgressIndicator("Creating project...", formatter)
        progress.start()
        
        result = project_manager.create_project(config)
        
        progress.stop()
        
        if result.success:
            end_time = time.time()
            duration = format_duration(end_time - start_time)
            
            formatter.success(f"Project created successfully in {duration}")
            
            # Create success summary
            success_data = {
                "Project Path": result.project_path,
                "Files Created": result.created_files,
                "Template Used": template.name,
                "Build Time": duration
            }
            
            next_steps = [
                f"cd {result.project_path}",
                "Review the generated files",
                "Install dependencies if needed",
                "Run the build commands",
                "Test your MCP server"
            ]
            
            create_summary_report("Project Created Successfully", success_data, formatter, next_steps)
            
            return 0
        else:
            formatter.error(f"Project creation failed: {result.error_message}")
            return 1
            
    except KeyboardInterrupt:
        formatter.error("Operation cancelled by user")
        return 130
    except Exception as e:
        formatter.error(f"Unexpected error: {e}")
        if getattr(args, 'verbose', 0) > 2:
            import traceback
            traceback.print_exc()
        return 1


def list_templates(args):
    """List available server templates."""
    try:
        formatter = OutputFormatter(verbosity=getattr(args, 'verbose', 0))
        
        template_engine = TemplateEngineImpl()
        templates = template_engine.list_templates()
        
        if not templates:
            formatter.error("No templates available")
            return 1
        
        # Apply filters
        filtered_templates = templates
        
        if args.language:
            filtered_templates = [t for t in filtered_templates if t.language.value == args.language]
            formatter.verbose(f"Filtered by language: {args.language}")
        
        if args.framework:
            filtered_templates = [t for t in filtered_templates if t.framework.value == args.framework]
            formatter.verbose(f"Filtered by framework: {args.framework}")
        
        if not filtered_templates:
            formatter.error("No templates found matching the specified criteria")
            return 1
        
        # Create header
        title = f"Available Templates ({len(filtered_templates)} found)"
        if args.language or args.framework:
            filters = []
            if args.language:
                filters.append(f"language: {args.language}")
            if args.framework:
                filters.append(f"framework: {args.framework}")
            subtitle = f"Filtered by {', '.join(filters)}"
        else:
            subtitle = None
        
        formatter.header(title, subtitle)
        
        for i, template in enumerate(filtered_templates):
            # Template header
            formatter.section(f"{template.id}")
            formatter.key_value("Name", template.name)
            formatter.key_value("Language", template.language.value)
            formatter.key_value("Framework", template.framework.value)
            
            if args.detailed:
                formatter.key_value("Description", template.description)
                formatter.key_value("Dependencies", len(template.dependencies))
                formatter.key_value("Files", len(template.files))
                formatter.key_value("Build Commands", len(template.build_commands))
                
                if template.dependencies:
                    print("\n   Key Dependencies:")
                    for dep in template.dependencies[:3]:  # Show first 3
                        formatter.list_item(dep, indent=1)
                    if len(template.dependencies) > 3:
                        formatter.list_item(f"... and {len(template.dependencies) - 3} more", indent=1)
                
                if template.files:
                    print("\n   Template Files:")
                    for file_spec in template.files[:3]:  # Show first 3
                        formatter.list_item(file_spec.path, indent=1)
                    if len(template.files) > 3:
                        formatter.list_item(f"... and {len(template.files) - 3} more", indent=1)
            
            # Add spacing between templates
            if i < len(filtered_templates) - 1:
                print()
        
        if not args.detailed:
            formatter.info("Use --detailed flag for more information about each template")
        
        return 0
        
    except Exception as e:
        formatter = OutputFormatter()
        formatter.error(f"Error listing templates: {e}")
        return 1


def validate_project(args):
    """Validate an MCP server project."""
    try:
        formatter = OutputFormatter(verbosity=getattr(args, 'verbose', 0))
        project_path = Path(args.path)
        
        if not project_path.exists():
            formatter.error(f"Project path '{args.path}' does not exist")
            return 1
        
        if not project_path.is_dir():
            formatter.error(f"'{args.path}' is not a directory")
            return 1
        
        formatter.header(f"Validating MCP Server Project", f"Path: {args.path}")
        
        # Initialize validation engine
        from ..managers.validation_engine import MCPValidationEngine
        validator = MCPValidationEngine()
        
        # Run validation with progress indicator
        progress = ProgressIndicator("Running validation tests...", formatter)
        progress.start()
        
        result = validator.validate_server(str(project_path))
        
        progress.stop()
        
        # Create validation summary
        validation_data = {
            "Project Path": str(project_path),
            "Validation Status": "PASSED" if result.is_valid else "FAILED",
            "Tests Run": len(result.test_results),
            "Errors Found": len(result.errors),
            "Warnings": len(result.warnings)
        }
        
        if hasattr(result, 'performance_metrics') and result.performance_metrics:
            validation_data["Performance Score"] = result.performance_metrics.get('overall_score', 'N/A')
        
        if result.is_valid:
            formatter.success("Project validation passed!")
            create_summary_report("Validation Results", validation_data, formatter)
        else:
            formatter.error("Project validation failed!")
            
            # Show errors
            if result.errors:
                formatter.section("Errors Found")
                for i, error in enumerate(result.errors[:10], 1):  # Show first 10 errors
                    formatter.list_item(f"{error}")
                
                if len(result.errors) > 10:
                    formatter.list_item(f"... and {len(result.errors) - 10} more issues")
            
            # Show warnings
            if result.warnings:
                formatter.section("Warnings")
                for warning in result.warnings[:5]:  # Show first 5 warnings
                    formatter.list_item(f"{warning}")
                
                if len(result.warnings) > 5:
                    formatter.list_item(f"... and {len(result.warnings) - 5} more warnings")
            
            create_summary_report("Validation Results", validation_data, formatter)
        
        # Save report if requested
        if args.report:
            report_path = Path(args.report)
            formatter.verbose(f"Saving validation report to: {args.report}")
            
            with open(report_path, 'w') as f:
                json.dump({
                    'project_path': str(project_path),
                    'validation_result': {
                        'is_valid': result.is_valid,
                        'errors': result.errors,
                        'warnings': result.warnings,
                        'test_results': [str(r) for r in result.test_results],
                        'performance_metrics': getattr(result, 'performance_metrics', {})
                    }
                }, f, indent=2)
            
            formatter.success(f"Validation report saved to: {args.report}")
        
        return 0 if result.is_valid else 1
        
    except Exception as e:
        formatter = OutputFormatter()
        formatter.error(f"Error validating project: {e}")
        return 1


def show_info(args):
    """Show information about a template or project."""
    try:
        target_path = Path(args.target)
        
        # Check if it's a project directory
        if target_path.exists() and target_path.is_dir():
            print(f"📁 Project Information: {args.target}")
            print("=" * 40)
            
            # Look for project metadata
            metadata_files = ['pyproject.toml', 'package.json', 'Cargo.toml']
            found_metadata = False
            
            for metadata_file in metadata_files:
                metadata_path = target_path / metadata_file
                if metadata_path.exists():
                    print(f"📄 Found: {metadata_file}")
                    found_metadata = True
            
            if not found_metadata:
                print("⚠️  No recognized project metadata files found")
            
            # List directory contents
            files = list(target_path.iterdir())
            print(f"📂 Files: {len(files)}")
            
            for file_path in sorted(files)[:10]:  # Show first 10 files
                if file_path.is_dir():
                    print(f"   📁 {file_path.name}/")
                else:
                    print(f"   📄 {file_path.name}")
            
            if len(files) > 10:
                print(f"   ... and {len(files) - 10} more items")
        
        else:
            # Assume it's a template ID
            template_engine = TemplateEngineImpl()
            
            try:
                template = template_engine.get_template(args.target)
                
                print(f"🔧 Template Information: {template.id}")
                print("=" * 40)
                print(f"Name: {template.name}")
                print(f"Language: {template.language.value}")
                print(f"Framework: {template.framework.value}")
                print(f"Description: {template.description}")
                print()
                
                print(f"📦 Dependencies ({len(template.dependencies)}):")
                for dep in template.dependencies:
                    print(f"  - {dep}")
                print()
                
                print(f"📄 Files ({len(template.files)}):")
                for file_spec in template.files:
                    print(f"  - {file_spec.path}")
                print()
                
                print(f"🔨 Build Commands ({len(template.build_commands)}):")
                for cmd in template.build_commands:
                    print(f"  - {cmd}")
                
                if template.configuration_schema:
                    print("\n⚙️  Configuration Options:")
                    schema = template.configuration_schema
                    if 'properties' in schema:
                        for prop, config in schema['properties'].items():
                            desc = config.get('description', 'No description')
                            default = config.get('default', 'No default')
                            print(f"  - {prop}: {desc} (default: {default})")
                
            except Exception:
                print(f"❌ Template '{args.target}' not found")
                return 1
        
        return 0
        
    except Exception as e:
        print(f"❌ Error showing info: {e}", file=sys.stderr)
        return 1


def generate_config(args):
    """Generate example configuration file."""
    try:
        from .config_loader import create_example_config, save_config_file
        
        formatter = OutputFormatter(verbosity=getattr(args, 'verbose', 0))
        
        formatter.header("Generating Configuration File", f"Output: {args.output}")
        
        # Create base configuration
        config = create_example_config()
        
        # Customize for specific template if requested
        if args.template:
            template_engine = TemplateEngineImpl()
            
            try:
                template = template_engine.get_template(args.template)
                config['template'] = template.id
                
                # Add template-specific settings from schema
                if template.configuration_schema and 'properties' in template.configuration_schema:
                    template_settings = {}
                    properties = template.configuration_schema['properties']
                    
                    for prop_name, prop_config in properties.items():
                        default_value = prop_config.get('default')
                        if default_value is not None:
                            template_settings[prop_name] = default_value
                    
                    if template_settings:
                        config['custom_settings'] = template_settings
                
                formatter.success(f"Generated configuration for template: {template.name}")
                
            except Exception as e:
                formatter.warning(f"Template '{args.template}' not found, using default configuration")
        
        # Save configuration file
        save_config_file(config, args.output, args.format)
        
        formatter.success(f"Configuration file saved to: {args.output}")
        formatter.key_value("Format", args.format.upper())
        
        # Show preview of generated config
        formatter.section("Configuration Preview")
        
        if args.format == 'json':
            import json
            print(json.dumps(config, indent=2))
        else:
            import yaml
            print(yaml.dump(config, default_flow_style=False))
        
        # Usage instructions
        next_steps = [
            "Edit the configuration file to customize your project settings",
            f"Use with: mcp-builder create <name> --config {args.output}"
        ]
        
        formatter.section("Usage Instructions")
        for i, step in enumerate(next_steps, 1):
            formatter.list_item(f"{i}. {step}")
        
        return 0
        
    except Exception as e:
        formatter = OutputFormatter()
        formatter.error(f"Error generating configuration: {e}")
        return 1


def validate_config(args):
    """Validate configuration file."""
    try:
        from .config_loader import load_config_file, validate_config_schema
        
        formatter = OutputFormatter(verbosity=getattr(args, 'verbose', 0))
        
        formatter.header("Validating Configuration File", f"File: {args.config_file}")
        
        # Check file exists and is readable
        config_error = validate_config_file(args.config_file)
        if config_error:
            formatter.error(config_error)
            return 1
        
        # Load configuration
        progress = ProgressIndicator("Loading configuration...", formatter)
        progress.start()
        
        config = load_config_file(args.config_file)
        
        progress.stop("Configuration file loaded successfully")
        
        # Validate schema
        validated_config = validate_config_schema(config)
        formatter.success("Configuration schema is valid")
        
        # Validate template if specified
        if 'template' in validated_config:
            template_engine = TemplateEngineImpl()
            available_templates = [t.id for t in template_engine.list_templates()]
            
            template_error = validate_template_id(validated_config['template'], available_templates)
            if template_error:
                formatter.warning(template_error)
            else:
                formatter.success(f"Template '{validated_config['template']}' is available")
        
        # Create configuration summary
        config_summary = {}
        
        for key, value in validated_config.items():
            if key == 'custom_settings' and isinstance(value, dict):
                config_summary["Custom Settings"] = value
            elif key == 'environment_variables' and isinstance(value, dict):
                config_summary["Environment Variables"] = {k: "***" for k in value.keys()}  # Hide values for security
            elif key == 'additional_dependencies' and isinstance(value, list):
                config_summary["Additional Dependencies"] = value
            else:
                config_summary[key.replace('_', ' ').title()] = value
        
        create_summary_report("Configuration Summary", config_summary, formatter)
        
        formatter.success("Configuration validation completed successfully")
        return 0
        
    except Exception as e:
        formatter = OutputFormatter()
        formatter.error(f"Configuration validation failed: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = create_main_parser()
    args = parser.parse_args()
    
    # Validate verbosity level
    if hasattr(args, 'verbose'):
        verbosity_error = validate_verbosity_level(args.verbose)
        if verbosity_error:
            formatter = OutputFormatter()
            formatter.error(verbosity_error)
            return 1
    
    # Set up quiet mode
    original_stdout = None
    if hasattr(args, 'quiet') and args.quiet:
        # Suppress all output except errors by redirecting stdout
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    
    try:
        if hasattr(args, 'func'):
            try:
                return args.func(args)
            except KeyboardInterrupt:
                formatter = OutputFormatter()
                formatter.error("Operation cancelled by user")
                return 130
            except Exception as e:
                formatter = OutputFormatter()
                formatter.error(f"Error: {e}")
                if hasattr(args, 'verbose') and args.verbose > 2:
                    import traceback
                    traceback.print_exc()
                return 1
        else:
            parser.print_help()
            return 1
    
    finally:
        # Restore stdout if it was redirected
        if original_stdout:
            sys.stdout.close()
            sys.stdout = original_stdout


if __name__ == "__main__":
    sys.exit(main())