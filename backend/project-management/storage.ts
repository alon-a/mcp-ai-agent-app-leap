import { 
  Project, 
  ProjectSummary, 
  ProjectVersion, 
  CreateProjectRequest, 
  UpdateProjectRequest,
  ProjectListRequest,
  ProjectListResponse,
  ProjectHistoryRequest,
  ProjectHistoryResponse
} from './types';

// In-memory storage implementation
// In production, this would be replaced with a proper database
class ProjectStorage {
  private projects: Map<string, Project> = new Map();
  private userProjects: Map<string, Set<string>> = new Map(); // userId -> projectIds

  private generateId(): string {
    return `proj_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private ensureUserProjectSet(userId: string): void {
    if (!this.userProjects.has(userId)) {
      this.userProjects.set(userId, new Set());
    }
  }

  private hasAccess(project: Project, userId: string, requiredPermission: 'read' | 'write' | 'admin' = 'read'): boolean {
    // Owner has full access
    if (project.userId === userId) {
      return true;
    }

    // Check sharing permissions
    const userPermission = project.sharing.permissions[userId];
    if (!userPermission) {
      return false;
    }

    // Permission hierarchy: admin > write > read
    const permissionLevels = { 'read': 1, 'write': 2, 'admin': 3 };
    return permissionLevels[userPermission] >= permissionLevels[requiredPermission];
  }

  async createProject(request: CreateProjectRequest): Promise<Project> {
    const projectId = this.generateId();
    const now = new Date();

    const project: Project = {
      id: projectId,
      name: request.name,
      description: request.description,
      userId: request.userId,
      status: 'draft',
      mode: request.mode,
      createdAt: now,
      updatedAt: now,
      configuration: request.configuration,
      metadata: {
        lastAccessedAt: now,
      },
      sharing: {
        isPublic: false,
        sharedWith: [],
        permissions: {},
      },
      version: {
        current: 1,
        history: [{
          version: 1,
          createdAt: now,
          configuration: request.configuration,
          notes: 'Initial version',
        }],
      },
    };

    this.projects.set(projectId, project);
    this.ensureUserProjectSet(request.userId);
    this.userProjects.get(request.userId)!.add(projectId);

    return project;
  }

  async getProject(projectId: string, userId: string): Promise<Project | null> {
    const project = this.projects.get(projectId);
    if (!project || !this.hasAccess(project, userId)) {
      return null;
    }

    // Update last accessed time
    project.metadata.lastAccessedAt = new Date();
    return project;
  }

  async updateProject(request: UpdateProjectRequest): Promise<Project | null> {
    const project = this.projects.get(request.id);
    if (!project || !this.hasAccess(project, request.userId, 'write')) {
      return null;
    }

    const now = new Date();
    let versionIncremented = false;

    // Update basic fields
    if (request.name !== undefined) {
      project.name = request.name;
    }
    if (request.description !== undefined) {
      project.description = request.description;
    }

    // Update configuration and create new version if changed
    if (request.configuration) {
      const configChanged = JSON.stringify(project.configuration) !== JSON.stringify(request.configuration);
      
      if (configChanged) {
        project.configuration = request.configuration;
        project.version.current += 1;
        project.version.history.push({
          version: project.version.current,
          createdAt: now,
          configuration: request.configuration,
          notes: 'Configuration updated',
        });
        versionIncremented = true;
      }
    }

    project.updatedAt = now;
    project.metadata.lastAccessedAt = now;

    return project;
  }

  async deleteProject(projectId: string, userId: string): Promise<boolean> {
    const project = this.projects.get(projectId);
    if (!project || !this.hasAccess(project, userId, 'admin')) {
      return false;
    }

    // Remove from user's project set
    this.userProjects.get(project.userId)?.delete(projectId);
    
    // Remove from shared users' access
    for (const sharedUserId of project.sharing.sharedWith) {
      this.userProjects.get(sharedUserId)?.delete(projectId);
    }

    // Delete the project
    this.projects.delete(projectId);
    return true;
  }

  async listProjects(request: ProjectListRequest): Promise<ProjectListResponse> {
    const { userId, status, mode, limit = 20, offset = 0, sortBy = 'updatedAt', sortOrder = 'desc', includeShared = true } = request;

    let projectIds: string[] = [];

    // Get user's own projects
    const userProjectIds = this.userProjects.get(userId) || new Set();
    projectIds.push(...Array.from(userProjectIds));

    // Add shared projects if requested
    if (includeShared) {
      for (const [projectId, project] of this.projects) {
        if (project.sharing.sharedWith.includes(userId) && !projectIds.includes(projectId)) {
          projectIds.push(projectId);
        }
      }
    }

    // Filter and map to projects
    let projects = projectIds
      .map(id => this.projects.get(id))
      .filter((project): project is Project => {
        if (!project) return false;
        if (status && project.status !== status) return false;
        if (mode && project.mode !== mode) return false;
        return true;
      });

    // Sort projects
    projects.sort((a, b) => {
      let aValue: any, bValue: any;
      
      switch (sortBy) {
        case 'name':
          aValue = a.name.toLowerCase();
          bValue = b.name.toLowerCase();
          break;
        case 'createdAt':
          aValue = a.createdAt.getTime();
          bValue = b.createdAt.getTime();
          break;
        case 'updatedAt':
        default:
          aValue = a.updatedAt.getTime();
          bValue = b.updatedAt.getTime();
          break;
      }

      if (sortOrder === 'asc') {
        return aValue < bValue ? -1 : aValue > bValue ? 1 : 0;
      } else {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      }
    });

    const total = projects.length;
    const paginatedProjects = projects.slice(offset, offset + limit);

    // Convert to summaries
    const projectSummaries: ProjectSummary[] = paginatedProjects.map(project => ({
      id: project.id,
      name: project.name,
      description: project.description,
      status: project.status,
      mode: project.mode,
      createdAt: project.createdAt,
      updatedAt: project.updatedAt,
      metadata: project.metadata,
      isShared: project.userId !== userId,
      canEdit: this.hasAccess(project, userId, 'write'),
    }));

    return {
      projects: projectSummaries,
      total,
      hasMore: offset + limit < total,
    };
  }

  async shareProject(projectId: string, ownerId: string, targetUserId: string, permission: 'read' | 'write' | 'admin'): Promise<boolean> {
    const project = this.projects.get(projectId);
    if (!project || !this.hasAccess(project, ownerId, 'admin')) {
      return false;
    }

    // Add to sharing
    if (!project.sharing.sharedWith.includes(targetUserId)) {
      project.sharing.sharedWith.push(targetUserId);
    }
    project.sharing.permissions[targetUserId] = permission;

    // Add to target user's project set
    this.ensureUserProjectSet(targetUserId);
    this.userProjects.get(targetUserId)!.add(projectId);

    project.updatedAt = new Date();
    return true;
  }

  async unshareProject(projectId: string, ownerId: string, targetUserId: string): Promise<boolean> {
    const project = this.projects.get(projectId);
    if (!project || !this.hasAccess(project, ownerId, 'admin')) {
      return false;
    }

    // Remove from sharing
    project.sharing.sharedWith = project.sharing.sharedWith.filter(id => id !== targetUserId);
    delete project.sharing.permissions[targetUserId];

    // Remove from target user's project set
    this.userProjects.get(targetUserId)?.delete(projectId);

    project.updatedAt = new Date();
    return true;
  }

  async getProjectHistory(request: ProjectHistoryRequest): Promise<ProjectHistoryResponse> {
    const { projectId, userId, limit = 10, offset = 0 } = request;
    
    const project = this.projects.get(projectId);
    if (!project || !this.hasAccess(project, userId)) {
      return { versions: [], total: 0, hasMore: false };
    }

    const versions = project.version.history
      .sort((a, b) => b.version - a.version) // Most recent first
      .slice(offset, offset + limit);

    return {
      versions,
      total: project.version.history.length,
      hasMore: offset + limit < project.version.history.length,
    };
  }

  async updateProjectStatus(projectId: string, status: Project['status']): Promise<boolean> {
    const project = this.projects.get(projectId);
    if (!project) {
      return false;
    }

    project.status = status;
    project.updatedAt = new Date();
    
    if (status === 'completed') {
      project.completedAt = new Date();
    }

    return true;
  }

  // Cleanup methods for resource management
  async cleanupOldProjects(olderThanDays: number = 30): Promise<number> {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);

    let deletedCount = 0;
    
    for (const [projectId, project] of this.projects) {
      if (project.status === 'failed' && project.updatedAt < cutoffDate) {
        await this.deleteProject(projectId, project.userId);
        deletedCount++;
      }
    }

    return deletedCount;
  }

  async getStorageStats(): Promise<{ totalProjects: number; projectsByStatus: Record<string, number>; projectsByMode: Record<string, number> }> {
    const stats = {
      totalProjects: this.projects.size,
      projectsByStatus: {} as Record<string, number>,
      projectsByMode: {} as Record<string, number>,
    };

    for (const project of this.projects.values()) {
      stats.projectsByStatus[project.status] = (stats.projectsByStatus[project.status] || 0) + 1;
      stats.projectsByMode[project.mode] = (stats.projectsByMode[project.mode] || 0) + 1;
    }

    return stats;
  }
}

// Export singleton instance
export const projectStorage = new ProjectStorage();