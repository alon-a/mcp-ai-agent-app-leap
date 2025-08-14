import React, { useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Code, 
  Zap, 
  Database, 
  Globe, 
  Server, 
  Layers,
  CheckCircle,
  Info,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  AlertTriangle,
  FileText
} from 'lucide-react';
import { TechnologyStack } from '../AdvancedBuildWizard';
import { TemplateSelector } from '../template/TemplateSelector';

interface TechnologyStackStepProps {
  configuration: TechnologyStack;
  onChange: (config: TechnologyStack) => void;
  errors?: string[];
  warnings?: string[];
  showAdvanced?: boolean;
  onToggleAdvanced?: () => void;
}

// Language options with their frameworks and templates
const languageOptions = {
  python: {
    name: 'Python',
    icon: '🐍',
    description: 'Robust, mature ecosystem with excellent MCP support',
    frameworks: [
      { id: 'fastmcp', name: 'FastMCP', description: 'High-level Python framework for MCP servers' },
      { id: 'mcp-sdk', name: 'MCP SDK', description: 'Low-level Python SDK for maximum control' },
    ],
    templates: [
      { id: 'database-server', name: 'Database Server', description: 'Connect to SQL/NoSQL databases' },
      { id: 'file-system', name: 'File System', description: 'File and directory operations' },
      { id: 'api-integration', name: 'API Integration', description: 'REST/GraphQL API connections' },
      { id: 'custom-tools', name: 'Custom Tools', description: 'Custom tool implementations' },
    ],
    pros: ['Mature ecosystem', 'Extensive libraries', 'Great for data processing'],
    cons: ['Slower than compiled languages', 'GIL limitations'],
  },
  typescript: {
    name: 'TypeScript',
    icon: '📘',
    description: 'Type-safe JavaScript with excellent tooling and performance',
    frameworks: [
      { id: 'mcp-sdk-ts', name: 'MCP SDK TypeScript', description: 'Official TypeScript SDK' },
      { id: 'express-mcp', name: 'Express MCP', description: 'Express.js-based MCP server' },
    ],
    templates: [
      { id: 'web-scraper', name: 'Web Scraper', description: 'Extract data from websites' },
      { id: 'file-manager', name: 'File Manager', description: 'Advanced file operations' },
      { id: 'git-integration', name: 'Git Integration', description: 'Git repository management' },
      { id: 'webhook-server', name: 'Webhook Server', description: 'Handle incoming webhooks' },
    ],
    pros: ['Type safety', 'Great tooling', 'Fast development'],
    cons: ['Node.js dependency', 'Runtime type checking needed'],
  },
  go: {
    name: 'Go',
    icon: '🐹',
    description: 'Fast, compiled language with excellent concurrency support',
    frameworks: [
      { id: 'mcp-go', name: 'MCP Go', description: 'Native Go implementation' },
      { id: 'gin-mcp', name: 'Gin MCP', description: 'Gin-based MCP server framework' },
    ],
    templates: [
      { id: 'high-performance', name: 'High Performance', description: 'Optimized for speed and efficiency' },
      { id: 'microservice', name: 'Microservice', description: 'Containerized microservice architecture' },
      { id: 'cli-tools', name: 'CLI Tools', description: 'Command-line tool integration' },
    ],
    pros: ['Excellent performance', 'Built-in concurrency', 'Single binary deployment'],
    cons: ['Verbose syntax', 'Smaller ecosystem'],
  },
  rust: {
    name: 'Rust',
    icon: '🦀',
    description: 'Memory-safe systems programming with zero-cost abstractions',
    frameworks: [
      { id: 'mcp-rust', name: 'MCP Rust', description: 'Native Rust implementation' },
      { id: 'tokio-mcp', name: 'Tokio MCP', description: 'Async Rust with Tokio runtime' },
    ],
    templates: [
      { id: 'system-integration', name: 'System Integration', description: 'Low-level system operations' },
      { id: 'crypto-tools', name: 'Crypto Tools', description: 'Cryptographic operations' },
      { id: 'performance-critical', name: 'Performance Critical', description: 'Maximum performance applications' },
    ],
    pros: ['Memory safety', 'Zero-cost abstractions', 'Excellent performance'],
    cons: ['Steep learning curve', 'Longer compile times'],
  },
  java: {
    name: 'Java',
    icon: '☕',
    description: 'Enterprise-grade platform with robust ecosystem and tooling',
    frameworks: [
      { id: 'spring-mcp', name: 'Spring MCP', description: 'Spring Boot-based MCP server' },
      { id: 'mcp-java', name: 'MCP Java', description: 'Pure Java implementation' },
    ],
    templates: [
      { id: 'enterprise-integration', name: 'Enterprise Integration', description: 'Connect to enterprise systems' },
      { id: 'data-processing', name: 'Data Processing', description: 'Large-scale data operations' },
      { id: 'message-queue', name: 'Message Queue', description: 'Message broker integration' },
    ],
    pros: ['Mature ecosystem', 'Enterprise support', 'JVM performance'],
    cons: ['Verbose syntax', 'Memory overhead'],
  },
};

