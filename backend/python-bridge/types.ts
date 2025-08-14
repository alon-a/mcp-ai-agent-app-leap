// Request/Response types for Python API communication

export interface CreateProjectRequest {
  name: string;
  description?: string;
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
  userId: string;
}

export interface CreateProjectResponse {
  projectId: string;
  status: 'initiated' | 'queued' | 'in_progress' | 'completed' | 'failed';
  message?: string;
}

export interface ProjectProgressResponse {
  projectId: string;
  phase: string;
  percentage: number;
  message: string;
  timestamp: string;
  estimatedTimeRemaining?: number;
  errors?: ErrorEntry[];
}

export interface ErrorEntry {
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  phase: string;
  timestamp: string;
  recoveryActions?: string[];
}

export interface ValidationRequest {
  projectId: string;
  validationType: 'basic' | 'comprehensive' | 'custom';
  customRules?: string[];
}

export interface ValidationResponse {
  projectId: string;
  status: 'passed' | 'failed' | 'warning';
  results: ValidationResult[];
  summary: {
    totalChecks: number;
    passed: number;
    failed: number;
    warnings: number;
  };
}

export interface ValidationResult {
  rule: string;
  status: 'passed' | 'failed' | 'warning';
  message: string;
  file?: string;
  line?: number;
  suggestions?: string[];
}

export interface PythonAPIConfig {
  baseUrl: string;
  timeout: number;
  retryAttempts: number;
  retryDelay: number;
  apiKey?: string;
}

export interface ConnectionPoolConfig {
  maxConnections: number;
  connectionTimeout: number;
  idleTimeout: number;
  keepAlive: boolean;
}