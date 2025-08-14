import { api } from "encore.dev/api";
import { 
  Template,
  TemplateSummary,
  CreateTemplateRequest,
  UpdateTemplateRequest,
  ImportTemplateRequest,
  ExportTemplateRequest,
  TemplateSearchRequest,
  TemplateSearchResponse,
  ValidateTemplateRequest,
  ValidationResult,
  RateTemplateRequest,
  TemplateRating,
  ForkTemplateRequest,
  TemplateUsageStats
} from './types';
import { templateStorage } from './storage';

// Request/Response interfaces for API endpoints
interface AuthenticatedRequest {
  userId: string;
}

interface CreateTemplateAPIRequest extends AuthenticatedRequest {
  template: Omit<CreateTemplateRequest, 'userId'>;
}

interface GetTemplateAPIRequest extends AuthenticatedRequest {
  templateId: string;
}

interface UpdateTemplateAPIRequest extends AuthenticatedRequest {
  templateId: string;
  updates: Omit<UpdateTemplateRequest, 'id' | 'userId'>;
}

interface DeleteTemplateAPIRequest extends AuthenticatedRequest {
  templateId: string;
}

interface SearchTemplatesAPIRequest extends AuthenticatedRequest {
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
}

interface ValidateTemplateAPIRequest extends AuthenticatedRequest {
  templateId?: string;
  templateData?: Partial<Template>;
}

interface RateTemplateAPIRequest extends AuthenticatedRequest {
  templateId: string;
  rating: number;
  review?: string;
}

interface ForkTemplateAPIRequest extends AuthenticatedRequest {
  templateId: string;
  name: string;
  description?: string;
}

interface ImportTemplateAPIRequest extends AuthenticatedRequest {
  import: Omit<ImportTemplateRequest, 'userId'>;
}

interface ExportTemplateAPIRequest extends AuthenticatedRequest {
  templateId: string;
  format: 'zip' | 'json' | 'github';
  includeMetadata: boolean;
}

// Authentication middleware
function authenticateUser(req: AuthenticatedRequest): void {
  if (!req.userId) {
    throw api.APIError.unauthenticated("User ID is required");
  }
}

// Error handling utility
function handleStorageError(error: any, operation: string): never {
  console.error(`Template Management ${operation} Error:`, error);
  throw api.APIError.internal(`Failed to ${operation}: ${error.message}`);
}

// API Endpoints

export const createTemplate = api(
  { method: "POST", path: "/template-management/templates", expose: true },
  async (req: CreateTemplateAPIRequest): Promise<Template> => {
    try {
      authenticateUser(req);
      
      const createRequest: CreateTemplateRequest = {
        ...req.template,
        userId: req.userId,
      };
      
      const template = await templateStorage.createTemplate(createRequest);
      return template;
    } catch (error) {
      handleStorageError(error, 'create template');
    }
  }
);

export const getTemplate = api(
  { method: "GET", path: "/template-management/templates/:templateId", expose: true },
  async (req: GetTemplateAPIRequest): Promise<Template> => {
    try {
      authenticateUser(req);
      
      const template = await templateStorage.getTemplate(req.templateId, req.userId);
      if (!template) {
        throw api.APIError.notFound("Template not found or access denied");
      }
      
      return template;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'get template');
    }
  }
);

export const updateTemplate = api(
  { method: "PUT", path: "/template-management/templates/:templateId", expose: true },
  async (req: UpdateTemplateAPIRequest): Promise<Template> => {
    try {
      authenticateUser(req);
      
      const updateRequest: UpdateTemplateRequest = {
        id: req.templateId,
        ...req.updates,
        userId: req.userId,
      };
      
      const template = await templateStorage.updateTemplate(updateRequest);
      if (!template) {
        throw api.APIError.notFound("Template not found or access denied");
      }
      
      return template;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'update template');
    }
  }
);

export const deleteTemplate = api(
  { method: "DELETE", path: "/template-management/templates/:templateId", expose: true },
  async (req: DeleteTemplateAPIRequest): Promise<{ success: boolean }> => {
    try {
      authenticateUser(req);
      
      const success = await templateStorage.deleteTemplate(req.templateId, req.userId);
      if (!success) {
        throw api.APIError.notFound("Template not found, access denied, or cannot delete built-in template");
      }
      
      return { success: true };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'delete template');
    }
  }
);

export const searchTemplates = api(
  { method: "GET", path: "/template-management/templates", expose: true },
  async (req: SearchTemplatesAPIRequest): Promise<TemplateSearchResponse> => {
    try {
      authenticateUser(req);
      
      const searchRequest: TemplateSearchRequest = {
        query: req.query,
        category: req.category,
        language: req.language,
        framework: req.framework,
        tags: req.tags,
        difficulty: req.difficulty,
        minRating: req.minRating,
        sortBy: req.sortBy,
        sortOrder: req.sortOrder,
        limit: req.limit,
        offset: req.offset,
        userId: req.userId,
      };
      
      const response = await templateStorage.searchTemplates(searchRequest);
      return response;
    } catch (error) {
      handleStorageError(error, 'search templates');
    }
  }
);

