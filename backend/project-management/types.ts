// Project Management types and interfaces

export interface Project {
  id: string;
  name: string;
  description?: string;
  userId: string;
  status: 'draft' | 'building' | 'completed' | 'failed' | 'cancelled';
  mode: 'quick' | 'advanced';
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  
  // Configuration
  configuration: ProjectConfiguration;
  
  // Metadata
  metadata: {
    language?: string;
    framework?: string;
    template?: string;
    fileCount?: number;
    buildDuration?: number;
    lastAccessedAt?: Date;
  };
  
  // Sharing and collaboration
  sharing: {
    isPublic: boolean;
    sharedWith: string[]; // User IDs
    permissions: Record<string, 'read' | 'write' | 'admin'>;
  };
  
  // Version information
  version: {
    current: number;
    history: ProjectVersion[];
  };
}

export interface ProjectConfiguration {
  // Quick mode configuration
  quickConfig?: {
    serverType: 'file_system' | 'database' | 'api_integration' | 'git_repository' | 'custom';
    basicSettings: Record<string, any>;
  };
  
  // Advanced mode configuration
  advancedConfig?: {
    template: string;
    language: 'python' | 'typescript' | 'go' | 'rust' | 'java';
    framework: string;
    customSettings: Record<string, any>;
    environmentVariables: Record<string, string>;
    additionalDependencies: string[];
    productionFeatures: {
      enableDocker: boolean;
      enableKubernetes: boolean;
      enableMonitoring: boolean;
      enableSecurity: boolean;
    };
  };
}

export interface ProjectVersion {
  version: number;
  createdAt: Date;
  configuration: ProjectConfiguration;
  buildId?: string;
  notes?: string;
  fileSnapshot?: string; // Reference to stored files
}

export interface ProjectSummary {
  id: string;
  name: string;
  description?: string;
  status: Project['status'];
  mode: Project['mode'];
  createdAt: Date;
  updatedAt: Date;
  metadata: Project['metadata'];
  isShared: boolean;
  canEdit: boolean;
}

export interface CreateProjectRequest {
  name: string;
  description?: string;
  mode: 'quick' | 'advanced';
  configuration: ProjectConfiguration;
  userId: string;
}

export interface UpdateProjectRequest {
  id: string;
  name?: string;
  description?: string;
  configuration?: ProjectConfiguration;
  userId: string;
}

export interface ShareProjectRequest {
  projectId: string;
  userId: string;
  targetUserId: string;
  permission: 'read' | 'write' | 'admin';
}

export interface ProjectListRequest {
  userId: string;
  status?: Project['status'];
  mode?: Project['mode'];
  limit?: number;
  offset?: number;
  sortBy?: 'createdAt' | 'updatedAt' | 'name';
  sortOrder?: 'asc' | 'desc';
  includeShared?: boolean;
}

export interface ProjectListResponse {
  projects: ProjectSummary[];
  total: number;
  hasMore: boolean;
}

export interface ProjectHistoryRequest {
  projectId: string;
  userId: string;
  limit?: number;
  offset?: number;
}

export interface ProjectHistoryResponse {
  versions: ProjectVersion[];
  total: number;
  hasMore: boolean;
}