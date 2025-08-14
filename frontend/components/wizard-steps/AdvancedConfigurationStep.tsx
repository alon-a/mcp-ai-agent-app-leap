import React, { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Plus, 
  Trash2, 
  Settings, 
  Cloud, 
  Database,
  Key,
  Package,
  Code,
  Info,
  AlertCircle,
  Lightbulb
} from 'lucide-react';
import { AdvancedConfiguration } from '../AdvancedBuildWizard';

interface AdvancedConfigurationStepProps {
  configuration: AdvancedConfiguration;
  onChange: (config: AdvancedConfiguration) => void;
  errors?: string[];
  warnings?: string[];
  showAdvanced?: boolean;
  onToggleAdvanced?: () => void;
}

// Cloud provider options
const cloudProviders = [
  { id: 'aws', name: 'Amazon Web Services', icon: '☁️' },
  { id: 'gcp', name: 'Google Cloud Platform', icon: '🌐' },
  { id: 'azure', name: 'Microsoft Azure', icon: '🔷' },
];

// Deployment target options
const deploymentTargets = [
  { 
    id: 'local', 
    name: 'Local Development', 
    description: 'Run locally for development and testing',
    icon: '💻'
  },
  { 
    id: 'cloud', 
    name: 'Cloud Deployment', 
    description: 'Deploy to cloud platforms with managed services',
    icon: '☁️'
  },
  { 
    id: 'kubernetes', 
    name: 'Kubernetes Cluster', 
    description: 'Deploy to Kubernetes for orchestrated scaling',
    icon: '⚙️'
  },
];

// Common environment variables
const commonEnvVars = [
  { key: 'NODE_ENV', value: 'production', description: 'Application environment' },
  { key: 'PORT', value: '8080', description: 'Server port' },
  { key: 'LOG_LEVEL', value: 'info', description: 'Logging level' },
  { key: 'DATABASE_URL', value: '', description: 'Database connection string' },
  { key: 'REDIS_URL', value: '', description: 'Redis cache connection' },
  { key: 'API_KEY', value: '', description: 'External API key' },
];

// Common dependencies by language
const commonDependencies = {
  python: [
    'requests', 'pydantic', 'python-dotenv', 'uvicorn', 'fastapi',
    'sqlalchemy', 'redis', 'prometheus-client', 'structlog'
  ],
  typescript: [
    'express', 'cors', 'helmet', 'dotenv', 'winston', 'joi',
    'redis', 'pg', 'mongoose', 'axios'
  ],
  go: [
    'github.com/gin-gonic/gin', 'github.com/joho/godotenv',
    'github.com/sirupsen/logrus', 'github.com/go-redis/redis/v8',
    'gorm.io/gorm', 'github.com/prometheus/client_golang'
  ],
  rust: [
    'tokio', 'serde', 'serde_json', 'reqwest', 'dotenv',
    'tracing', 'redis', 'sqlx', 'prometheus'
  ],
  java: [
    'org.springframework.boot:spring-boot-starter-web',
    'org.springframework.boot:spring-boot-starter-data-jpa',
    'org.springframework.boot:spring-boot-starter-cache',
    'io.micrometer:micrometer-registry-prometheus'
  ],
};