export const validateTemplate = api(
  { method: "POST", path: "/template-management/templates/validate", expose: true },
  async (req: ValidateTemplateAPIRequest): Promise<ValidationResult> => {
    try {
      authenticateUser(req);
      
      const result = await templateStorage.validateTemplate(req.templateId, req.templateData);
      return result;
    } catch (error) {
      handleStorageError(error, 'validate template');
    }
  }
);

export const rateTemplate = api(
  { method: "POST", path: "/template-management/templates/:templateId/rate", expose: true },
  async (req: RateTemplateAPIRequest): Promise<TemplateRating> => {
    try {
      authenticateUser(req);
      
      if (req.rating < 1 || req.rating > 5) {
        throw api.APIError.invalidArgument("Rating must be between 1 and 5");
      }
      
      const rateRequest: RateTemplateRequest = {
        templateId: req.templateId,
        rating: req.rating,
        review: req.review,
        userId: req.userId,
      };
      
      const rating = await templateStorage.rateTemplate(rateRequest);
      return rating;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'rate template');
    }
  }
);

export const forkTemplate = api(
  { method: "POST", path: "/template-management/templates/:templateId/fork", expose: true },
  async (req: ForkTemplateAPIRequest): Promise<Template> => {
    try {
      authenticateUser(req);
      
      const forkRequest: ForkTemplateRequest = {
        templateId: req.templateId,
        name: req.name,
        description: req.description,
        userId: req.userId,
      };
      
      const forkedTemplate = await templateStorage.forkTemplate(forkRequest);
      return forkedTemplate;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'fork template');
    }
  }
);

export const importTemplate = api(
  { method: "POST", path: "/template-management/templates/import", expose: true },
  async (req: ImportTemplateAPIRequest): Promise<{ message: string; templateId?: string }> => {
    try {
      authenticateUser(req);
      
      // This is a placeholder implementation
      // In a real system, this would handle importing from various sources
      const importRequest: ImportTemplateRequest = {
        ...req.import,
        userId: req.userId,
      };
      
      // For now, return a message indicating the feature is not yet implemented
      return {
        message: "Template import functionality is not yet implemented. This would handle importing from GitHub, GitLab, files, or URLs.",
      };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'import template');
    }
  }
);

export const exportTemplate = api(
  { method: "POST", path: "/template-management/templates/:templateId/export", expose: true },
  async (req: ExportTemplateAPIRequest): Promise<{ downloadUrl: string; format: string }> => {
    try {
      authenticateUser(req);
      
      const template = await templateStorage.getTemplate(req.templateId, req.userId);
      if (!template) {
        throw api.APIError.notFound("Template not found or access denied");
      }
      
      // Increment download count
      await templateStorage.incrementDownloadCount(req.templateId);
      
      // This is a placeholder implementation
      // In a real system, this would generate the actual export file
      const exportRequest: ExportTemplateRequest = {
        templateId: req.templateId,
        format: req.format,
        includeMetadata: req.includeMetadata,
        userId: req.userId,
      };
      
      return {
        downloadUrl: `/template-management/templates/${req.templateId}/download?format=${req.format}`,
        format: req.format,
      };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'export template');
    }
  }
);

export const getTemplateUsageStats = api(
  { method: "GET", path: "/template-management/templates/:templateId/stats", expose: true },
  async (req: GetTemplateAPIRequest): Promise<TemplateUsageStats> => {
    try {
      authenticateUser(req);
      
      const stats = await templateStorage.getTemplateUsageStats(req.templateId);
      if (!stats) {
        throw api.APIError.notFound("Template stats not found");
      }
      
      return stats;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'get template usage stats');
    }
  }
);

// Admin/maintenance endpoints
export const getStorageStats = api(
  { method: "GET", path: "/template-management/admin/stats", expose: false },
  async (): Promise<{
    totalTemplates: number;
    templatesByCategory: Record<string, number>;
    templatesByLanguage: Record<string, number>;
    totalDownloads: number;
  }> => {
    try {
      const stats = await templateStorage.getStorageStats();
      return stats;
    } catch (error) {
      handleStorageError(error, 'get storage stats');
    }
  }
);

// Health check endpoint
export const healthCheck = api(
  { method: "GET", path: "/template-management/health", expose: true },
  async (): Promise<{ status: string; templateCount: number }> => {
    try {
      const stats = await templateStorage.getStorageStats();
      
      return {
        status: 'healthy',
        templateCount: stats.totalTemplates,
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        templateCount: 0,
      };
    }
  }
);