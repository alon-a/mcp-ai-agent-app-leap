import { api } from "encore.dev/api";
import { 
  CreateProjectRequest, 
  CreateProjectResponse, 
  ProjectProgressResponse, 
  ValidationRequest, 
  ValidationResponse 
} from './types';
import { PythonAPIClient } from './client';

// Configuration from environment variables
const pythonAPIUrl = process.env.PYTHON_API_URL;
const pythonAPIKey = process.env.PYTHON_API_KEY;

// Initialize Python API client
const pythonClient = new PythonAPIClient(
  {
    baseUrl: pythonAPIUrl || 'http://localhost:8000',
    timeout: 30000, // 30 seconds
    retryAttempts: 3,
    retryDelay: 1000, // 1 second base delay
    apiKey: pythonAPIKey,
  },
  {
    maxConnections: 10,
    connectionTimeout: 5000,
    idleTimeout: 30000,
    keepAlive: true,
  }
);

// Request/Response interfaces for API endpoints
interface AuthenticatedRequest {
  userId: string;
}

interface CreateProjectAPIRequest extends AuthenticatedRequest {
  project: Omit<CreateProjectRequest, 'userId'>;
}

interface ProjectProgressAPIRequest extends AuthenticatedRequest {
  projectId: string;
}

interface CancelProjectAPIRequest extends AuthenticatedRequest {
  projectId: string;
}

interface ValidateProjectAPIRequest extends AuthenticatedRequest {
  validation: ValidationRequest;
}

// Authentication middleware
function authenticateUser(req: AuthenticatedRequest): void {
  if (!req.userId) {
    throw api.APIError.unauthenticated("User ID is required");
  }
  
  // Additional authentication logic can be added here
  // For now, we just validate that userId is present
}

// Error transformation utility
function handlePythonAPIError(error: any): never {
  console.error('Python API Error:', error);
  
  if (error.message?.includes('timeout')) {
    throw api.APIError.unavailable("Python service is temporarily unavailable");
  }
  
  if (error.message?.includes('Connection pool exhausted')) {
    throw api.APIError.resourceExhausted("Too many concurrent requests. Please try again later.");
  }
  
  if (error.message?.includes('HTTP 400')) {
    throw api.APIError.invalidArgument("Invalid request parameters");
  }
  
  if (error.message?.includes('HTTP 401')) {
    throw api.APIError.unauthenticated("Authentication failed with Python service");
  }
  
  if (error.message?.includes('HTTP 403')) {
    throw api.APIError.permissionDenied("Access denied to Python service");
  }
  
  if (error.message?.includes('HTTP 404')) {
    throw api.APIError.notFound("Requested resource not found");
  }
  
  if (error.message?.includes('HTTP 5')) {
    throw api.APIError.internal("Python service internal error");
  }
  
  throw api.APIError.internal(`Unexpected error: ${error.message}`);
}

// API Endpoints

export const createProject = api(
  { method: "POST", path: "/python-bridge/projects", expose: true },
  async (req: CreateProjectAPIRequest): Promise<CreateProjectResponse> => {
    try {
      authenticateUser(req);
      
      const projectRequest: CreateProjectRequest = {
        ...req.project,
        userId: req.userId,
      };
      
      const response = await pythonClient.createProject(projectRequest);
      
      return response;
    } catch (error) {
      handlePythonAPIError(error);
    }
  }
);

export const getProjectProgress = api(
  { method: "GET", path: "/python-bridge/projects/:projectId/progress", expose: true },
  async (req: ProjectProgressAPIRequest): Promise<ProjectProgressResponse> => {
    try {
      authenticateUser(req);
      
      const response = await pythonClient.getProjectProgress(req.projectId);
      
      return response;
    } catch (error) {
      handlePythonAPIError(error);
    }
  }
);

export const cancelProject = api(
  { method: "DELETE", path: "/python-bridge/projects/:projectId", expose: true },
  async (req: CancelProjectAPIRequest): Promise<{ success: boolean; message?: string }> => {
    try {
      authenticateUser(req);
      
      const response = await pythonClient.cancelProject(req.projectId);
      
      return response;
    } catch (error) {
      handlePythonAPIError(error);
    }
  }
);

export const validateProject = api(
  { method: "POST", path: "/python-bridge/validate", expose: true },
  async (req: ValidateProjectAPIRequest): Promise<ValidationResponse> => {
    try {
      authenticateUser(req);
      
      const response = await pythonClient.validateProject(req.validation);
      
      return response;
    } catch (error) {
      handlePythonAPIError(error);
    }
  }
);

export const getProjectStatus = api(
  { method: "GET", path: "/python-bridge/projects/:projectId/status", expose: true },
  async (req: ProjectProgressAPIRequest): Promise<{ status: string; message?: string }> => {
    try {
      authenticateUser(req);
      
      const response = await pythonClient.getProjectStatus(req.projectId);
      
      return response;
    } catch (error) {
      handlePythonAPIError(error);
    }
  }
);

// Health check endpoint
export const healthCheck = api(
  { method: "GET", path: "/python-bridge/health", expose: true },
  async (): Promise<{ status: string; connections: { active: number; max: number } }> => {
    try {
      const stats = pythonClient.getConnectionStats();
      
      return {
        status: 'healthy',
        connections: stats,
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        connections: { active: 0, max: 0 },
      };
    }
  }
);