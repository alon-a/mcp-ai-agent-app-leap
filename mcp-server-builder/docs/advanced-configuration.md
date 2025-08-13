# Advanced Configuration and Customization

This guide covers advanced configuration patterns, customization techniques, and best practices for the MCP Server Builder.

## Advanced Configuration Patterns

### 1. Environment-Specific Configurations

Create different configurations for development, staging, and production environments.

#### Development Configuration

```python
dev_config = {
    'output_directory': './dev-servers',
    'custom_settings': {
        'server_name': 'Development Server',
        'description': 'Development environment server',
        'transport': 'stdio',
        'enable_debug': True,
        'enable_hot_reload': True,
        'log_level': 'DEBUG'
    },
    'environment_variables': {
        'ENVIRONMENT': 'development',
        'DEBUG': 'true',
        'DATABASE_URL': 'sqlite:///dev.db',
        'CACHE_TTL': '60',  # Short cache for development
        'RATE_LIMIT_ENABLED': 'false'
    },
    'additional_dependencies': [
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'black>=23.0.0',
        'flake8>=6.0.0'
    ]
}
```

#### Staging Configuration

```python
staging_config = {
    'output_directory': './staging-servers',
    'custom_settings': {
        'server_name': 'Staging Server',
        'description': 'Staging environment server',
        'transport': 'http',
        'host': '0.0.0.0',
        'port': 8080,
        'enable_metrics': True,
        'enable_health_check': True,
        'log_level': 'INFO'
    },
    'environment_variables': {
        'ENVIRONMENT': 'staging',
        'DEBUG': 'false',
        'DATABASE_URL': 'postgresql://user:pass@staging-db:5432/app',
        'REDIS_URL': 'redis://staging-redis:6379/0',
        'CACHE_TTL': '300',
        'RATE_LIMIT_ENABLED': 'true',
        'RATE_LIMIT_REQUESTS': '100',
        'RATE_LIMIT_WINDOW': '60'
    },
    'additional_dependencies': [
        'gunicorn>=21.0.0',
        'prometheus-client>=0.17.0',
        'redis>=4.5.0',
        'psycopg2-binary>=2.9.0'
    ]
}
```

#### Production Configuration

```python
production_config = {
    'output_directory': '/opt/mcp-servers',
    'custom_settings': {
        'server_name': 'Production Server',
        'description': 'Production environment server',
        'transport': 'http',
        'host': '0.0.0.0',
        'port': 8080,
        'enable_metrics': True,
        'enable_health_check': True,
        'enable_security_headers': True,
        'enable_request_logging': True,
        'log_level': 'WARNING'
    },
    'environment_variables': {
        'ENVIRONMENT': 'production',
        'DEBUG': 'false',
        'DATABASE_URL': 'postgresql://user:pass@prod-db:5432/app',
        'REDIS_URL': 'redis://prod-redis:6379/0',
        'CACHE_TTL': '3600',
        'RATE_LIMIT_ENABLED': 'true',
        'RATE_LIMIT_REQUESTS': '1000',
        'RATE_LIMIT_WINDOW': '3600',
        'SSL_CERT_PATH': '/etc/ssl/certs/server.crt',
        'SSL_KEY_PATH': '/etc/ssl/private/server.key'
    },
    'additional_dependencies': [
        'gunicorn>=21.0.0',
        'prometheus-client>=0.17.0',
        'redis>=4.5.0',
        'psycopg2-binary>=2.9.0',
        'cryptography>=41.0.0',
        'sentry-sdk>=1.32.0'
    ]
}
```

### 2. Multi-Service Architecture Configuration

Configure servers for microservices architecture with service discovery and load balancing.

