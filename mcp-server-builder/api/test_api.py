"""Simple test script for the FastAPI wrapper."""

import asyncio
import json
import requests
import websockets
from typing import Dict, Any


class MCPBuilderAPIClient:
    """Simple client for testing the MCP Builder API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def health_check(self) -> Dict[str, Any]:
        """Test the health check endpoint."""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def create_project(self, name: str, template: str, **kwargs) -> Dict[str, Any]:
        """Create a new project."""
        data = {
            "name": name,
            "template": template,
            **kwargs
        }
        
        response = self.session.post(
            f"{self.base_url}/api/v1/projects",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status."""
        response = self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}/status"
        )
        response.raise_for_status()
        return response.json()
    
    def get_project_details(self, project_id: str) -> Dict[str, Any]:
        """Get project details."""
        response = self.session.get(
            f"{self.base_url}/api/v1/projects/{project_id}/details"
        )
        response.raise_for_status()
        return response.json()
    
    def list_projects(self) -> Dict[str, Any]:
        """List all projects."""
        response = self.session.get(f"{self.base_url}/api/v1/projects")
        response.raise_for_status()
        return response.json()
    
    def cancel_project(self, project_id: str) -> Dict[str, Any]:
        """Cancel a project."""
        response = self.session.delete(
            f"{self.base_url}/api/v1/projects/{project_id}"
        )
        response.raise_for_status()
        return response.json()
    
    def validate_project(self, project_id: str, validation_type: str = "comprehensive") -> Dict[str, Any]:
        """Validate a project."""
        data = {"validation_type": validation_type}
        
        response = self.session.post(
            f"{self.base_url}/api/v1/projects/{project_id}/validate",
            json=data
        )
        response.raise_for_status()
        return response.json()
    
    async def monitor_progress(self, project_id: str, duration: int = 60):
        """Monitor project progress via WebSocket."""
        uri = f"ws://localhost:8000/api/v1/projects/{project_id}/progress"
        
        try:
            async with websockets.connect(uri) as websocket:
                print(f"Connected to progress monitoring for project {project_id}")
                
                # Listen for messages for the specified duration
                start_time = asyncio.get_event_loop().time()
                
                while (asyncio.get_event_loop().time() - start_time) < duration:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        data = json.loads(message)
                        print(f"Progress update: {data}")
                        
                        # Break if project is completed or failed
                        if data.get("type") in ["project_completed", "project_failed", "project_error"]:
                            break
                            
                    except asyncio.TimeoutError:
                        # Send a ping to keep connection alive
                        await websocket.send("ping")
                        
        except Exception as e:
            print(f"WebSocket error: {e}")


async def test_api():
    """Run basic API tests."""
    client = MCPBuilderAPIClient()
    
    try:
        # Test health check
        print("Testing health check...")
        health = client.health_check()
        print(f"Health check: {health}")
        
        # Test project creation
        print("\nTesting project creation...")
        project_data = client.create_project(
            name="test-project",
            template="basic-python",
            custom_settings={"description": "Test project"}
        )
        project_id = project_data["project_id"]
        print(f"Created project: {project_data}")
        
        # Monitor progress
        print(f"\nMonitoring progress for project {project_id}...")
        await client.monitor_progress(project_id, duration=30)
        
        # Test project status
        print(f"\nGetting project status...")
        status = client.get_project_status(project_id)
        print(f"Project status: {status}")
        
        # Test project details
        print(f"\nGetting project details...")
        details = client.get_project_details(project_id)
        print(f"Project details: {details}")
        
        # Test project listing
        print(f"\nListing all projects...")
        projects = client.list_projects()
        print(f"Projects: {projects}")
        
        # Test validation (if project is complete)
        if status.get("status") == "completed":
            print(f"\nValidating project...")
            validation = client.validate_project(project_id)
            print(f"Validation results: {validation}")
        
        print("\nAll tests completed successfully!")
        
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("Starting MCP Builder API tests...")
    asyncio.run(test_api())