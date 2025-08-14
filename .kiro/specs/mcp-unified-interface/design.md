# Design Document: MCP Unified Interface Integration

## Overview

This document outlines the technical design for integrating the MCP Assistant App with the MCP Server Builder into a unified web interface. The solution provides a seamless user experience that combines the simplicity of quick generation with the power of comprehensive automation.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Unified MCP Interface                        │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (React/TypeScript)                                   │
│  ├── Mode Selector Component                                   │
│  ├── Quick Generate Interface (Existing)                       │
│  ├── Advanced Build Interface (New)                            │
│  ├── Progress Monitoring Dashboard (New)                       │
│  ├── File Browser & Editor (Enhanced)                          │
│  ├── Template Manager (New)                                    │
│  └── AI Chat Assistant (Enhanced)                              │
├─────────────────────────────────────────────────────────────────┤
│  Backend (Encore.ts + Python Bridge)                           │
│  ├── Existing Encore.ts Services                               │
│  ├── Python Bridge Service (New)                               │
│  ├── Project Management Service (New)                          │
│  ├── Template Management Service (New)                         │
│  ├── Progress Tracking Service (New)                           │
│  └── File Management Service (Enhanced)                        │
├─────────────────────────────────────────────────────────────────┤
│  Integration Layer                                              │
│  ├── REST API Gateway                                          │
│  ├── WebSocket Connection (Progress Updates)                   │
│  ├── File Storage Service                                      │
│  └── Authentication & Authorization                            │
├─────────────────────────────────────────────────────────────────┤
│  MCP Server Builder (Python)                                   │
│  ├── HTTP API Wrapper (New)                                    │
│  ├── Project Manager                                           │
│  ├── Template Engine                                           │
│  ├── Build System                                              │
│  ├── Validation Engine                                         │
│  └── Progress Tracker                                          │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

#### 1. Frontend Components

##### Mode Selector Component
```typescript
interface ModeSelector {
  currentMode: 'quick' | 'advanced';
  onModeChange: (mode: 'quick' | 'advanced') => void;
  userExperience: 'beginner' | 'intermediate' | 'expert';
}
```

**Features:**
- Visual mode switcher with clear descriptions
- Progressive disclosure based on user experience level
- Contextual help and guidance
- Smooth transitions between modes

##### Advanced Build Interface
```typescript
interface AdvancedBuildInterface {
  templateSelector: TemplateSelector;
  configurationForm: ConfigurationForm;
  progressMonitor: ProgressMonitor;
  validationResults: ValidationResults;
}
```

**Features:**
- Multi-step wizard for complex configurations
- Real-time validation and preview
- Template customization interface
- Language and framework selection

##### Progress Monitoring Dashboard
```typescript
interface ProgressMonitor {
  currentPhase: string;
  percentage: number;
  estimatedTimeRemaining: number;
  phaseHistory: PhaseHistory[];
  errorLog: ErrorEntry[];
  cancelBuild: () => void;
}
```

**Features:**
- Real-time progress updates via WebSocket
- Phase-by-phase breakdown
- Error handling and recovery options
- Build cancellation capability

#### 2. Backend Services

##### Python Bridge Service
```typescript
// Encore.ts service
export const pythonBridge = api.service("python-bridge", {
  createProject: api.post("/create", createProjectHandler),
  getProgress: api.get("/progress/:projectId", getProgressHandler),
  cancelProject: api.delete("/cancel/:projectId", cancelProjectHandler),
  validateProject: api.post("/validate", validateProjectHandler),
});
```

**Implementation:**
- HTTP client for Python API communication
- Request/response transformation
- Error handling and retry logic
- Session management

##### Project Management Service
```typescript
interface ProjectManagementService {
  createProject(request: CreateProjectRequest): Promise<ProjectResult>;
  getProjectStatus(projectId: string): Promise<ProjectStatus>;
  listProjects(userId: string): Promise<ProjectSummary[]>;
  deleteProject(projectId: string): Promise<boolean>;
}
```

**Features:**
- Project lifecycle management
- User project isolation
- Project history and versioning
- Cleanup and resource management

#### 3. Integration Layer

##### REST API Gateway
```typescript
interface APIGateway {
  routes: {
    '/api/quick/*': QuickGenerateService;
    '/api/advanced/*': PythonBridgeService;
    '/api/projects/*': ProjectManagementService;
    '/api/templates/*': TemplateManagementService;
    '/api/files/*': FileManagementService;
  };
  middleware: [
    AuthenticationMiddleware,
    AuthorizationMiddleware,
    RateLimitingMiddleware,
    LoggingMiddleware
  ];
}
```