```python
microservice_config = {
    'custom_settings': {
        'server_name': 'User Service',
        'description': 'User management microservice',
        'transport': 'http',
        'host': '0.0.0.0',
        'port': 8001,
        'service_discovery': {
            'enabled': True,
            'consul_host': 'consul.service.consul',
            'consul_port': 8500,
            'service_name': 'user-service',
            'health_check_interval': 30
        },
        'load_balancer': {
            'enabled': True,
            'strategy': 'round_robin',
            'health_check_path': '/health'
        }
    },
    'environment_variables': {
        'SERVICE_NAME': 'user-service',
        'SERVICE_VERSION': '1.0.0',
        'CONSUL_HOST': 'consul.service.consul',
        'CONSUL_PORT': '8500',
        'DATABASE_URL': 'postgresql://user:pass@user-db:5432/users',
        'MESSAGE_QUEUE_URL': 'amqp://guest:guest@rabbitmq:5672/',
        'TRACING_ENDPOINT': 'http://jaeger:14268/api/traces'
    },
    'additional_dependencies': [
        'consul-python>=1.1.0',
        'pika>=1.3.0',
        'opentelemetry-api>=1.20.0',
        'opentelemetry-sdk>=1.20.0',
        'opentelemetry-instrumentation-fastapi>=0.41b0'
    ]
}
```

### 3. High-Performance Configuration

Optimize for high-throughput scenarios with connection pooling and caching.

```python
high_performance_config = {
    'custom_settings': {
        'server_name': 'High Performance Server',
        'description': 'Optimized for high throughput',
        'transport': 'http',
        'host': '0.0.0.0',
        'port': 8080,
        'workers': 4,
        'worker_class': 'uvicorn.workers.UvicornWorker',
        'max_connections': 1000,
        'connection_pool_size': 20,
        'enable_compression': True,
        'compression_level': 6,
        'enable_caching': True,
        'cache_backend': 'redis'
    },
    'environment_variables': {
        'WORKERS': '4',
        'MAX_CONNECTIONS': '1000',
        'CONNECTION_POOL_SIZE': '20',
        'DATABASE_POOL_SIZE': '20',
        'DATABASE_MAX_OVERFLOW': '30',
        'REDIS_POOL_SIZE': '10',
        'CACHE_DEFAULT_TTL': '3600',
        'ENABLE_QUERY_CACHE': 'true',
        'ENABLE_RESULT_COMPRESSION': 'true'
    },
    'additional_dependencies': [
        'uvicorn[standard]>=0.23.0',
        'gunicorn>=21.0.0',
        'redis[hiredis]>=4.5.0',
        'sqlalchemy[asyncio]>=2.0.0',
        'asyncpg>=0.28.0',
        'orjson>=3.9.0',
        'lz4>=4.3.0'
    ]
}
```

## Custom Template Configurations

### 1. Feature Flag Configuration

Enable/disable features based on configuration flags.

```python
feature_flag_config = {
    'custom_settings': {
        'server_name': 'Feature Flag Server',
        'features': {
            'authentication': {
                'enabled': True,
                'provider': 'oauth2',
                'jwt_secret': '{{JWT_SECRET}}',
                'token_expiry': 3600
            },
            'rate_limiting': {
                'enabled': True,
                'strategy': 'sliding_window',
                'requests_per_minute': 60,
                'burst_size': 10
            },
            'caching': {
                'enabled': True,
                'backend': 'redis',
                'default_ttl': 300,
                'max_memory': '100mb'
            },
            'monitoring': {
                'enabled': True,
                'metrics_port': 9090,
                'tracing_enabled': True,
                'log_sampling_rate': 0.1
            },
            'database': {
                'read_replicas': True,
                'connection_pooling': True,
                'query_timeout': 30,
                'slow_query_threshold': 1.0
            }
        }
    },
    'environment_variables': {
        'JWT_SECRET': 'your-jwt-secret-key',
        'OAUTH2_CLIENT_ID': 'your-oauth2-client-id',
        'OAUTH2_CLIENT_SECRET': 'your-oauth2-client-secret',
        'REDIS_URL': 'redis://localhost:6379/0',
        'DATABASE_READ_URL': 'postgresql://readonly:pass@read-db:5432/app',
        'DATABASE_WRITE_URL': 'postgresql://readwrite:pass@write-db:5432/app'
    }
}
```

### 2. Plugin-Based Configuration

Configure servers with pluggable components.

