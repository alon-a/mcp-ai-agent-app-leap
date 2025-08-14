"""Enhanced WebSocket manager with session isolation and connection management."""

import asyncio
import json
import logging
from typing import Dict, Any, Optional, Set, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect


class ConnectionState(Enum):
    """WebSocket connection states."""
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"


@dataclass
class ConnectionInfo:
    """Information about a WebSocket connection."""
    websocket: WebSocket
    project_id: str
    user_id: Optional[str] = None
    connected_at: datetime = field(default_factory=datetime.now)
    last_ping: datetime = field(default_factory=datetime.now)
    state: ConnectionState = ConnectionState.CONNECTING
    error_count: int = 0
    max_errors: int = 5


class EnhancedWebSocketManager:
    """Enhanced WebSocket manager with session isolation and robust connection handling."""
    
    def __init__(self, ping_interval: int = 30, connection_timeout: int = 300):
        """Initialize the WebSocket manager.
        
        Args:
            ping_interval: Interval in seconds for ping messages
            connection_timeout: Timeout in seconds for inactive connections
        """
        # Map connection_id -> ConnectionInfo
        self.connections: Dict[str, ConnectionInfo] = {}
        
        # Map project_id -> set of connection_ids
        self.project_connections: Dict[str, Set[str]] = {}
        
        # Map user_id -> set of connection_ids (for user session isolation)
        self.user_connections: Dict[str, Set[str]] = {}
        
        self.ping_interval = ping_interval
        self.connection_timeout = connection_timeout
        self.logger = logging.getLogger(__name__)
        
        # Start background tasks
        self._cleanup_task = None
        self._ping_task = None
        self._start_background_tasks()
    
    def _start_background_tasks(self):
        """Start background tasks for connection management."""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_connections())
        
        if self._ping_task is None or self._ping_task.done():
            self._ping_task = asyncio.create_task(self._ping_connections())
    
    async def connect(self, websocket: WebSocket, project_id: str, user_id: Optional[str] = None) -> str:
        """Accept a WebSocket connection and return connection ID.
        
        Args:
            websocket: WebSocket instance
            project_id: Project identifier
            user_id: Optional user identifier for session isolation
            
        Returns:
            Unique connection identifier
        """
        try:
            await websocket.accept()
            
            # Generate unique connection ID
            connection_id = f"{project_id}_{datetime.now().timestamp()}_{id(websocket)}"
            
            # Create connection info
            connection_info = ConnectionInfo(
                websocket=websocket,
                project_id=project_id,
                user_id=user_id,
                state=ConnectionState.CONNECTED
            )
            
            # Store connection
            self.connections[connection_id] = connection_info
            
            # Update project connections
            if project_id not in self.project_connections:
                self.project_connections[project_id] = set()
            self.project_connections[project_id].add(connection_id)
            
            # Update user connections if user_id provided
            if user_id:
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection_id)
            
            # Send connection confirmation
            await self._send_to_connection(connection_id, {
                "type": "connection_established",
                "connection_id": connection_id,
                "project_id": project_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "server_info": {
                    "ping_interval": self.ping_interval,
                    "connection_timeout": self.connection_timeout
                }
            })
            
            self.logger.info(f"WebSocket connected: {connection_id} for project {project_id}")
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Failed to establish WebSocket connection: {e}")
            raise
    
    async def disconnect(self, connection_id: str, reason: str = "client_disconnect"):
        """Disconnect a WebSocket connection.
        
        Args:
            connection_id: Connection identifier
            reason: Reason for disconnection
        """
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        connection_info.state = ConnectionState.DISCONNECTING
        
        try:
            # Send disconnection message
            await self._send_to_connection(connection_id, {
                "type": "connection_closing",
                "connection_id": connection_id,
                "reason": reason,
                "timestamp": datetime.now().isoformat()
            })
            
            # Close WebSocket
            await connection_info.websocket.close()
            
        except Exception as e:
            self.logger.warning(f"Error during WebSocket disconnection: {e}")
        
        finally:
            # Clean up connection references
            self._remove_connection(connection_id)
            self.logger.info(f"WebSocket disconnected: {connection_id} (reason: {reason})")
    
    def _remove_connection(self, connection_id: str):
        """Remove connection from all tracking structures."""
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        
        # Remove from project connections
        if connection_info.project_id in self.project_connections:
            self.project_connections[connection_info.project_id].discard(connection_id)
            if not self.project_connections[connection_info.project_id]:
                del self.project_connections[connection_info.project_id]
        
        # Remove from user connections
        if connection_info.user_id and connection_info.user_id in self.user_connections:
            self.user_connections[connection_info.user_id].discard(connection_id)
            if not self.user_connections[connection_info.user_id]:
                del self.user_connections[connection_info.user_id]
        
        # Remove main connection
        del self.connections[connection_id]
    
    async def broadcast_to_project(self, project_id: str, message: Dict[str, Any], exclude_user: Optional[str] = None):
        """Broadcast a message to all connections for a project.
        
        Args:
            project_id: Project identifier
            message: Message to broadcast
            exclude_user: Optional user ID to exclude from broadcast
        """
        if project_id not in self.project_connections:
            return
        
        # Get all connection IDs for the project
        connection_ids = self.project_connections[project_id].copy()
        
        # Filter out excluded user if specified
        if exclude_user:
            connection_ids = {
                conn_id for conn_id in connection_ids
                if self.connections.get(conn_id, {}).user_id != exclude_user
            }
        
        # Send to all connections
        tasks = []
        for connection_id in connection_ids:
            tasks.append(self._send_to_connection(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any]):
        """Broadcast a message to all connections for a user.
        
        Args:
            user_id: User identifier
            message: Message to broadcast
        """
        if user_id not in self.user_connections:
            return
        
        connection_ids = self.user_connections[user_id].copy()
        
        tasks = []
        for connection_id in connection_ids:
            tasks.append(self._send_to_connection(connection_id, message))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_to_connection(self, connection_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific connection.
        
        Args:
            connection_id: Connection identifier
            message: Message to send
            
        Returns:
            True if message was sent successfully
        """
        if connection_id not in self.connections:
            return False
        
        connection_info = self.connections[connection_id]
        
        if connection_info.state != ConnectionState.CONNECTED:
            return False
        
        try:
            await connection_info.websocket.send_text(json.dumps(message))
            return True
            
        except WebSocketDisconnect:
            await self.disconnect(connection_id, "websocket_disconnect")
            return False
            
        except Exception as e:
            connection_info.error_count += 1
            self.logger.warning(f"Error sending to connection {connection_id}: {e}")
            
            if connection_info.error_count >= connection_info.max_errors:
                await self.disconnect(connection_id, "max_errors_exceeded")
            
            return False
    
    async def handle_client_message(self, connection_id: str, message: str):
        """Handle incoming message from client.
        
        Args:
            connection_id: Connection identifier
            message: Message from client
        """
        if connection_id not in self.connections:
            return
        
        connection_info = self.connections[connection_id]
        connection_info.last_ping = datetime.now()
        
        try:
            # Try to parse as JSON
            data = json.loads(message)
            message_type = data.get("type", "unknown")
            
            if message_type == "ping":
                # Respond to ping
                await self._send_to_connection(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            
            elif message_type == "subscribe":
                # Handle subscription requests
                await self._handle_subscription(connection_id, data)
            
            elif message_type == "unsubscribe":
                # Handle unsubscription requests
                await self._handle_unsubscription(connection_id, data)
            
            else:
                # Echo back unknown messages
                await self._send_to_connection(connection_id, {
                    "type": "echo",
                    "original_message": data,
                    "timestamp": datetime.now().isoformat()
                })
                
        except json.JSONDecodeError:
            # Handle plain text messages
            if message.lower() == "ping":
                await self._send_to_connection(connection_id, {
                    "type": "pong",
                    "timestamp": datetime.now().isoformat()
                })
            else:
                await self._send_to_connection(connection_id, {
                    "type": "echo",
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                })
    
    async def _handle_subscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle subscription requests."""
        # Implementation for handling subscriptions to specific events
        await self._send_to_connection(connection_id, {
            "type": "subscription_confirmed",
            "subscription": data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _handle_unsubscription(self, connection_id: str, data: Dict[str, Any]):
        """Handle unsubscription requests."""
        # Implementation for handling unsubscriptions
        await self._send_to_connection(connection_id, {
            "type": "unsubscription_confirmed",
            "unsubscription": data,
            "timestamp": datetime.now().isoformat()
        })
    
    async def _cleanup_connections(self):
        """Background task to clean up stale connections."""
        while True:
            try:
                current_time = datetime.now()
                stale_connections = []
                
                for connection_id, connection_info in self.connections.items():
                    # Check for timeout
                    if (current_time - connection_info.last_ping).total_seconds() > self.connection_timeout:
                        stale_connections.append(connection_id)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id, "timeout")
                
                # Sleep before next cleanup
                await asyncio.sleep(60)  # Run cleanup every minute
                
            except Exception as e:
                self.logger.error(f"Error in connection cleanup: {e}")
                await asyncio.sleep(60)
    
    async def _ping_connections(self):
        """Background task to ping connections."""
        while True:
            try:
                current_time = datetime.now()
                
                for connection_id, connection_info in list(self.connections.items()):
                    if connection_info.state == ConnectionState.CONNECTED:
                        # Send ping if it's time
                        if (current_time - connection_info.last_ping).total_seconds() > self.ping_interval:
                            await self._send_to_connection(connection_id, {
                                "type": "ping",
                                "timestamp": current_time.isoformat()
                            })
                
                await asyncio.sleep(self.ping_interval)
                
            except Exception as e:
                self.logger.error(f"Error in ping task: {e}")
                await asyncio.sleep(self.ping_interval)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about current connections."""
        return {
            "total_connections": len(self.connections),
            "projects_with_connections": len(self.project_connections),
            "users_with_connections": len(self.user_connections),
            "connections_by_state": {
                state.value: sum(1 for conn in self.connections.values() if conn.state == state)
                for state in ConnectionState
            },
            "connections_by_project": {
                project_id: len(conn_ids)
                for project_id, conn_ids in self.project_connections.items()
            }
        }
    
    async def cleanup(self):
        """Clean up all connections and stop background tasks."""
        # Cancel background tasks
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
        
        # Disconnect all connections
        connection_ids = list(self.connections.keys())
        for connection_id in connection_ids:
            await self.disconnect(connection_id, "server_shutdown")
        
        self.logger.info("WebSocket manager cleanup completed")