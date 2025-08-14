# MCP Server Builder API

FastAPI wrapper for the MCP Server Builder, providing REST API endpoints and WebSocket support for real-time progress monitoring.

## Features

- **REST API**: Create, manage, and monitor MCP server projects
- **WebSocket Support**: Real-time progress updates during project creation
- **Validation**: Comprehensive testing and validation endpoints
- **Type Safety**: Full Pydantic model validation for requests and responses
- **Async Support**: Non-blocking project creation and monitoring

## Installation

1. Install dependencies:
```bash
pip install -r api/requirements.txt
```

2. Start the API server:
```bash
python run_api.py
```

The API will be available at `http://localhost:8000` with interactive documentation at `http://localhost:8000/docs`.

## API Endpoints

### Project Management

- `POST /api/v1/projects` - Create a new project
- `GET /api/v1/projects` - List all projects
- `GET /api/v1/projects/{project_id}/status` - Get project status
- `GET /api/v1/projects/{project_id}/details` - Get project details
- `DELETE /api/v1/projects/{project_id}` - Cancel/cleanup project

### Validation

- `POST /api/v1/projects/{project_id}/validate` - Run validation tests

### Real-time Updates

- `WS /api/v1/projects/{project_id}/progress` - WebSocket for progress updates

### Health Check

- `GET /health` - Service health check

## Usage Examples

### Create a Project

```python
import requests

response = requests.post("http://localhost:8000/api/v1/projects", json={
    "name": "my-mcp-server",
    "template": "basic-python",
    "custom_settings": {
        "description": "My custom MCP server"
    }
})

project_data = response.json()
project_id = project_data["project_id"]
```

### Monitor Progress

```python
import asyncio
import websockets
import json

async def monitor_progress(project_id):
    uri = f"ws://localhost:8000/api/v1/projects/{project_id}/progress"
    
    async with websockets.connect(uri) as websocket:
        while True:
            message = await websocket.recv()
            data = json.loads(message)
            print(f"Progress: {data}")
            
            if data.get("type") in ["project_completed", "project_failed"]:
                break

asyncio.run(monitor_progress(project_id))
```

### Get Project Status

```python
response = requests.get(f"http://localhost:8000/api/v1/projects/{project_id}/status")
status = response.json()
print(f"Status: {status['status']}, Progress: {status['progress_percentage']}%")
```

## Configuration

The API can be configured using environment variables with the `MCP_API_` prefix:

- `MCP_API_HOST` - Server host (default: 0.0.0.0)
- `MCP_API_PORT` - Server port (default: 8000)
- `MCP_API_LOG_LEVEL` - Log level (default: info)
- `MCP_API_DEFAULT_OUTPUT_DIRECTORY` - Default output directory for projects

## Testing

Run the test script to verify the API functionality:

```bash
python api/test_api.py
```

This will test all major endpoints and WebSocket functionality.

## Integration

This API is designed to be integrated with web frontends (like the MCP Assistant App) to provide a unified interface for MCP server creation and management.

The API provides:
- Type-safe request/response models
- Real-time progress updates
- Comprehensive error handling
- Project lifecycle management
- Validation and testing capabilities