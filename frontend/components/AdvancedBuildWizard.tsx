import React, { useState, useEffect } from 'react';
import { 
  ChevronLeft, 
  ChevronRight, 
  Save, 
  Upload, 
  Download,
  Eye,
  CheckCircle,
  AlertCircle,
  Settings,
  Code,
  Server,
  Cloud,
  ChevronDown,
  ChevronUp,
  Info,
  Lightbulb
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Select } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { ProjectBasicsStep } from './wizard-steps/ProjectBasicsStep';
import { TechnologyStackStep } from './wizard-steps/TechnologyStackStep';
import { ProductionFeaturesStep } from './wizard-steps/ProductionFeaturesStep';
import { AdvancedConfigurationStep } from './wizard-steps/AdvancedConfigurationStep';

// Configuration interfaces
export interface ProjectBasics {
  name: string;
  description: string;
  version: string;
  author: string;
}

export interface TechnologyStack {
  language: 'python' | 'typescript' | 'go' | 'rust' | 'java';
  framework: string;
  template: string;
}

export interface ProductionFeatures {
  enableDocker: boolean;
  enableKubernetes: boolean;
  enableMonitoring: boolean;
  enableSecurity: boolean;
  enableCaching: boolean;
  enableMetrics: boolean;
}

export interface AdvancedConfiguration {
  environmentVariables: Record<string, string>;
  additionalDependencies: string[];
  customSettings: Record<string, any>;
  deploymentTarget: 'local' | 'cloud' | 'kubernetes';
  cloudProvider?: 'aws' | 'gcp' | 'azure';
}

export interface UnifiedProjectConfig {
  basics: ProjectBasics;
  technology: TechnologyStack;
  production: ProductionFeatures;
  advanced: AdvancedConfiguration;
}

// Wizard step interface
interface WizardStep {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  isValid: (config: UnifiedProjectConfig) => boolean;
  isOptional?: boolean;
}

// Wizard steps configuration
const wizardSteps: WizardStep[] = [
  {
    id: 'basics',
    title: 'Project Basics',
    description: 'Define your project name, description, and basic information',
    icon: Settings,
    isValid: (config) => !!(config.basics.name && config.basics.description),
  },
  {
    id: 'technology',
    title: 'Technology Stack',
    description: 'Choose your programming language, framework, and template',
    icon: Code,
    isValid: (config) => !!(config.technology.language && config.technology.framework),
  },
  {
    id: 'production',
    title: 'Production Features',
    description: 'Configure deployment, monitoring, and production capabilities',
    icon: Server,
    isValid: () => true, // Production features are optional
    isOptional: true,
  },
  {
    id: 'advanced',
    title: 'Advanced Configuration',
    description: 'Fine-tune environment variables, dependencies, and custom settings',
    icon: Cloud,
    isValid: () => true, // Advanced configuration is optional
    isOptional: true,
  },
];

interface AdvancedBuildWizardProps {
  onConfigurationComplete: (config: UnifiedProjectConfig) => void;
  onCancel: () => void;
  initialConfig?: Partial<UnifiedProjectConfig>;
  className?: string;
}