export const TechnologyStackStep: React.FC<TechnologyStackStepProps> = ({
  configuration,
  onChange,
  errors = [],
  warnings = [],
  showAdvanced = false,
  onToggleAdvanced,
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState<keyof typeof languageOptions>(
    configuration.language || 'python'
  );
  const [selectedFramework, setSelectedFramework] = useState(configuration.framework);
  const [selectedTemplate, setSelectedTemplate] = useState(configuration.template);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);

  useEffect(() => {
    onChange({
      language: selectedLanguage,
      framework: selectedFramework,
      template: selectedTemplate,
    });
  }, [selectedLanguage, selectedFramework, selectedTemplate, onChange]);

  const currentLanguage = languageOptions[selectedLanguage];
  const hasError = (field: string) => {
    return errors.some(error => error.toLowerCase().includes(field.toLowerCase()));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Technology Stack
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Choose the programming language, framework, and template that best fits your project needs.
        </p>
      </div>

      {/* Language Selection */}
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
          Programming Language *
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(languageOptions).map(([key, language]) => (
            <Card
              key={key}
              className={`
                p-4 cursor-pointer transition-all border-2
                ${selectedLanguage === key 
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                  : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                }
                ${hasError('language') ? 'border-red-500' : ''}
              `}
              onClick={() => setSelectedLanguage(key as keyof typeof languageOptions)}
            >
              <div className="flex items-start space-x-3">
                <div className="text-2xl">{language.icon}</div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                      {language.name}
                    </h4>
                    {selectedLanguage === key && (
                      <CheckCircle className="h-4 w-4 text-blue-500" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {language.description}
                  </p>
                  
                  {/* Pros and Cons */}
                  <div className="mt-3 space-y-2">
                    <div className="flex flex-wrap gap-1">
                      {language.pros.slice(0, 2).map((pro, index) => (
                        <Badge key={index} variant="secondary" className="text-xs bg-green-100 text-green-700">
                          {pro}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Framework Selection */}
      {currentLanguage && (
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Framework *
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {currentLanguage.frameworks.map((framework) => (
              <Card
                key={framework.id}
                className={`
                  p-4 cursor-pointer transition-all border-2
                  ${selectedFramework === framework.id 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                  ${hasError('framework') ? 'border-red-500' : ''}
                `}
                onClick={() => setSelectedFramework(framework.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        {framework.name}
                      </h4>
                      {selectedFramework === framework.id && (
                        <CheckCircle className="h-4 w-4 text-blue-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {framework.description}
                    </p>
                  </div>
                  <Code className="h-5 w-5 text-gray-400" />
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* Template Selection */}
      {currentLanguage && selectedFramework && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                Project Template
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Choose a template to get started quickly, or browse all available templates.
              </p>
            </div>
            
            <Button
              variant="outline"
              onClick={() => setShowTemplateSelector(true)}
              className="flex items-center space-x-2"
            >
              <FileText className="h-4 w-4" />
              <span>Browse Templates</span>
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {currentLanguage.templates.map((template) => (
              <Card
                key={template.id}
                className={`
                  p-4 cursor-pointer transition-all border-2
                  ${selectedTemplate === template.id 
                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                    : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                  }
                `}
                onClick={() => setSelectedTemplate(template.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        {template.name}
                      </h4>
                      {selectedTemplate === template.id && (
                        <CheckCircle className="h-4 w-4 text-blue-500" />
                      )}
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {template.description}
                    </p>
                  </div>
                  <Layers className="h-5 w-5 text-gray-400" />
                </div>
              </Card>
            ))}
            
            {/* Custom Template Option */}
            <Card
              className={`
                p-4 cursor-pointer transition-all border-2 border-dashed
                ${selectedTemplate === 'custom' 
                  ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' 
                  : 'border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500'
                }
              `}
              onClick={() => setSelectedTemplate('custom')}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                      Custom Template
                    </h4>
                    {selectedTemplate === 'custom' && (
                      <CheckCircle className="h-4 w-4 text-blue-500" />
                    )}
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    Start with a minimal setup and build your own structure
                  </p>
                </div>
                <Server className="h-5 w-5 text-gray-400" />
              </div>
            </Card>
          </div>
        </div>
      )}

      {/* Template Selector Modal */}
      {showTemplateSelector && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-7xl w-full max-h-[90vh] overflow-hidden">
            <TemplateSelector
              selectedLanguage={selectedLanguage}
              selectedFramework={selectedFramework}
              onTemplateSelect={(template, customization) => {
                setSelectedTemplate(template.id);
                setShowTemplateSelector(false);
                // Store template customization for later use
                console.log('Template selected:', template, customization);
              }}
              onCancel={() => setShowTemplateSelector(false)}
              className="p-6"
            />
          </div>
        </div>
      )}

      {/* Progressive Disclosure - Advanced Options */}
      {selectedLanguage && selectedFramework && onToggleAdvanced && (
        <div className="border-t pt-4">
          <Button
            variant="ghost"
            onClick={onToggleAdvanced}
            className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            <span>Advanced Technology Options</span>
            <Badge variant="secondary" className="text-xs">
              Optional
            </Badge>
          </Button>
          
          {showAdvanced && (
            <div className="mt-4 space-y-4 pl-4 border-l-2 border-gray-200 dark:border-gray-700">
              {/* Runtime Version */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Runtime Version
                </label>
                <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800">
                  {selectedLanguage === 'python' && (
                    <>
                      <option value="3.11">Python 3.11 (Recommended)</option>
                      <option value="3.10">Python 3.10</option>
                      <option value="3.12">Python 3.12 (Latest)</option>
                    </>
                  )}
                  {selectedLanguage === 'typescript' && (
                    <>
                      <option value="18">Node.js 18 LTS (Recommended)</option>
                      <option value="20">Node.js 20 LTS</option>
                      <option value="21">Node.js 21 (Latest)</option>
                    </>
                  )}
                  {selectedLanguage === 'go' && (
                    <>
                      <option value="1.21">Go 1.21 (Recommended)</option>
                      <option value="1.20">Go 1.20</option>
                      <option value="1.22">Go 1.22 (Latest)</option>
                    </>
                  )}
                </select>
              </div>
              
              {/* Build Tool */}
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Build Tool
                </label>
                <select className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800">
                  {selectedLanguage === 'python' && (
                    <>
                      <option value="pip">pip (Standard)</option>
                      <option value="poetry">Poetry (Recommended)</option>
                      <option value="pipenv">Pipenv</option>
                    </>
                  )}
                  {selectedLanguage === 'typescript' && (
                    <>
                      <option value="npm">npm (Standard)</option>
                      <option value="yarn">Yarn</option>
                      <option value="pnpm">pnpm (Fast)</option>
                    </>
                  )}
                </select>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Validation Warnings */}
      {warnings.length > 0 && (
        <Card className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <div className="flex items-start space-x-2">
            <Lightbulb className="h-4 w-4 text-yellow-500 mt-0.5" />
            <div>
              <h4 className="font-medium text-yellow-900 dark:text-yellow-100 text-sm">
                Technology Recommendations:
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

      {/* Technology Summary */}
      {selectedLanguage && selectedFramework && (
        <Card className="p-4 bg-gray-50 dark:bg-gray-800/50">
          <div className="flex items-start space-x-3">
            <Info className="h-5 w-5 text-blue-500 mt-0.5" />
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                Technology Stack Summary
              </h4>
              <div className="space-y-2 text-sm">
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Language:</span>
                  <Badge variant="secondary">{currentLanguage.name}</Badge>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="font-medium text-gray-700 dark:text-gray-300">Framework:</span>
                  <Badge variant="secondary">
                    {currentLanguage.frameworks.find(f => f.id === selectedFramework)?.name}
                  </Badge>
                </div>
                {selectedTemplate && (
                  <div className="flex items-center space-x-2">
                    <span className="font-medium text-gray-700 dark:text-gray-300">Template:</span>
                    <Badge variant="secondary">
                      {selectedTemplate === 'custom' 
                        ? 'Custom Template' 
                        : currentLanguage.templates.find(t => t.id === selectedTemplate)?.name
                      }
                    </Badge>
                  </div>
                )}
              </div>
              
              {/* Advantages */}
              <div className="mt-3">
                <span className="font-medium text-gray-700 dark:text-gray-300">Key advantages:</span>
                <div className="flex flex-wrap gap-1 mt-1">
                  {currentLanguage.pros.map((pro, index) => (
                    <Badge key={index} variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                      {pro}
                    </Badge>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
};