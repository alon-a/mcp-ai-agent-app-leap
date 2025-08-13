"""Interactive mode for MCP Server Builder CLI."""

import sys
from typing import Dict, Any, Optional, List
from ..managers.template_engine import TemplateEngineImpl
from ..models.base import ServerTemplate, ProjectConfig


class InteractiveMode:
    """Handles interactive template selection and configuration."""
    
    def __init__(self, template_engine: TemplateEngineImpl):
        self.template_engine = template_engine
    
    def run(self, project_name: str, output_dir: str) -> ProjectConfig:
        """Run interactive mode to configure a new project."""
        print(f"\n🚀 Welcome to MCP Server Builder Interactive Mode")
        print(f"Creating project: {project_name}")
        print(f"Output directory: {output_dir}")
        print("-" * 50)
        
        # Select template
        template = self._select_template()
        if not template:
            print("❌ No template selected. Exiting.")
            sys.exit(1)
        
        # Configure template
        config = self._configure_template(template, project_name, output_dir)
        
        # Confirm configuration
        if self._confirm_configuration(config, template):
            return config
        else:
            print("❌ Configuration cancelled. Exiting.")
            sys.exit(1)
    
    def _select_template(self) -> Optional[ServerTemplate]:
        """Interactive template selection."""
        templates = self.template_engine.list_templates()
        
        if not templates:
            print("❌ No templates available.")
            return None
        
        print("\n📋 Available Templates:")
        for i, template in enumerate(templates, 1):
            print(f"  {i}. {template.name}")
            print(f"     Language: {template.language.value}")
            print(f"     Framework: {template.framework.value}")
            print(f"     Description: {template.description}")
            print()
        
        while True:
            try:
                choice = input(f"Select template (1-{len(templates)}) or 'q' to quit: ").strip()
                
                if choice.lower() == 'q':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    selected = templates[index]
                    print(f"\n✅ Selected: {selected.name}")
                    return selected
                else:
                    print(f"❌ Please enter a number between 1 and {len(templates)}")
            
            except ValueError:
                print("❌ Please enter a valid number or 'q' to quit")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled.")
                return None
    
    def _configure_template(self, template: ServerTemplate, project_name: str, output_dir: str) -> ProjectConfig:
        """Interactive template configuration."""
        print(f"\n⚙️  Configuring {template.name}")
        print("-" * 30)
        
        custom_settings = {}
        
        # Get configuration schema
        schema = template.configuration_schema
        if schema and 'properties' in schema:
            properties = schema['properties']
            required = schema.get('required', [])
            
            for prop_name, prop_config in properties.items():
                prop_type = prop_config.get('type', 'string')
                description = prop_config.get('description', '')
                default = prop_config.get('default')
                enum_values = prop_config.get('enum')
                
                # Skip server_name as we use the project name
                if prop_name == 'server_name':
                    custom_settings[prop_name] = project_name
                    continue
                
                # Build prompt
                prompt = f"{prop_name}"
                if description:
                    prompt += f" ({description})"
                
                if enum_values:
                    prompt += f" [{'/'.join(enum_values)}]"
                elif default is not None:
                    prompt += f" [default: {default}]"
                
                if prop_name in required:
                    prompt += " (required)"
                
                prompt += ": "
                
                # Get user input
                while True:
                    try:
                        value = input(prompt).strip()
                        
                        # Use default if empty and not required
                        if not value and prop_name not in required and default is not None:
                            value = str(default)
                        
                        # Validate required fields
                        if not value and prop_name in required:
                            print(f"❌ {prop_name} is required")
                            continue
                        
                        # Validate enum values
                        if enum_values and value and value not in enum_values:
                            print(f"❌ {prop_name} must be one of: {', '.join(enum_values)}")
                            continue
                        
                        # Convert type
                        if value:
                            if prop_type == 'integer':
                                value = int(value)
                            elif prop_type == 'number':
                                value = float(value)
                            elif prop_type == 'boolean':
                                value = value.lower() in ('true', 'yes', '1', 'on')
                        
                        if value or value == 0 or value is False:  # Include falsy values except empty string
                            custom_settings[prop_name] = value
                        
                        break
                        
                    except ValueError as e:
                        print(f"❌ Invalid value for {prop_name}: {e}")
                    except KeyboardInterrupt:
                        print("\n❌ Configuration cancelled.")
                        sys.exit(1)
        
        # Ask for additional dependencies
        print("\n📦 Additional Dependencies (optional)")
        additional_deps = []
        while True:
            dep = input("Enter dependency (or press Enter to finish): ").strip()
            if not dep:
                break
            additional_deps.append(dep)
            print(f"  ✅ Added: {dep}")
        
        # Ask for environment variables
        print("\n🔧 Environment Variables (optional)")
        env_vars = {}
        while True:
            var_input = input("Enter environment variable (KEY=VALUE or press Enter to finish): ").strip()
            if not var_input:
                break
            
            if '=' in var_input:
                key, value = var_input.split('=', 1)
                env_vars[key.strip()] = value.strip()
                print(f"  ✅ Added: {key.strip()}={value.strip()}")
            else:
                print("❌ Please use format: KEY=VALUE")
        
        return ProjectConfig(
            name=project_name,
            template_id=template.id,
            output_directory=output_dir,
            custom_settings=custom_settings,
            environment_variables=env_vars,
            additional_dependencies=additional_deps
        )
    
    def _confirm_configuration(self, config: ProjectConfig, template: ServerTemplate) -> bool:
        """Show configuration summary and ask for confirmation."""
        print("\n📋 Configuration Summary")
        print("=" * 40)
        print(f"Project Name: {config.name}")
        print(f"Template: {template.name}")
        print(f"Output Directory: {config.output_directory}")
        
        if config.custom_settings:
            print("\nCustom Settings:")
            for key, value in config.custom_settings.items():
                print(f"  {key}: {value}")
        
        if config.additional_dependencies:
            print("\nAdditional Dependencies:")
            for dep in config.additional_dependencies:
                print(f"  - {dep}")
        
        if config.environment_variables:
            print("\nEnvironment Variables:")
            for key, value in config.environment_variables.items():
                print(f"  {key}: {value}")
        
        print("\nTemplate Dependencies:")
        for dep in template.dependencies:
            print(f"  - {dep}")
        
        print("\nBuild Commands:")
        for cmd in template.build_commands:
            print(f"  - {cmd}")
        
        print("=" * 40)
        
        while True:
            try:
                confirm = input("Create project with this configuration? [Y/n]: ").strip().lower()
                if confirm in ('', 'y', 'yes'):
                    return True
                elif confirm in ('n', 'no'):
                    return False
                else:
                    print("❌ Please enter 'y' for yes or 'n' for no")
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled.")
                return False