export const AdvancedConfigurationStep: React.FC<AdvancedConfigurationStepProps> = ({
  configuration,
  onChange,
  errors = [],
  warnings = [],
  showAdvanced = false,
  onToggleAdvanced,
}) => {
  const [newEnvKey, setNewEnvKey] = useState('');
  const [newEnvValue, setNewEnvValue] = useState('');
  const [newDependency, setNewDependency] = useState('');
  const [customSettingsJson, setCustomSettingsJson] = useState(
    JSON.stringify(configuration.customSettings, null, 2)
  );

  const handleDeploymentTargetChange = (target: 'local' | 'cloud' | 'kubernetes') => {
    const newConfig = {
      ...configuration,
      deploymentTarget: target,
    };
    
    // Clear cloud provider if not cloud deployment
    if (target !== 'cloud') {
      newConfig.cloudProvider = undefined;
    }
    
    onChange(newConfig);
  };

  const handleCloudProviderChange = (provider: 'aws' | 'gcp' | 'azure') => {
    onChange({
      ...configuration,
      cloudProvider: provider,
    });
  };

  const handleAddEnvVar = () => {
    if (newEnvKey && newEnvValue) {
      onChange({
        ...configuration,
        environmentVariables: {
          ...configuration.environmentVariables,
          [newEnvKey]: newEnvValue,
        },
      });
      setNewEnvKey('');
      setNewEnvValue('');
    }
  };

  const handleRemoveEnvVar = (key: string) => {
    const newEnvVars = { ...configuration.environmentVariables };
    delete newEnvVars[key];
    onChange({
      ...configuration,
      environmentVariables: newEnvVars,
    });
  };

  const handleUpdateEnvVar = (key: string, value: string) => {
    onChange({
      ...configuration,
      environmentVariables: {
        ...configuration.environmentVariables,
        [key]: value,
      },
    });
  };

  const handleAddCommonEnvVar = (envVar: { key: string; value: string }) => {
    onChange({
      ...configuration,
      environmentVariables: {
        ...configuration.environmentVariables,
        [envVar.key]: envVar.value,
      },
    });
  };

  const handleAddDependency = () => {
    if (newDependency && !configuration.additionalDependencies.includes(newDependency)) {
      onChange({
        ...configuration,
        additionalDependencies: [...configuration.additionalDependencies, newDependency],
      });
      setNewDependency('');
    }
  };

  const handleRemoveDependency = (dependency: string) => {
    onChange({
      ...configuration,
      additionalDependencies: configuration.additionalDependencies.filter(d => d !== dependency),
    });
  };

  const handleAddCommonDependency = (dependency: string) => {
    if (!configuration.additionalDependencies.includes(dependency)) {
      onChange({
        ...configuration,
        additionalDependencies: [...configuration.additionalDependencies, dependency],
      });
    }
  };

  const handleCustomSettingsChange = (value: string) => {
    setCustomSettingsJson(value);
    try {
      const parsed = JSON.parse(value);
      onChange({
        ...configuration,
        customSettings: parsed,
      });
    } catch (error) {
      // Invalid JSON, don't update configuration
    }
  };

  const isValidJson = (str: string) => {
    try {
      JSON.parse(str);
      return true;
    } catch {
      return false;
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Advanced Configuration
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Fine-tune your MCP server with custom environment variables, dependencies, and deployment settings.
        </p>
      </div>

      <Tabs defaultValue="deployment" className="w-full">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="deployment">Deployment</TabsTrigger>
          <TabsTrigger value="environment">Environment</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
          <TabsTrigger value="custom">Custom Settings</TabsTrigger>
        </TabsList>

        {/* Deployment Configuration */}
        <TabsContent value="deployment" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Cloud className="h-5 w-5 text-blue-500" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Deployment Target
              </h3>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {deploymentTargets.map((target) => (
                <Card
                  key={target.id}
                  className={`
                    p-4 cursor-pointer transition-all border-2
                    ${configuration.deploymentTarget === target.id 
                      ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                      : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }
                  `}
                  onClick={() => handleDeploymentTargetChange(target.id as any)}
                >
                  <div className="text-center">
                    <div className="text-2xl mb-2">{target.icon}</div>
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                      {target.name}
                    </h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {target.description}
                    </p>
                  </div>
                </Card>
              ))}
            </div>

            {/* Cloud Provider Selection */}
            {configuration.deploymentTarget === 'cloud' && (
              <div>
                <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-3">
                  Cloud Provider
                </h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {cloudProviders.map((provider) => (
                    <Card
                      key={provider.id}
                      className={`
                        p-4 cursor-pointer transition-all border-2
                        ${configuration.cloudProvider === provider.id 
                          ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                        }
                      `}
                      onClick={() => handleCloudProviderChange(provider.id as any)}
                    >
                      <div className="text-center">
                        <div className="text-2xl mb-2">{provider.icon}</div>
                        <h5 className="font-medium text-gray-900 dark:text-gray-100">
                          {provider.name}
                        </h5>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Environment Variables */}
        <TabsContent value="environment" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Key className="h-5 w-5 text-green-500" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Environment Variables
              </h3>
            </div>

            {/* Common Environment Variables */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                Common Variables
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {commonEnvVars.map((envVar) => (
                  <Button
                    key={envVar.key}
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddCommonEnvVar(envVar)}
                    disabled={configuration.environmentVariables.hasOwnProperty(envVar.key)}
                    className="justify-start h-auto p-2"
                  >
                    <div className="text-left">
                      <div className="font-medium">{envVar.key}</div>
                      <div className="text-xs text-gray-500">{envVar.description}</div>
                    </div>
                  </Button>
                ))}
              </div>
            </div>

            {/* Add New Environment Variable */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                Add Custom Variable
              </h4>
              <div className="flex space-x-2">
                <Input
                  placeholder="Variable name (e.g., API_KEY)"
                  value={newEnvKey}
                  onChange={(e) => setNewEnvKey(e.target.value)}
                  className="flex-1"
                />
                <Input
                  placeholder="Value"
                  value={newEnvValue}
                  onChange={(e) => setNewEnvValue(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleAddEnvVar} disabled={!newEnvKey || !newEnvValue}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Current Environment Variables */}
            {Object.keys(configuration.environmentVariables).length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                  Configured Variables ({Object.keys(configuration.environmentVariables).length})
                </h4>
                <div className="space-y-2">
                  {Object.entries(configuration.environmentVariables).map(([key, value]) => (
                    <div key={key} className="flex items-center space-x-2 p-3 bg-gray-50 dark:bg-gray-800 rounded-lg">
                      <Label className="font-medium text-gray-700 dark:text-gray-300 min-w-0 flex-shrink-0">
                        {key}
                      </Label>
                      <Input
                        value={value}
                        onChange={(e) => handleUpdateEnvVar(key, e.target.value)}
                        className="flex-1"
                      />
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleRemoveEnvVar(key)}
                        className="text-red-600 hover:text-red-700"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Dependencies */}
        <TabsContent value="dependencies" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Package className="h-5 w-5 text-purple-500" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Additional Dependencies
              </h3>
            </div>

            {/* Common Dependencies */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                Common Packages
              </h4>
              <div className="flex flex-wrap gap-2">
                {(commonDependencies.python || []).map((dep) => (
                  <Button
                    key={dep}
                    variant="outline"
                    size="sm"
                    onClick={() => handleAddCommonDependency(dep)}
                    disabled={configuration.additionalDependencies.includes(dep)}
                    className="text-xs"
                  >
                    {dep}
                  </Button>
                ))}
              </div>
            </div>

            {/* Add Custom Dependency */}
            <div className="mb-6">
              <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                Add Custom Package
              </h4>
              <div className="flex space-x-2">
                <Input
                  placeholder="Package name (e.g., requests>=2.28.0)"
                  value={newDependency}
                  onChange={(e) => setNewDependency(e.target.value)}
                  className="flex-1"
                />
                <Button onClick={handleAddDependency} disabled={!newDependency}>
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
            </div>

            {/* Current Dependencies */}
            {configuration.additionalDependencies.length > 0 && (
              <div>
                <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-3">
                  Added Dependencies ({configuration.additionalDependencies.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {configuration.additionalDependencies.map((dep) => (
                    <Badge
                      key={dep}
                      variant="secondary"
                      className="flex items-center space-x-1 px-3 py-1"
                    >
                      <span>{dep}</span>
                      <button
                        onClick={() => handleRemoveDependency(dep)}
                        className="ml-1 text-red-500 hover:text-red-700"
                      >
                        <Trash2 className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </Card>
        </TabsContent>

        {/* Custom Settings */}
        <TabsContent value="custom" className="space-y-6">
          <Card className="p-6">
            <div className="flex items-center space-x-2 mb-4">
              <Code className="h-5 w-5 text-orange-500" />
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Custom Settings (JSON)
              </h3>
            </div>

            <div className="space-y-4">
              <div className="flex items-start space-x-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <Info className="h-4 w-4 text-blue-500 mt-0.5" />
                <div className="text-sm text-blue-700 dark:text-blue-300">
                  <p className="font-medium mb-1">Custom Configuration</p>
                  <p>Add any additional configuration as JSON. This will be merged with the generated configuration.</p>
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="custom-settings">JSON Configuration</Label>
                <Textarea
                  id="custom-settings"
                  value={customSettingsJson}
                  onChange={(e) => handleCustomSettingsChange(e.target.value)}
                  className={`min-h-[200px] font-mono text-sm ${
                    !isValidJson(customSettingsJson) ? 'border-red-500' : ''
                  }`}
                  placeholder={`{
  "server": {
    "timeout": 30000,
    "maxConnections": 100
  },
  "logging": {
    "format": "json",
    "level": "info"
  }
}`}
                />
                {!isValidJson(customSettingsJson) && (
                  <div className="flex items-center space-x-2 text-sm text-red-600 dark:text-red-400">
                    <AlertCircle className="h-4 w-4" />
                    <span>Invalid JSON format</span>
                  </div>
                )}
              </div>

              {/* JSON Preview */}
              {isValidJson(customSettingsJson) && Object.keys(configuration.customSettings).length > 0 && (
                <div className="mt-4">
                  <h4 className="font-medium text-gray-900 dark:text-gray-100 mb-2">
                    Configuration Preview
                  </h4>
                  <div className="bg-gray-50 dark:bg-gray-800 p-3 rounded-lg">
                    <pre className="text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">
                      {JSON.stringify(configuration.customSettings, null, 2)}
                    </pre>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Validation Warnings */}
      {warnings.length > 0 && (
        <Card className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start space-x-2">
            <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900 dark:text-yellow-100 text-sm">
                Configuration Suggestions:
              </h4>
              <ul className="mt-1 text-xs text-yellow-700 dark:text-yellow-300 list-disc list-inside">
                {warnings.map((warning, index) => (
                  <li key={index}>{warning}</li>
                ))}
              </ul>
            </div>
          </div>
        </Card>
      )}

      {/* Configuration Summary */}
      <Card className="p-4 bg-gray-50 dark:bg-gray-800/50">
        <div className="flex items-start space-x-3">
          <Settings className="h-5 w-5 text-gray-500 mt-0.5" />
          <div>
            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Advanced Configuration Summary
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Deployment:</span>
                <div className="mt-1">
                  <Badge variant="secondary">
                    {deploymentTargets.find(t => t.id === configuration.deploymentTarget)?.name}
                  </Badge>
                  {configuration.cloudProvider && (
                    <Badge variant="secondary" className="ml-1">
                      {cloudProviders.find(p => p.id === configuration.cloudProvider)?.name}
                    </Badge>
                  )}
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Environment Variables:</span>
                <div className="mt-1">
                  <Badge variant="outline">
                    {Object.keys(configuration.environmentVariables).length} variables
                  </Badge>
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Dependencies:</span>
                <div className="mt-1">
                  <Badge variant="outline">
                    {configuration.additionalDependencies.length} packages
                  </Badge>
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-700 dark:text-gray-300">Custom Settings:</span>
                <div className="mt-1">
                  <Badge variant="outline">
                    {Object.keys(configuration.customSettings).length} settings
                  </Badge>
                </div>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
};