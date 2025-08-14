import { api } from "encore.dev/api";
import { 
  Project,
  ProjectSummary,
  CreateProjectRequest,
  UpdateProjectRequest,
  ShareProjectRequest,
  ProjectListRequest,
  ProjectListResponse,
  ProjectHistoryRequest,
  ProjectHistoryResponse
} from './types';
import { projectStorage } from './storage';

// Request/Response interfaces for API endpoints
interface AuthenticatedRequest {
  userId: string;
}

interface CreateProjectAPIRequest extends AuthenticatedRequest {
  project: Omit<CreateProjectRequest, 'userId'>;
}

interface GetProjectAPIRequest extends AuthenticatedRequest {
  projectId: string;
}

interface UpdateProjectAPIRequest extends AuthenticatedRequest {
  projectId: string;
  updates: Omit<UpdateProjectRequest, 'id' | 'userId'>;
}

interface DeleteProjectAPIRequest extends AuthenticatedRequest {
  projectId: string;
}

interface ShareProjectAPIRequest extends AuthenticatedRequest {
  projectId: string;
  targetUserId: string;
  permission: 'read' | 'write' | 'admin';
}

interface UnshareProjectAPIRequest extends AuthenticatedRequest {
  projectId: string;
  targetUserId: string;
}

interface ListProjectsAPIRequest extends AuthenticatedRequest {
  status?: Project['status'];
  mode?: Project['mode'];
  limit?: number;
  offset?: number;
  sortBy?: 'createdAt' | 'updatedAt' | 'name';
  sortOrder?: 'asc' | 'desc';
  includeShared?: boolean;
}

interface GetProjectHistoryAPIRequest extends AuthenticatedRequest {
  projectId: string;
  limit?: number;
  offset?: number;
}

interface UpdateProjectStatusAPIRequest {
  projectId: string;
  status: Project['status'];
  // This endpoint is for internal use by other services
}

// Authentication middleware
function authenticateUser(req: AuthenticatedRequest): void {
  if (!req.userId) {
    throw api.APIError.unauthenticated("User ID is required");
  }
}

// Error handling utility
function handleStorageError(error: any, operation: string): never {
  console.error(`Project Management ${operation} Error:`, error);
  throw api.APIError.internal(`Failed to ${operation}: ${error.message}`);
}

// API Endpoints

export const createProject = api(
  { method: "POST", path: "/project-management/projects", expose: true },
  async (req: CreateProjectAPIRequest): Promise<Project> => {
    try {
      authenticateUser(req);
      
      const createRequest: CreateProjectRequest = {
        ...req.project,
        userId: req.userId,
      };
      
      const project = await projectStorage.createProject(createRequest);
      return project;
    } catch (error) {
      handleStorageError(error, 'create project');
    }
  }
);

export const getProject = api(
  { method: "GET", path: "/project-management/projects/:projectId", expose: true },
  async (req: GetProjectAPIRequest): Promise<Project> => {
    try {
      authenticateUser(req);
      
      const project = await projectStorage.getProject(req.projectId, req.userId);
      if (!project) {
        throw api.APIError.notFound("Project not found or access denied");
      }
      
      return project;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'get project');
    }
  }
);

export const updateProject = api(
  { method: "PUT", path: "/project-management/projects/:projectId", expose: true },
  async (req: UpdateProjectAPIRequest): Promise<Project> => {
    try {
      authenticateUser(req);
      
      const updateRequest: UpdateProjectRequest = {
        id: req.projectId,
        ...req.updates,
        userId: req.userId,
      };
      
      const project = await projectStorage.updateProject(updateRequest);
      if (!project) {
        throw api.APIError.notFound("Project not found or access denied");
      }
      
      return project;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'update project');
    }
  }
);

export const deleteProject = api(
  { method: "DELETE", path: "/project-management/projects/:projectId", expose: true },
  async (req: DeleteProjectAPIRequest): Promise<{ success: boolean }> => {
    try {
      authenticateUser(req);
      
      const success = await projectStorage.deleteProject(req.projectId, req.userId);
      if (!success) {
        throw api.APIError.notFound("Project not found or access denied");
      }
      
      return { success: true };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'delete project');
    }
  }
);

