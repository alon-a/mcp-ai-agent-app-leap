# Step-by-Step Tutorials

This document provides detailed tutorials for creating different types of MCP servers using the MCP Server Builder.

## Tutorial 1: Building a Weather Information Server

In this tutorial, you'll create a Python MCP server that provides weather information using a public weather API.

### Prerequisites

- Python 3.8+
- Internet connection
- Weather API key (we'll use OpenWeatherMap)

### Step 1: Get Your API Key

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Get your API key from the dashboard

### Step 2: Create the Server

```python
from mcp_server_builder.managers.project_manager import ProjectManagerImpl

# Initialize the manager
manager = ProjectManagerImpl()

# Create weather server
result = manager.create_project(
    name="weather-server",
    template="python-fastmcp",
    config={
        'output_directory': './weather-project',
        'custom_settings': {
            'server_name': 'Weather Information Server',
            'description': 'Provides current weather and forecasts',
            'transport': 'stdio'
        },
        'environment_variables': {
            'OPENWEATHER_API_KEY': 'your-api-key-here',
            'DEBUG': 'true'
        },
        'additional_dependencies': [
            'httpx>=0.24.0',
            'python-dotenv>=1.0.0',
            'pydantic>=2.0.0'
        ]
    }
)

if result.success:
    print(f"✅ Weather server created at: {result.project_path}")
else:
    print("❌ Failed to create server:")
    for error in result.errors:
        print(f"  - {error}")
```

### Step 3: Customize the Server Code

Navigate to your project directory and modify the main server file:

**File: `weather-project/weather-server/main.py`**
```python
#!/usr/bin/env python3
"""Weather Information Server

A Model Context Protocol server that provides weather information.
"""

import asyncio
import os
from typing import Optional
import httpx
from fastmcp import FastMCP
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create MCP server instance
mcp = FastMCP("Weather Information Server")

class WeatherData(BaseModel):
    """Weather data model."""
    location: str
    temperature: float
    description: str
    humidity: int
    wind_speed: float

class ForecastData(BaseModel):
    """Forecast data model."""
    location: str
    forecasts: list[dict]

@mcp.tool()
async def get_current_weather(city: str, country_code: str = "US") -> WeatherData:
    """Get current weather for a city.
    
    Args:
        city: Name of the city
        country_code: ISO country code (default: US)
        
    Returns:
        Current weather information
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        raise ValueError("OpenWeather API key not configured")
    
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': f"{city},{country_code}",
        'appid': api_key,
        'units': 'metric'
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    return WeatherData(
        location=f"{data['name']}, {data['sys']['country']}",
        temperature=data['main']['temp'],
        description=data['weather'][0]['description'],
        humidity=data['main']['humidity'],
        wind_speed=data['wind']['speed']
    )

@mcp.tool()
async def get_weather_forecast(city: str, country_code: str = "US", days: int = 5) -> ForecastData:
    """Get weather forecast for a city.
    
    Args:
        city: Name of the city
        country_code: ISO country code (default: US)
        days: Number of days to forecast (1-5)
        
    Returns:
        Weather forecast information
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        raise ValueError("OpenWeather API key not configured")
    
    url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': f"{city},{country_code}",
        'appid': api_key,
        'units': 'metric',
        'cnt': days * 8  # 8 forecasts per day (3-hour intervals)
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        data = response.json()
    
    forecasts = []
    for item in data['list']:
        forecasts.append({
            'datetime': item['dt_txt'],
            'temperature': item['main']['temp'],
            'description': item['weather'][0]['description'],
            'humidity': item['main']['humidity']
        })
    
    return ForecastData(
        location=f"{data['city']['name']}, {data['city']['country']}",
        forecasts=forecasts
    )

@mcp.resource("weather://locations")
def get_supported_locations() -> dict:
    """Get list of commonly requested locations."""
    return {
        "popular_cities": [
            {"city": "New York", "country": "US"},
            {"city": "London", "country": "GB"},
            {"city": "Tokyo", "country": "JP"},
            {"city": "Paris", "country": "FR"},
            {"city": "Sydney", "country": "AU"}
        ]
    }

async def main():
    """Run the weather MCP server."""
    async with mcp.run_server() as server:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 4: Create Environment File

Create a `.env` file in your project directory:

**File: `weather-project/weather-server/.env`**
```
OPENWEATHER_API_KEY=your-actual-api-key-here
DEBUG=true
```

### Step 5: Install and Test

```bash
cd weather-project/weather-server

# Install dependencies
pip install -e .

# Test the server
python main.py
```

### Step 6: Validate the Server

```python
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = "./weather-project/weather-server"

# Validate the server
startup_ok = validator.validate_server_startup(project_path)
protocol_ok = validator.validate_mcp_protocol(project_path)

print(f"Server startup: {'✅' if startup_ok else '❌'}")
print(f"Protocol compliance: {'✅' if protocol_ok else '❌'}")
```

## Tutorial 2: Building a File Processing Server

Create a server that can read, analyze, and process various file types.

### Step 1: Create the Server

```python
result = manager.create_project(
    name="file-processor",
    template="python-fastmcp",
    config={
        'output_directory': './file-processing-project',
        'custom_settings': {
            'server_name': 'File Processing Server',
            'description': 'Processes and analyzes files',
            'transport': 'stdio'
        },
        'environment_variables': {
            'MAX_FILE_SIZE': '10485760',  # 10MB
            'ALLOWED_EXTENSIONS': 'txt,csv,json,xml,pdf'
        },
        'additional_dependencies': [
            'pandas>=2.0.0',
            'openpyxl>=3.1.0',
            'python-magic>=0.4.0',
            'PyPDF2>=3.0.0',
            'chardet>=5.0.0'
        ]
    }
)
```

### Step 2: Implement File Processing Tools

**File: `file-processing-project/file-processor/main.py`**
```python
#!/usr/bin/env python3
"""File Processing Server

A Model Context Protocol server for file processing and analysis.
"""

import asyncio
import os
import json
import csv
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import magic
import chardet
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("File Processing Server")

class FileInfo(BaseModel):
    """File information model."""
    name: str
    size: int
    type: str
    encoding: Optional[str] = None
    line_count: Optional[int] = None

class ProcessingResult(BaseModel):
    """File processing result model."""
    file_info: FileInfo
    content_preview: str
    analysis: Dict[str, Any]

@mcp.tool()
async def analyze_file(file_path: str) -> FileInfo:
    """Analyze a file and return basic information.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        File information including type, size, and encoding
    """
    path = Path(file_path)
    
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Get file size
    size = path.stat().st_size
    
    # Check file size limit
    max_size = int(os.getenv('MAX_FILE_SIZE', '10485760'))
    if size > max_size:
        raise ValueError(f"File too large: {size} bytes (max: {max_size})")
    
    # Detect file type
    file_type = magic.from_file(str(path), mime=True)
    
    # Detect encoding for text files
    encoding = None
    line_count = None
    if file_type.startswith('text/'):
        with open(path, 'rb') as f:
            raw_data = f.read()
            encoding_result = chardet.detect(raw_data)
            encoding = encoding_result['encoding']
        
        # Count lines
        try:
            with open(path, 'r', encoding=encoding) as f:
                line_count = sum(1 for _ in f)
        except:
            line_count = None
    
    return FileInfo(
        name=path.name,
        size=size,
        type=file_type,
        encoding=encoding,
        line_count=line_count
    )

@mcp.tool()
async def read_text_file(file_path: str, max_lines: int = 100) -> ProcessingResult:
    """Read and analyze a text file.
    
    Args:
        file_path: Path to the text file
        max_lines: Maximum number of lines to preview
        
    Returns:
        File processing result with content preview and analysis
    """
    file_info = await analyze_file(file_path)
    
    if not file_info.type.startswith('text/'):
        raise ValueError(f"Not a text file: {file_info.type}")
    
    path = Path(file_path)
    
    # Read file content
    with open(path, 'r', encoding=file_info.encoding) as f:
        lines = []
        for i, line in enumerate(f):
            if i >= max_lines:
                break
            lines.append(line.rstrip())
    
    content_preview = '\n'.join(lines)
    if file_info.line_count and file_info.line_count > max_lines:
        content_preview += f"\n... ({file_info.line_count - max_lines} more lines)"
    
    # Basic text analysis
    full_content = '\n'.join(lines)
    analysis = {
        'character_count': len(full_content),
        'word_count': len(full_content.split()),
        'preview_lines': len(lines),
        'total_lines': file_info.line_count
    }
    
    return ProcessingResult(
        file_info=file_info,
        content_preview=content_preview,
        analysis=analysis
    )

@mcp.tool()
async def process_csv_file(file_path: str, max_rows: int = 10) -> ProcessingResult:
    """Process and analyze a CSV file.
    
    Args:
        file_path: Path to the CSV file
        max_rows: Maximum number of rows to preview
        
    Returns:
        CSV processing result with data preview and analysis
    """
    file_info = await analyze_file(file_path)
    
    # Read CSV file
    df = pd.read_csv(file_path)
    
    # Create preview
    preview_df = df.head(max_rows)
    content_preview = preview_df.to_string()
    
    # Analysis
    analysis = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'column_names': df.columns.tolist(),
        'column_types': df.dtypes.astype(str).to_dict(),
        'missing_values': df.isnull().sum().to_dict(),
        'preview_rows': len(preview_df)
    }
    
    # Add basic statistics for numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
        analysis['numeric_summary'] = df[numeric_columns].describe().to_dict()
    
    return ProcessingResult(
        file_info=file_info,
        content_preview=content_preview,
        analysis=analysis
    )