##### WebSocket Connection
```typescript
interface WebSocketService {
  connections: Map<string, WebSocket>;
  subscribeToProgress(projectId: string, userId: string): void;
  broadcastProgress(projectId: string, progress: ProgressUpdate): void;
  handleDisconnection(userId: string): void;
}
```

#### 4. MCP Server Builder HTTP API Wrapper

```python
# New HTTP API wrapper for MCP Server Builder
from fastapi import FastAPI, BackgroundTasks
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

app = FastAPI()

class MCPBuilderAPI:
    def __init__(self):
        self.project_manager = ProjectManagerImpl()
        self.active_projects = {}
    
    @app.post("/api/v1/projects")
    async def create_project(self, request: CreateProjectRequest, background_tasks: BackgroundTasks):
        project_id = str(uuid.uuid4())
        background_tasks.add_task(self._execute_project_creation, project_id, request)
        return {"project_id": project_id, "status": "initiated"}
    
    @app.get("/api/v1/projects/{project_id}/progress")
    async def get_progress(self, project_id: str):
        return self.project_manager.get_project_progress(project_id)
    
    @app.post("/api/v1/projects/{project_id}/validate")
    async def validate_project(self, project_id: str):
        return self.validation_engine.run_comprehensive_tests(project_path)
```

## Data Models

### Project Configuration
```typescript
interface UnifiedProjectConfig {
  // Basic configuration (both modes)
  name: string;
  description?: string;
  mode: 'quick' | 'advanced';
  
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
```

### Progress Tracking
```typescript
interface ProgressUpdate {
  projectId: string;
  phase: string;
  percentage: number;
  message: string;
  timestamp: Date;
  estimatedTimeRemaining?: number;
  errors?: ErrorEntry[];
}

interface ErrorEntry {
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  phase: string;
  timestamp: Date;
  recoveryActions?: string[];
}
```

### Template Management
```typescript
interface TemplateDefinition {
  id: string;
  name: string;
  description: string;
  category: 'built-in' | 'custom' | 'community';
  language: string;
  framework: string;
  configurationSchema: JSONSchema;
  previewFiles: string[];
  tags: string[];
  author?: string;
  version: string;
}
```

## User Interface Design

### Mode Selection Interface
```
┌─────────────────────────────────────────────────────────────────┐
│  🚀 MCP Server Generator - Choose Your Approach                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────┐    ┌─────────────────────────────────┐ │
│  │   🎯 Quick Generate  │    │   🏗️ Advanced Build            │ │
│  │                     │    │                                 │ │
│  │ • Fast & Simple     │    │ • Production Ready              │ │
│  │ • TypeScript/Node   │    │ • Multi-Language Support       │ │
│  │ • Immediate Results │    │ • Comprehensive Validation     │ │
│  │ • Perfect for       │    │ • Docker/K8s Configs          │ │
│  │   Learning          │    │ • Custom Templates             │ │
│  │                     │    │                                 │ │
│  │ [Start Quick Build] │    │ [Start Advanced Build]         │ │
│  └─────────────────────┘    └─────────────────────────────────┘ │
│                                                                 │
│  💡 Not sure which to choose? Ask our AI assistant! 💬         │
└─────────────────────────────────────────────────────────────────┘
```

### Advanced Build Configuration Interface
```
┌─────────────────────────────────────────────────────────────────┐
│  🏗️ Advanced MCP Server Builder                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Step 1: Project Basics                                        │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Project Name: [my-production-server        ]               │ │
│  │ Description:  [Production-ready MCP server ]               │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Step 2: Technology Stack                                      │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Language:  [Python ▼] [TypeScript] [Go] [Rust] [Java]     │ │
│  │ Framework: [FastMCP ▼] [Low-level SDK]                    │ │
│  │ Template:  [Custom Database Server ▼]                     │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  Step 3: Configuration (▼ Advanced Options)                    │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ Transport: [HTTP ▼] Port: [8080]                          │ │
│  │ ☑ Enable Monitoring  ☑ Enable Security  ☑ Enable Docker  │ │
│  │ ☐ Enable Kubernetes  ☐ Enable Caching   ☐ Enable Metrics │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [< Back] [Preview Configuration] [Start Build >]              │
└─────────────────────────────────────────────────────────────────┘
```

