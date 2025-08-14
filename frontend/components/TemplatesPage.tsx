import React from 'react';
import { FileTemplate, Search, Filter, Star, Download } from 'lucide-react';
import { Button } from '@/components/ui/button';

export const TemplatesPage: React.FC = () => {
  const templates = [
    {
      id: 1,
      name: 'File System Server',
      description: 'Basic file system operations with read/write capabilities',
      category: 'Built-in',
      language: 'TypeScript',
      downloads: 1250,
      rating: 4.8,
    },
    {
      id: 2,
      name: 'Database Server',
      description: 'SQL database integration with query capabilities',
      category: 'Built-in',
      language: 'Python',
      downloads: 890,
      rating: 4.6,
    },
    {
      id: 3,
      name: 'API Integration Server',
      description: 'REST API client with authentication support',
      category: 'Built-in',
      language: 'TypeScript',
      downloads: 670,
      rating: 4.7,
    },
  ];

  return (
    <div className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
              Templates
            </h1>
            <p className="text-gray-600 dark:text-gray-400 mt-2">
              Browse and use pre-built MCP server templates
            </p>
          </div>
          <Button variant="outline">
            <FileTemplate className="h-4 w-4 mr-2" />
            Create Template
          </Button>
        </div>

        {/* Search and Filter Bar */}
        <div className="flex items-center space-x-4 mb-8">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search templates..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
          <Button variant="outline" className="flex items-center space-x-2">
            <Filter className="h-4 w-4" />
            <span>Filter</span>
          </Button>
        </div>

        {/* Template Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {templates.map((template) => (
            <div
              key={template.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-md border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                    <FileTemplate className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                      {template.name}
                    </h3>
                    <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 px-2 py-1 rounded">
                      {template.category}
                    </span>
                  </div>
                </div>
              </div>

              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                {template.description}
              </p>

              <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                <span className="font-medium">{template.language}</span>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <Star className="h-4 w-4 text-yellow-500 fill-current" />
                    <span>{template.rating}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Download className="h-4 w-4" />
                    <span>{template.downloads}</span>
                  </div>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button size="sm" className="flex-1">
                  Use Template
                </Button>
                <Button size="sm" variant="outline">
                  Preview
                </Button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};