export const AdvancedBuildWizard: React.FC<AdvancedBuildWizardProps> = ({
  onConfigurationComplete,
  onCancel,
  initialConfig,
  className = '',
}) => {
  const { toast } = useToast();
  const [currentStep, setCurrentStep] = useState(0);
  const [configuration, setConfiguration] = useState<UnifiedProjectConfig>({
    basics: {
      name: '',
      description: '',
      version: '1.0.0',
      author: '',
      ...initialConfig?.basics,
    },
    technology: {
      language: 'python',
      framework: '',
      template: '',
      ...initialConfig?.technology,
    },
    production: {
      enableDocker: false,
      enableKubernetes: false,
      enableMonitoring: false,
      enableSecurity: false,
      enableCaching: false,
      enableMetrics: false,
      ...initialConfig?.production,
    },
    advanced: {
      environmentVariables: {},
      additionalDependencies: [],
      customSettings: {},
      deploymentTarget: 'local',
      ...initialConfig?.advanced,
    },
  });

  const [validationErrors, setValidationErrors] = useState<Record<string, string[]>>({});
  const [showPreview, setShowPreview] = useState(false);
  const [showAdvancedOptions, setShowAdvancedOptions] = useState<Record<string, boolean>>({});
  const [validationWarnings, setValidationWarnings] = useState<Record<string, string[]>>({});
  const [intelligentDefaults, setIntelligentDefaults] = useState<Record<string, any>>({});

  // Apply intelligent defaults based on configuration
  const applyIntelligentDefaults = (config: UnifiedProjectConfig): UnifiedProjectConfig => {
    const newConfig = { ...config };
    
    // Apply language-specific defaults
    if (config.technology.language === 'python') {
      if (!config.basics.version) newConfig.basics.version = '1.0.0';
      if (!config.advanced.environmentVariables.PYTHON_VERSION) {
        newConfig.advanced.environmentVariables = {
          ...newConfig.advanced.environmentVariables,
          PYTHON_VERSION: '3.11'
        };
      }
      // Recommend production features for Python
      if (!config.production.enableDocker && !config.production.enableMonitoring) {
        setValidationWarnings(prev => ({
          ...prev,
          production: ['Consider enabling Docker and Monitoring for Python production deployments']
        }));
      }
    }
    
    if (config.technology.language === 'typescript') {
      if (!config.basics.version) newConfig.basics.version = '1.0.0';
      if (!config.advanced.environmentVariables.NODE_ENV) {
        newConfig.advanced.environmentVariables = {
          ...newConfig.advanced.environmentVariables,
          NODE_ENV: 'production',
          PORT: '8080'
        };
      }
    }
    
    // Apply template-specific defaults
    if (config.technology.template === 'database-server') {
      if (!config.advanced.environmentVariables.DATABASE_URL) {
        newConfig.advanced.environmentVariables = {
          ...newConfig.advanced.environmentVariables,
          DATABASE_URL: 'postgresql://localhost:5432/mcp_server'
        };
      }
      newConfig.production.enableSecurity = true;
      newConfig.production.enableMonitoring = true;
    }
    
    if (config.technology.template === 'api-integration') {
      if (!config.advanced.environmentVariables.API_TIMEOUT) {
        newConfig.advanced.environmentVariables = {
          ...newConfig.advanced.environmentVariables,
          API_TIMEOUT: '30000',
          RATE_LIMIT: '100'
        };
      }
      newConfig.production.enableCaching = true;
    }
    
    return newConfig;
  };

  // Enhanced validation with warnings and suggestions
  const validateCurrentStep = (): boolean => {
    const step = wizardSteps[currentStep];
    const isValid = step.isValid(configuration);
    const errors: string[] = [];
    const warnings: string[] = [];
    
    if (step.id === 'basics') {
      if (!configuration.basics.name) errors.push('Project name is required');
      if (!configuration.basics.description) errors.push('Project description is required');
      
      // Validation warnings
      if (configuration.basics.name && !/^[a-z0-9-]+$/.test(configuration.basics.name)) {
        warnings.push('Project name should use lowercase letters and hyphens only');
      }
      if (configuration.basics.description && configuration.basics.description.length < 20) {
        warnings.push('Consider adding a more detailed description for better documentation');
      }
    }
    
    if (step.id === 'technology') {
      if (!configuration.technology.language) errors.push('Programming language is required');
      if (!configuration.technology.framework) errors.push('Framework selection is required');
      
      // Language-specific warnings
      if (configuration.technology.language === 'rust' && !configuration.production.enableDocker) {
        warnings.push('Docker is highly recommended for Rust deployments');
      }
      if (configuration.technology.language === 'java' && !configuration.production.enableMetrics) {
        warnings.push('Performance metrics are valuable for Java applications');
      }
    }
    
    if (step.id === 'production') {
      const enabledFeatures = Object.values(configuration.production).filter(Boolean).length;
      if (enabledFeatures === 0) {
        warnings.push('Consider enabling at least Docker and Monitoring for production readiness');
      }
      if (configuration.production.enableKubernetes && !configuration.production.enableDocker) {
        errors.push('Docker must be enabled when using Kubernetes');
      }
    }
    
    if (step.id === 'advanced') {
      const envVarCount = Object.keys(configuration.advanced.environmentVariables).length;
      if (envVarCount === 0) {
        warnings.push('Environment variables help configure your server for different environments');
      }
      
      // Validate environment variable names
      Object.keys(configuration.advanced.environmentVariables).forEach(key => {
        if (!/^[A-Z_][A-Z0-9_]*$/.test(key)) {
          warnings.push(`Environment variable "${key}" should use UPPER_CASE format`);
        }
      });
    }
    
    setValidationErrors({ [step.id]: errors });
    setValidationWarnings({ [step.id]: warnings });
    
    return errors.length === 0;
  };

  // Handle step navigation
  const handleNext = () => {
    if (validateCurrentStep()) {
      if (currentStep < wizardSteps.length - 1) {
        setCurrentStep(currentStep + 1);
      } else {
        handleComplete();
      }
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepClick = (stepIndex: number) => {
    // Allow navigation to previous steps or next step if current is valid
    if (stepIndex <= currentStep || validateCurrentStep()) {
      setCurrentStep(stepIndex);
    }
  };

  // Toggle advanced options visibility
  const toggleAdvancedOptions = (section: string) => {
    setShowAdvancedOptions(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  // Handle configuration changes with intelligent defaults
  const handleConfigurationChange = (newConfig: UnifiedProjectConfig) => {
    const configWithDefaults = applyIntelligentDefaults(newConfig);
    setConfiguration(configWithDefaults);
  };

  // Handle configuration completion
  const handleComplete = () => {
    if (validateAllSteps()) {
      const finalConfig = applyIntelligentDefaults(configuration);
      onConfigurationComplete(finalConfig);
      toast({
        title: "Configuration Complete",
        description: "Your advanced build configuration is ready with intelligent defaults applied!",
      });
    }
  };

  // Validate all steps
  const validateAllSteps = (): boolean => {
    const allErrors: Record<string, string[]> = {};
    let isValid = true;

    wizardSteps.forEach((step) => {
      if (!step.isValid(configuration) && !step.isOptional) {
        isValid = false;
        allErrors[step.id] = [`${step.title} configuration is incomplete`];
      }
    });

    setValidationErrors(allErrors);
    return isValid;
  };

  // Save configuration to local storage
  const handleSaveConfiguration = () => {
    try {
      const configName = configuration.basics.name || 'unnamed-config';
      const timestamp = new Date().toISOString();
      const savedConfigs = JSON.parse(localStorage.getItem('mcp-saved-configs') || '[]');
      
      savedConfigs.push({
        name: configName,
        timestamp,
        configuration,
      });
      
      localStorage.setItem('mcp-saved-configs', JSON.stringify(savedConfigs));
      
      toast({
        title: "Configuration Saved",
        description: `Configuration "${configName}" has been saved locally.`,
      });
    } catch (error) {
      toast({
        title: "Save Failed",
        description: "Failed to save configuration. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Load configuration from file
  const handleLoadConfiguration = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const loadedConfig = JSON.parse(e.target?.result as string);
        setConfiguration({ ...configuration, ...loadedConfig });
        toast({
          title: "Configuration Loaded",
          description: "Configuration has been loaded successfully.",
        });
      } catch (error) {
        toast({
          title: "Load Failed",
          description: "Invalid configuration file format.",
          variant: "destructive",
        });
      }
    };
    reader.readAsText(file);
  };

  // Export configuration
  const handleExportConfiguration = () => {
    try {
      const configBlob = new Blob([JSON.stringify(configuration, null, 2)], {
        type: 'application/json',
      });
      const url = URL.createObjectURL(configBlob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${configuration.basics.name || 'mcp-config'}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      
      toast({
        title: "Configuration Exported",
        description: "Configuration file has been downloaded.",
      });
    } catch (error) {
      toast({
        title: "Export Failed",
        description: "Failed to export configuration. Please try again.",
        variant: "destructive",
      });
    }
  };

  return (
    <div className={`max-w-6xl mx-auto ${className}`}>
      {/* Wizard Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Advanced MCP Server Builder
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Configure your production-ready MCP server with comprehensive options and validation.
        </p>
      </div>

      {/* Progress Steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {wizardSteps.map((step, index) => {
            const isActive = index === currentStep;
            const isCompleted = index < currentStep;
            const isValid = step.isValid(configuration);
            const hasErrors = validationErrors[step.id]?.length > 0;
            
            return (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => handleStepClick(index)}
                  className={`
                    flex items-center justify-center w-12 h-12 rounded-full border-2 transition-all
                    ${isActive 
                      ? 'border-blue-500 bg-blue-500 text-white' 
                      : isCompleted 
                        ? 'border-green-500 bg-green-500 text-white'
                        : hasErrors
                          ? 'border-red-500 bg-red-50 text-red-500'
                          : 'border-gray-300 bg-white text-gray-400 hover:border-gray-400'
                    }
                  `}
                  disabled={index > currentStep && !validateCurrentStep()}
                >
                  {isCompleted ? (
                    <CheckCircle className="h-6 w-6" />
                  ) : hasErrors ? (
                    <AlertCircle className="h-6 w-6" />
                  ) : (
                    <step.icon className="h-6 w-6" />
                  )}
                </button>
                
                <div className="ml-3 min-w-0 flex-1">
                  <p className={`text-sm font-medium ${isActive ? 'text-blue-600' : 'text-gray-900 dark:text-gray-100'}`}>
                    {step.title}
                    {step.isOptional && (
                      <Badge variant="secondary" className="ml-2 text-xs">
                        Optional
                      </Badge>
                    )}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    {step.description}
                  </p>
                </div>
                
                {index < wizardSteps.length - 1 && (
                  <div className="w-8 h-px bg-gray-300 dark:bg-gray-600 mx-4" />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Configuration Actions */}
      <div className="mb-6 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleSaveConfiguration}
            disabled={!configuration.basics.name}
          >
            <Save className="h-4 w-4 mr-2" />
            Save Config
          </Button>
          
          <div className="relative">
            <input
              type="file"
              accept=".json"
              onChange={handleLoadConfiguration}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <Button variant="outline" size="sm">
              <Upload className="h-4 w-4 mr-2" />
              Load Config
            </Button>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleExportConfiguration}
            disabled={!configuration.basics.name}
          >
            <Download className="h-4 w-4 mr-2" />
            Export Config
          </Button>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={() => setShowPreview(!showPreview)}
        >
          <Eye className="h-4 w-4 mr-2" />
          {showPreview ? 'Hide' : 'Show'} Preview
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Configuration Panel */}
        <div className="lg:col-span-2">
          <Card className="p-6">
            {/* Step Content */}
            <div className="min-h-[400px]">
              {currentStep === 0 && (
                <ProjectBasicsStep
                  configuration={configuration.basics}
                  onChange={(basics) => handleConfigurationChange({ ...configuration, basics })}
                  errors={validationErrors.basics}
                  warnings={validationWarnings.basics}
                  showAdvanced={showAdvancedOptions.basics}
                  onToggleAdvanced={() => toggleAdvancedOptions('basics')}
                />
              )}
              
              {currentStep === 1 && (
                <TechnologyStackStep
                  configuration={configuration.technology}
                  onChange={(technology) => handleConfigurationChange({ ...configuration, technology })}
                  errors={validationErrors.technology}
                  warnings={validationWarnings.technology}
                  showAdvanced={showAdvancedOptions.technology}
                  onToggleAdvanced={() => toggleAdvancedOptions('technology')}
                />
              )}
              
              {currentStep === 2 && (
                <ProductionFeaturesStep
                  configuration={configuration.production}
                  onChange={(production) => handleConfigurationChange({ ...configuration, production })}
                  errors={validationErrors.production}
                  warnings={validationWarnings.production}
                  showAdvanced={showAdvancedOptions.production}
                  onToggleAdvanced={() => toggleAdvancedOptions('production')}
                />
              )}
              
              {currentStep === 3 && (
                <AdvancedConfigurationStep
                  configuration={configuration.advanced}
                  onChange={(advanced) => handleConfigurationChange({ ...configuration, advanced })}
                  errors={validationErrors.advanced}
                  warnings={validationWarnings.advanced}
                  showAdvanced={showAdvancedOptions.advanced}
                  onToggleAdvanced={() => toggleAdvancedOptions('advanced')}
                />
              )}
            </div>
            
            {/* Validation Errors */}
            {validationErrors[wizardSteps[currentStep].id]?.length > 0 && (
              <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                <div className="flex items-start space-x-2">
                  <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-red-900 dark:text-red-100">
                      Please fix the following issues:
                    </h4>
                    <ul className="mt-2 text-sm text-red-700 dark:text-red-300 list-disc list-inside">
                      {validationErrors[wizardSteps[currentStep].id].map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Validation Warnings */}
            {validationWarnings[wizardSteps[currentStep].id]?.length > 0 && (
              <div className="mt-4 p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                <div className="flex items-start space-x-2">
                  <Lightbulb className="h-5 w-5 text-yellow-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-yellow-900 dark:text-yellow-100">
                      Suggestions for improvement:
                    </h4>
                    <ul className="mt-2 text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside">
                      {validationWarnings[wizardSteps[currentStep].id].map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            )}

            {/* Intelligent Defaults Applied */}
            {Object.keys(intelligentDefaults).length > 0 && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-start space-x-2">
                  <Info className="h-5 w-5 text-blue-500 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900 dark:text-blue-100">
                      Intelligent defaults applied:
                    </h4>
                    <p className="mt-1 text-sm text-blue-700 dark:text-blue-300">
                      We've automatically configured some settings based on your selections. You can modify these in the Advanced Configuration step.
                    </p>
                  </div>
                </div>
              </div>
            )}
            
            {/* Navigation Buttons */}
            <div className="mt-8 flex items-center justify-between">
              <Button
                variant="outline"
                onClick={currentStep === 0 ? onCancel : handlePrevious}
              >
                <ChevronLeft className="h-4 w-4 mr-2" />
                {currentStep === 0 ? 'Cancel' : 'Previous'}
              </Button>
              
              <div className="text-sm text-gray-500 dark:text-gray-400">
                Step {currentStep + 1} of {wizardSteps.length}
              </div>
              
              <Button onClick={handleNext}>
                {currentStep === wizardSteps.length - 1 ? 'Complete' : 'Next'}
                <ChevronRight className="h-4 w-4 ml-2" />
              </Button>
            </div>
          </Card>
        </div>

        {/* Configuration Preview Panel */}
        {showPreview && (
          <div className="lg:col-span-1">
            <Card className="p-4 sticky top-4">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Configuration Preview
              </h3>
              <div className="space-y-4 text-sm">
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">Project</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    {configuration.basics.name || 'Unnamed Project'}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">Technology</h4>
                  <p className="text-gray-600 dark:text-gray-400">
                    {configuration.technology.language || 'Not selected'} 
                    {configuration.technology.framework && ` / ${configuration.technology.framework}`}
                  </p>
                </div>
                
                <div>
                  <h4 className="font-medium text-gray-700 dark:text-gray-300">Features</h4>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {Object.entries(configuration.production)
                      .filter(([_, enabled]) => enabled)
                      .map(([feature, _]) => (
                        <Badge key={feature} variant="secondary" className="text-xs">
                          {feature.replace('enable', '')}
                        </Badge>
                      ))}
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
};