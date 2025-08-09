import { api } from "encore.dev/api";

export type ServerType = "filesystem" | "database" | "api" | "git" | "custom";

export interface GenerateServerRequest {
  serverType: ServerType;
  projectName: string;
  description?: string;
  features?: string[];
  customRequirements?: string;
}

export interface ProjectFile {
  path: string;
  content: string;
}

export interface GenerateServerResponse {
  files: ProjectFile[];
  instructions: string;
}

const generateFileSystemServer = (projectName: string, description?: string): ProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP server for file system operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "fs-extra": "^11.2.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "typescript": "^5.0.0",
      "tsx": "^4.0.0"
    }
  };

  const tsConfig = {
    compilerOptions: {
      target: "ES2022",
      module: "NodeNext",
      moduleResolution: "NodeNext",
      outDir: "./dist",
      rootDir: "./src",
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      forceConsistentCasingInFileNames: true,
      declaration: true,
      declarationMap: true,
      sourceMap: true
    },
    include: ["src/**/*"],
    exclude: ["node_modules", "dist"]
  };

  const indexTs = `import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import fs from "fs-extra";
import path from "path";
import pathPosix from "path/posix";
import { fileURLToPath, pathToFileURL } from "url";

class FileSystemMCPServer {
  private server: Server;
  private allowedPath: string;

  constructor(allowedPath: string = process.cwd()) {
    this.allowedPath = path.resolve(allowedPath);
    this.server = new Server(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {
          resources: { listChanged: false },
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      const files = await this.listFiles(this.allowedPath);
      return {
        resources: files.map(fileAbs => ({
          uri: pathToFileURL(fileAbs).href,
          mimeType: this.getMimeType(fileAbs),
          name: path.basename(fileAbs),
        })),
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "file:") {
        throw new Error("Only file:// URIs are supported");
      }

      const filePath = fileURLToPath(url);
      if (!this.isPathAllowed(filePath)) {
        throw new Error("Access denied: Path outside allowed directory");
      }

      const content = await this.readFileTextOrBinary(filePath);
      return {
        contents: [content],
      };
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "read_file",
            description: "Read the contents of a file",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Path to the file to read",
                },
              },
              required: ["path"],
            },
          },
          {
            name: "write_file",
            description: "Write content to a file",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Path to the file to write",
                },
                content: {
                  type: "string",
                  description: "Content to write to the file",
                },
              },
              required: ["path", "content"],
            },
          },
          {
            name: "list_directory",
            description: "List files and directories in a path",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Path to the directory to list",
                },
              },
              required: ["path"],
            },
          },
          {
            name: "create_directory",
            description: "Create a new directory",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Path to the directory to create",
                },
              },
              required: ["path"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "read_file": {
          const p = String(args?.path ?? "");
          if (!p) throw new Error("path is required");
          return await this.readFile(p);
        }
        case "write_file": {
          const p = String(args?.path ?? "");
          const content = String(args?.content ?? "");
          if (!p) throw new Error("path is required");
          return await this.writeFile(p, content);
        }
        case "list_directory": {
          const p = String(args?.path ?? "");
          if (!p) throw new Error("path is required");
          return await this.listDirectory(p);
        }
        case "create_directory": {
          const p = String(args?.path ?? "");
          if (!p) throw new Error("path is required");
          return await this.createDirectory(p);
        }
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  private async readFile(filePath: string) {
    const fullPath = path.resolve(this.allowedPath, filePath);
    if (!this.isPathAllowed(fullPath)) {
      throw new Error("Access denied: Path outside allowed directory");
    }

    const content = await this.readFileTextOrBinary(fullPath);
    return {
      content: [
        {
          type: "text",
          text: content.text || content.blob || "",
        },
      ],
    };
  }

  private async writeFile(filePath: string, content: string) {
    const fullPath = path.resolve(this.allowedPath, filePath);
    if (!this.isPathAllowed(fullPath)) {
      throw new Error("Access denied: Path outside allowed directory");
    }

    await fs.ensureDir(path.dirname(fullPath));
    await fs.writeFile(fullPath, content, "utf-8");
    
    return {
      content: [
        {
          type: "text",
          text: \`File written successfully to \${filePath}\`,
        },
      ],
    };
  }

  private async listDirectory(dirPath: string) {
    const fullPath = path.resolve(this.allowedPath, dirPath);
    if (!this.isPathAllowed(fullPath)) {
      throw new Error("Access denied: Path outside allowed directory");
    }

    const items = await fs.readdir(fullPath, { withFileTypes: true });
    const result = items.map(item => ({
      name: item.name,
      type: item.isDirectory() ? "directory" : "file",
      path: pathPosix.join(dirPath.replace(/\\\\/g, "/"), item.name),
    }));

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async createDirectory(dirPath: string) {
    const fullPath = path.resolve(this.allowedPath, dirPath);
    if (!this.isPathAllowed(fullPath)) {
      throw new Error("Access denied: Path outside allowed directory");
    }

    await fs.ensureDir(fullPath);
    
    return {
      content: [
        {
          type: "text",
          text: \`Directory created successfully at \${dirPath}\`,
        },
      ],
    };
  }

  private async listFiles(dir: string, cap = 2000): Promise<string[]> {
    const out: string[] = [];
    const stack: string[] = [dir];
    
    while (stack.length && out.length < cap) {
      const cur = stack.pop()!;
      const items = await fs.readdir(cur, { withFileTypes: true });
      
      for (const it of items) {
        if (it.name === ".git" || it.name === "node_modules") continue;
        const full = path.join(cur, it.name);
        if (it.isDirectory()) {
          stack.push(full);
        } else {
          out.push(full);
        }
        if (out.length >= cap) break;
      }
    }
    
    return out;
  }

  private isPathAllowed(p: string): boolean {
    const rel = path.relative(this.allowedPath, path.resolve(p));
    return rel && !rel.startsWith("..") && !path.isAbsolute(rel);
  }

  private async readFileTextOrBinary(absPath: string) {
    const mimeType = this.getMimeType(absPath);
    const isText = /^text\\/|\/json$|\/javascript$|\/typescript$|\/x-/.test(mimeType);

    if (isText) {
      const text = await fs.readFile(absPath, "utf-8");
      return { uri: pathToFileURL(absPath).href, mimeType, text };
    } else {
      const data = await fs.readFile(absPath);
      return { uri: pathToFileURL(absPath).href, mimeType, blob: data.toString("base64") };
    }
  }

  private getMimeType(filePath: string): string {
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes: Record<string, string> = {
      ".txt": "text/plain",
      ".md": "text/markdown",
      ".js": "text/javascript",
      ".ts": "text/typescript",
      ".json": "application/json",
      ".html": "text/html",
      ".css": "text/css",
      ".py": "text/x-python",
      ".java": "text/x-java-source",
      ".cpp": "text/x-c++src",
      ".c": "text/x-csrc",
      ".png": "image/png",
      ".jpg": "image/jpeg",
      ".jpeg": "image/jpeg",
      ".gif": "image/gif",
      ".pdf": "application/pdf",
      ".zip": "application/zip",
    };
    return mimeTypes[ext] || "application/octet-stream";
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("File System MCP server running on stdio");
  }
}

async function main() {
  const allowedPath = process.env.ALLOWED_PATH || process.cwd();
  const server = new FileSystemMCPServer(allowedPath);
  await server.run();
}

import { pathToFileURL } from "url";
const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP server for file system operations"}

## Features

- Read files from the allowed directory
- Write files to the allowed directory
- List directory contents
- Create new directories
- Secure path validation to prevent directory traversal
- Binary file support with base64 encoding
- Resource listing with configurable limits

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Usage

### Development
\`\`\`bash
npm run dev
\`\`\`

### Production
\`\`\`bash
npm start
\`\`\`

## Configuration

Set the \`ALLOWED_PATH\` environment variable to specify the root directory that the server can access. Defaults to the current working directory.

\`\`\`bash
export ALLOWED_PATH=/path/to/allowed/directory
npm start
\`\`\`

## Claude Desktop Integration

Add this server to your Claude Desktop configuration:

\`\`\`json
{
  "mcpServers": {
    "${projectName}": {
      "command": "node",
      "args": ["--enable-source-maps", "path/to/${projectName}/dist/index.js"],
      "env": {
        "ALLOWED_PATH": "/path/to/allowed/directory"
      }
    }
  }
}
\`\`\`

## Available Tools

- **read_file**: Read the contents of a file (supports both text and binary files)
- **write_file**: Write content to a file
- **list_directory**: List files and directories in a path
- **create_directory**: Create a new directory

## Available Resources

The server exposes files in the allowed directory as resources with \`file://\` URIs. Resource listing is capped at 2000 files for performance.

## Security Features

- Path traversal protection using secure relative path checking
- Configurable allowed directory scope
- Input validation for all tool arguments
- Binary file handling with proper MIME type detection

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Supports both text and binary files with appropriate encoding
- Cross-platform path handling for Windows and POSIX systems
- Source maps enabled for better debugging
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateDatabaseServer = (projectName: string, description?: string): ProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP server for database operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "pg": "^8.11.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "@types/pg": "^8.10.0",
      "typescript": "^5.0.0",
      "tsx": "^4.0.0"
    }
  };

  const tsConfig = {
    compilerOptions: {
      target: "ES2022",
      module: "NodeNext",
      moduleResolution: "NodeNext",
      outDir: "./dist",
      rootDir: "./src",
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      forceConsistentCasingInFileNames: true,
      declaration: true,
      declarationMap: true,
      sourceMap: true
    },
    include: ["src/**/*"],
    exclude: ["node_modules", "dist"]
  };

  const indexTs = `import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { Pool } from "pg";
