import { 
  Template, 
  TemplateSummary, 
  TemplateVersion,
  CreateTemplateRequest, 
  UpdateTemplateRequest,
  TemplateSearchRequest,
  TemplateSearchResponse,
  ValidationResult,
  ValidationError,
  ValidationWarning,
  TemplateRating,
  RateTemplateRequest,
  ForkTemplateRequest,
  TemplateUsageStats
} from './types';

// In-memory storage implementation
// In production, this would be replaced with a proper database
class TemplateStorage {
  private templates: Map<string, Template> = new Map();
  private userTemplates: Map<string, Set<string>> = new Map(); // userId -> templateIds
  private templateRatings: Map<string, TemplateRating[]> = new Map(); // templateId -> ratings
  private templateUsage: Map<string, TemplateUsageStats> = new Map(); // templateId -> stats

  constructor() {
    this.initializeBuiltInTemplates();
  }

  private generateId(): string {
    return `tpl_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private ensureUserTemplateSet(userId: string): void {
    if (!this.userTemplates.has(userId)) {
      this.userTemplates.set(userId, new Set());
    }
  }

  private hasAccess(template: Template, userId: string, requiredPermission: 'read' | 'write' | 'admin' = 'read'): boolean {
    // Built-in templates are readable by everyone
    if (template.category === 'built-in' && requiredPermission === 'read') {
      return true;
    }

    // Community templates are readable by everyone
    if (template.category === 'community' && template.sharing.isPublic && requiredPermission === 'read') {
      return true;
    }

    // Owner has full access
    if (template.createdBy === userId) {
      return true;
    }

    return false;
  }

  private initializeBuiltInTemplates(): void {
    const builtInTemplates: Partial<Template>[] = [
      {
        name: "Basic File System Server",
        description: "A simple MCP server that provides file system operations",
        language: "typescript",
        framework: "MCP SDK",
        metadata: {
          tags: ["filesystem", "basic", "beginner"],
          difficulty: "beginner",
          estimatedTime: 15,
        },
        configuration: {
          schema: {
            type: "object",
            properties: {
              rootPath: { type: "string", default: "./data" },
              allowedExtensions: { type: "array", items: { type: "string" }, default: [".txt", ".json", ".md"] },
            },
            required: ["rootPath"],
          },
          defaultValues: {
            rootPath: "./data",
            allowedExtensions: [".txt", ".json", ".md"],
          },
          requiredFields: ["rootPath"],
          conditionalFields: {},
        },
        dependencies: {
          runtime: {
            "@modelcontextprotocol/sdk": "^0.5.0",
          },
          development: {
            "typescript": "^5.0.0",
            "@types/node": "^20.0.0",
          },
          system: ["node >= 18"],
          services: [],
        },
      },
      {
        name: "Database Integration Server",
        description: "MCP server with database connectivity and ORM integration",
        language: "python",
        framework: "FastMCP",
        metadata: {
          tags: ["database", "orm", "intermediate"],
          difficulty: "intermediate",
          estimatedTime: 45,
        },
        configuration: {
          schema: {
            type: "object",
            properties: {
              databaseUrl: { type: "string" },
              databaseType: { type: "string", enum: ["postgresql", "mysql", "sqlite"] },
              enableMigrations: { type: "boolean", default: true },
            },
            required: ["databaseUrl", "databaseType"],
          },
          defaultValues: {
            databaseType: "postgresql",
            enableMigrations: true,
          },
          requiredFields: ["databaseUrl", "databaseType"],
          conditionalFields: {},
        },
        dependencies: {
          runtime: {
            "fastmcp": "^0.9.0",
            "sqlalchemy": "^2.0.0",
            "psycopg2-binary": "^2.9.0",
          },
          development: {
            "pytest": "^7.0.0",
            "black": "^23.0.0",
          },
          system: ["python >= 3.8"],
          services: ["postgresql"],
        },
      },
    ];

    builtInTemplates.forEach((templateData, index) => {
      const template: Template = {
        id: `builtin_${index + 1}`,
        name: templateData.name!,
        description: templateData.description!,
        category: 'built-in',
        language: templateData.language as any,
        framework: templateData.framework!,
        version: '1.0.0',
        metadata: {
          author: 'MCP Team',
          tags: templateData.metadata!.tags,
          difficulty: templateData.metadata!.difficulty as any,
          estimatedTime: templateData.metadata!.estimatedTime,
          lastUpdated: new Date(),
          downloadCount: Math.floor(Math.random() * 1000),
          rating: 4.5 + Math.random() * 0.5,
          ratingCount: Math.floor(Math.random() * 100) + 10,
        },
        configuration: templateData.configuration!,
        structure: {
          files: [],
          directories: ['src', 'tests', 'docs'],
          entryPoint: 'src/index.ts',
          buildScript: 'npm run build',
          testScript: 'npm test',
        },
        dependencies: templateData.dependencies!,
        sharing: {
          isPublic: true,
          isPublished: true,
          publishedAt: new Date(),
          license: 'MIT',
        },
        versioning: {
          current: '1.0.0',
          history: [{
            version: '1.0.0',
            createdAt: new Date(),
            changes: 'Initial version',
            configuration: templateData.configuration!,
            structure: {
              files: [],
              directories: ['src', 'tests', 'docs'],
              entryPoint: 'src/index.ts',
              buildScript: 'npm run build',
              testScript: 'npm test',
            },
            dependencies: templateData.dependencies!,
          }],
        },
        createdAt: new Date(),
        updatedAt: new Date(),
        createdBy: 'system',
      };

      this.templates.set(template.id, template);
    });
  }

  async createTemplate(request: CreateTemplateRequest): Promise<Template> {
    const templateId = this.generateId();
    const now = new Date();

    const template: Template = {
      id: templateId,
      name: request.name,
      description: request.description,
      category: 'custom',
      language: request.language,
      framework: request.framework,
      version: '1.0.0',
      metadata: {
        authorId: request.userId,
        tags: request.tags,
        difficulty: request.difficulty,
        estimatedTime: request.estimatedTime,
        lastUpdated: now,
        downloadCount: 0,
        rating: 0,
        ratingCount: 0,
      },
      configuration: request.configuration,
      structure: request.structure,
      dependencies: request.dependencies,
      sharing: {
        isPublic: false,
        isPublished: false,
        license: request.license,
      },
      versioning: {
        current: '1.0.0',
        history: [{
          version: '1.0.0',
          createdAt: now,
          changes: 'Initial version',
          configuration: request.configuration,
          structure: request.structure,
          dependencies: request.dependencies,
        }],
      },
      createdAt: now,
      updatedAt: now,
      createdBy: request.userId,
    };

    this.templates.set(templateId, template);
    this.ensureUserTemplateSet(request.userId);
    this.userTemplates.get(request.userId)!.add(templateId);

    // Initialize usage stats
    this.templateUsage.set(templateId, {
      templateId,
      totalDownloads: 0,
      recentDownloads: 0,
      totalProjects: 0,
      recentProjects: 0,
      averageRating: 0,
      ratingDistribution: {},
    });

    return template;
  }

  async getTemplate(templateId: string, userId: string): Promise<Template | null> {
    const template = this.templates.get(templateId);
    if (!template || !this.hasAccess(template, userId)) {
      return null;
    }

    return template;
  }

  async updateTemplate(request: UpdateTemplateRequest): Promise<Template | null> {
    const template = this.templates.get(request.id);
    if (!template || !this.hasAccess(template, request.userId, 'write')) {
      return null;
    }

    const now = new Date();
    let versionIncremented = false;

    // Update basic fields
    if (request.name !== undefined) {
      template.name = request.name;
    }
    if (request.description !== undefined) {
      template.description = request.description;
    }
    if (request.tags !== undefined) {
      template.metadata.tags = request.tags;
    }
    if (request.difficulty !== undefined) {
      template.metadata.difficulty = request.difficulty;
    }
    if (request.estimatedTime !== undefined) {
      template.metadata.estimatedTime = request.estimatedTime;
    }
    if (request.license !== undefined) {
      template.sharing.license = request.license;
    }

    // Update configuration, structure, or dependencies and create new version if changed
    const configChanged = request.configuration && JSON.stringify(template.configuration) !== JSON.stringify(request.configuration);
    const structureChanged = request.structure && JSON.stringify(template.structure) !== JSON.stringify(request.structure);
    const dependenciesChanged = request.dependencies && JSON.stringify(template.dependencies) !== JSON.stringify(request.dependencies);

    if (configChanged || structureChanged || dependenciesChanged) {
      if (request.configuration) template.configuration = request.configuration;
      if (request.structure) template.structure = request.structure;
      if (request.dependencies) template.dependencies = request.dependencies;

      // Increment version
      const versionParts = template.versioning.current.split('.').map(Number);
      versionParts[2]++; // Increment patch version
      template.versioning.current = versionParts.join('.');

      template.versioning.history.push({
        version: template.versioning.current,
        createdAt: now,
        changes: 'Template updated',
        configuration: template.configuration,
        structure: template.structure,
        dependencies: template.dependencies,
      });
      versionIncremented = true;
    }

    template.updatedAt = now;
    template.metadata.lastUpdated = now;

    return template;
  }

  async deleteTemplate(templateId: string, userId: string): Promise<boolean> {
    const template = this.templates.get(templateId);
    if (!template || !this.hasAccess(template, userId, 'admin')) {
      return false;
    }

    // Don't allow deletion of built-in templates
    if (template.category === 'built-in') {
      return false;
    }

    // Remove from user's template set
    this.userTemplates.get(template.createdBy)?.delete(templateId);

    // Delete the template
    this.templates.delete(templateId);
    this.templateRatings.delete(templateId);
    this.templateUsage.delete(templateId);

    return true;
  }

  async searchTemplates(request: TemplateSearchRequest): Promise<TemplateSearchResponse> {
    const { 
      query, 
      category, 
      language, 
      framework, 
      tags, 
      difficulty, 
      minRating = 0,
      sortBy = 'rating', 
      sortOrder = 'desc', 
      limit = 20, 
      offset = 0,
      userId 
    } = request;

    let templates = Array.from(this.templates.values()).filter(template => {
      // Access control
      if (!this.hasAccess(template, userId || '', 'read')) {
        return false;
      }

      // Text search
      if (query) {
        const searchText = `${template.name} ${template.description} ${template.metadata.tags.join(' ')}`.toLowerCase();
        if (!searchText.includes(query.toLowerCase())) {
          return false;
        }
      }

      // Category filter
      if (category && template.category !== category) {
        return false;
      }

      // Language filter
      if (language && template.language !== language && template.language !== 'multi') {
        return false;
      }

      // Framework filter
      if (framework && template.framework !== framework) {
        return false;
      }

      // Tags filter
      if (tags && tags.length > 0) {
        const hasAllTags = tags.every(tag => template.metadata.tags.includes(tag));
        if (!hasAllTags) {
          return false;
        }
      }

      // Difficulty filter
      if (difficulty && template.metadata.difficulty !== difficulty) {
        return false;
      }

      // Rating filter
      if (template.metadata.rating < minRating) {
        return false;
      }

      return true;
    });

    // Sort templates
    templates.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'downloads':
          aValue = a.metadata.downloadCount;
          bValue = b.metadata.downloadCount;
          break;
        case 'updated':
          aValue = a.updatedAt.getTime();
          bValue = b.updatedAt.getTime();
          break;
        case 'created':
          aValue = a.createdAt.getTime();
          bValue = b.createdAt.getTime();
          break;
        case 'rating':
        default:
          aValue = a.metadata.rating;
          bValue = b.metadata.rating;
          break;
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    const total = templates.length;
    const paginatedTemplates = templates.slice(offset, offset + limit);

    // Convert to summaries
    const templateSummaries: TemplateSummary[] = paginatedTemplates.map(template => ({
      id: template.id,
      name: template.name,
      description: template.description,
      category: template.category,
      language: template.language,
      framework: template.framework,
      version: template.version,
      metadata: template.metadata,
      isOwned: template.createdBy === userId,
      canEdit: this.hasAccess(template, userId || '', 'write'),
    }));

    // Calculate facets
    const facets = {
      categories: {} as Record<string, number>,
      languages: {} as Record<string, number>,
      frameworks: {} as Record<string, number>,
      tags: {} as Record<string, number>,
    };

    for (const template of templates) {
      facets.categories[template.category] = (facets.categories[template.category] || 0) + 1;
      facets.languages[template.language] = (facets.languages[template.language] || 0) + 1;
      facets.frameworks[template.framework] = (facets.frameworks[template.framework] || 0) + 1;
      
      for (const tag of template.metadata.tags) {
        facets.tags[tag] = (facets.tags[tag] || 0) + 1;
      }
    }

    return {
      templates: templateSummaries,
      total,
      hasMore: offset + limit < total,
      facets,
    };
  }

  async validateTemplate(templateId?: string, templateData?: Partial<Template>): Promise<ValidationResult> {
    const errors: ValidationError[] = [];
    const warnings: ValidationWarning[] = [];
    const suggestions: string[] = [];

    let template: Template | Partial<Template> | undefined;

    if (templateId) {
      template = this.templates.get(templateId);
      if (!template) {
        errors.push({
          field: 'templateId',
          message: 'Template not found',
          code: 'TEMPLATE_NOT_FOUND',
        });
        return { isValid: false, errors, warnings, suggestions };
      }
    } else if (templateData) {
      template = templateData;
    } else {
      errors.push({
        field: 'template',
        message: 'Either templateId or templateData must be provided',
        code: 'MISSING_TEMPLATE_DATA',
      });
      return { isValid: false, errors, warnings, suggestions };
    }

    // Validate required fields
    if (!template.name) {
      errors.push({
        field: 'name',
        message: 'Template name is required',
        code: 'MISSING_NAME',
      });
    }

    if (!template.description) {
      errors.push({
        field: 'description',
        message: 'Template description is required',
        code: 'MISSING_DESCRIPTION',
      });
    }

    if (!template.language) {
      errors.push({
        field: 'language',
        message: 'Template language is required',
        code: 'MISSING_LANGUAGE',
      });
    }

    // Validate configuration schema
    if (template.configuration?.schema) {
      try {
        JSON.stringify(template.configuration.schema);
      } catch (error) {
        errors.push({
          field: 'configuration.schema',
          message: 'Invalid JSON schema',
          code: 'INVALID_SCHEMA',
        });
      }
    }

    // Validate dependencies
    if (template.dependencies?.runtime) {
      for (const [pkg, version] of Object.entries(template.dependencies.runtime)) {
        if (!version || typeof version !== 'string') {
          warnings.push({
            field: `dependencies.runtime.${pkg}`,
            message: 'Package version should be specified',
            code: 'MISSING_VERSION',
          });
        }
      }
    }

    // Add suggestions
    if (template.metadata?.tags && template.metadata.tags.length === 0) {
      suggestions.push('Add tags to improve template discoverability');
    }

    if (!template.sharing?.license) {
      suggestions.push('Consider adding a license to clarify usage terms');
    }

    return {
      isValid: errors.length === 0,
      errors,
      warnings,
      suggestions,
    };
  }

  async rateTemplate(request: RateTemplateRequest): Promise<TemplateRating> {
    const template = this.templates.get(request.templateId);
    if (!template) {
      throw new Error('Template not found');
    }

    const now = new Date();
    const ratingId = `rating_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

    const rating: TemplateRating = {
      id: ratingId,
      templateId: request.templateId,
      userId: request.userId,
      rating: request.rating,
      review: request.review,
      createdAt: now,
      updatedAt: now,
    };

    // Store rating
    if (!this.templateRatings.has(request.templateId)) {
      this.templateRatings.set(request.templateId, []);
    }
    
    // Remove existing rating from this user
    const ratings = this.templateRatings.get(request.templateId)!;
    const existingIndex = ratings.findIndex(r => r.userId === request.userId);
    if (existingIndex >= 0) {
      ratings.splice(existingIndex, 1);
    }
    
    ratings.push(rating);

    // Update template rating statistics
    const avgRating = ratings.reduce((sum, r) => sum + r.rating, 0) / ratings.length;
    template.metadata.rating = Math.round(avgRating * 10) / 10;
    template.metadata.ratingCount = ratings.length;

    return rating;
  }