@mcp.tool()
async def process_json_file(file_path: str) -> ProcessingResult:
    """Process and analyze a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        JSON processing result with structure analysis
    """
    file_info = await analyze_file(file_path)
    
    # Read JSON file
    with open(file_path, 'r', encoding=file_info.encoding) as f:
        data = json.load(f)
    
    # Create preview (pretty-printed JSON)
    content_preview = json.dumps(data, indent=2)[:1000]
    if len(content_preview) >= 1000:
        content_preview += "\n... (truncated)"
    
    # Analyze JSON structure
    def analyze_structure(obj, path="root"):
        if isinstance(obj, dict):
            return {
                'type': 'object',
                'keys': list(obj.keys()),
                'key_count': len(obj),
                'nested_structure': {k: analyze_structure(v, f"{path}.{k}") 
                                   for k, v in obj.items() if isinstance(v, (dict, list))}
            }
        elif isinstance(obj, list):
            return {
                'type': 'array',
                'length': len(obj),
                'item_types': list(set(type(item).__name__ for item in obj)),
                'sample_structure': analyze_structure(obj[0], f"{path}[0]") if obj else None
            }
        else:
            return {'type': type(obj).__name__}
    
    analysis = {
        'structure': analyze_structure(data),
        'total_size_bytes': file_info.size
    }
    
    return ProcessingResult(
        file_info=file_info,
        content_preview=content_preview,
        analysis=analysis
    )

