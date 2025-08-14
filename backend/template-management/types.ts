// Template Management types and interfaces

export interface Template {
  id: string;
  name: string;
  description: string;
  category: 'built-in' | 'custom' | 'community';
  language: 'python' | 'typescript' | 'go' | 'rust' | 'java' | 'multi';
  framework: string;
  version: string;
  
  // Template metadata
  metadata: {
    author?: string;
    authorId?: string;
    tags: string[];
    difficulty: 'beginner' | 'intermediate' | 'advanced';
    estimatedTime: number; // in minutes
    lastUpdated: Date;
    downloadCount: number;
    rating: number; // 0-5
    ratingCount: number;
  };
  
  // Template configuration
  configuration: {
    schema: JSONSchema; // JSON Schema for template configuration
    defaultValues: Record<string, any>;
    requiredFields: string[];
    conditionalFields: Record<string, ConditionalField>;
  };
  
  // Template files and structure
  structure: {
    files: TemplateFile[];
    directories: string[];
    entryPoint?: string;
    buildScript?: string;
    testScript?: string;
  };
  
  // Dependencies and requirements
  dependencies: {
    runtime: Record<string, string>; // package -> version
    development: Record<string, string>;
    system: string[]; // system requirements
    services: string[]; // external services needed
  };
  
  // Sharing and marketplace
  sharing: {
    isPublic: boolean;
    isPublished: boolean;
    publishedAt?: Date;
    license: string;
    repository?: string;
    documentation?: string;
  };
  
  // Version control
  versioning: {
    current: string;
    history: TemplateVersion[];
    parentTemplate?: string; // for forked templates
  };
  
  // Creation and ownership
  createdAt: Date;
  updatedAt: Date;
  createdBy: string; // userId
}

export interface TemplateFile {
  path: string;
  content: string;
  isTemplate: boolean; // true if file contains template variables
  encoding: 'utf8' | 'base64';
  permissions?: string; // unix permissions
}

export interface TemplateVersion {
  version: string;
  createdAt: Date;
  changes: string;
  configuration: Template['configuration'];
  structure: Template['structure'];
  dependencies: Template['dependencies'];
}

export interface ConditionalField {
  condition: string; // JavaScript expression
  fields: string[];
}

export interface JSONSchema {
  type: string;
  properties: Record<string, any>;
  required?: string[];
  additionalProperties?: boolean;
}

export interface TemplateSummary {
  id: string;
  name: string;
  description: string;
  category: Template['category'];
  language: Template['language'];
  framework: string;
  version: string;
  metadata: Template['metadata'];
  isOwned: boolean;
  canEdit: boolean;
}

export interface CreateTemplateRequest {
  name: string;
  description: string;
  language: Template['language'];
  framework: string;
  tags: string[];
  difficulty: Template['metadata']['difficulty'];
  estimatedTime: number;
  configuration: Template['configuration'];
  structure: Template['structure'];
  dependencies: Template['dependencies'];
  license: string;
  userId: string;
}

export interface UpdateTemplateRequest {
  id: string;
  name?: string;
  description?: string;
  tags?: string[];
  difficulty?: Template['metadata']['difficulty'];
  estimatedTime?: number;
  configuration?: Template['configuration'];
  structure?: Template['structure'];
  dependencies?: Template['dependencies'];
  license?: string;
  userId: string;
}

export interface ImportTemplateRequest {
  source: 'github' | 'gitlab' | 'file' | 'url';
  sourceUrl?: string;
  fileData?: string; // base64 encoded zip file
  name?: string;
  description?: string;
  userId: string;
}

export interface ExportTemplateRequest {
  templateId: string;
  format: 'zip' | 'json' | 'github';
  includeMetadata: boolean;
  userId: string;
}

export interface TemplateSearchRequest {
  query?: string;
  category?: Template['category'];
  language?: Template['language'];
  framework?: string;
  tags?: string[];
  difficulty?: Template['metadata']['difficulty'];
  minRating?: number;
  sortBy?: 'name' | 'rating' | 'downloads' | 'updated' | 'created';
  sortOrder?: 'asc' | 'desc';
  limit?: number;
  offset?: number;
  userId?: string; // for personalized results
}

export interface TemplateSearchResponse {
  templates: TemplateSummary[];
  total: number;
  hasMore: boolean;
  facets: {
    categories: Record<string, number>;
    languages: Record<string, number>;
    frameworks: Record<string, number>;
    tags: Record<string, number>;
  };
}

export interface ValidateTemplateRequest {
  templateId?: string;
  templateData?: Partial<Template>;
  userId: string;
}

export interface ValidationResult {
  isValid: boolean;
  errors: ValidationError[];
  warnings: ValidationWarning[];
  suggestions: string[];
}

export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationWarning {
  field: string;
  message: string;
  code: string;
}

export interface RateTemplateRequest {
  templateId: string;
  rating: number; // 1-5
  review?: string;
  userId: string;
}

export interface TemplateRating {
  id: string;
  templateId: string;
  userId: string;
  rating: number;
  review?: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface ForkTemplateRequest {
  templateId: string;
  name: string;
  description?: string;
  userId: string;
}

export interface TemplateUsageStats {
  templateId: string;
  totalDownloads: number;
  recentDownloads: number; // last 30 days
  totalProjects: number;
  recentProjects: number; // last 30 days
  averageRating: number;
  ratingDistribution: Record<number, number>; // rating -> count
}