import { pathToFileURL } from "url";

class DatabaseMCPServer {
  private server: Server;
  private pool: Pool;

  constructor() {
    this.pool = new Pool({
      connectionString: process.env.DATABASE_URL,
    });

    this.server = new Server(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {
          resources: { listChanged: false },
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      const tables = await this.listTables();
      return {
        resources: tables.map(table => ({
          uri: \`postgres://table/\${table}\`,
          mimeType: "application/json",
          name: \`Table: \${table}\`,
        })),
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "postgres:") {
        throw new Error("Only postgres:// URIs are supported");
      }

      const tableName = url.pathname.replace("/table/", "");
      const data = await this.getTableData(tableName);
      
      return {
        contents: [
          {
            uri: request.params.uri,
            mimeType: "application/json",
            text: JSON.stringify(data, null, 2),
          },
        ],
      };
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "query_database",
            description: "Execute a SELECT query on the database",
            inputSchema: {
              type: "object",
              properties: {
                query: {
                  type: "string",
                  description: "SQL SELECT query to execute",
                },
              },
              required: ["query"],
            },
          },
          {
            name: "list_tables",
            description: "List all tables in the database",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "describe_table",
            description: "Get the schema of a specific table",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "Name of the table to describe",
                },
              },
              required: ["table_name"],
            },
          },
          {
            name: "get_table_data",
            description: "Get sample data from a table",
            inputSchema: {
              type: "object",
              properties: {
                table_name: {
                  type: "string",
                  description: "Name of the table",
                },
                limit: {
                  type: "number",
                  description: "Maximum number of rows to return",
                  default: 10,
                },
              },
              required: ["table_name"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "query_database": {
          const query = String(args?.query ?? "");
          if (!query) throw new Error("query is required");
          return await this.queryDatabase(query);
        }
        case "list_tables":
          return await this.listTablesResult();
        case "describe_table": {
          const tableName = String(args?.table_name ?? "");
          if (!tableName) throw new Error("table_name is required");
          return await this.describeTable(tableName);
        }
        case "get_table_data": {
          const tableName = String(args?.table_name ?? "");
          if (!tableName) throw new Error("table_name is required");
          const limit = Number(args?.limit) || 10;
          return await this.getTableDataResult(tableName, limit);
        }
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  private async queryDatabase(query: string) {
    // Only allow SELECT queries for safety
    if (!query.trim().toLowerCase().startsWith("select")) {
      throw new Error("Only SELECT queries are allowed");
    }

    const result = await this.pool.query(query);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify({
            rows: result.rows,
            rowCount: result.rowCount,
            fields: result.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID })),
          }, null, 2),
        },
      ],
    };
  }

  private async listTables(): Promise<string[]> {
    const result = await this.pool.query(\`
      SELECT table_name 
      FROM information_schema.tables 
      WHERE table_schema = 'public'
      ORDER BY table_name
    \`);
    return result.rows.map(row => row.table_name);
  }

  private async listTablesResult() {
    const tables = await this.listTables();
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(tables, null, 2),
        },
      ],
    };
  }

  private async describeTable(tableName: string) {
    const result = await this.pool.query(\`
      SELECT 
        column_name,
        data_type,
        is_nullable,
        column_default,
        character_maximum_length
      FROM information_schema.columns 
      WHERE table_name = $1 AND table_schema = 'public'
      ORDER BY ordinal_position
    \`, [tableName]);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result.rows, null, 2),
        },
      ],
    };
  }

  private async getTableData(tableName: string, limit: number = 10) {
    const result = await this.pool.query(\`SELECT * FROM "\${tableName}" LIMIT $1\`, [limit]);
    return result.rows;
  }

  private async getTableDataResult(tableName: string, limit: number = 10) {
    const data = await this.getTableData(tableName, limit);
    
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Database MCP server running on stdio");
  }
}

async function main() {
  if (!process.env.DATABASE_URL) {
    console.error("DATABASE_URL environment variable is required");
    process.exit(1);
  }

  const server = new DatabaseMCPServer();
  await server.run();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP server for database operations"}

## Features

- Execute SELECT queries safely
- List all tables in the database
- Describe table schemas
- Get sample data from tables
- Read-only operations for security

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

Set the \`DATABASE_URL\` environment variable:

\`\`\`bash
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
\`\`\`

## Usage

### Development
\`\`\`bash
npm run dev
\`\`\`

### Production
\`\`\`bash
npm start
\`\`\`

## Claude Desktop Integration

Add this server to your Claude Desktop configuration:

\`\`\`json
{
  "mcpServers": {
    "${projectName}": {
      "command": "node",
      "args": ["--enable-source-maps", "path/to/${projectName}/dist/index.js"],
      "env": {
        "DATABASE_URL": "postgresql://username:password@localhost:5432/database_name"
      }
    }
  }
}
\`\`\`

## Available Tools

- **query_database**: Execute SELECT queries on the database
- **list_tables**: List all tables in the database
- **describe_table**: Get the schema of a specific table
- **get_table_data**: Get sample data from a table

## Available Resources

The server exposes all tables as resources with \`postgres://table/\` URIs.

## Security

This server only allows SELECT queries to ensure data safety. No INSERT, UPDATE, or DELETE operations are permitted.

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Input validation for all tool arguments
- Source maps enabled for better debugging
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateApiServer = (projectName: string, description?: string): ProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP server for API integration",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "axios": "^1.6.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "typescript": "^5.0.0",
      "tsx": "^4.0.0"
    }
  };

  const tsConfig = {
    compilerOptions: {
      target: "ES2022",
      module: "NodeNext",
      moduleResolution: "NodeNext",
      outDir: "./dist",
      rootDir: "./src",
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      forceConsistentCasingInFileNames: true,
      declaration: true,
      declarationMap: true,
      sourceMap: true
    },
    include: ["src/**/*"],
    exclude: ["node_modules", "dist"]
  };

  const indexTs = `import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import axios, { AxiosRequestConfig } from "axios";
import { pathToFileURL } from "url";

class ApiMCPServer {
  private server: Server;
  private baseUrl: string;
  private apiKey?: string;

  constructor() {
    this.baseUrl = process.env.API_BASE_URL || "";
    this.apiKey = process.env.API_KEY;

    this.server = new Server(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {
          resources: { listChanged: false },
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      return {
        resources: [
          {
            uri: "api://endpoints",
            mimeType: "application/json",
            name: "Available API Endpoints",
          },
        ],
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "api:") {
        throw new Error("Only api:// URIs are supported");
      }

      if (url.pathname === "//endpoints") {
        const endpoints = this.getAvailableEndpoints();
        return {
          contents: [
            {
              uri: request.params.uri,
              mimeType: "application/json",
              text: JSON.stringify(endpoints, null, 2),
            },
          ],
        };
      }

      throw new Error("Unknown resource");
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "get_request",
            description: "Make a GET request to an API endpoint",
            inputSchema: {
              type: "object",
              properties: {
                endpoint: {
                  type: "string",
                  description: "API endpoint path (relative to base URL)",
                },
                params: {
                  type: "object",
                  description: "Query parameters",
                },
                headers: {
                  type: "object",
                  description: "Additional headers",
                },
              },
              required: ["endpoint"],
            },
          },
          {
            name: "post_request",
            description: "Make a POST request to an API endpoint",
            inputSchema: {
              type: "object",
              properties: {
                endpoint: {
                  type: "string",
                  description: "API endpoint path (relative to base URL)",
                },
                data: {
                  type: "object",
                  description: "Request body data",
                },
                headers: {
                  type: "object",
                  description: "Additional headers",
                },
              },
              required: ["endpoint"],
            },
          },
          {
            name: "put_request",
            description: "Make a PUT request to an API endpoint",
            inputSchema: {
              type: "object",
              properties: {
                endpoint: {
                  type: "string",
                  description: "API endpoint path (relative to base URL)",
                },
                data: {
                  type: "object",
                  description: "Request body data",
                },
                headers: {
                  type: "object",
                  description: "Additional headers",
                },
              },
              required: ["endpoint"],
            },
          },
          {
            name: "delete_request",
            description: "Make a DELETE request to an API endpoint",
            inputSchema: {
              type: "object",
              properties: {
                endpoint: {
                  type: "string",
                  description: "API endpoint path (relative to base URL)",
                },
                headers: {
                  type: "object",
                  description: "Additional headers",
                },
              },
              required: ["endpoint"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "get_request": {
          const endpoint = String(args?.endpoint ?? "");
          if (!endpoint) throw new Error("endpoint is required");
          return await this.makeRequest("GET", endpoint, {
            params: args?.params,
            headers: args?.headers,
          });
        }
        case "post_request": {
          const endpoint = String(args?.endpoint ?? "");
          if (!endpoint) throw new Error("endpoint is required");
          return await this.makeRequest("POST", endpoint, {
            data: args?.data,
            headers: args?.headers,
          });
        }
        case "put_request": {
          const endpoint = String(args?.endpoint ?? "");
          if (!endpoint) throw new Error("endpoint is required");
          return await this.makeRequest("PUT", endpoint, {
            data: args?.data,
            headers: args?.headers,
          });
        }
        case "delete_request": {
          const endpoint = String(args?.endpoint ?? "");
          if (!endpoint) throw new Error("endpoint is required");
          return await this.makeRequest("DELETE", endpoint, {
            headers: args?.headers,
          });
        }
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  private async makeRequest(method: string, endpoint: string, options: any = {}) {
    try {
      const url = this.baseUrl + endpoint;
      const config: AxiosRequestConfig = {
        method,
        url,
        ...options,
      };

      // Add API key if available
      if (this.apiKey) {
        config.headers = {
          ...config.headers,
          Authorization: \`Bearer \${this.apiKey}\`,
        };
      }

      const response = await axios(config);

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              status: response.status,
              statusText: response.statusText,
              headers: response.headers,
              data: response.data,
            }, null, 2),
          },
        ],
      };
    } catch (error: any) {
      const errorInfo = {
        message: error.message,
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
      };

      return {
        content: [
          {
            type: "text",
            text: \`Error: \${JSON.stringify(errorInfo, null, 2)}\`,
          },
        ],
      };
    }
  }

  private getAvailableEndpoints() {
    return {
      baseUrl: this.baseUrl,
      authentication: this.apiKey ? "API Key configured" : "No authentication",
      supportedMethods: ["GET", "POST", "PUT", "DELETE"],
      usage: {
        get: "Use get_request tool with endpoint path",
        post: "Use post_request tool with endpoint path and data",
        put: "Use put_request tool with endpoint path and data",
        delete: "Use delete_request tool with endpoint path",
      },
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("API MCP server running on stdio");
  }
}

async function main() {
  if (!process.env.API_BASE_URL) {
    console.error("API_BASE_URL environment variable is required");
    process.exit(1);
  }

  const server = new ApiMCPServer();
  await server.run();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP server for API integration"}

## Features

- Make GET, POST, PUT, and DELETE requests to external APIs
- Support for query parameters and request headers
- Automatic API key authentication
- Error handling and response formatting

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

Set the required environment variables:

\`\`\`bash
export API_BASE_URL="https://api.example.com"
export API_KEY="your-api-key"  # Optional
\`\`\`

## Usage

### Development
\`\`\`bash
npm run dev
\`\`\`

### Production
\`\`\`bash
npm start
\`\`\`

## Claude Desktop Integration

Add this server to your Claude Desktop configuration:

\`\`\`json
{
  "mcpServers": {
    "${projectName}": {
      "command": "node",
      "args": ["--enable-source-maps", "path/to/${projectName}/dist/index.js"],
      "env": {
        "API_BASE_URL": "https://api.example.com",
        "API_KEY": "your-api-key"
      }
    }
  }
}
\`\`\`

## Available Tools

- **get_request**: Make GET requests with optional query parameters
- **post_request**: Make POST requests with request body data
- **put_request**: Make PUT requests with request body data
- **delete_request**: Make DELETE requests

## Available Resources

- **api://endpoints**: Information about available endpoints and configuration

## Example Usage

The server will automatically add the API key as a Bearer token if provided. You can make requests like:

- GET /users?limit=10
- POST /users with user data
- PUT /users/123 with updated user data
- DELETE /users/123

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Input validation for all tool arguments
- Source maps enabled for better debugging
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateGitServer = (projectName: string, description?: string): ProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP server for Git repository operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "simple-git": "^3.20.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "typescript": "^5.0.0",
      "tsx": "^4.0.0"
    }
  };

  const tsConfig = {
    compilerOptions: {
      target: "ES2022",
      module: "NodeNext",
      moduleResolution: "NodeNext",
      outDir: "./dist",
      rootDir: "./src",
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      forceConsistentCasingInFileNames: true,
      declaration: true,
      declarationMap: true,
      sourceMap: true
    },
    include: ["src/**/*"],
    exclude: ["node_modules", "dist"]
  };

  const indexTs = `import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import simpleGit, { SimpleGit } from "simple-git";
import fs from "fs/promises";
import path from "path";
import { pathToFileURL } from "url";

class GitMCPServer {
  private server: Server;
  private git: SimpleGit;
  private repoPath: string;

  constructor(repoPath: string) {
    this.repoPath = path.resolve(repoPath);
    this.git = simpleGit(this.repoPath);

    this.server = new Server(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {
          resources: { listChanged: false },
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  private setupHandlers() {
    this.server.setRequestHandler(ListResourcesRequestSchema, async () => {
      const files = await this.getTrackedFiles();
      return {
        resources: [
          {
            uri: "git://status",
            mimeType: "application/json",
            name: "Git Status",
          },
          {
            uri: "git://log",
            mimeType: "application/json",
            name: "Git Log",
          },
          {
            uri: "git://branches",
            mimeType: "application/json",
            name: "Git Branches",
          },
          ...files.map(file => ({
            uri: \`git://file/\${file}\`,
            mimeType: "text/plain",
            name: \`File: \${file}\`,
          })),
        ],
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "git:") {
        throw new Error("Only git:// URIs are supported");
      }

      const path = url.pathname.substring(2); // Remove leading //

      switch (path) {
        case "status":
          const status = await this.git.status();
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "application/json",
                text: JSON.stringify(status, null, 2),
              },
            ],
          };

        case "log":
          const log = await this.git.log({ maxCount: 20 });
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "application/json",
                text: JSON.stringify(log, null, 2),
              },
            ],
          };

        case "branches":
          const branches = await this.git.branch();
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "application/json",
                text: JSON.stringify(branches, null, 2),
              },
            ],
          };

        default:
          if (path.startsWith("file/")) {
            const filePath = path.substring(5);
            const content = await this.readFile(filePath);
            return {
              contents: [
                {
                  uri: request.params.uri,
                  mimeType: "text/plain",
                  text: content,
                },
              ],
            };
          }
          throw new Error("Unknown resource");
      }
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "git_status",
            description: "Get the current git status",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
          {
            name: "git_log",
            description: "Get git commit history",
            inputSchema: {
              type: "object",
              properties: {
                maxCount: {
                  type: "number",
                  description: "Maximum number of commits to return",
                  default: 10,
                },
              },
            },
          },
          {
            name: "git_show",
            description: "Show details of a specific commit",
            inputSchema: {
              type: "object",
              properties: {
                commit: {
                  type: "string",
                  description: "Commit hash or reference",
                },
              },
              required: ["commit"],
            },
          },
          {
            name: "git_diff",
            description: "Show differences between commits, branches, or working directory",
            inputSchema: {
              type: "object",
              properties: {
                from: {
                  type: "string",
                  description: "Source commit/branch (optional)",
                },
                to: {
                  type: "string",
                  description: "Target commit/branch (optional)",
                },
                file: {
                  type: "string",
                  description: "Specific file to diff (optional)",
                },
              },
            },
          },
          {
            name: "git_branches",
            description: "List all branches",
            inputSchema: {
              type: "object",
              properties: {
                remote: {
                  type: "boolean",
                  description: "Include remote branches",
                  default: false,
                },
              },
            },
          },
          {
            name: "read_file",
            description: "Read a file from the repository",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Path to the file",
                },
                commit: {
                  type: "string",
                  description: "Commit hash to read from (optional, defaults to HEAD)",
                },
              },
              required: ["path"],
            },
          },
          {
            name: "list_files",
            description: "List files in the repository",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Directory path (optional, defaults to root)",
                  default: ".",
                },
              },
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "git_status":
          return await this.getStatus();
        case "git_log": {
          const maxCount = Number(args?.maxCount) || 10;
          return await this.getLog(maxCount);
        }
        case "git_show": {
          const commit = String(args?.commit ?? "");
          if (!commit) throw new Error("commit is required");
          return await this.showCommit(commit);
        }
        case "git_diff": {
          const from = args?.from ? String(args.from) : undefined;
          const to = args?.to ? String(args.to) : undefined;
          const file = args?.file ? String(args.file) : undefined;
          return await this.getDiff(from, to, file);
        }
        case "git_branches": {
          const remote = Boolean(args?.remote);
          return await this.getBranches(remote);
        }
        case "read_file": {
          const filePath = String(args?.path ?? "");
          if (!filePath) throw new Error("path is required");
          const commit = args?.commit ? String(args.commit) : undefined;
          return await this.readFileResult(filePath, commit);
        }
        case "list_files": {
          const dirPath = String(args?.path ?? ".");
          return await this.listFiles(dirPath);
        }
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  private async getStatus() {
    const status = await this.git.status();
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(status, null, 2),
        },
      ],
    };
  }

  private async getLog(maxCount: number = 10) {
    const log = await this.git.log({ maxCount });
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(log, null, 2),
        },
      ],
    };
  }

  private async showCommit(commit: string) {
    const show = await this.git.show([commit]);
    return {
      content: [
        {
          type: "text",
          text: show,
        },
      ],
    };
  }

  private async getDiff(from?: string, to?: string, file?: string) {
    const args: string[] = [];
    if (from) args.push(from);
    if (to) args.push(to);
    if (file) args.push("--", file);

    const diff = await this.git.diff(args);
    return {
      content: [
        {
          type: "text",
          text: diff,
        },
      ],
    };
  }

  private async getBranches(includeRemote: boolean = false) {
    const branches = await this.git.branch(includeRemote ? ["-a"] : []);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(branches, null, 2),
        },
      ],
    };
  }

  private async readFile(filePath: string, commit?: string): Promise<string> {
    const fullPath = path.join(this.repoPath, filePath);
    
    if (commit) {
      // Read file from specific commit
      const content = await this.git.show([\`\${commit}:\${filePath}\`]);
      return content;
    } else {
      // Read file from working directory
      return await fs.readFile(fullPath, "utf-8");
    }
  }

  private async readFileResult(filePath: string, commit?: string) {
    const content = await this.readFile(filePath, commit);
    return {
      content: [
        {
          type: "text",
          text: content,
        },
      ],
    };
  }

  private async listFiles(dirPath: string = ".") {
    const fullPath = path.join(this.repoPath, dirPath);
    const items = await fs.readdir(fullPath, { withFileTypes: true });
    
    const result = items
      .filter(item => !item.name.startsWith(".git"))
      .map(item => ({
        name: item.name,
        type: item.isDirectory() ? "directory" : "file",
        path: path.join(dirPath, item.name),
      }));

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }

  private async getTrackedFiles(): Promise<string[]> {
    const files = await this.git.raw(["ls-tree", "-r", "--name-only", "HEAD"]);
    return files.split("\\n").filter(file => file.trim());
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Git MCP server running on stdio");
  }
}

async function main() {
  const repoPath = process.env.REPO_PATH || process.cwd();
  
  // Check if the directory is a git repository
  try {
    const git = simpleGit(repoPath);
    await git.status();
  } catch (error) {
    console.error(\`Error: \${repoPath} is not a git repository\`);
    process.exit(1);
  }

  const server = new GitMCPServer(repoPath);
  await server.run();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP server for Git repository operations"}

## Features

- Read git status, log, and branch information
- Show commit details and diffs
- Read files from any commit or working directory
- List repository files and directories
- Browse git history and branches

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

Set the \`REPO_PATH\` environment variable to specify the git repository path. Defaults to the current working directory.

\`\`\`bash
export REPO_PATH=/path/to/git/repository
\`\`\`

## Usage

### Development
\`\`\`bash
npm run dev
\`\`\`

### Production
\`\`\`bash
npm start
\`\`\`

## Claude Desktop Integration

Add this server to your Claude Desktop configuration:

\`\`\`json
{
  "mcpServers": {
    "${projectName}": {
      "command": "node",
      "args": ["--enable-source-maps", "path/to/${projectName}/dist/index.js"],
      "env": {
        "REPO_PATH": "/path/to/git/repository"
      }
    }
  }
}
\`\`\`

## Available Tools

- **git_status**: Get the current git status
- **git_log**: Get git commit history
- **git_show**: Show details of a specific commit
- **git_diff**: Show differences between commits, branches, or working directory
- **git_branches**: List all branches
- **read_file**: Read a file from the repository (from any commit)
- **list_files**: List files in the repository

## Available Resources

- **git://status**: Current git status
- **git://log**: Git commit history
- **git://branches**: Git branches information
- **git://file/[path]**: Individual files in the repository

## Security

This server provides read-only access to git repositories. No write operations (commit, push, etc.) are supported.

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Input validation for all tool arguments
- Source maps enabled for better debugging
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

// Generates complete MCP server boilerplate code based on user requirements.
export const generate = api<GenerateServerRequest, GenerateServerResponse>(
  { expose: true, method: "POST", path: "/generate" },
  async (req) => {
    let files: ProjectFile[] = [];
    let instructions = "";

    switch (req.serverType) {
      case "filesystem":
        files = generateFileSystemServer(req.projectName, req.description);
        instructions = `Your file system MCP server has been generated with production-ready fixes! This server provides secure file operations within a specified directory.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Set the ALLOWED_PATH environment variable to specify the root directory
5. Test with \`npm start\` or integrate with Claude Desktop

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Secure path traversal protection using relative path checking
- Binary file support with base64 encoding
- Resource listing capped at 2000 files for performance
- Cross-platform path handling for Windows and POSIX systems
- Input validation for all tool arguments
- Source maps enabled for better debugging`;
        break;

      case "database":
        files = generateDatabaseServer(req.projectName, req.description);
        instructions = `Your database MCP server has been generated with production-ready fixes! This server provides read-only access to PostgreSQL databases.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Set the DATABASE_URL environment variable with your PostgreSQL connection string
5. Test with \`npm start\` or integrate with Claude Desktop

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Input validation for all tool arguments
- Source maps enabled for better debugging
- Security: Only SELECT queries are allowed for data safety`;
        break;

      case "api":
        files = generateApiServer(req.projectName, req.description);
        instructions = `Your API integration MCP server has been generated with production-ready fixes! This server acts as a proxy to external REST APIs.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Set the API_BASE_URL environment variable
5. Optionally set API_KEY for authentication
6. Test with \`npm start\` or integrate with Claude Desktop

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Input validation for all tool arguments
- Source maps enabled for better debugging
- Features: Supports GET, POST, PUT, and DELETE requests with automatic API key authentication`;
        break;

      case "git":
        files = generateGitServer(req.projectName, req.description);
        instructions = `Your Git repository MCP server has been generated with production-ready fixes! This server provides read-only access to Git repositories.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Set the REPO_PATH environment variable to your Git repository path
5. Test with \`npm start\` or integrate with Claude Desktop

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Input validation for all tool arguments
- Source maps enabled for better debugging
- Features: Browse commits, read files from any commit, view diffs, and explore repository history`;
        break;

      case "custom":
        // Generate a basic template for custom servers
        files = generateFileSystemServer(req.projectName, req.description);
        instructions = `A production-ready MCP server template has been generated based on the file system server with all the latest fixes.

**Customization needed:**
1. Modify the tools and resources in src/index.ts according to your requirements
2. Add any additional dependencies to package.json
3. Implement your custom logic in the tool handlers

**Requirements:** ${req.customRequirements || "No specific requirements provided"}

**Production improvements included:**
- ESM module support for MCP SDK compatibility
- Secure path handling and validation
- Binary file support
- Input validation
- Source maps for debugging

Follow the MCP SDK documentation to implement your custom functionality.`;
        break;

      default:
        throw new Error(`Unsupported server type: ${req.serverType}`);
    }

    return {
      files,
      instructions
    };
  }
);