```python
plugin_config = {
    'custom_settings': {
        'server_name': 'Plugin-Based Server',
        'plugins': {
            'authentication': {
                'plugin': 'jwt_auth',
                'config': {
                    'secret_key': '{{JWT_SECRET}}',
                    'algorithm': 'HS256',
                    'expiration': 3600
                }
            },
            'storage': {
                'plugin': 'postgresql_storage',
                'config': {
                    'connection_string': '{{DATABASE_URL}}',
                    'pool_size': 10,
                    'max_overflow': 20
                }
            },
            'cache': {
                'plugin': 'redis_cache',
                'config': {
                    'url': '{{REDIS_URL}}',
                    'default_ttl': 300,
                    'key_prefix': 'mcp:'
                }
            },
            'messaging': {
                'plugin': 'rabbitmq_messaging',
                'config': {
                    'url': '{{RABBITMQ_URL}}',
                    'exchange': 'mcp_events',
                    'queue_prefix': 'mcp_'
                }
            }
        }
    },
    'additional_dependencies': [
        'pyjwt>=2.8.0',
        'sqlalchemy>=2.0.0',
        'redis>=4.5.0',
        'pika>=1.3.0',
        'pluggy>=1.3.0'
    ]
}
```

## Dynamic Configuration Loading

### 1. Configuration from External Sources

Load configuration from external sources like Consul, etcd, or cloud services.

```python
def load_config_from_consul(consul_host: str, consul_port: int, service_name: str) -> dict:
    """Load configuration from Consul KV store."""
    import consul
    
    c = consul.Consul(host=consul_host, port=consul_port)
    
    # Get configuration from Consul
    config_key = f"services/{service_name}/config"
    _, config_data = c.kv.get(config_key)
    
    if config_data:
        import json
        return json.loads(config_data['Value'].decode('utf-8'))
    
    return {}

def load_config_from_aws_ssm(parameter_name: str) -> dict:
    """Load configuration from AWS Systems Manager Parameter Store."""
    import boto3
    import json
    
    ssm = boto3.client('ssm')
    
    try:
        response = ssm.get_parameter(
            Name=parameter_name,
            WithDecryption=True
        )
        return json.loads(response['Parameter']['Value'])
    except Exception as e:
        print(f"Failed to load config from SSM: {e}")
        return {}

# Usage example
consul_config = load_config_from_consul('consul.service.consul', 8500, 'mcp-server')
aws_config = load_config_from_aws_ssm('/mcp-server/production/config')

# Merge configurations
final_config = {**consul_config, **aws_config}
```

### 2. Configuration Validation and Schema

Validate configuration against schemas to ensure correctness.

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List

class DatabaseConfig(BaseModel):
    url: str
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=200)
    timeout: int = Field(default=30, ge=1, le=300)

class CacheConfig(BaseModel):
    backend: str = Field(default='redis')
    url: str
    default_ttl: int = Field(default=300, ge=1)
    max_memory: str = Field(default='100mb')

class SecurityConfig(BaseModel):
    enable_https: bool = Field(default=False)
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    cors_origins: List[str] = Field(default_factory=list)
    
    @validator('ssl_cert_path')
    def validate_ssl_cert(cls, v, values):
        if values.get('enable_https') and not v:
            raise ValueError('SSL certificate path required when HTTPS is enabled')
        return v

class ServerConfig(BaseModel):
    server_name: str
    description: str
    host: str = Field(default='0.0.0.0')
    port: int = Field(default=8080, ge=1024, le=65535)
    workers: int = Field(default=1, ge=1, le=32)
    database: DatabaseConfig
    cache: CacheConfig
    security: SecurityConfig
    features: Dict[str, Any] = Field(default_factory=dict)

def validate_and_create_project(config_dict: dict) -> dict:
    """Validate configuration and create project."""
    try:
        # Validate configuration
        validated_config = ServerConfig(**config_dict)
        
        # Convert back to dict for project creation
        return validated_config.dict()
        
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")

# Usage
config_dict = {
    'server_name': 'Validated Server',
    'description': 'Server with validated configuration',
    'database': {
        'url': 'postgresql://user:pass@localhost/db',
        'pool_size': 15
    },
    'cache': {
        'url': 'redis://localhost:6379/0'
    },
    'security': {
        'enable_https': True,
        'ssl_cert_path': '/etc/ssl/certs/server.crt',
        'ssl_key_path': '/etc/ssl/private/server.key',
        'cors_origins': ['https://myapp.com']
    }
}

