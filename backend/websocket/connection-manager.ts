import { 
  WebSocketConnection, 
  ProgressUpdate, 
  WebSocketMessage, 
  SubscribeMessage, 
  UnsubscribeMessage, 
  ProgressMessage, 
  ErrorMessage, 
  PingMessage, 
  PongMessage,
  ConnectionStats,
  BroadcastRequest
} from './types';

export class WebSocketConnectionManager {
  private connections: Map<string, WebSocketConnection> = new Map();
  private userConnections: Map<string, Set<string>> = new Map(); // userId -> connectionIds
  private projectSubscriptions: Map<string, Set<string>> = new Map(); // projectId -> connectionIds
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor() {
    this.startHeartbeat();
    this.startCleanup();
  }

  private generateConnectionId(): string {
    return `conn_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private ensureUserConnectionSet(userId: string): void {
    if (!this.userConnections.has(userId)) {
      this.userConnections.set(userId, new Set());
    }
  }

  private ensureProjectSubscriptionSet(projectId: string): void {
    if (!this.projectSubscriptions.has(projectId)) {
      this.projectSubscriptions.set(projectId, new Set());
    }
  }

  private sendMessage(connection: WebSocketConnection, message: WebSocketMessage): boolean {
    try {
      if (connection.socket.readyState === WebSocket.OPEN) {
        connection.socket.send(JSON.stringify(message));
        connection.lastActivity = new Date();
        return true;
      }
      return false;
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
      return false;
    }
  }

  private handleMessage(connection: WebSocketConnection, rawMessage: string): void {
    try {
      const message: WebSocketMessage = JSON.parse(rawMessage);
      connection.lastActivity = new Date();

      switch (message.type) {
        case 'subscribe':
          this.handleSubscribe(connection, message as SubscribeMessage);
          break;
        case 'unsubscribe':
          this.handleUnsubscribe(connection, message as UnsubscribeMessage);
          break;
        case 'ping':
          this.handlePing(connection, message as PingMessage);
          break;
        default:
          this.sendError(connection, 'Unknown message type', 'UNKNOWN_MESSAGE_TYPE');
      }
    } catch (error) {
      console.error('Failed to handle WebSocket message:', error);
      this.sendError(connection, 'Invalid message format', 'INVALID_MESSAGE');
    }
  }

  private handleSubscribe(connection: WebSocketConnection, message: SubscribeMessage): void {
    const { projectId } = message.data;
    
    if (!projectId) {
      this.sendError(connection, 'Project ID is required', 'MISSING_PROJECT_ID');
      return;
    }

    // Add subscription
    connection.subscriptions.add(projectId);
    this.ensureProjectSubscriptionSet(projectId);
    this.projectSubscriptions.get(projectId)!.add(connection.id);

    // Send confirmation
    this.sendMessage(connection, {
      type: 'progress',
      data: {
        projectId,
        phase: 'subscribed',
        percentage: 0,
        message: `Subscribed to project ${projectId}`,
        timestamp: new Date(),
      },
      timestamp: new Date(),
    });
  }

  private handleUnsubscribe(connection: WebSocketConnection, message: UnsubscribeMessage): void {
    const { projectId } = message.data;
    
    if (!projectId) {
      this.sendError(connection, 'Project ID is required', 'MISSING_PROJECT_ID');
      return;
    }

    // Remove subscription
    connection.subscriptions.delete(projectId);
    this.projectSubscriptions.get(projectId)?.delete(connection.id);

    // Send confirmation
    this.sendMessage(connection, {
      type: 'progress',
      data: {
        projectId,
        phase: 'unsubscribed',
        percentage: 0,
        message: `Unsubscribed from project ${projectId}`,
        timestamp: new Date(),
      },
      timestamp: new Date(),
    });
  }

  private handlePing(connection: WebSocketConnection, message: PingMessage): void {
    const pongMessage: PongMessage = {
      type: 'pong',
      data: {
        timestamp: new Date(),
      },
      timestamp: new Date(),
    };
    
    this.sendMessage(connection, pongMessage);
  }

  private sendError(connection: WebSocketConnection, message: string, code?: string): void {
    const errorMessage: ErrorMessage = {
      type: 'error',
      data: {
        message,
        code,
      },
      timestamp: new Date(),
    };
    
    this.sendMessage(connection, errorMessage);
  }

  private startHeartbeat(): void {
    this.heartbeatInterval = setInterval(() => {
      const now = new Date();
      const pingMessage: PingMessage = {
        type: 'ping',
        data: {
          timestamp: now,
        },
        timestamp: now,
      };

      for (const connection of this.connections.values()) {
        if (connection.socket.readyState === WebSocket.OPEN) {
          this.sendMessage(connection, pingMessage);
        }
      }
    }, 30000); // Ping every 30 seconds
  }

  private startCleanup(): void {
    this.cleanupInterval = setInterval(() => {
      this.cleanupStaleConnections();
    }, 60000); // Cleanup every minute
  }

  private cleanupStaleConnections(): void {
    const now = new Date();
    const staleThreshold = 5 * 60 * 1000; // 5 minutes

    for (const [connectionId, connection] of this.connections) {
      const timeSinceLastActivity = now.getTime() - connection.lastActivity.getTime();
      
      if (connection.socket.readyState !== WebSocket.OPEN || timeSinceLastActivity > staleThreshold) {
        this.removeConnection(connectionId);
      }
    }
  }

  // Public methods

  addConnection(userId: string, socket: WebSocket): string {
    const connectionId = this.generateConnectionId();
    const now = new Date();

    const connection: WebSocketConnection = {
      id: connectionId,
      userId,
      socket,
      subscriptions: new Set(),
      connectedAt: now,
      lastActivity: now,
    };

    // Set up socket event handlers
    socket.onmessage = (event) => {
      this.handleMessage(connection, event.data);
    };

    socket.onclose = () => {
      this.removeConnection(connectionId);
    };

    socket.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.removeConnection(connectionId);
    };

    // Store connection
    this.connections.set(connectionId, connection);
    this.ensureUserConnectionSet(userId);
    this.userConnections.get(userId)!.add(connectionId);

    console.log(`WebSocket connection established: ${connectionId} for user ${userId}`);
    return connectionId;
  }

  removeConnection(connectionId: string): void {
    const connection = this.connections.get(connectionId);
    if (!connection) {
      return;
    }

    // Remove from user connections
    this.userConnections.get(connection.userId)?.delete(connectionId);

    // Remove from project subscriptions
    for (const projectId of connection.subscriptions) {
      this.projectSubscriptions.get(projectId)?.delete(connectionId);
    }

    // Close socket if still open
    if (connection.socket.readyState === WebSocket.OPEN) {
      connection.socket.close();
    }

    // Remove connection
    this.connections.delete(connectionId);

    console.log(`WebSocket connection removed: ${connectionId}`);
  }

  broadcastProgress(request: BroadcastRequest): number {
    const { projectId, update, excludeUserId } = request;
    const subscribedConnections = this.projectSubscriptions.get(projectId);
    
    if (!subscribedConnections || subscribedConnections.size === 0) {
      return 0;
    }

    const progressMessage: ProgressMessage = {
      type: 'progress',
      data: update,
      timestamp: new Date(),
    };

    let sentCount = 0;

    for (const connectionId of subscribedConnections) {
      const connection = this.connections.get(connectionId);
      if (!connection) {
        continue;
      }

      // Skip excluded user
      if (excludeUserId && connection.userId === excludeUserId) {
        continue;
      }

      if (this.sendMessage(connection, progressMessage)) {
        sentCount++;
      }
    }

    return sentCount;
  }

  broadcastToUser(userId: string, message: WebSocketMessage): number {
    const userConnections = this.userConnections.get(userId);
    
    if (!userConnections || userConnections.size === 0) {
      return 0;
    }

    let sentCount = 0;

    for (const connectionId of userConnections) {
      const connection = this.connections.get(connectionId);
      if (!connection) {
        continue;
      }

      if (this.sendMessage(connection, message)) {
        sentCount++;
      }
    }

    return sentCount;
  }

  getConnectionStats(): ConnectionStats {
    const stats: ConnectionStats = {
      totalConnections: this.connections.size,
      activeConnections: 0,
      subscriptionsByProject: {},
      connectionsByUser: {},
    };

    // Count active connections
    for (const connection of this.connections.values()) {
      if (connection.socket.readyState === WebSocket.OPEN) {
        stats.activeConnections++;
      }
    }

    // Count subscriptions by project
    for (const [projectId, connections] of this.projectSubscriptions) {
      stats.subscriptionsByProject[projectId] = connections.size;
    }

    // Count connections by user
    for (const [userId, connections] of this.userConnections) {
      stats.connectionsByUser[userId] = connections.size;
    }

    return stats;
  }

  getUserConnections(userId: string): string[] {
    const connections = this.userConnections.get(userId);
    return connections ? Array.from(connections) : [];
  }

  getProjectSubscribers(projectId: string): string[] {
    const connections = this.projectSubscriptions.get(projectId);
    if (!connections) {
      return [];
    }

    const userIds: string[] = [];
    for (const connectionId of connections) {
      const connection = this.connections.get(connectionId);
      if (connection && !userIds.includes(connection.userId)) {
        userIds.push(connection.userId);
      }
    }

    return userIds;
  }

  shutdown(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
    }
    
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
    }

    // Close all connections
    for (const connectionId of this.connections.keys()) {
      this.removeConnection(connectionId);
    }
  }
}

// Export singleton instance
export const connectionManager = new WebSocketConnectionManager();