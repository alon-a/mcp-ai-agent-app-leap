import React, { useState, useEffect } from 'react';
import {
  X,
  Settings,
  CheckCircle,
  AlertCircle,
  Info,
  Lightbulb,
  Save,
  RotateCcw,
  Eye,
  EyeOff,
  HelpCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/components/ui/use-toast';

interface Template {
  id: string;
  name: string;
  description: string;
  category: 'built-in' | 'custom' | 'community';
  language: 'python' | 'typescript' | 'go' | 'rust' | 'java' | 'multi';
  framework: string;
  version: string;
  metadata: {
    author?: string;
    tags: string[];
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    estimatedTime: number;
    lastUpdated: Date;
    downloadCount: number;
    rating: number;
    ratingCount: number;
  };
  configuration: {
    schema: any;
    defaultValues: Record<string, any>;
    requiredFields: string[];
  };
  structure: {
    files: Array<{
      path: string;
      content: string;
      isTemplate: boolean;
    }>;
    directories: string[];
    entryPoint?: string;
  };
  dependencies: {
    runtime: Record<string, string>;
    development: Record<string, string>;
    system: string[];
    services: string[];
  };
}

interface TemplateCustomizerProps {
  template: Template;
  onComplete: (template: Template, customization: Record<string, any>) => void;
  onCancel: () => void;
}

interface ValidationError {
  field: string;
  message: string;
}

interface FieldDefinition {
  key: string;
  title: string;
  type: string;
  description?: string;
  default?: any;
  required: boolean;
  enum?: string[];
  minimum?: number;
  maximum?: number;
  pattern?: string;
  format?: string;
}

export const TemplateCustomizer: React.FC<TemplateCustomizerProps> = ({
  template,
  onComplete,
  onCancel
}) => {
  const { toast } = useToast();
  const [values, setValues] = useState<Record<string, any>>({});
  const [errors, setErrors] = useState<ValidationError[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [showPreview, setShowPreview] = useState(false);
  const [validationStatus, setValidationStatus] = useState<'idle' | 'validating' | 'valid' | 'invalid'>('idle');

  // Parse JSON Schema to field definitions
  const parseSchema = (schema: any): FieldDefinition[] => {
    const fields: FieldDefinition[] = [];
    
    if (schema.properties) {
      Object.entries(schema.properties).forEach(([key, prop]: [string, any]) => {
        fields.push({
          key,
          title: prop.title || key.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase()),
          type: prop.type || 'string',
          description: prop.description,
          default: prop.default || template.configuration.defaultValues[key],
          required: template.configuration.requiredFields.includes(key),
          enum: prop.enum,
          minimum: prop.minimum,
          maximum: prop.maximum,
          pattern: prop.pattern,
          format: prop.format
        });
      });
    }
    
    return fields;
  };

  const fields = parseSchema(template.configuration.schema);
  const requiredFields = fields.filter(f => f.required);
  const optionalFields = fields.filter(f => !f.required);

  // Initialize values with defaults
  useEffect(() => {
    const initialValues: Record<string, any> = {};
    fields.forEach(field => {
      if (field.default !== undefined) {
        initialValues[field.key] = field.default;
      }
    });
    setValues(initialValues);
  }, [template]);

  // Validate form
  const validateForm = (): boolean => {
    const newErrors: ValidationError[] = [];
    const newWarnings: string[] = [];

    fields.forEach(field => {
      const value = values[field.key];
      
      // Required field validation
      if (field.required && (value === undefined || value === null || value === '')) {
        newErrors.push({
          field: field.key,
          message: `${field.title} is required`
        });
      }
      
      // Type validation
      if (value !== undefined && value !== null && value !== '') {
        switch (field.type) {
          case 'number':
            const numValue = Number(value);
            if (isNaN(numValue)) {
              newErrors.push({
                field: field.key,
                message: `${field.title} must be a valid number`
              });
            } else {
              if (field.minimum !== undefined && numValue < field.minimum) {
                newErrors.push({
                  field: field.key,
                  message: `${field.title} must be at least ${field.minimum}`
                });
              }
              if (field.maximum !== undefined && numValue > field.maximum) {
                newErrors.push({
                  field: field.key,
                  message: `${field.title} must be at most ${field.maximum}`
                });
              }
            }
            break;
            
          case 'string':
            if (field.pattern) {
              const regex = new RegExp(field.pattern);
              if (!regex.test(String(value))) {
                newErrors.push({
                  field: field.key,
                  message: `${field.title} format is invalid`
                });
              }
            }
            
            if (field.format === 'email') {
              const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
              if (!emailRegex.test(String(value))) {
                newErrors.push({
                  field: field.key,
                  message: `${field.title} must be a valid email address`
                });
              }
            }
            
            if (field.format === 'uri') {
              try {
                new URL(String(value));
              } catch {
                newErrors.push({
                  field: field.key,
                  message: `${field.title} must be a valid URL`
                });
              }
            }
            break;
            
          case 'boolean':
            if (typeof value !== 'boolean') {
              newErrors.push({
                field: field.key,
                message: `${field.title} must be true or false`
              });
            }
            break;
        }
        
        // Enum validation
        if (field.enum && !field.enum.includes(String(value))) {
          newErrors.push({
            field: field.key,
            message: `${field.title} must be one of: ${field.enum.join(', ')}`
          });
        }
      }
    });

    // Template-specific warnings
    if (template.language === 'python' && values.database_url && !values.database_url.startsWith('postgresql://')) {
      newWarnings.push('Consider using PostgreSQL for better performance with Python applications');
    }
    
    if (template.id.includes('database') && !values.pool_size) {
      newWarnings.push('Setting a connection pool size is recommended for database servers');
    }
    
    if (template.id.includes('api') && !values.rate_limit) {
      newWarnings.push('Rate limiting is recommended for API integration servers');
    }

    setErrors(newErrors);
    setWarnings(newWarnings);
    setValidationStatus(newErrors.length === 0 ? 'valid' : 'invalid');
    
    return newErrors.length === 0;
  };

  // Handle value changes
  const handleValueChange = (key: string, value: any) => {
    setValues(prev => ({ ...prev, [key]: value }));
    setValidationStatus('idle');
    
    // Clear field-specific errors
    setErrors(prev => prev.filter(error => error.field !== key));
  };

  // Reset to defaults
  const resetToDefaults = () => {
    const defaultValues: Record<string, any> = {};
    fields.forEach(field => {
      if (field.default !== undefined) {
        defaultValues[field.key] = field.default;
      }
    });
    setValues(defaultValues);
    setErrors([]);
    setWarnings([]);
    setValidationStatus('idle');
    
    toast({
      title: "Reset to defaults",
      description: "All fields have been reset to their default values.",
    });
  };

  // Handle form submission
  const handleSubmit = () => {
    setValidationStatus('validating');
    
    setTimeout(() => {
      if (validateForm()) {
        onComplete(template, values);
        toast({
          title: "Template customized",
          description: "Your template has been customized and is ready to use!",
        });
      }
    }, 500);
  };

  // Render form field
  const renderField = (field: FieldDefinition) => {
    const hasError = errors.some(error => error.field === field.key);
    const fieldError = errors.find(error => error.field === field.key);
    
    return (
      <div key={field.key} className="space-y-2">
        <div className="flex items-center space-x-2">
          <Label htmlFor={field.key} className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {field.title}
            {field.required && <span className="text-red-500 ml-1">*</span>}
          </Label>
          
          {field.description && (
            <div className="group relative">
              <HelpCircle className="h-4 w-4 text-gray-400 cursor-help" />
              <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded-lg opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                {field.description}
              </div>
            </div>
          )}
        </div>
        
        {field.type === 'boolean' ? (
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id={field.key}
              checked={values[field.key] || false}
              onChange={(e) => handleValueChange(field.key, e.target.checked)}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <Label htmlFor={field.key} className="text-sm text-gray-600 dark:text-gray-400">
              {field.description || `Enable ${field.title}`}
            </Label>
          </div>
        ) : field.enum ? (
          <select
            id={field.key}
            value={values[field.key] || ''}
            onChange={(e) => handleValueChange(field.key, e.target.value)}
            className={`w-full px-3 py-2 border rounded-md bg-white dark:bg-gray-800 text-sm ${
              hasError 
                ? 'border-red-500 focus:ring-red-500' 
                : 'border-gray-300 dark:border-gray-600 focus:ring-blue-500'
            }`}
          >
            <option value="">Select {field.title}</option>
            {field.enum.map(option => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        ) : field.type === 'number' ? (
          <Input
            type="number"
            id={field.key}
            value={values[field.key] || ''}
            onChange={(e) => handleValueChange(field.key, e.target.value ? Number(e.target.value) : '')}
            min={field.minimum}
            max={field.maximum}
            className={hasError ? 'border-red-500 focus:ring-red-500' : ''}
            placeholder={field.default ? String(field.default) : `Enter ${field.title.toLowerCase()}`}
          />
        ) : field.key.includes('description') || field.key.includes('comment') ? (
          <Textarea
            id={field.key}
            value={values[field.key] || ''}
            onChange={(e) => handleValueChange(field.key, e.target.value)}
            className={hasError ? 'border-red-500 focus:ring-red-500' : ''}
            placeholder={field.default ? String(field.default) : `Enter ${field.title.toLowerCase()}`}
            rows={3}
          />
        ) : (
          <Input
            type={field.format === 'password' ? 'password' : 'text'}
            id={field.key}
            value={values[field.key] || ''}
            onChange={(e) => handleValueChange(field.key, e.target.value)}
            className={hasError ? 'border-red-500 focus:ring-red-500' : ''}
            placeholder={field.default ? String(field.default) : `Enter ${field.title.toLowerCase()}`}
          />
        )}
        
        {fieldError && (
          <div className="flex items-center space-x-1 text-red-600 text-xs">
            <AlertCircle className="h-3 w-3" />
            <span>{fieldError.message}</span>
          </div>
        )}
        
        {field.description && !hasError && (
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {field.description}
          </p>
        )}
      </div>
    );
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-900 rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-4">
            <Settings className="h-6 w-6 text-blue-500" />
            <div>
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
                Customize Template
              </h2>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Configure {template.name} for your specific needs
              </p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowPreview(!showPreview)}
            >
              {showPreview ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              {showPreview ? 'Hide' : 'Show'} Preview
            </Button>
            <Button variant="outline" onClick={onCancel}>
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Content */}
        <div className="flex h-[calc(90vh-180px)]">
          {/* Form */}
          <div className={`${showPreview ? 'w-2/3' : 'w-full'} overflow-y-auto p-6`}>
            <div className="space-y-6">
              {/* Required Fields */}
              {requiredFields.length > 0 && (
                <div>
                  <div className="flex items-center space-x-2 mb-4">
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      Required Configuration
                    </h3>
                    <Badge variant="destructive" className="text-xs">
                      Required
                    </Badge>
                  </div>
                  <div className="space-y-4">
                    {requiredFields.map(renderField)}
                  </div>
                </div>
              )}

              {/* Optional Fields */}
              {optionalFields.length > 0 && (
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center space-x-2">
                      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                        Optional Configuration
                      </h3>
                      <Badge variant="secondary" className="text-xs">
                        Optional
                      </Badge>
                    </div>
                    
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setShowAdvanced(!showAdvanced)}
                    >
                      {showAdvanced ? 'Hide' : 'Show'} Advanced Options
                    </Button>
                  </div>
                  
                  {showAdvanced && (
                    <div className="space-y-4">
                      {optionalFields.map(renderField)}
                    </div>
                  )}
                </div>
              )}

              {/* Validation Status */}
              {validationStatus === 'validating' && (
                <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
                  <div className="flex items-center space-x-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    <span className="text-sm text-blue-700 dark:text-blue-300">
                      Validating configuration...
                    </span>
                  </div>
                </Card>
              )}

              {/* Validation Errors */}
              {errors.length > 0 && (
                <Card className="p-4 bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800">
                  <div className="flex items-start space-x-2">
                    <AlertCircle className="h-5 w-5 text-red-500 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-red-900 dark:text-red-100 mb-2">
                        Please fix the following issues:
                      </h4>
                      <ul className="text-sm text-red-700 dark:text-red-300 list-disc list-inside space-y-1">
                        {errors.map((error, index) => (
                          <li key={index}>{error.message}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Card>
              )}

              {/* Validation Warnings */}
              {warnings.length > 0 && (
                <Card className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
                  <div className="flex items-start space-x-2">
                    <Lightbulb className="h-5 w-5 text-yellow-500 mt-0.5" />
                    <div>
                      <h4 className="font-medium text-yellow-900 dark:text-yellow-100 mb-2">
                        Recommendations:
                      </h4>
                      <ul className="text-sm text-yellow-700 dark:text-yellow-300 list-disc list-inside space-y-1">
                        {warnings.map((warning, index) => (
                          <li key={index}>{warning}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </Card>
              )}

              {/* Success State */}
              {validationStatus === 'valid' && errors.length === 0 && (
                <Card className="p-4 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5 text-green-500" />
                    <span className="text-sm text-green-700 dark:text-green-300">
                      Configuration is valid and ready to use!
                    </span>
                  </div>
                </Card>
              )}
            </div>
          </div>

          {/* Preview Panel */}
          {showPreview && (
            <div className="w-1/3 border-l border-gray-200 dark:border-gray-700 overflow-y-auto p-6">
              <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">
                Configuration Preview
              </h3>
              
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Current Values
                  </h4>
                  <div className="bg-gray-50 dark:bg-gray-800 rounded-lg p-3">
                    <pre className="text-xs text-gray-900 dark:text-gray-100 overflow-auto">
                      {JSON.stringify(values, null, 2)}
                    </pre>
                  </div>
                </div>
                
                <div>
                  <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                    Template Info
                  </h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Language:</span>
                      <Badge variant="secondary">{template.language}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Framework:</span>
                      <Badge variant="outline">{template.framework}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600 dark:text-gray-400">Version:</span>
                      <span className="font-mono text-xs">{template.version}</span>
                    </div>
                  </div>
                </div>
                
                {Object.keys(template.dependencies.runtime).length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                      Dependencies
                    </h4>
                    <div className="space-y-1">
                      {Object.entries(template.dependencies.runtime).slice(0, 5).map(([pkg, version]) => (
                        <div key={pkg} className="flex justify-between text-xs">
                          <span className="font-mono text-gray-600 dark:text-gray-400">{pkg}</span>
                          <span className="text-gray-500">{version}</span>
                        </div>
                      ))}
                      {Object.keys(template.dependencies.runtime).length > 5 && (
                        <div className="text-xs text-gray-500">
                          +{Object.keys(template.dependencies.runtime).length - 5} more...
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between p-6 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              onClick={resetToDefaults}
              disabled={validationStatus === 'validating'}
            >
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
            
            <Button
              variant="ghost"
              onClick={() => validateForm()}
              disabled={validationStatus === 'validating'}
            >
              Validate Configuration
            </Button>
          </div>
          
          <div className="flex items-center space-x-2">
            <Button variant="outline" onClick={onCancel}>
              Cancel
            </Button>
            <Button 
              onClick={handleSubmit}
              disabled={validationStatus === 'validating' || (validationStatus === 'invalid' && errors.length > 0)}
            >
              {validationStatus === 'validating' ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Validating...
                </>
              ) : (
                <>
                  <CheckCircle className="h-4 w-4 mr-2" />
                  Use Template
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};