  async forkTemplate(request: ForkTemplateRequest): Promise<Template> {
    const originalTemplate = this.templates.get(request.templateId);
    if (!originalTemplate || !this.hasAccess(originalTemplate, request.userId, 'read')) {
      throw new Error('Template not found or access denied');
    }

    const now = new Date();
    const forkedTemplateId = this.generateId();

    const forkedTemplate: Template = {
      ...originalTemplate,
      id: forkedTemplateId,
      name: request.name,
      description: request.description || `Fork of ${originalTemplate.name}`,
      category: 'custom',
      metadata: {
        ...originalTemplate.metadata,
        authorId: request.userId,
        downloadCount: 0,
        rating: 0,
        ratingCount: 0,
        lastUpdated: now,
      },
      sharing: {
        isPublic: false,
        isPublished: false,
        license: originalTemplate.sharing.license,
      },
      versioning: {
        current: '1.0.0',
        history: [{
          version: '1.0.0',
          createdAt: now,
          changes: `Forked from ${originalTemplate.name} v${originalTemplate.versioning.current}`,
          configuration: originalTemplate.configuration,
          structure: originalTemplate.structure,
          dependencies: originalTemplate.dependencies,
        }],
        parentTemplate: request.templateId,
      },
      createdAt: now,
      updatedAt: now,
      createdBy: request.userId,
    };

    this.templates.set(forkedTemplateId, forkedTemplate);
    this.ensureUserTemplateSet(request.userId);
    this.userTemplates.get(request.userId)!.add(forkedTemplateId);

    // Initialize usage stats
    this.templateUsage.set(forkedTemplateId, {
      templateId: forkedTemplateId,
      totalDownloads: 0,
      recentDownloads: 0,
      totalProjects: 0,
      recentProjects: 0,
      averageRating: 0,
      ratingDistribution: {},
    });

    return forkedTemplate;
  }