@mcp.resource("files://supported-types")
def get_supported_file_types() -> dict:
    """Get list of supported file types."""
    return {
        "supported_types": [
            {"extension": "txt", "description": "Plain text files"},
            {"extension": "csv", "description": "Comma-separated values"},
            {"extension": "json", "description": "JSON data files"},
            {"extension": "xml", "description": "XML documents"},
            {"extension": "pdf", "description": "PDF documents (basic info only)"}
        ],
        "max_file_size": os.getenv('MAX_FILE_SIZE', '10485760'),
        "allowed_extensions": os.getenv('ALLOWED_EXTENSIONS', '').split(',')
    }

async def main():
    """Run the file processing MCP server."""
    async with mcp.run_server() as server:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Test the File Processor

Create test files and validate:

```python
# Create test CSV file
import pandas as pd

test_data = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['New York', 'London', 'Tokyo']
})
test_data.to_csv('test_data.csv', index=False)

# Test the server
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = "./file-processing-project/file-processor"

# Run validation
results = validator.run_comprehensive_tests(project_path)
print(f"Validation results: {results}")
```

## Tutorial 3: Building a Database Query Server

Create a server that can connect to databases and execute queries safely.

### Step 1: Create the Server

```python
result = manager.create_project(
    name="database-server",
    template="python-fastmcp",
    config={
        'output_directory': './database-project',
        'custom_settings': {
            'server_name': 'Database Query Server',
            'description': 'Executes safe database queries',
            'transport': 'stdio'
        },
        'environment_variables': {
            'DATABASE_URL': 'sqlite:///example.db',
            'MAX_QUERY_RESULTS': '1000',
            'QUERY_TIMEOUT': '30'
        },
        'additional_dependencies': [
            'sqlalchemy>=2.0.0',
            'pandas>=2.0.0',
            'sqlite3'  # Built-in, but listed for clarity
        ]
    }
)
```