validated_config = validate_and_create_project(config_dict)
```

## Advanced Customization Techniques

### 1. Custom File Generation

Generate custom files based on configuration.

```python
def generate_custom_files(project_path: str, config: dict) -> List[str]:
    """Generate custom configuration files."""
    import os
    import json
    import yaml
    from pathlib import Path
    
    generated_files = []
    project_dir = Path(project_path)
    
    # Generate Docker Compose file
    if config.get('enable_docker'):
        docker_compose = {
            'version': '3.8',
            'services': {
                'mcp-server': {
                    'build': '.',
                    'ports': [f"{config.get('port', 8080)}:8080"],
                    'environment': config.get('environment_variables', {}),
                    'depends_on': []
                }
            }
        }
        
        # Add database service if configured
        if 'database' in config:
            docker_compose['services']['postgres'] = {
                'image': 'postgres:15',
                'environment': {
                    'POSTGRES_DB': 'app',
                    'POSTGRES_USER': 'user',
                    'POSTGRES_PASSWORD': 'password'
                },
                'volumes': ['postgres_data:/var/lib/postgresql/data']
            }
            docker_compose['services']['mcp-server']['depends_on'].append('postgres')
            docker_compose['volumes'] = {'postgres_data': {}}
        
        # Add Redis service if configured
        if 'cache' in config:
            docker_compose['services']['redis'] = {
                'image': 'redis:7-alpine',
                'volumes': ['redis_data:/data']
            }
            docker_compose['services']['mcp-server']['depends_on'].append('redis')
            if 'volumes' not in docker_compose:
                docker_compose['volumes'] = {}
            docker_compose['volumes']['redis_data'] = {}
        
        compose_file = project_dir / 'docker-compose.yml'
        with open(compose_file, 'w') as f:
            yaml.dump(docker_compose, f, default_flow_style=False)
        generated_files.append(str(compose_file))
    
    # Generate Kubernetes manifests
    if config.get('enable_kubernetes'):
        k8s_dir = project_dir / 'k8s'
        k8s_dir.mkdir(exist_ok=True)
        
        # Deployment manifest
        deployment = {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': config['server_name'].lower().replace(' ', '-'),
                'labels': {'app': config['server_name'].lower().replace(' ', '-')}
            },
            'spec': {
                'replicas': config.get('replicas', 3),
                'selector': {
                    'matchLabels': {'app': config['server_name'].lower().replace(' ', '-')}
                },
                'template': {
                    'metadata': {
                        'labels': {'app': config['server_name'].lower().replace(' ', '-')}
                    },
                    'spec': {
                        'containers': [{
                            'name': 'mcp-server',
                            'image': f"{config['server_name'].lower().replace(' ', '-')}:latest",
                            'ports': [{'containerPort': config.get('port', 8080)}],
                            'env': [
                                {'name': k, 'value': v} 
                                for k, v in config.get('environment_variables', {}).items()
                            ]
                        }]
                    }
                }
            }
        }
        
        deployment_file = k8s_dir / 'deployment.yaml'
        with open(deployment_file, 'w') as f:
            yaml.dump(deployment, f, default_flow_style=False)
        generated_files.append(str(deployment_file))
        
        # Service manifest
        service = {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': f"{config['server_name'].lower().replace(' ', '-')}-service"
            },
            'spec': {
                'selector': {'app': config['server_name'].lower().replace(' ', '-')},
                'ports': [{
                    'protocol': 'TCP',
                    'port': 80,
                    'targetPort': config.get('port', 8080)
                }],
                'type': 'ClusterIP'
            }
        }
        
        service_file = k8s_dir / 'service.yaml'
        with open(service_file, 'w') as f:
            yaml.dump(service, f, default_flow_style=False)
        generated_files.append(str(service_file))
    
    # Generate monitoring configuration
    if config.get('enable_monitoring'):
        monitoring_dir = project_dir / 'monitoring'
        monitoring_dir.mkdir(exist_ok=True)
        
        # Prometheus configuration
        prometheus_config = {
            'global': {
                'scrape_interval': '15s'
            },
            'scrape_configs': [{
                'job_name': 'mcp-server',
                'static_configs': [{
                    'targets': [f"localhost:{config.get('metrics_port', 9090)}"]
                }]
            }]
        }
        
        prometheus_file = monitoring_dir / 'prometheus.yml'
        with open(prometheus_file, 'w') as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        generated_files.append(str(prometheus_file))
        
        # Grafana dashboard
        dashboard = {
            'dashboard': {
                'title': f"{config['server_name']} Dashboard",
                'panels': [
                    {
                        'title': 'Request Rate',
                        'type': 'graph',
                        'targets': [{
                            'expr': 'rate(http_requests_total[5m])',
                            'legendFormat': 'Requests/sec'
                        }]
                    },
                    {
                        'title': 'Response Time',
                        'type': 'graph',
                        'targets': [{
                            'expr': 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))',
                            'legendFormat': '95th percentile'
                        }]
                    }
                ]
            }
        }
        
        dashboard_file = monitoring_dir / 'dashboard.json'
        with open(dashboard_file, 'w') as f:
            json.dump(dashboard, f, indent=2)
        generated_files.append(str(dashboard_file))
    
    return generated_files

