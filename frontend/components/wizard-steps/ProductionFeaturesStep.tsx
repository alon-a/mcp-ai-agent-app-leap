import React from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Container, 
  Cloud, 
  Shield, 
  Activity, 
  Database, 
  BarChart3,
  CheckCircle,
  Info,
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Lightbulb
} from 'lucide-react';
import { ProductionFeatures } from '../AdvancedBuildWizard';

interface ProductionFeaturesStepProps {
  configuration: ProductionFeatures;
  onChange: (config: ProductionFeatures) => void;
  errors?: string[];
  warnings?: string[];
  showAdvanced?: boolean;
  onToggleAdvanced?: () => void;
}

// Production feature definitions
const productionFeatures = [
  {
    key: 'enableDocker' as keyof ProductionFeatures,
    title: 'Docker Containerization',
    description: 'Generate Dockerfile and container configuration for easy deployment',
    icon: Container,
    category: 'Deployment',
    benefits: ['Consistent environments', 'Easy deployment', 'Scalability'],
    requirements: ['Docker runtime'],
    complexity: 'Low',
    recommended: true,
  },
  {
    key: 'enableKubernetes' as keyof ProductionFeatures,
    title: 'Kubernetes Support',
    description: 'Generate Kubernetes manifests for orchestrated deployment',
    icon: Cloud,
    category: 'Orchestration',
    benefits: ['Auto-scaling', 'High availability', 'Service discovery'],
    requirements: ['Kubernetes cluster', 'Docker enabled'],
    complexity: 'High',
    recommended: false,
    dependsOn: ['enableDocker'],
  },
  {
    key: 'enableSecurity' as keyof ProductionFeatures,
    title: 'Security Hardening',
    description: 'Add authentication, authorization, and security best practices',
    icon: Shield,
    category: 'Security',
    benefits: ['Access control', 'Data protection', 'Audit logging'],
    requirements: ['Authentication provider'],
    complexity: 'Medium',
    recommended: true,
  },
  {
    key: 'enableMonitoring' as keyof ProductionFeatures,
    title: 'Health Monitoring',
    description: 'Add health checks, metrics collection, and alerting',
    icon: Activity,
    category: 'Observability',
    benefits: ['System visibility', 'Proactive alerts', 'Performance tracking'],
    requirements: ['Monitoring stack'],
    complexity: 'Medium',
    recommended: true,
  },
  {
    key: 'enableCaching' as keyof ProductionFeatures,
    title: 'Response Caching',
    description: 'Implement caching strategies for improved performance',
    icon: Database,
    category: 'Performance',
    benefits: ['Faster responses', 'Reduced load', 'Better UX'],
    requirements: ['Cache store (Redis/Memcached)'],
    complexity: 'Medium',
    recommended: false,
  },
  {
    key: 'enableMetrics' as keyof ProductionFeatures,
    title: 'Performance Metrics',
    description: 'Collect and expose performance metrics and analytics',
    icon: BarChart3,
    category: 'Analytics',
    benefits: ['Performance insights', 'Usage analytics', 'Optimization data'],
    requirements: ['Metrics collector'],
    complexity: 'Low',
    recommended: false,
  },
];

// Group features by category
const featuresByCategory = productionFeatures.reduce((acc, feature) => {
  if (!acc[feature.category]) {
    acc[feature.category] = [];
  }
  acc[feature.category].push(feature);
  return acc;
}, {} as Record<string, typeof productionFeatures>);