### Step 2: Implement Database Tools

**File: `database-project/database-server/main.py`**
```python
#!/usr/bin/env python3
"""Database Query Server

A Model Context Protocol server for safe database operations.
"""

import asyncio
import os
import re
from typing import List, Dict, Any, Optional
import pandas as pd
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from fastmcp import FastMCP
from pydantic import BaseModel

mcp = FastMCP("Database Query Server")

class QueryResult(BaseModel):
    """Database query result model."""
    columns: List[str]
    rows: List[List[Any]]
    row_count: int
    execution_time: float

class TableInfo(BaseModel):
    """Database table information model."""
    name: str
    columns: List[Dict[str, str]]
    row_count: Optional[int] = None

# Initialize database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///example.db')
engine = create_engine(DATABASE_URL)

# Safe query patterns (only SELECT statements)
SAFE_QUERY_PATTERN = re.compile(r'^\s*SELECT\s+', re.IGNORECASE | re.MULTILINE)

def is_safe_query(query: str) -> bool:
    """Check if a query is safe (read-only)."""
    # Remove comments
    query_clean = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    query_clean = re.sub(r'/\*.*?\*/', '', query_clean, flags=re.DOTALL)
    
    # Check if it's a SELECT query
    return bool(SAFE_QUERY_PATTERN.match(query_clean.strip()))

@mcp.tool()
async def execute_query(query: str, limit: int = 100) -> QueryResult:
    """Execute a safe database query.
    
    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return
        
    Returns:
        Query results with columns and data
    """
    if not is_safe_query(query):
        raise ValueError("Only SELECT queries are allowed")
    
    max_results = int(os.getenv('MAX_QUERY_RESULTS', '1000'))
    limit = min(limit, max_results)
    
    # Add LIMIT clause if not present
    if 'LIMIT' not in query.upper():
        query = f"{query.rstrip(';')} LIMIT {limit}"
    
    try:
        import time
        start_time = time.time()
        
        with engine.connect() as conn:
            result = conn.execute(text(query))
            columns = list(result.keys())
            rows = [list(row) for row in result.fetchall()]
        
        execution_time = time.time() - start_time
        
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            execution_time=execution_time
        )
        
    except SQLAlchemyError as e:
        raise ValueError(f"Database error: {str(e)}")

@mcp.tool()
async def get_table_info(table_name: str) -> TableInfo:
    """Get information about a database table.
    
    Args:
        table_name: Name of the table to inspect
        
    Returns:
        Table information including columns and types
    """
    try:
        inspector = inspect(engine)
        
        # Check if table exists
        if table_name not in inspector.get_table_names():
            raise ValueError(f"Table '{table_name}' does not exist")
        
        # Get column information
        columns = []
        for column in inspector.get_columns(table_name):
            columns.append({
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column['default']) if column['default'] else None
            })
        
        # Get row count
        try:
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
                row_count = result.scalar()
        except:
            row_count = None
        
        return TableInfo(
            name=table_name,
            columns=columns,
            row_count=row_count
        )
        
    except SQLAlchemyError as e:
        raise ValueError(f"Database error: {str(e)}")

@mcp.tool()
async def list_tables() -> List[str]:
    """List all tables in the database.
    
    Returns:
        List of table names
    """
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    except SQLAlchemyError as e:
        raise ValueError(f"Database error: {str(e)}")

@mcp.tool()
async def query_to_dataframe(query: str, limit: int = 100) -> Dict[str, Any]:
    """Execute query and return results as DataFrame info.
    
    Args:
        query: SQL SELECT query to execute
        limit: Maximum number of rows to return
        
    Returns:
        DataFrame information and basic statistics
    """
    query_result = await execute_query(query, limit)
    
    # Create DataFrame
    df = pd.DataFrame(query_result.rows, columns=query_result.columns)
    
    # Basic statistics
    info = {
        'shape': df.shape,
        'columns': df.columns.tolist(),
        'dtypes': df.dtypes.astype(str).to_dict(),
        'memory_usage': df.memory_usage(deep=True).to_dict(),
        'execution_time': query_result.execution_time
    }
    
    # Add statistics for numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    if len(numeric_columns) > 0:
        info['numeric_summary'] = df[numeric_columns].describe().to_dict()
    
    # Add value counts for categorical columns
    categorical_columns = df.select_dtypes(include=['object']).columns
    if len(categorical_columns) > 0:
        info['categorical_summary'] = {}
        for col in categorical_columns:
            if df[col].nunique() <= 10:  # Only for columns with few unique values
                info['categorical_summary'][col] = df[col].value_counts().to_dict()
    
    return info

@mcp.resource("database://schema")
def get_database_schema() -> dict:
    """Get database schema information."""
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        schema = {
            'database_url': DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL,
            'table_count': len(tables),
            'tables': {}
        }
        
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            schema['tables'][table_name] = {
                'column_count': len(columns),
                'columns': [
                    {
                        'name': col['name'],
                        'type': str(col['type']),
                        'nullable': col['nullable']
                    }
                    for col in columns
                ]
            }
        
        return schema
        
    except Exception as e:
        return {'error': str(e)}

# Initialize sample data if using SQLite
def initialize_sample_data():
    """Initialize sample data for demonstration."""
    if 'sqlite' in DATABASE_URL.lower():
        try:
            with engine.connect() as conn:
                # Create sample table
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS employees (
                        id INTEGER PRIMARY KEY,
                        name TEXT NOT NULL,
                        department TEXT,
                        salary REAL,
                        hire_date DATE
                    )
                """))
                
                # Insert sample data
                conn.execute(text("""
                    INSERT OR IGNORE INTO employees (id, name, department, salary, hire_date)
                    VALUES 
                        (1, 'Alice Johnson', 'Engineering', 75000, '2022-01-15'),
                        (2, 'Bob Smith', 'Marketing', 65000, '2021-03-20'),
                        (3, 'Charlie Brown', 'Engineering', 80000, '2020-07-10'),
                        (4, 'Diana Prince', 'HR', 70000, '2023-02-01'),
                        (5, 'Eve Wilson', 'Marketing', 68000, '2022-11-30')
                """))
                
                conn.commit()
        except Exception as e:
            print(f"Warning: Could not initialize sample data: {e}")

# Initialize sample data on startup
initialize_sample_data()

async def main():
    """Run the database query MCP server."""
    async with mcp.run_server() as server:
        await server.serve()

if __name__ == "__main__":
    asyncio.run(main())
```

