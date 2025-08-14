// WebSocket service types and interfaces

export interface WebSocketConnection {
  id: string;
  userId: string;
  socket: WebSocket;
  subscriptions: Set<string>; // Project IDs
  connectedAt: Date;
  lastActivity: Date;
}

export interface ProgressUpdate {
  projectId: string;
  phase: string;
  percentage: number;
  message: string;
  timestamp: Date;
  estimatedTimeRemaining?: number;
  errors?: ErrorEntry[];
  metadata?: Record<string, any>;
}

export interface ErrorEntry {
  severity: 'low' | 'medium' | 'high' | 'critical';
  message: string;
  phase: string;
  timestamp: Date;
  recoveryActions?: string[];
}

export interface WebSocketMessage {
  type: 'subscribe' | 'unsubscribe' | 'progress' | 'error' | 'ping' | 'pong';
  data: any;
  timestamp: Date;
}

export interface SubscribeMessage {
  type: 'subscribe';
  data: {
    projectId: string;
  };
}

export interface UnsubscribeMessage {
  type: 'unsubscribe';
  data: {
    projectId: string;
  };
}

export interface ProgressMessage {
  type: 'progress';
  data: ProgressUpdate;
}

export interface ErrorMessage {
  type: 'error';
  data: {
    message: string;
    code?: string;
    details?: any;
  };
}

export interface PingMessage {
  type: 'ping';
  data: {
    timestamp: Date;
  };
}

export interface PongMessage {
  type: 'pong';
  data: {
    timestamp: Date;
  };
}

export interface ConnectionStats {
  totalConnections: number;
  activeConnections: number;
  subscriptionsByProject: Record<string, number>;
  connectionsByUser: Record<string, number>;
}

export interface BroadcastRequest {
  projectId: string;
  update: ProgressUpdate;
  excludeUserId?: string;
}