# Usage in project creation
def create_advanced_project(name: str, template: str, config: dict):
    """Create project with advanced customizations."""
    from mcp_server_builder.managers.project_manager import ProjectManagerImpl
    
    manager = ProjectManagerImpl()
    
    # Create base project
    result = manager.create_project(name, template, config)
    
    if result.success:
        # Generate additional custom files
        custom_files = generate_custom_files(result.project_path, config)
        print(f"Generated {len(custom_files)} custom files:")
        for file_path in custom_files:
            print(f"  - {file_path}")
    
    return result
```

### 2. Post-Creation Hooks

Execute custom logic after project creation.

```python
def setup_git_repository(project_path: str, config: dict):
    """Initialize Git repository with proper configuration."""
    import subprocess
    import os
    
    os.chdir(project_path)
    
    # Initialize Git repository
    subprocess.run(['git', 'init'], check=True)
    
    # Create .gitignore
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv/
pip-log.txt
pip-delete-this-directory.txt

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite

# Build artifacts
dist/
build/
*.egg-info/

# Docker
.dockerignore
"""
    
    with open('.gitignore', 'w') as f:
        f.write(gitignore_content.strip())
    
    # Initial commit
    subprocess.run(['git', 'add', '.'], check=True)
    subprocess.run(['git', 'commit', '-m', 'Initial commit'], check=True)
    
    # Set up remote if specified
    if 'git_remote' in config:
        subprocess.run(['git', 'remote', 'add', 'origin', config['git_remote']], check=True)

def setup_ci_cd(project_path: str, config: dict):
    """Set up CI/CD pipeline configuration."""
    import os
    from pathlib import Path
    
    project_dir = Path(project_path)
    
    # GitHub Actions
    if config.get('ci_provider') == 'github':
        github_dir = project_dir / '.github' / 'workflows'
        github_dir.mkdir(parents=True, exist_ok=True)
        
        workflow = """
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e .
        pip install pytest pytest-cov
    
    - name: Run tests
      run: |
        pytest --cov=src tests/
    
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker image
      run: |
        docker build -t ${{ github.repository }}:${{ github.sha }} .
        docker tag ${{ github.repository }}:${{ github.sha }} ${{ github.repository }}:latest
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push ${{ github.repository }}:${{ github.sha }}
        docker push ${{ github.repository }}:latest

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to production
      run: |
        # Add deployment commands here
        echo "Deploying to production..."