### Step 3: Test Database Operations

```python
# Test the database server
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = "./database-project/database-server"

# Validate the server
results = validator.run_comprehensive_tests(project_path)
print(f"Database server validation: {results}")

# Test specific functionality
import sqlite3

# Create test database
conn = sqlite3.connect('test.db')
conn.execute('''
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY,
        name TEXT,
        price REAL,
        category TEXT
    )
''')
conn.execute('''
    INSERT INTO products (name, price, category) VALUES
    ('Laptop', 999.99, 'Electronics'),
    ('Book', 19.99, 'Education'),
    ('Coffee', 4.99, 'Food')
''')
conn.commit()
conn.close()
```

## Tutorial 4: Building a TypeScript MCP Server

Create a TypeScript-based MCP server with modern tooling.

### Step 1: Create TypeScript Server

```python
result = manager.create_project(
    name="typescript-api-server",
    template="typescript-sdk",
    config={
        'output_directory': './typescript-project',
        'custom_settings': {
            'server_name': 'TypeScript API Server',
            'description': 'Modern TypeScript MCP server',
            'port': 3000
        },
        'additional_dependencies': [
            'axios',
            'dotenv',
            '@types/node'
        ]
    }
)
```

### Step 2: Examine Generated Structure

The TypeScript template creates:
```
typescript-api-server/
├── src/
│   └── index.ts          # Main server file
├── package.json          # Node.js dependencies
├── tsconfig.json         # TypeScript configuration
├── README.md            # Documentation
└── .gitignore           # Git ignore rules
```