export const listProjects = api(
  { method: "GET", path: "/project-management/projects", expose: true },
  async (req: ListProjectsAPIRequest): Promise<ProjectListResponse> => {
    try {
      authenticateUser(req);
      
      const listRequest: ProjectListRequest = {
        userId: req.userId,
        status: req.status,
        mode: req.mode,
        limit: req.limit,
        offset: req.offset,
        sortBy: req.sortBy,
        sortOrder: req.sortOrder,
        includeShared: req.includeShared,
      };
      
      const response = await projectStorage.listProjects(listRequest);
      return response;
    } catch (error) {
      handleStorageError(error, 'list projects');
    }
  }
);

export const shareProject = api(
  { method: "POST", path: "/project-management/projects/:projectId/share", expose: true },
  async (req: ShareProjectAPIRequest): Promise<{ success: boolean }> => {
    try {
      authenticateUser(req);
      
      if (req.userId === req.targetUserId) {
        throw api.APIError.invalidArgument("Cannot share project with yourself");
      }
      
      const success = await projectStorage.shareProject(
        req.projectId, 
        req.userId, 
        req.targetUserId, 
        req.permission
      );
      
      if (!success) {
        throw api.APIError.notFound("Project not found or access denied");
      }
      
      return { success: true };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'share project');
    }
  }
);

export const unshareProject = api(
  { method: "DELETE", path: "/project-management/projects/:projectId/share/:targetUserId", expose: true },
  async (req: UnshareProjectAPIRequest): Promise<{ success: boolean }> => {
    try {
      authenticateUser(req);
      
      const success = await projectStorage.unshareProject(
        req.projectId, 
        req.userId, 
        req.targetUserId
      );
      
      if (!success) {
        throw api.APIError.notFound("Project not found or access denied");
      }
      
      return { success: true };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleStorageError(error, 'unshare project');
    }
  }
);

export const getProjectHistory = api(
  { method: "GET", path: "/project-management/projects/:projectId/history", expose: true },
  async (req: GetProjectHistoryAPIRequest): Promise<ProjectHistoryResponse> => {
    try {
      authenticateUser(req);
      
      const historyRequest: ProjectHistoryRequest = {
        projectId: req.projectId,
        userId: req.userId,
        limit: req.limit,
        offset: req.offset,
      };
      
      const response = await projectStorage.getProjectHistory(historyRequest);
      return response;
    } catch (error) {
      handleStorageError(error, 'get project history');
    }
  }
);

// Internal API for other services to update project status
export const updateProjectStatus = api(
  { method: "PUT", path: "/project-management/internal/projects/:projectId/status", expose: false },
  async (req: UpdateProjectStatusAPIRequest): Promise<{ success: boolean }> => {
    try {
      const success = await projectStorage.updateProjectStatus(req.projectId, req.status);
      return { success };
    } catch (error) {
      handleStorageError(error, 'update project status');
    }
  }
);

// Admin/maintenance endpoints
export const cleanupOldProjects = api(
  { method: "POST", path: "/project-management/admin/cleanup", expose: false },
  async (req: { olderThanDays?: number }): Promise<{ deletedCount: number }> => {
    try {
      const deletedCount = await projectStorage.cleanupOldProjects(req.olderThanDays);
      return { deletedCount };
    } catch (error) {
      handleStorageError(error, 'cleanup old projects');
    }
  }
);

export const getStorageStats = api(
  { method: "GET", path: "/project-management/admin/stats", expose: false },
  async (): Promise<{ totalProjects: number; projectsByStatus: Record<string, number>; projectsByMode: Record<string, number> }> => {
    try {
      const stats = await projectStorage.getStorageStats();
      return stats;
    } catch (error) {
      handleStorageError(error, 'get storage stats');
    }
  }
);