"""
        
        with open(github_dir / 'ci.yml', 'w') as f:
            f.write(workflow.strip())

def run_post_creation_hooks(project_path: str, config: dict):
    """Run all post-creation hooks."""
    hooks = config.get('post_creation_hooks', [])
    
    for hook in hooks:
        if hook == 'git':
            setup_git_repository(project_path, config)
        elif hook == 'ci_cd':
            setup_ci_cd(project_path, config)
        elif callable(hook):
            hook(project_path, config)

# Enhanced project creation with hooks
def create_project_with_hooks(name: str, template: str, config: dict):
    """Create project with post-creation hooks."""
    from mcp_server_builder.managers.project_manager import ProjectManagerImpl
    
    manager = ProjectManagerImpl()
    
    # Create base project
    result = manager.create_project(name, template, config)
    
    if result.success:
        # Run post-creation hooks
        run_post_creation_hooks(result.project_path, config)
        
        # Generate custom files
        if config.get('generate_custom_files'):
            custom_files = generate_custom_files(result.project_path, config)
            result.created_files.extend(custom_files)
    
    return result
```

## Configuration Management Best Practices

### 1. Configuration Hierarchy

Implement a configuration hierarchy with proper precedence.

```python
import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any

class ConfigManager:
    """Manages configuration from multiple sources with proper precedence."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.config = {}
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from multiple sources in order of precedence."""
        
        # 1. Default configuration (lowest precedence)
        self._load_defaults()
        
        # 2. Configuration files
        self._load_config_files()
        
        # 3. Environment variables
        self._load_environment_variables()
        
        # 4. Command line arguments (highest precedence)
        self._load_command_line_args()
        
        return self.config
    
    def _load_defaults(self):
        """Load default configuration values."""
        self.config.update({
            'server_name': f'Default {self.service_name}',
            'host': '0.0.0.0',
            'port': 8080,
            'log_level': 'INFO',
            'debug': False,
            'workers': 1
        })
    
    def _load_config_files(self):
        """Load configuration from files."""
        config_paths = [
            f'/etc/{self.service_name}/config.yaml',
            f'~/.{self.service_name}/config.yaml',
            './config.yaml',
            './config.json'
        ]
        
        for config_path in config_paths:
            path = Path(config_path).expanduser()
            if path.exists():
                try:
                    with open(path) as f:
                        if path.suffix.lower() in ['.yaml', '.yml']:
                            file_config = yaml.safe_load(f)
                        else:
                            file_config = json.load(f)
                    
                    self.config.update(file_config)
                    print(f"Loaded config from: {path}")
                except Exception as e:
                    print(f"Failed to load config from {path}: {e}")
    
    def _load_environment_variables(self):
        """Load configuration from environment variables."""
        env_prefix = f"{self.service_name.upper()}_"
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower()
                
                # Try to parse as JSON for complex values
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    # Handle boolean values
                    if value.lower() in ('true', 'false'):
                        parsed_value = value.lower() == 'true'
                    # Handle numeric values
                    elif value.isdigit():
                        parsed_value = int(value)
                    elif value.replace('.', '').isdigit():
                        parsed_value = float(value)
                    else:
                        parsed_value = value
                
                self.config[config_key] = parsed_value
    
    def _load_command_line_args(self):
        """Load configuration from command line arguments."""
        import sys
        import argparse
        
        parser = argparse.ArgumentParser()
        parser.add_argument('--host', help='Server host')
        parser.add_argument('--port', type=int, help='Server port')
        parser.add_argument('--log-level', help='Log level')
        parser.add_argument('--debug', action='store_true', help='Enable debug mode')
        parser.add_argument('--config', help='Configuration file path')
        
        args, _ = parser.parse_known_args()
        
        # Update config with non-None command line arguments
        for key, value in vars(args).items():
            if value is not None:
                self.config[key.replace('-', '_')] = value

# Usage
config_manager = ConfigManager('mcp-server')
final_config = config_manager.load_config()
```

### 2. Configuration Validation and Type Safety

Implement robust configuration validation.

```python
from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class TransportType(str, Enum):
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"

class DatabaseConfig(BaseModel):
    url: str = Field(..., description="Database connection URL")
    pool_size: int = Field(default=10, ge=1, le=100)
    max_overflow: int = Field(default=20, ge=0, le=200)
    timeout: int = Field(default=30, ge=1, le=300)
    echo: bool = Field(default=False, description="Enable SQL query logging")
    
    @validator('url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'mysql://', 'sqlite:///')):
            raise ValueError('Unsupported database URL scheme')
        return v

class CacheConfig(BaseModel):
    backend: str = Field(default='memory', regex='^(memory|redis|memcached)$')
    url: Optional[str] = None
    default_ttl: int = Field(default=300, ge=1)
    max_size: int = Field(default=1000, ge=1)
    
    @root_validator
    def validate_cache_config(cls, values):
        backend = values.get('backend')
        url = values.get('url')
        
        if backend in ('redis', 'memcached') and not url:
            raise ValueError(f'{backend} backend requires URL')
        
        return values

class SecurityConfig(BaseModel):
    enable_https: bool = Field(default=False)
    ssl_cert_path: Optional[str] = None
    ssl_key_path: Optional[str] = None
    cors_enabled: bool = Field(default=False)
    cors_origins: List[str] = Field(default_factory=list)
    rate_limiting: bool = Field(default=False)
    rate_limit_requests: int = Field(default=100, ge=1)
    rate_limit_window: int = Field(default=60, ge=1)
    
    @root_validator
    def validate_ssl_config(cls, values):
        enable_https = values.get('enable_https')
        ssl_cert_path = values.get('ssl_cert_path')
        ssl_key_path = values.get('ssl_key_path')
        
        if enable_https and (not ssl_cert_path or not ssl_key_path):
            raise ValueError('SSL certificate and key paths required for HTTPS')
        
        return values

class MonitoringConfig(BaseModel):
    enabled: bool = Field(default=False)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    health_check_enabled: bool = Field(default=True)
    tracing_enabled: bool = Field(default=False)
    tracing_endpoint: Optional[str] = None
    log_sampling_rate: float = Field(default=1.0, ge=0.0, le=1.0)

class ServerConfig(BaseModel):
    # Basic server configuration
    server_name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)
    version: str = Field(default="1.0.0", regex=r'^\d+\.\d+\.\d+$')
    
    # Network configuration
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8080, ge=1024, le=65535)
    transport: TransportType = Field(default=TransportType.STDIO)
    
    # Runtime configuration
    workers: int = Field(default=1, ge=1, le=32)
    max_connections: int = Field(default=1000, ge=1)
    timeout: int = Field(default=30, ge=1, le=300)
    
    # Logging configuration
    log_level: LogLevel = Field(default=LogLevel.INFO)
    log_file: Optional[str] = None
    debug: bool = Field(default=False)
    
    # Component configurations
    database: Optional[DatabaseConfig] = None
    cache: Optional[CacheConfig] = None
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Feature flags
    features: Dict[str, Any] = Field(default_factory=dict)
    
    # Environment-specific settings
    environment: str = Field(default="development", regex='^(development|staging|production)$')
    
    @validator('host')
    def validate_host(cls, v):
        import ipaddress
        try:
            ipaddress.ip_address(v)
        except ValueError:
            # Allow hostnames
            if not v.replace('.', '').replace('-', '').isalnum():
                raise ValueError('Invalid host format')
        return v
    
    @root_validator
    def validate_transport_config(cls, values):
        transport = values.get('transport')
        port = values.get('port')
        
        if transport == TransportType.STDIO and port != 8080:
            # STDIO doesn't use network ports, but we allow port config for consistency
            pass
        
        return values

def validate_and_normalize_config(config_dict: Dict[str, Any]) -> ServerConfig:
    """Validate and normalize configuration."""
    try:
        return ServerConfig(**config_dict)
    except Exception as e:
        raise ValueError(f"Configuration validation failed: {e}")

# Usage example
config_dict = {
    'server_name': 'My MCP Server',
    'description': 'A well-configured MCP server',
    'host': '0.0.0.0',
    'port': 8080,
    'transport': 'http',
    'workers': 4,
    'log_level': 'INFO',
    'database': {
        'url': 'postgresql://user:pass@localhost/db',
        'pool_size': 20
    },
    'cache': {
        'backend': 'redis',
        'url': 'redis://localhost:6379/0',
        'default_ttl': 600
    },
    'security': {
        'cors_enabled': True,
        'cors_origins': ['https://myapp.com'],
        'rate_limiting': True,
        'rate_limit_requests': 1000
    },
    'monitoring': {
        'enabled': True,
        'metrics_port': 9090,
        'tracing_enabled': True
    }
}

# Validate configuration
validated_config = validate_and_normalize_config(config_dict)
print(f"Validated configuration: {validated_config.dict()}")
```

This advanced configuration guide provides comprehensive patterns for creating sophisticated, production-ready MCP servers with proper configuration management, validation, and customization capabilities.