### Step 3: Customize TypeScript Server

**File: `typescript-project/typescript-api-server/src/index.ts`**
```typescript
#!/usr/bin/env node

/**
 * TypeScript API Server
 * A modern TypeScript MCP server with API integration capabilities
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import axios from 'axios';
import * as dotenv from 'dotenv';

// Load environment variables
dotenv.config();

interface ApiResponse {
  data: any;
  status: number;
  headers: Record<string, string>;
}

interface WeatherData {
  location: string;
  temperature: number;
  description: string;
  humidity: number;
}

class TypeScriptApiServer {
  private server: Server;

  constructor() {
    this.server = new Server(
      {
        name: 'TypeScript API Server',
        version: '1.0.0',
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupToolHandlers();
    this.setupErrorHandling();
  }

  private setupToolHandlers(): void {
    // List available tools
    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: 'fetch_api_data',
            description: 'Fetch data from a REST API endpoint',
            inputSchema: {
              type: 'object',
              properties: {
                url: {
                  type: 'string',
                  description: 'API endpoint URL',
                },
                method: {
                  type: 'string',
                  enum: ['GET', 'POST'],
                  description: 'HTTP method',
                  default: 'GET',
                },
                headers: {
                  type: 'object',
                  description: 'HTTP headers',
                  additionalProperties: { type: 'string' },
                },
                data: {
                  type: 'object',
                  description: 'Request body data (for POST requests)',
                },
              },
              required: ['url'],
            },
          },
          {
            name: 'get_weather',
            description: 'Get weather information for a city',
            inputSchema: {
              type: 'object',
              properties: {
                city: {
                  type: 'string',
                  description: 'City name',
                },
                country: {
                  type: 'string',
                  description: 'Country code (optional)',
                  default: 'US',
                },
              },
              required: ['city'],
            },
          },
          {
            name: 'validate_json',
            description: 'Validate JSON data against a schema',
            inputSchema: {
              type: 'object',
              properties: {
                data: {
                  type: 'object',
                  description: 'JSON data to validate',
                },
                schema: {
                  type: 'object',
                  description: 'JSON schema for validation',
                },
              },
              required: ['data', 'schema'],
            },
          },
        ] as Tool[],
      };
    });

    // Handle tool calls
    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        switch (name) {
          case 'fetch_api_data':
            return await this.fetchApiData(args);
          case 'get_weather':
            return await this.getWeather(args);
          case 'validate_json':
            return await this.validateJson(args);
          default:
            throw new Error(`Unknown tool: ${name}`);
        }
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'Unknown error';
        return {
          content: [
            {
              type: 'text',
              text: `Error: ${errorMessage}`,
            },
          ],
          isError: true,
        };
      }
    });
  }

  private async fetchApiData(args: any): Promise<any> {
    const { url, method = 'GET', headers = {}, data } = args;

    try {
      const response = await axios({
        method,
        url,
        headers,
        data: method === 'POST' ? data : undefined,
        timeout: 10000,
      });

      const result: ApiResponse = {
        data: response.data,
        status: response.status,
        headers: response.headers as Record<string, string>,
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`API request failed: ${error.response?.status} ${error.message}`);
      }
      throw error;
    }
  }

  private async getWeather(args: any): Promise<any> {
    const { city, country = 'US' } = args;
    const apiKey = process.env.OPENWEATHER_API_KEY;

    if (!apiKey) {
      throw new Error('OpenWeather API key not configured');
    }

    const url = 'http://api.openweathermap.org/data/2.5/weather';
    const params = {
      q: `${city},${country}`,
      appid: apiKey,
      units: 'metric',
    };

    try {
      const response = await axios.get(url, { params });
      const data = response.data;

      const weather: WeatherData = {
        location: `${data.name}, ${data.sys.country}`,
        temperature: data.main.temp,
        description: data.weather[0].description,
        humidity: data.main.humidity,
      };

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify(weather, null, 2),
          },
        ],
      };
    } catch (error) {
      if (axios.isAxiosError(error)) {
        throw new Error(`Weather API request failed: ${error.response?.status} ${error.message}`);
      }
      throw error;
    }
  }

  private async validateJson(args: any): Promise<any> {
    const { data, schema } = args;

    try {
      // Simple JSON schema validation (you might want to use a proper library like ajv)
      const isValid = this.simpleJsonValidation(data, schema);
      
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              valid: isValid,
              data,
              schema,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      throw new Error(`JSON validation failed: ${error}`);
    }
  }

  private simpleJsonValidation(data: any, schema: any): boolean {
    // This is a very basic validation - in production, use a proper JSON schema validator
    if (schema.type === 'object' && typeof data === 'object') {
      if (schema.required) {
        for (const prop of schema.required) {
          if (!(prop in data)) {
            return false;
          }
        }
      }
      return true;
    }
    return typeof data === schema.type;
  }

  private setupErrorHandling(): void {
    this.server.onerror = (error) => {
      console.error('[MCP Error]', error);
    };

    process.on('SIGINT', async () => {
      await this.server.close();
      process.exit(0);
    });
  }

  async run(): Promise<void> {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error('TypeScript API Server running on stdio');
  }
}

// Start the server
const server = new TypeScriptApiServer();
server.run().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});
```

