#!/usr/bin/env python3
"""Startup script for the MCP Server Builder API."""

import sys
import os
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Add the src directory to Python path
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))

if __name__ == "__main__":
    import uvicorn
    from api.config import settings
    
    print(f"Starting MCP Server Builder API on {settings.host}:{settings.port}")
    print(f"API Documentation available at: http://{settings.host}:{settings.port}/docs")
    
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level
    )