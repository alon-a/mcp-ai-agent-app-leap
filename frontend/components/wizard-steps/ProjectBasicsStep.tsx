import React from 'react';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ChevronDown, ChevronUp, AlertTriangle, Lightbulb } from 'lucide-react';
import { ProjectBasics } from '../AdvancedBuildWizard';

interface ProjectBasicsStepProps {
  configuration: ProjectBasics;
  onChange: (config: ProjectBasics) => void;
  errors?: string[];
  warnings?: string[];
  showAdvanced?: boolean;
  onToggleAdvanced?: () => void;
}

export const ProjectBasicsStep: React.FC<ProjectBasicsStepProps> = ({
  configuration,
  onChange,
  errors = [],
  warnings = [],
  showAdvanced = false,
  onToggleAdvanced,
}) => {
  const handleChange = (field: keyof ProjectBasics, value: string) => {
    onChange({
      ...configuration,
      [field]: value,
    });
  };

  const hasError = (field: string) => {
    return errors.some(error => error.toLowerCase().includes(field.toLowerCase()));
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          Project Basics
        </h2>
        <p className="text-gray-600 dark:text-gray-400">
          Let's start with the fundamental information about your MCP server project.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Project Name */}
        <div className="space-y-2">
          <Label htmlFor="project-name" className="text-sm font-medium">
            Project Name *
          </Label>
          <Input
            id="project-name"
            type="text"
            placeholder="my-awesome-mcp-server"
            value={configuration.name}
            onChange={(e) => handleChange('name', e.target.value)}
            className={hasError('name') ? 'border-red-500' : ''}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            A unique name for your MCP server project (lowercase, hyphens allowed)
          </p>
        </div>

        {/* Version */}
        <div className="space-y-2">
          <Label htmlFor="project-version" className="text-sm font-medium">
            Version
          </Label>
          <Input
            id="project-version"
            type="text"
            placeholder="1.0.0"
            value={configuration.version}
            onChange={(e) => handleChange('version', e.target.value)}
          />
          <p className="text-xs text-gray-500 dark:text-gray-400">
            Semantic version for your project (e.g., 1.0.0)
          </p>
        </div>
      </div>

      {/* Project Description */}
      <div className="space-y-2">
        <Label htmlFor="project-description" className="text-sm font-medium">
          Project Description *
        </Label>
        <Textarea
          id="project-description"
          placeholder="Describe what your MCP server does and its main capabilities..."
          value={configuration.description}
          onChange={(e) => handleChange('description', e.target.value)}
          className={`min-h-[100px] ${hasError('description') ? 'border-red-500' : ''}`}
        />
        <p className="text-xs text-gray-500 dark:text-gray-400">
          A clear description of your MCP server's purpose and functionality
        </p>
      </div>

      {/* Progressive Disclosure - Advanced Options */}
      {onToggleAdvanced && (
        <div className="border-t pt-4">
          <Button
            variant="ghost"
            onClick={onToggleAdvanced}
            className="flex items-center space-x-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100"
          >
            {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            <span>Advanced Options</span>
            <Badge variant="secondary" className="text-xs">
              Optional
            </Badge>
          </Button>
          
          {showAdvanced && (
            <div className="mt-4 space-y-4 pl-4 border-l-2 border-gray-200 dark:border-gray-700">
              {/* Author */}
              <div className="space-y-2">
                <Label htmlFor="project-author" className="text-sm font-medium">
                  Author
                </Label>
                <Input
                  id="project-author"
                  type="text"
                  placeholder="Your Name or Organization"
                  value={configuration.author}
                  onChange={(e) => handleChange('author', e.target.value)}
                />
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  The author or organization responsible for this project
                </p>
              </div>
              
              {/* Additional Metadata */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    License
                  </Label>
                  <Input
                    type="text"
                    placeholder="MIT"
                    defaultValue="MIT"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Software license for your project
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-sm font-medium">
                    Repository URL
                  </Label>
                  <Input
                    type="url"
                    placeholder="https://github.com/username/repo"
                  />
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Git repository URL (optional)
                  </p>
                </div>
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
                Suggestions:
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

      {/* Project Guidelines Card */}
      <Card className="p-4 bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
        <h3 className="font-semibold text-blue-900 dark:text-blue-100 mb-2">
          💡 Project Naming Guidelines
        </h3>
        <ul className="text-sm text-blue-700 dark:text-blue-300 space-y-1">
          <li>• Use lowercase letters and hyphens (kebab-case)</li>
          <li>• Make it descriptive and memorable</li>
          <li>• Avoid special characters and spaces</li>
          <li>• Consider including "mcp" in the name for clarity</li>
        </ul>
      </Card>

      {/* Example Projects Card */}
      <Card className="p-4 bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
        <h3 className="font-semibold text-green-900 dark:text-green-100 mb-2">
          📚 Example Project Ideas
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm text-green-700 dark:text-green-300">
          <div>
            <strong>Database Integration:</strong>
            <p>Connect to PostgreSQL, MySQL, or MongoDB</p>
          </div>
          <div>
            <strong>File System Access:</strong>
            <p>Read, write, and manage files and directories</p>
          </div>
          <div>
            <strong>API Integration:</strong>
            <p>Connect to REST APIs, GraphQL, or webhooks</p>
          </div>
          <div>
            <strong>Git Repository:</strong>
            <p>Interact with Git repositories and version control</p>
          </div>
        </div>
      </Card>
    </div>
  );
};