export const ProductionFeaturesStep: React.FC<ProductionFeaturesStepProps> = ({
  configuration,
  onChange,
  errors = [],
  warnings = [],
  showAdvanced = false,
  onToggleAdvanced,
}) => {
  const handleFeatureToggle = (featureKey: keyof ProductionFeatures) => {
    const newConfig = {
      ...configuration,
      [featureKey]: !configuration[featureKey],
    };

    // Handle dependencies
    const feature = productionFeatures.find(f => f.key === featureKey);
    if (feature?.dependsOn && newConfig[featureKey]) {
      // Enable dependencies when enabling a feature
      feature.dependsOn.forEach(dep => {
        newConfig[dep as keyof ProductionFeatures] = true;
      });
    } else if (!newConfig[featureKey]) {
      // Disable dependent features when disabling a feature
      productionFeatures.forEach(f => {
        if (f.dependsOn?.includes(featureKey as string)) {
          newConfig[f.key] = false;
        }
      });
    }

    onChange(newConfig);
  };

  const getComplexityColor = (complexity: string) => {
    switch (complexity) {
      case 'Low':
        return 'bg-green-100 text-green-700 border-green-200';
      case 'Medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'High':
        return 'bg-red-100 text-red-700 border-red-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const enabledFeatures = productionFeatures.filter(f => configuration[f.key]);
  const recommendedFeatures = productionFeatures.filter(f => f.recommended && !configuration[f.key]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Production Features
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Configure production-ready features for deployment, monitoring, and security. 
          These features are optional but recommended for production environments.
        </p>
      </div>

      {/* Recommended Features Alert */}
      {recommendedFeatures.length > 0 && (
        <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div className="flex items-start space-x-3">
            <Info className="h-5 w-5 text-blue-500 mt-0.5" />
            <div>
              <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
                Recommended for Production
              </h3>
              <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                Consider enabling these features for a production-ready deployment:
              </p>
              <div className="flex flex-wrap gap-2">
                {recommendedFeatures.map(feature => (
                  <Badge 
                    key={feature.key} 
                    variant="outline" 
                    className="bg-blue-100 text-blue-700 border-blue-300 cursor-pointer hover:bg-blue-200"
                    onClick={() => handleFeatureToggle(feature.key)}
                  >
                    {feature.title}
                  </Badge>
                ))}
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Feature Categories */}
      <div className="space-y-6">
        {Object.entries(featuresByCategory).map(([category, features]) => (
          <div key={category}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
              {category}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {features.map((feature) => {
                const isEnabled = configuration[feature.key];
                const isDisabled = feature.dependsOn?.some(dep => 
                  !configuration[dep as keyof ProductionFeatures]
                );

                return (
                  <Card
                    key={feature.key}
                    className={`
                      p-4 cursor-pointer transition-all border-2
                      ${isEnabled 
                        ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                        : isDisabled
                          ? 'border-gray-200 dark:border-gray-700 opacity-50 cursor-not-allowed'
                          : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                      }
                    `}
                    onClick={() => !isDisabled && handleFeatureToggle(feature.key)}
                  >
                    <div className="flex items-start space-x-3">
                      <div className={`
                        p-2 rounded-lg
                        ${isEnabled 
                          ? 'bg-blue-100 dark:bg-blue-800' 
                          : 'bg-gray-100 dark:bg-gray-800'
                        }
                      `}>
                        <feature.icon className={`
                          h-5 w-5 
                          ${isEnabled 
                            ? 'text-blue-600 dark:text-blue-400' 
                            : 'text-gray-500 dark:text-gray-400'
                          }
                        `} />
                      </div>
                      
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center space-x-2">
                            <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                              {feature.title}
                            </h4>
                            {isEnabled && (
                              <CheckCircle className="h-4 w-4 text-blue-500" />
                            )}
                            {feature.recommended && !isEnabled && (
                              <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                                Recommended
                              </Badge>
                            )}
                          </div>
                          <Badge 
                            variant="outline" 
                            className={`text-xs ${getComplexityColor(feature.complexity)}`}
                          >
                            {feature.complexity}
                          </Badge>
                        </div>
                        
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                          {feature.description}
                        </p>
                        
                        {/* Benefits */}
                        <div className="mb-3">
                          <div className="flex flex-wrap gap-1">
                            {feature.benefits.slice(0, 3).map((benefit, index) => (
                              <Badge key={index} variant="secondary" className="text-xs">
                                {benefit}
                              </Badge>
                            ))}
                          </div>
                        </div>
                        
                        {/* Requirements */}
                        <div className="text-xs text-gray-500 dark:text-gray-400">
                          <span className="font-medium">Requires:</span> {feature.requirements.join(', ')}
                        </div>
                        
                        {/* Dependencies Warning */}
                        {isDisabled && feature.dependsOn && (
                          <div className="mt-2 flex items-center space-x-1 text-xs text-amber-600 dark:text-amber-400">
                            <AlertTriangle className="h-3 w-3" />
                            <span>
                              Requires: {feature.dependsOn.map(dep => 
                                productionFeatures.find(f => f.key === dep)?.title
                              ).join(', ')}
                            </span>
                          </div>
                        )}
                      </div>
                    </div>
                  </Card>
                );
              })}
            </div>
          </div>
        ))}
      </div>

      {/* Configuration Summary */}
      {enabledFeatures.length > 0 && (
        <Card className="p-4 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-start space-x-3">
            <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Enabled Production Features ({enabledFeatures.length})
              </h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                {enabledFeatures.map(feature => (
                  <div key={feature.key} className="flex items-center space-x-2">
                    <feature.icon className="h-4 w-4 text-blue-500" />
                    <span className="font-medium text-gray-700 dark:text-gray-300">
                      {feature.title}
                    </span>
                    <Badge variant="outline" className={`text-xs ${getComplexityColor(feature.complexity)}`}>
                      {feature.complexity}
                    </Badge>
                  </div>
                ))}
              </div>
              
              {/* Deployment Readiness */}
              <div className="mt-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                <div className="flex items-center space-x-2">
                  <CheckCircle className="h-4 w-4 text-green-500" />
                  <span className="text-sm font-medium text-green-900 dark:text-green-100">
                    Production Readiness Score: {Math.round((enabledFeatures.length / productionFeatures.length) * 100)}%
                  </span>
                </div>
                <p className="text-xs text-green-700 dark:text-green-300 mt-1">
                  Your server will include {enabledFeatures.length} production features for enhanced reliability and monitoring.
                </p>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Validation Warnings */}
      {warnings.length > 0 && (
        <Card className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start space-x-2">
            <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900 dark:text-yellow-100 text-sm">
                Production Recommendations:
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

      {/* No Features Selected */}
      {enabledFeatures.length === 0 && (
        <Card className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-5 w-5 text-yellow-500 mt-0.5" />
            <div>
              <h4 className="font-semibold text-yellow-900 dark:text-yellow-100 mb-2">
                Basic Configuration
              </h4>
              <p className="text-sm text-yellow-700 dark:text-yellow-300">
                No production features are currently enabled. Your server will be generated with basic functionality only. 
                Consider enabling some features for production deployment.
              </p>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};