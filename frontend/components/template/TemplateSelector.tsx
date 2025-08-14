import React, { useState, useEffect, useMemo } from 'react';
import { 
  Search, 
  Filter, 
  Star, 
  Download, 
  Eye, 
  FileText, 
  CheckCircle,
  AlertCircle,
  Clock,
  User,
  Tag,
  ChevronDown,
  ChevronUp,
  Grid,
  List,
  SortAsc,
  SortDesc
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { useToast } from '@/components/ui/use-toast';
import { TemplatePreview } from './TemplatePreview';
import { TemplateCustomizer } from './TemplateCustomizer';

// Template interfaces (matching backend types)
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

interface TemplateSearchFilters {
  query: string;
  category: string;
  language: string;
  framework: string;
  difficulty: string;
  minRating: number;
  tags: string[];
  sortBy: 'name' | 'rating' | 'downloads' | 'updated' | 'created';
  sortOrder: 'asc' | 'desc';
}

interface TemplateSelectorProps {
  selectedLanguage?: string;
  selectedFramework?: string;
  onTemplateSelect: (template: Template, customization?: Record<string, any>) => void;
  onCancel?: () => void;
  className?: string;
}

// Mock template data (in real implementation, this would come from the backend)
const mockTemplates: Template[] = [
  {
    id: 'python-database-server',
    name: 'Database Server',
    description: 'Connect to SQL/NoSQL databases with comprehensive query capabilities and connection pooling',
    category: 'built-in',
    language: 'python',
    framework: 'fastmcp',
    version: '1.2.0',
    metadata: {
      author: 'MCP Team',
      tags: ['database', 'sql', 'postgresql', 'mysql', 'mongodb'],
      difficulty: 'intermediate',
      estimatedTime: 15,
      lastUpdated: new Date('2024-01-15'),
      downloadCount: 1250,
      rating: 4.8,
      ratingCount: 45
    },
    configuration: {
      schema: {
        type: 'object',
        properties: {
          database_url: { type: 'string', title: 'Database URL' },
          pool_size: { type: 'number', title: 'Connection Pool Size', default: 10 },
          timeout: { type: 'number', title: 'Query Timeout (seconds)', default: 30 }
        },
        required: ['database_url']
      },
      defaultValues: {
        pool_size: 10,
        timeout: 30
      },
      requiredFields: ['database_url']
    },
    structure: {
      files: [
        { path: 'main.py', content: '# Database server implementation', isTemplate: true },
        { path: 'config.py', content: '# Configuration settings', isTemplate: true },
        { path: 'models.py', content: '# Database models', isTemplate: true }
      ],
      directories: ['src', 'tests', 'docs'],
      entryPoint: 'main.py'
    },
    dependencies: {
      runtime: { 'sqlalchemy': '>=2.0.0', 'psycopg2': '>=2.9.0' },
      development: { 'pytest': '>=7.0.0', 'black': '>=22.0.0' },
      system: ['postgresql-client'],
      services: ['postgresql']
    }
  },
  {
    id: 'typescript-web-scraper',
    name: 'Web Scraper',
    description: 'Extract data from websites with support for JavaScript rendering and rate limiting',
    category: 'built-in',
    language: 'typescript',
    framework: 'mcp-sdk-ts',
    version: '1.0.3',
    metadata: {
      author: 'MCP Team',
      tags: ['scraping', 'web', 'puppeteer', 'cheerio'],
      difficulty: 'beginner',
      estimatedTime: 10,
      lastUpdated: new Date('2024-01-10'),
      downloadCount: 890,
      rating: 4.6,
      ratingCount: 32
    },
    configuration: {
      schema: {
        type: 'object',
        properties: {
          user_agent: { type: 'string', title: 'User Agent', default: 'MCP-Scraper/1.0' },
          rate_limit: { type: 'number', title: 'Rate Limit (requests/second)', default: 1 },
          timeout: { type: 'number', title: 'Request Timeout (ms)', default: 10000 }
        },
        required: []
      },
      defaultValues: {
        user_agent: 'MCP-Scraper/1.0',
        rate_limit: 1,
        timeout: 10000
      },
      requiredFields: []
    },
    structure: {
      files: [
        { path: 'src/index.ts', content: '// Web scraper implementation', isTemplate: true },
        { path: 'src/scraper.ts', content: '// Scraping logic', isTemplate: true },
        { path: 'package.json', content: '// Package configuration', isTemplate: true }
      ],
      directories: ['src', 'dist', 'tests'],
      entryPoint: 'src/index.ts'
    },
    dependencies: {
      runtime: { 'puppeteer': '^21.0.0', 'cheerio': '^1.0.0' },
      development: { 'typescript': '^5.0.0', '@types/node': '^20.0.0' },
      system: ['chromium'],
      services: []
    }
  },
  {
    id: 'go-high-performance',
    name: 'High Performance Server',
    description: 'Optimized for speed and efficiency with built-in metrics and health checks',
    category: 'built-in',
    language: 'go',
    framework: 'mcp-go',
    version: '2.1.0',
    metadata: {
      author: 'MCP Team',
      tags: ['performance', 'metrics', 'health-check', 'concurrent'],
      difficulty: 'advanced',
      estimatedTime: 25,
      lastUpdated: new Date('2024-01-20'),
      downloadCount: 670,
      rating: 4.9,
      ratingCount: 28
    },
    configuration: {
      schema: {
        type: 'object',
        properties: {
          port: { type: 'number', title: 'Server Port', default: 8080 },
          workers: { type: 'number', title: 'Worker Goroutines', default: 10 },
          buffer_size: { type: 'number', title: 'Buffer Size', default: 1024 }
        },
        required: []
      },
      defaultValues: {
        port: 8080,
        workers: 10,
        buffer_size: 1024
      },
      requiredFields: []
    },
    structure: {
      files: [
        { path: 'main.go', content: '// High performance server', isTemplate: true },
        { path: 'server.go', content: '// Server implementation', isTemplate: true },
        { path: 'go.mod', content: '// Go module definition', isTemplate: true }
      ],
      directories: ['cmd', 'internal', 'pkg'],
      entryPoint: 'main.go'
    },
    dependencies: {
      runtime: { 'github.com/gorilla/mux': 'v1.8.0' },
      development: {},
      system: [],
      services: []
    }
  }
];

export const TemplateSelector: React.FC<TemplateSelectorProps> = ({
  selectedLanguage,
  selectedFramework,
  onTemplateSelect,
  onCancel,
  className = ''
}) => {
  const { toast } = useToast();
  const [templates, setTemplates] = useState<Template[]>(mockTemplates);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<Template | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [showCustomizer, setShowCustomizer] = useState(false);
  
  const [filters, setFilters] = useState<TemplateSearchFilters>({
    query: '',
    category: '',
    language: selectedLanguage || '',
    framework: selectedFramework || '',
    difficulty: '',
    minRating: 0,
    tags: [],
    sortBy: 'rating',
    sortOrder: 'desc'
  });

  // Filter and sort templates
  const filteredTemplates = useMemo(() => {
    let filtered = templates.filter(template => {
      // Text search
      if (filters.query) {
        const query = filters.query.toLowerCase();
        const searchText = `${template.name} ${template.description} ${template.metadata.tags.join(' ')}`.toLowerCase();
        if (!searchText.includes(query)) return false;
      }
      
      // Category filter
      if (filters.category && template.category !== filters.category) return false;
      
      // Language filter
      if (filters.language && template.language !== filters.language) return false;
      
      // Framework filter
      if (filters.framework && template.framework !== filters.framework) return false;
      
      // Difficulty filter
      if (filters.difficulty && template.metadata.difficulty !== filters.difficulty) return false;
      
      // Rating filter
      if (filters.minRating > 0 && template.metadata.rating < filters.minRating) return false;
      
      // Tags filter
      if (filters.tags.length > 0) {
        const hasAllTags = filters.tags.every(tag => 
          template.metadata.tags.some(templateTag => 
            templateTag.toLowerCase().includes(tag.toLowerCase())
          )
        );
        if (!hasAllTags) return false;
      }
      
      return true;
    });

    // Sort templates
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (filters.sortBy) {
        case 'name':
          comparison = a.name.localeCompare(b.name);
          break;
        case 'rating':
          comparison = b.metadata.rating - a.metadata.rating;
          break;
        case 'downloads':
          comparison = b.metadata.downloadCount - a.metadata.downloadCount;
          break;
        case 'updated':
          comparison = new Date(b.metadata.lastUpdated).getTime() - new Date(a.metadata.lastUpdated).getTime();
          break;
        case 'created':
          comparison = new Date(b.metadata.lastUpdated).getTime() - new Date(a.metadata.lastUpdated).getTime();
          break;
      }
      
      return filters.sortOrder === 'asc' ? comparison : -comparison;
    });

    return filtered;
  }, [templates, filters]);

  // Get available filter options
  const filterOptions = useMemo(() => {
    const categories = [...new Set(templates.map(t => t.category))];
    const languages = [...new Set(templates.map(t => t.language))];
    const frameworks = [...new Set(templates.map(t => t.framework))];
    const difficulties = [...new Set(templates.map(t => t.metadata.difficulty))];
    const allTags = [...new Set(templates.flatMap(t => t.metadata.tags))];
    
    return { categories, languages, frameworks, difficulties, allTags };
  }, [templates]);

  const handleTemplateClick = (template: Template) => {
    setSelectedTemplate(template);
    setShowPreview(true);
  };

  const handleUseTemplate = (template: Template) => {
    if (template.configuration.requiredFields.length > 0 || Object.keys(template.configuration.schema.properties || {}).length > 0) {
      setSelectedTemplate(template);
      setShowCustomizer(true);
    } else {
      onTemplateSelect(template);
    }
  };

  const handleCustomizationComplete = (template: Template, customization: Record<string, any>) => {
    onTemplateSelect(template, customization);
    setShowCustomizer(false);
  };

  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'beginner': return 'bg-green-100 text-green-700 border-green-200';
      case 'intermediate': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'advanced': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'built-in': return '🏗️';
      case 'custom': return '🎨';
      case 'community': return '👥';
      default: return '📦';
    }
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Template Selection
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Choose a template to get started quickly with your MCP server
          </p>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')}
          >
            {viewMode === 'grid' ? <List className="h-4 w-4" /> : <Grid className="h-4 w-4" />}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowFilters(!showFilters)}
          >
            <Filter className="h-4 w-4 mr-2" />
            Filters
            {showFilters ? <ChevronUp className="h-4 w-4 ml-2" /> : <ChevronDown className="h-4 w-4 ml-2" />}
          </Button>
        </div>
      </div>

      {/* Search and Quick Filters */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
          <Input
            placeholder="Search templates by name, description, or tags..."
            value={filters.query}
            onChange={(e) => setFilters(prev => ({ ...prev, query: e.target.value }))}
            className="pl-10"
          />
        </div>
        
        <div className="flex items-center space-x-2">
          <select
            value={filters.sortBy}
            onChange={(e) => setFilters(prev => ({ ...prev, sortBy: e.target.value as any }))}
            className="px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
          >
            <option value="rating">Rating</option>
            <option value="downloads">Downloads</option>
            <option value="name">Name</option>
            <option value="updated">Updated</option>
          </select>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => setFilters(prev => ({ 
              ...prev, 
              sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc' 
            }))}
          >
            {filters.sortOrder === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <Card className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Category
              </label>
              <select
                value={filters.category}
                onChange={(e) => setFilters(prev => ({ ...prev, category: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option value="">All Categories</option>
                {filterOptions.categories.map(category => (
                  <option key={category} value={category}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Language
              </label>
              <select
                value={filters.language}
                onChange={(e) => setFilters(prev => ({ ...prev, language: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option value="">All Languages</option>
                {filterOptions.languages.map(language => (
                  <option key={language} value={language}>
                    {language.charAt(0).toUpperCase() + language.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Difficulty
              </label>
              <select
                value={filters.difficulty}
                onChange={(e) => setFilters(prev => ({ ...prev, difficulty: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option value="">All Levels</option>
                {filterOptions.difficulties.map(difficulty => (
                  <option key={difficulty} value={difficulty}>
                    {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                  </option>
                ))}
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Min Rating
              </label>
              <select
                value={filters.minRating}
                onChange={(e) => setFilters(prev => ({ ...prev, minRating: Number(e.target.value) }))}
                className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-md bg-white dark:bg-gray-800 text-sm"
              >
                <option value={0}>Any Rating</option>
                <option value={4}>4+ Stars</option>
                <option value={4.5}>4.5+ Stars</option>
                <option value={4.8}>4.8+ Stars</option>
              </select>
            </div>
          </div>
        </Card>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
        <span>
          {filteredTemplates.length} template{filteredTemplates.length !== 1 ? 's' : ''} found
        </span>
        
        {(filters.query || filters.category || filters.language || filters.difficulty || filters.minRating > 0) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setFilters({
              query: '',
              category: '',
              language: selectedLanguage || '',
              framework: selectedFramework || '',
              difficulty: '',
              minRating: 0,
              tags: [],
              sortBy: 'rating',
              sortOrder: 'desc'
            })}
          >
            Clear Filters
          </Button>
        )}
      </div>

      {/* Template Grid/List */}
      <div className={viewMode === 'grid' 
        ? 'grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6' 
        : 'space-y-4'
      }>
        {filteredTemplates.map((template) => (
          <Card
            key={template.id}
            className={`cursor-pointer transition-all hover:shadow-lg border-2 hover:border-blue-200 dark:hover:border-blue-800 ${
              viewMode === 'list' ? 'p-4' : 'p-6'
            }`}
            onClick={() => handleTemplateClick(template)}
          >
            <CardHeader className={viewMode === 'list' ? 'pb-2' : 'pb-4'}>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">
                    {getCategoryIcon(template.category)}
                  </div>
                  <div className="flex-1 min-w-0">
                    <CardTitle className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {template.name}
                    </CardTitle>
                    <div className="flex items-center space-x-2 mt-1">
                      <Badge variant="secondary" className="text-xs">
                        {template.language}
                      </Badge>
                      <Badge 
                        variant="outline" 
                        className={`text-xs ${getDifficultyColor(template.metadata.difficulty)}`}
                      >
                        {template.metadata.difficulty}
                      </Badge>
                    </div>
                  </div>
                </div>
                
                <div className="flex items-center space-x-1 text-sm text-gray-500">
                  <Star className="h-4 w-4 text-yellow-500 fill-current" />
                  <span>{template.metadata.rating}</span>
                </div>
              </div>
            </CardHeader>
            
            <CardContent>
              <p className="text-gray-600 dark:text-gray-400 text-sm mb-4 line-clamp-2">
                {template.description}
              </p>
              
              <div className="flex flex-wrap gap-1 mb-4">
                {template.metadata.tags.slice(0, 3).map((tag, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {tag}
                  </Badge>
                ))}
                {template.metadata.tags.length > 3 && (
                  <Badge variant="outline" className="text-xs">
                    +{template.metadata.tags.length - 3}
                  </Badge>
                )}
              </div>
              
              <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-4">
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-1">
                    <Download className="h-3 w-3" />
                    <span>{template.metadata.downloadCount}</span>
                  </div>
                  <div className="flex items-center space-x-1">
                    <Clock className="h-3 w-3" />
                    <span>{template.metadata.estimatedTime}min</span>
                  </div>
                  {template.metadata.author && (
                    <div className="flex items-center space-x-1">
                      <User className="h-3 w-3" />
                      <span>{template.metadata.author}</span>
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex space-x-2">
                <Button 
                  size="sm" 
                  className="flex-1"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleUseTemplate(template);
                  }}
                >
                  Use Template
                </Button>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleTemplateClick(template);
                  }}
                >
                  <Eye className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredTemplates.length === 0 && (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-2">
            No templates found
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Try adjusting your search criteria or filters
          </p>
          <Button
            variant="outline"
            onClick={() => setFilters({
              query: '',
              category: '',
              language: selectedLanguage || '',
              framework: selectedFramework || '',
              difficulty: '',
              minRating: 0,
              tags: [],
              sortBy: 'rating',
              sortOrder: 'desc'
            })}
          >
            Clear All Filters
          </Button>
        </div>
      )}

      {/* Template Preview Modal */}
      {showPreview && selectedTemplate && (
        <TemplatePreview
          template={selectedTemplate}
          onClose={() => {
            setShowPreview(false);
            setSelectedTemplate(null);
          }}
          onUseTemplate={() => {
            setShowPreview(false);
            handleUseTemplate(selectedTemplate);
          }}
        />
      )}

      {/* Template Customizer Modal */}
      {showCustomizer && selectedTemplate && (
        <TemplateCustomizer
          template={selectedTemplate}
          onComplete={handleCustomizationComplete}
          onCancel={() => {
            setShowCustomizer(false);
            setSelectedTemplate(null);
          }}
        />
      )}
    </div>
  );
};