import { 
  CreateProjectRequest, 
  CreateProjectResponse, 
  ProjectProgressResponse, 
  ValidationRequest, 
  ValidationResponse,
  PythonAPIConfig,
  ConnectionPoolConfig 
} from './types';

export class PythonAPIClient {
  private config: PythonAPIConfig;
  private connectionPool: Map<string, AbortController> = new Map();
  private activeConnections = 0;
  private maxConnections: number;

  constructor(config: PythonAPIConfig, poolConfig: ConnectionPoolConfig) {
    this.config = config;
    this.maxConnections = poolConfig.maxConnections;
  }

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    // Connection pooling check
    if (this.activeConnections >= this.maxConnections) {
      throw new Error('Connection pool exhausted');
    }

    const controller = new AbortController();
    const requestId = `${Date.now()}-${Math.random()}`;
    
    try {
      this.activeConnections++;
      this.connectionPool.set(requestId, controller);

      const url = `${this.config.baseUrl}${endpoint}`;
      const requestOptions: RequestInit = {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': this.config.apiKey ? `Bearer ${this.config.apiKey}` : '',
          ...options.headers,
        },
        timeout: this.config.timeout,
      };

      const response = await fetch(url, requestOptions);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      return data as T;

    } catch (error) {
      // Retry logic
      if (retryCount < this.config.retryAttempts && this.shouldRetry(error)) {
        await this.delay(this.config.retryDelay * Math.pow(2, retryCount));
        return this.makeRequest<T>(endpoint, options, retryCount + 1);
      }
      
      throw this.transformError(error);
    } finally {
      this.activeConnections--;
      this.connectionPool.delete(requestId);
    }
  }

  private shouldRetry(error: any): boolean {
    // Retry on network errors, timeouts, and 5xx status codes
    if (error.name === 'AbortError') return false;
    if (error.message?.includes('HTTP 4')) return false; // Don't retry client errors
    return true;
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  private transformError(error: any): Error {
    if (error.name === 'AbortError') {
      return new Error('Request timeout');
    }
    if (error.message?.includes('Connection pool exhausted')) {
      return new Error('Service temporarily unavailable - too many concurrent requests');
    }
    return error instanceof Error ? error : new Error(String(error));
  }

  // API Methods
  async createProject(request: CreateProjectRequest): Promise<CreateProjectResponse> {
    return this.makeRequest<CreateProjectResponse>('/api/v1/projects', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getProjectProgress(projectId: string): Promise<ProjectProgressResponse> {
    return this.makeRequest<ProjectProgressResponse>(`/api/v1/projects/${projectId}/progress`);
  }

  async cancelProject(projectId: string): Promise<{ success: boolean; message?: string }> {
    return this.makeRequest<{ success: boolean; message?: string }>(`/api/v1/projects/${projectId}`, {
      method: 'DELETE',
    });
  }

  async validateProject(request: ValidationRequest): Promise<ValidationResponse> {
    return this.makeRequest<ValidationResponse>('/api/v1/validate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getProjectStatus(projectId: string): Promise<{ status: string; message?: string }> {
    return this.makeRequest<{ status: string; message?: string }>(`/api/v1/projects/${projectId}/status`);
  }

  // Connection management
  cancelAllRequests(): void {
    for (const [requestId, controller] of this.connectionPool) {
      controller.abort();
      this.connectionPool.delete(requestId);
    }
    this.activeConnections = 0;
  }

  getConnectionStats(): { active: number; max: number } {
    return {
      active: this.activeConnections,
      max: this.maxConnections
    };
  }
}