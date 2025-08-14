import { api } from "encore.dev/api";
import { 
  ProgressUpdate, 
  BroadcastRequest, 
  ConnectionStats, 
  WebSocketMessage 
} from './types';
import { connectionManager } from './connection-manager';

// Request/Response interfaces for API endpoints
interface AuthenticatedRequest {
  userId: string;
}

interface BroadcastProgressRequest {
  projectId: string;
  update: ProgressUpdate;
  excludeUserId?: string;
}

interface BroadcastToUserRequest extends AuthenticatedRequest {
  targetUserId: string;
  message: WebSocketMessage;
}

interface GetConnectionStatsRequest extends AuthenticatedRequest {
  // Admin endpoint - could add role checking here
}

interface GetProjectSubscribersRequest extends AuthenticatedRequest {
  projectId: string;
}

// Authentication middleware
function authenticateUser(req: AuthenticatedRequest): void {
  if (!req.userId) {
    throw api.APIError.unauthenticated("User ID is required");
  }
}

// Error handling utility
function handleWebSocketError(error: any, operation: string): never {
  console.error(`WebSocket ${operation} Error:`, error);
  throw api.APIError.internal(`Failed to ${operation}: ${error.message}`);
}

// API Endpoints

// Broadcast progress update to all subscribers of a project
export const broadcastProgress = api(
  { method: "POST", path: "/websocket/broadcast/progress", expose: false },
  async (req: BroadcastProgressRequest): Promise<{ sentCount: number }> => {
    try {
      const broadcastRequest: BroadcastRequest = {
        projectId: req.projectId,
        update: req.update,
        excludeUserId: req.excludeUserId,
      };
      
      const sentCount = connectionManager.broadcastProgress(broadcastRequest);
      
      return { sentCount };
    } catch (error) {
      handleWebSocketError(error, 'broadcast progress');
    }
  }
);

// Broadcast message to all connections of a specific user
export const broadcastToUser = api(
  { method: "POST", path: "/websocket/broadcast/user", expose: false },
  async (req: BroadcastToUserRequest): Promise<{ sentCount: number }> => {
    try {
      authenticateUser(req);
      
      const sentCount = connectionManager.broadcastToUser(req.targetUserId, req.message);
      
      return { sentCount };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleWebSocketError(error, 'broadcast to user');
    }
  }
);

// Get connection statistics (admin endpoint)
export const getConnectionStats = api(
  { method: "GET", path: "/websocket/stats", expose: false },
  async (req: GetConnectionStatsRequest): Promise<ConnectionStats> => {
    try {
      authenticateUser(req);
      
      const stats = connectionManager.getConnectionStats();
      return stats;
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleWebSocketError(error, 'get connection stats');
    }
  }
);

// Get list of users subscribed to a project
export const getProjectSubscribers = api(
  { method: "GET", path: "/websocket/projects/:projectId/subscribers", expose: false },
  async (req: GetProjectSubscribersRequest): Promise<{ subscribers: string[] }> => {
    try {
      authenticateUser(req);
      
      const subscribers = connectionManager.getProjectSubscribers(req.projectId);
      
      return { subscribers };
    } catch (error) {
      if (error instanceof api.APIError) {
        throw error;
      }
      handleWebSocketError(error, 'get project subscribers');
    }
  }
);

// Get user's active connections
export const getUserConnections = api(
  { method: "GET", path: "/websocket/users/:userId/connections", expose: false },
  async (req: { userId: string }): Promise<{ connections: string[] }> => {
    try {
      const connections = connectionManager.getUserConnections(req.userId);
      
      return { connections };
    } catch (error) {
      handleWebSocketError(error, 'get user connections');
    }
  }
);

// Health check endpoint
export const healthCheck = api(
  { method: "GET", path: "/websocket/health", expose: true },
  async (): Promise<{ status: string; stats: ConnectionStats }> => {
    try {
      const stats = connectionManager.getConnectionStats();
      
      return {
        status: 'healthy',
        stats,
      };
    } catch (error) {
      return {
        status: 'unhealthy',
        stats: {
          totalConnections: 0,
          activeConnections: 0,
          subscriptionsByProject: {},
          connectionsByUser: {},
        },
      };
    }
  }
);

// Utility functions for other services to use

export async function notifyProjectProgress(
  projectId: string, 
  update: ProgressUpdate, 
  excludeUserId?: string
): Promise<number> {
  try {
    const request: BroadcastProgressRequest = {
      projectId,
      update,
      excludeUserId,
    };
    
    const response = await broadcastProgress(request);
    return response.sentCount;
  } catch (error) {
    console.error('Failed to notify project progress:', error);
    return 0;
  }
}

export async function notifyUser(
  userId: string, 
  message: WebSocketMessage
): Promise<number> {
  try {
    const request: BroadcastToUserRequest = {
      userId: 'system', // System user for internal calls
      targetUserId: userId,
      message,
    };
    
    const response = await broadcastToUser(request);
    return response.sentCount;
  } catch (error) {
    console.error('Failed to notify user:', error);
    return 0;
  }
}

// Graceful shutdown handler
process.on('SIGTERM', () => {
  console.log('Shutting down WebSocket service...');
  connectionManager.shutdown();
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('Shutting down WebSocket service...');
  connectionManager.shutdown();
  process.exit(0);
});