  async getTemplateUsageStats(templateId: string): Promise<TemplateUsageStats | null> {
    return this.templateUsage.get(templateId) || null;
  }

  async incrementDownloadCount(templateId: string): Promise<void> {
    const template = this.templates.get(templateId);
    if (template) {
      template.metadata.downloadCount++;
    }

    const stats = this.templateUsage.get(templateId);
    if (stats) {
      stats.totalDownloads++;
      stats.recentDownloads++;
    }
  }

  async getStorageStats(): Promise<{
    totalTemplates: number;
    templatesByCategory: Record<string, number>;
    templatesByLanguage: Record<string, number>;
    totalDownloads: number;
  }> {
    const stats = {
      totalTemplates: this.templates.size,
      templatesByCategory: {} as Record<string, number>,
      templatesByLanguage: {} as Record<string, number>,
      totalDownloads: 0,
    };

    for (const template of this.templates.values()) {
      stats.templatesByCategory[template.category] = (stats.templatesByCategory[template.category] || 0) + 1;
      stats.templatesByLanguage[template.language] = (stats.templatesByLanguage[template.language] || 0) + 1;
      stats.totalDownloads += template.metadata.downloadCount;
    }

    return stats;
  }
}

// Export singleton instance
export const templateStorage = new TemplateStorage();