### Progress Monitoring Interface
```
┌─────────────────────────────────────────────────────────────────┐
│  🔄 Building: my-production-server                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Overall Progress: ████████████████████░░░░ 75% (3 min left)   │
│                                                                 │
│  Current Phase: Installing Dependencies                         │
│  ████████████████████████████████████████ 100%                 │
│                                                                 │
│  ┌─ Build Phases ─────────────────────────────────────────────┐ │
│  │ ✅ Template Preparation     (2.3s)                         │ │
│  │ ✅ Directory Creation       (0.8s)                         │ │
│  │ ✅ File Download           (15.2s)                         │ │
│  │ ✅ Template Customization   (3.1s)                         │ │
│  │ 🔄 Installing Dependencies  (45.7s) - pip install...      │ │
│  │ ⏳ Build Execution                                          │ │
│  │ ⏳ Validation & Testing                                     │ │
│  │ ⏳ Deployment Config                                        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  📊 Live Logs:                                                 │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │ [14:23:45] Installing sqlalchemy>=2.0.0...                │ │
│  │ [14:23:47] Installing redis>=4.5.0...                     │ │
│  │ [14:23:49] Installing prometheus-client>=0.17.0...        │ │
│  │ [14:23:51] All dependencies installed successfully        │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  [Cancel Build] [View Details] [Minimize]                      │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Strategy

### Phase 1: Foundation (Weeks 1-2)
1. **Python API Wrapper Development**
   - Create FastAPI wrapper for MCP Server Builder
   - Implement basic CRUD operations
   - Add progress tracking endpoints
   - Set up WebSocket support for real-time updates

2. **Backend Integration**
   - Extend Encore.ts backend with Python bridge service
   - Implement project management service
   - Add WebSocket support for progress updates
   - Set up file storage and management

### Phase 2: Frontend Integration (Weeks 3-4)
1. **Mode Selection Interface**
   - Create mode selector component
   - Implement smooth transitions between modes
   - Add contextual help and guidance
   - Integrate with existing quick generate functionality

2. **Advanced Build Interface**
   - Develop multi-step configuration wizard
   - Implement template selection and customization
   - Add real-time validation and preview
   - Create progress monitoring dashboard

### Phase 3: Enhanced Features (Weeks 5-6)
1. **Template Management**
   - Build template editor interface
   - Implement template import/export
   - Add template validation and testing
   - Create template marketplace foundation

2. **File Management Enhancement**
   - Enhance file browser with advanced features
   - Add inline editing capabilities
   - Implement project comparison tools
   - Add version control integration

### Phase 4: Production Features (Weeks 7-8)
1. **Deployment Integration**
   - Add deployment configuration interfaces
   - Implement cloud platform integrations
   - Create deployment monitoring dashboard
   - Add automated deployment pipelines

2. **Testing and Validation**
   - Integrate comprehensive testing interface
   - Add custom test scenario creation
   - Implement automated quality gates
   - Create detailed reporting system

## Error Handling

### Error Categories and Responses
```typescript
interface ErrorHandlingStrategy {
  categories: {
    'network': {
      retry: true;
      maxRetries: 3;
      backoffStrategy: 'exponential';
      userMessage: 'Connection issue - retrying automatically';
    };
    'validation': {
      retry: false;
      showDetails: true;
      suggestFix: true;
      userMessage: 'Configuration error - please review settings';
    };
    'build': {
      retry: true;
      maxRetries: 1;
      showLogs: true;
      userMessage: 'Build failed - check logs for details';
    };
    'system': {
      retry: false;
      escalate: true;
      userMessage: 'System error - support has been notified';
    };
  };
}
```

## Security Considerations

### Authentication and Authorization
- JWT-based authentication for API access
- Role-based access control (RBAC) for different user types
- Project-level permissions and isolation
- Secure session management

### Data Protection
- Encryption in transit (HTTPS/WSS)
- Encryption at rest for sensitive configuration data
- Input validation and sanitization
- File upload security scanning

### API Security
- Rate limiting on all endpoints
- Request size limits
- CORS configuration
- API key management for Python bridge

## Performance Optimization

### Frontend Performance
- Code splitting for mode-specific components
- Lazy loading of advanced features
- Optimistic UI updates
- Efficient state management with React Query

### Backend Performance
- Connection pooling for Python API calls
- Caching of template definitions and metadata
- Asynchronous processing for long-running operations
- Resource cleanup and garbage collection

### Scalability Considerations
- Horizontal scaling of Python API instances
- Load balancing for concurrent builds
- Queue management for build requests
- Resource monitoring and auto-scaling

## Testing Strategy

### Unit Testing
- Component testing for all React components
- Service testing for backend APIs
- Python API wrapper testing
- Integration testing for bridge services

### End-to-End Testing
- User journey testing for both modes
- Cross-browser compatibility testing
- Performance testing under load
- Security penetration testing

### User Acceptance Testing
- Usability testing with target user groups
- A/B testing for interface improvements
- Accessibility testing for compliance
- Mobile responsiveness testing

This design provides a comprehensive foundation for integrating the MCP Assistant App with the MCP Server Builder while maintaining the strengths of both systems and providing a superior unified user experience.