### Step 4: Build and Test TypeScript Server

```bash
cd typescript-project/typescript-api-server

# Install dependencies
npm install

# Build the project
npm run build

# Run the server
npm start
```

### Step 5: Validate TypeScript Server

```python
from mcp_server_builder.managers.validation_engine import MCPValidationEngine

validator = MCPValidationEngine()
project_path = "./typescript-project/typescript-api-server"

# Validate the TypeScript server
results = validator.run_comprehensive_tests(project_path)
print(f"TypeScript server validation: {results}")
```

## Advanced Configuration Examples

### Multi-Transport Server Configuration

```python
result = manager.create_project(
    name="multi-transport-server",
    template="python-fastmcp",
    config={
        'custom_settings': {
            'server_name': 'Multi-Transport Server',
            'transport': 'http',  # Can be 'stdio', 'http', or 'sse'
            'host': '0.0.0.0',
            'port': 8080,
            'enable_cors': True,
            'cors_origins': ['http://localhost:3000', 'https://myapp.com']
        },
        'environment_variables': {
            'ENVIRONMENT': 'production',
            'LOG_LEVEL': 'INFO'
        }
    }
)
```

### Production-Ready Configuration

```python
production_config = {
    'output_directory': '/opt/mcp-servers',
    'custom_settings': {
        'server_name': 'Production MCP Server',
        'description': 'Production-ready MCP server with monitoring',
        'transport': 'http',
        'host': '0.0.0.0',
        'port': 8080,
        'enable_metrics': True,
        'enable_health_check': True,
        'enable_rate_limiting': True,
        'rate_limit_requests': 1000,
        'rate_limit_window': 3600
    },
    'environment_variables': {
        'ENVIRONMENT': 'production',
        'LOG_LEVEL': 'WARNING',
        'METRICS_PORT': '9090',
        'DATABASE_URL': 'postgresql://user:pass@db:5432/prod',
        'REDIS_URL': 'redis://redis:6379/0'
    },
    'additional_dependencies': [
        'prometheus-client>=0.17.0',
        'redis>=4.5.0',
        'psycopg2-binary>=2.9.0',
        'gunicorn>=21.0.0'
    ]
}

result = manager.create_project(
    name="production-server",
    template="python-fastmcp",
    config=production_config
)
```

## Next Steps

After completing these tutorials, you should:

1. **Experiment with Different Templates**: Try creating servers with different templates and configurations
2. **Customize Server Logic**: Modify the generated code to implement your specific business logic
3. **Add Error Handling**: Implement robust error handling and logging
4. **Deploy Your Servers**: Set up production deployment with proper monitoring
5. **Create Custom Templates**: Build your own templates for common patterns

### Additional Resources

- [API Reference](api-reference.md) - Complete API documentation
- [Template Development Guide](template-development-guide.md) - Create custom templates
- [Troubleshooting Guide](troubleshooting.md) - Solve common issues
- [FAQ](faq.md) - Frequently asked questions

These tutorials provide a solid foundation for building various types of MCP servers. Each example demonstrates different patterns and best practices that you can adapt for your specific use cases.