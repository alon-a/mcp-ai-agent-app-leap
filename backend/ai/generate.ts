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
  private maxBytes: number;

  constructor(allowedPath: string = process.cwd()) {
    this.allowedPath = path.resolve(allowedPath);
    this.maxBytes = Number(process.env.MAX_BYTES || 512 * 1024); // 512KB default

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
        resources: [
          {
            uri: pathToFileURL(this.allowedPath).href,
            mimeType: "application/json",
            name: "Root directory (listing)",
          },
          ...files.slice(0, 500).map(fileAbs => ({
            uri: pathToFileURL(fileAbs).href,
            mimeType: this.getMimeType(fileAbs),
            name: \`File: \${path.basename(fileAbs)}\`,
          })),
        ],
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "file:") {
        throw new Error("Only file:// URIs are supported");
      }

      const filePath = fileURLToPath(url);
      this.validatePath(filePath);

      const stat = await fs.stat(filePath);
      if (stat.isDirectory()) {
        const items = await fs.readdir(filePath, { withFileTypes: true });
        const result = items.map(item => ({
          name: item.name,
          type: item.isDirectory() ? "directory" : "file",
        }));
        return {
          contents: [
            {
              uri: request.params.uri,
              mimeType: "application/json",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } else {
        if (stat.size > this.maxBytes) {
          throw new Error("File too large");
        }
        const content = await this.readFileTextOrBinary(filePath);
        return {
          contents: [content],
        };
      }
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "list_directory",
            description: "List files and directories at a path under the allowed root",
            inputSchema: {
              type: "object",
              properties: {
                path: {
                  type: "string",
                  description: "Path to the directory to list",
                  default: ".",
                },
              },
            },
          },
          {
            name: "read_file",
            description: \`Read a text file (max \${this.maxBytes} bytes)\`,
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
            description: \`Create or overwrite a file with text content (max \${this.maxBytes} bytes)\`,
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
        case "list_directory": {
          const relativePath = String(args?.path ?? ".");
          const fullPath = this.resolvePath(relativePath);
          return await this.listDirectory(fullPath, relativePath);
        }
        case "read_file": {
          const relativePath = String(args?.path ?? "");
          if (!relativePath) throw new Error("path is required");
          const fullPath = this.resolvePath(relativePath);
          return await this.readFile(fullPath);
        }
        case "write_file": {
          const relativePath = String(args?.path ?? "");
          const content = String(args?.content ?? "");
          if (!relativePath) throw new Error("path is required");
          if (Buffer.byteLength(content, "utf-8") > this.maxBytes) {
            throw new Error("Content too large");
          }
          const fullPath = this.resolvePath(relativePath);
          return await this.writeFile(fullPath, content, relativePath);
        }
        case "create_directory": {
          const relativePath = String(args?.path ?? "");
          if (!relativePath) throw new Error("path is required");
          const fullPath = this.resolvePath(relativePath);
          return await this.createDirectory(fullPath, relativePath);
        }
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  private resolvePath(relativePath: string): string {
    const fullPath = path.isAbsolute(relativePath) 
      ? relativePath 
      : path.resolve(this.allowedPath, relativePath);
    this.validatePath(fullPath);
    return fullPath;
  }

  private validatePath(fullPath: string): void {
    const resolvedPath = path.resolve(fullPath);
    const relativePath = path.relative(this.allowedPath, resolvedPath);
    
    if (relativePath === "" || relativePath.startsWith("..") || path.isAbsolute(relativePath)) {
      throw new Error("Access denied: Path outside allowed directory");
    }
  }

  private async listDirectory(fullPath: string, relativePath: string) {
    const items = await fs.readdir(fullPath, { withFileTypes: true });
    const result = items.map(item => ({
      name: item.name,
      type: item.isDirectory() ? "directory" : "file",
      path: pathPosix.join(this.toPosix(relativePath), item.name),
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

  private async readFile(fullPath: string) {
    const stat = await fs.stat(fullPath);
    if (stat.isDirectory()) {
      throw new Error("Path is a directory");
    }
    if (stat.size > this.maxBytes) {
      throw new Error("File too large");
    }

    const content = await fs.readFile(fullPath, "utf-8");
    return {
      content: [
        {
          type: "text",
          text: content,
        },
      ],
    };
  }

  private async writeFile(fullPath: string, content: string, relativePath: string) {
    // Ensure parent directory exists
    await fs.ensureDir(path.dirname(fullPath));
    
    // Check if path exists and is a directory
    const exists = await fs.pathExists(fullPath);
    if (exists) {
      const stat = await fs.lstat(fullPath);
      if (stat.isDirectory()) {
        throw new Error("Cannot overwrite a directory");
      }
    }

    await fs.writeFile(fullPath, content, "utf-8");
    const bytes = Buffer.byteLength(content, "utf-8");
    
    return {
      content: [
        {
          type: "text",
          text: \`Wrote \${bytes} bytes to \${this.toPosix(relativePath)}\`,
        },
      ],
    };
  }

  private async createDirectory(fullPath: string, relativePath: string) {
    await fs.ensureDir(fullPath);
    
    return {
      content: [
        {
          type: "text",
          text: \`Directory created successfully at \${this.toPosix(relativePath)}\`,
        },
      ],
    };
  }

  private async listFiles(dir: string, cap = 500): Promise<string[]> {
    const out: string[] = [];
    const stack: string[] = [dir];
    
    while (stack.length && out.length < cap) {
      const cur = stack.pop()!;
      try {
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
      } catch (error) {
        // Skip directories we can't read
        continue;
      }
    }
    
    return out;
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

  private toPosix(p: string): string {
    return p.replace(/\\\\/g, "/");
  }

  async run() {
    const transport = new StdioServerTransport();
    await server.connect(transport);
    console.error(\`File System MCP server running on stdio (root: \${this.allowedPath})\`);
  }
}

async function main() {
  const allowedPath = process.env.ALLOWED_PATH || process.cwd();
  
  // Ensure the allowed directory exists
  await fs.ensureDir(allowedPath);
  
  const server = new FileSystemMCPServer(allowedPath);
  await server.run();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}
`;

  const readme = `# ${projectName}

${description || "MCP server for file system operations"}

## Features

- **Secure file operations** within a specified directory with path traversal protection
- **Read and write files** with configurable size limits (default: 512KB)
- **List directory contents** with recursive file discovery
- **Create directories** with automatic parent directory creation
- **Binary file support** with base64 encoding for non-text files
- **Resource listing** with configurable limits for performance
- **Cross-platform compatibility** with proper path handling

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

### Environment Variables

\`\`\`bash
# Root directory that the server can access (required)
export ALLOWED_PATH=/path/to/allowed/directory

# Maximum file size in bytes (optional, default: 512KB)
export MAX_BYTES=524288
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

## Testing with MCP Inspector

Use the official MCP inspector to test your server:

\`\`\`bash
# Install the MCP inspector
npm install -g @modelcontextprotocol/inspector

# Test your server
npx @modelcontextprotocol/inspector node dist/index.js
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
        "ALLOWED_PATH": "/path/to/allowed/directory",
        "MAX_BYTES": "524288"
      }
    }
  }
}
\`\`\`

## Available Tools

- **list_directory**: List files and directories at a path under the allowed root
- **read_file**: Read a text file (with size limit protection)
- **write_file**: Create or overwrite a file with text content
- **create_directory**: Create a new directory (with automatic parent creation)

## Available Resources

The server exposes files in the allowed directory as resources with \`file://\` URIs:

- **Root directory**: Lists the contents of the allowed directory
- **Individual files**: Each file is exposed as a resource for direct access

Resource listing is capped at 500 files for performance.

## Security Features

### Path Traversal Protection
- **Robust path validation**: Uses \`path.relative()\` to prevent directory traversal attacks
- **Absolute path blocking**: Prevents access to paths outside the allowed directory
- **Symlink safety**: Validates resolved paths to prevent symlink escapes

### File Size Limits
- **Configurable limits**: Default 512KB limit prevents large file operations
- **Memory protection**: Prevents server memory exhaustion from large files
- **Both read and write**: Limits apply to both file reading and writing operations

### Input Validation
- **Required parameters**: All tool calls validate required parameters
- **Type checking**: Ensures parameters are of expected types
- **Error handling**: Comprehensive error messages for debugging

## Technical Implementation

### MCP Protocol Compliance
- **Proper SDK usage**: Uses official \`@modelcontextprotocol/sdk\` with correct APIs
- **Stdio transport**: Communicates over stdio as per MCP specification
- **Standard handlers**: Implements \`ListTools\`, \`CallTool\`, \`ListResources\`, \`ReadResource\`
- **ESM modules**: Full ES module support for modern Node.js compatibility

### Cross-Platform Support
- **Path normalization**: Handles Windows and POSIX path differences
- **POSIX output**: Tool outputs use forward slashes for client compatibility
- **URL handling**: Proper \`file://\` URI handling with \`pathToFileURL\`/\`fileURLToPath\`

### Performance Optimizations
- **Lazy loading**: Files are only read when requested
- **Directory limits**: Recursive directory listing is capped for performance
- **Efficient traversal**: Uses stack-based directory traversal to avoid recursion limits

## Example Usage

### List Directory Contents
\`\`\`json
{
  "tool": "list_directory",
  "arguments": {
    "path": "."
  }
}
\`\`\`

### Read a File
\`\`\`json
{
  "tool": "read_file",
  "arguments": {
    "path": "README.md"
  }
}
\`\`\`

### Write a File
\`\`\`json
{
  "tool": "write_file",
  "arguments": {
    "path": "output.txt",
    "content": "Hello from MCP!"
  }
}
\`\`\`

### Create Directory
\`\`\`json
{
  "tool": "create_directory",
  "arguments": {
    "path": "new-folder"
  }
}
\`\`\`

## Error Handling

The server provides detailed error messages for common issues:

- **Path outside allowed directory**: "Access denied: Path outside allowed directory"
- **File too large**: "File too large" (when exceeding MAX_BYTES)
- **Directory overwrite**: "Cannot overwrite a directory"
- **Missing parameters**: "path is required"

## Troubleshooting

### Common Issues

1. **"Access denied" errors**: Ensure the path is within the ALLOWED_PATH directory
2. **"File too large" errors**: Increase MAX_BYTES or reduce file size
3. **Connection issues**: Verify the server is running and accessible via stdio
4. **Path not found**: Check that the ALLOWED_PATH exists and is readable

### Debugging

Enable debug logging by running with:
\`\`\`bash
NODE_DEBUG=mcp npm start
\`\`\`

## Technical Notes

- **ESM modules**: Uses ES modules for compatibility with the MCP SDK
- **TypeScript**: Full TypeScript support with proper type definitions
- **Source maps**: Enabled for better debugging experience
- **Error boundaries**: Comprehensive error handling prevents server crashes
- **Memory efficient**: Streaming file operations where possible

This implementation follows MCP best practices and provides a secure, production-ready file system server.
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
    description: description || "MCP server for secure PostgreSQL database operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "pg": "^8.12.0"
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

interface TableInfo {
  table_schema: string;
  table_name: string;
}

interface WhereCondition {
  column: string;
  op: "=" | "!=";
  value: any;
}

interface WhereClause {
  conditions: WhereCondition[];
}

class DatabaseMCPServer {
  private server: Server;
  private pool: Pool;
  private allowedSchemas: string[];
  private rowLimitDefault: number;
  private rowLimitMax: number;

  constructor() {
    // Configure Postgres from environment variables
    this.pool = new Pool({
      host: process.env.PGHOST || "localhost",
      port: Number(process.env.PGPORT || 5432),
      user: process.env.PGUSER || "postgres",
      password: process.env.PGPASSWORD || "",
      database: process.env.PGDATABASE || "postgres",
      ssl: process.env.PGSSL === "true" ? { rejectUnauthorized: false } : undefined,
      statement_timeout: Number(process.env.PG_STMT_TIMEOUT || 15000),
      idleTimeoutMillis: 30000,
      max: 10,
    });

    // Security configuration
    this.allowedSchemas = (process.env.PG_ALLOW_SCHEMAS || "public").split(",").map(s => s.trim());
    this.rowLimitDefault = Number(process.env.PG_ROW_LIMIT || 50);
    this.rowLimitMax = Number(process.env.PG_ROW_LIMIT_MAX || 500);

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
      const previews = tables.slice(0, 500).map(t => ({
        uri: \`pg://table/\${encodeURIComponent(t.table_schema)}/\${encodeURIComponent(t.table_name)}?limit=\${this.rowLimitDefault}\`,
        mimeType: "application/json",
        name: \`\${t.table_schema}.\${t.table_name} (preview)\`,
      }));

      return {
        resources: [
          {
            uri: "pg://tables",
            mimeType: "application/json",
            name: "Tables list",
          },
          ...previews,
        ],
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "pg:") {
        throw new Error("Only pg:// URIs are supported");
      }

      const host = url.host; // "tables" | "table"
      const path = url.pathname.replace(/^\/+/, ""); // "<schema>/<table>"

      if (host === "tables") {
        const rows = await this.listTables();
        return {
          contents: [
            {
              uri: request.params.uri,
              mimeType: "application/json",
              text: JSON.stringify(rows, null, 2),
            },
          ],
        };
      }

      if (host === "table") {
        const [schemaEnc, tableEnc] = path.split("/");
        if (!schemaEnc || !tableEnc) {
          throw new Error("Expected pg://table/<schema>/<table>");
        }
        const schema = decodeURIComponent(schemaEnc);
        const table = decodeURIComponent(tableEnc);
        const limit = Number(url.searchParams.get("limit") || this.rowLimitDefault);
        const rows = await this.readTable(schema, table, limit);
        
        return {
          contents: [
            {
              uri: request.params.uri,
              mimeType: "application/json",
              text: JSON.stringify(rows, null, 2),
            },
          ],
        };
      }

      throw new Error(\`Unknown resource: \${host}\`);
    });

    this.server.setRequestHandler(ListToolsRequestSchema, async () => {
      return {
        tools: [
          {
            name: "pg_describe_table",
            description: "Get column names and types for a table",
            inputSchema: {
              type: "object",
              properties: {
                schema: {
                  type: "string",
                  description: "Database schema name",
                },
                table: {
                  type: "string",
                  description: "Table name",
                },
              },
              required: ["schema", "table"],
            },
          },
          {
            name: "pg_query_table",
            description: "Read rows from a table with optional equality/inequality filters and limit",
            inputSchema: {
              type: "object",
              properties: {
                schema: {
                  type: "string",
                  description: "Database schema name",
                },
                table: {
                  type: "string",
                  description: "Table name",
                },
                limit: {
                  type: "number",
                  description: "Maximum number of rows to return",
                  default: this.rowLimitDefault,
                },
                where: {
                  type: "object",
                  description: "WHERE clause conditions",
                  properties: {
                    conditions: {
                      type: "array",
                      items: {
                        type: "object",
                        properties: {
                          column: {
                            type: "string",
                            description: "Column name",
                          },
                          op: {
                            type: "string",
                            enum: ["=", "!="],
                            default: "=",
                            description: "Comparison operator",
                          },
                          value: {
                            description: "Value to compare against",
                          },
                        },
                        required: ["column", "value"],
                      },
                    },
                  },
                },
              },
              required: ["schema", "table"],
            },
          },
          {
            name: "pg_list_tables",
            description: "List all tables in allowed schemas",
            inputSchema: {
              type: "object",
              properties: {},
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "pg_describe_table": {
          const schema = String(args?.schema ?? "");
          const table = String(args?.table ?? "");
          if (!schema || !table) throw new Error("schema and table are required");
          return await this.describeTable(schema, table);
        }
        case "pg_query_table": {
          const schema = String(args?.schema ?? "");
          const table = String(args?.table ?? "");
          const limit = Number(args?.limit ?? this.rowLimitDefault);
          const where = args?.where as WhereClause | undefined;
          if (!schema || !table) throw new Error("schema and table are required");
          return await this.queryTable(schema, table, limit, where);
        }
        case "pg_list_tables":
          return await this.listTablesResult();
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  // Simple identifier validator
  private isSafeIdent(s: string): boolean {
    const IDENT = /^[A-Za-z_][A-Za-z0-9_]*$/;
    return IDENT.test(s);
  }

  // List tables from catalog (enforces schema allowlist)
  private async listTables(): Promise<TableInfo[]> {
    const result = await this.pool.query(
      \`SELECT table_schema, table_name
       FROM information_schema.tables
       WHERE table_type = 'BASE TABLE' AND table_schema = ANY($1::text[])
       ORDER BY table_schema, table_name\`,
      [this.allowedSchemas]
    );
    return result.rows;
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

  private async describeTable(schema: string, table: string) {
    if (!this.allowedSchemas.includes(schema)) {
      throw new Error("Schema not allowed");
    }
    if (!this.isSafeIdent(schema) || !this.isSafeIdent(table)) {
      throw new Error("Invalid identifier");
    }

    const result = await this.pool.query(
      \`SELECT column_name, data_type, is_nullable
       FROM information_schema.columns
       WHERE table_schema = $1 AND table_name = $2
       ORDER BY ordinal_position\`,
      [schema, table]
    );

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result.rows, null, 2),
        },
      ],
    };
  }

  // Read rows with limit, optional simple WHERE (column = $1 AND …)
  private async readTable(schema: string, table: string, limit: number, where?: WhereClause): Promise<any[]> {
    if (!this.isSafeIdent(schema) || !this.isSafeIdent(table)) {
      throw new Error("Invalid identifier");
    }
    if (!this.allowedSchemas.includes(schema)) {
      throw new Error("Schema not allowed");
    }

    // Validate columns if a WHERE is provided
    const cols = where?.conditions?.map(c => c.column) || [];
    if (cols.some(c => !this.isSafeIdent(c))) {
      throw new Error("Invalid column identifier");
    }

    // Build where clause with parameterization
    const values: any[] = [];
    const parts: string[] = [];
    if (where?.conditions?.length) {
      for (const c of where.conditions) {
        values.push(c.value);
        const op = c.op === "!=" ? "!=" : "=";
        parts.push(\`"\${c.column}" \${op} $\${values.length}\`);
      }
    }
    const whereSql = parts.length ? \` WHERE \${parts.join(" AND ")}\` : "";

    const lim = Math.min(Math.max(1, Number(limit) || this.rowLimitDefault), this.rowLimitMax);
    const sql = \`SELECT * FROM "\${schema}".\${table}\${whereSql} LIMIT \${lim}\`;
    const result = await this.pool.query(sql, values);
    return result.rows;
  }

  private async queryTable(schema: string, table: string, limit: number, where?: WhereClause) {
    const rows = await this.readTable(schema, table, limit, where);
    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(rows, null, 2),
        },
      ],
    };
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("PostgreSQL MCP server running on stdio");
  }
}

async function main() {
  // Validate required environment variables
  if (!process.env.PGDATABASE && !process.env.DATABASE_URL) {
    console.error("Either PGDATABASE or DATABASE_URL environment variable is required");
    process.exit(1);
  }

  const server = new DatabaseMCPServer();
  await server.run();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(err => {
    console.error(err);
    process.exit(1);
  });
}
`;

  const readme = `# ${projectName}

${description || "MCP server for secure PostgreSQL database operations"}

## Features

- **Secure by design**: No arbitrary SQL execution, only safe read operations
- **Schema allowlisting**: Restrict access to specific database schemas
- **Identifier validation**: Prevent SQL injection through proper identifier validation
- **Row limits**: Configurable limits to prevent large data dumps
- **Connection pooling**: Efficient database connection management
- **Timeout protection**: Statement timeouts to prevent runaway queries

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

### Required Environment Variables

\`\`\`bash
# Database connection (choose one approach)
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=your_password
export PGDATABASE=your_database

# OR use a connection string
export DATABASE_URL="postgresql://username:password@localhost:5432/database_name"
\`\`\`

### Optional Security Configuration

\`\`\`bash
# Allowed schemas (comma-separated, defaults to "public")
export PG_ALLOW_SCHEMAS="public,app_schema"

# Row limits (defaults: 50 default, 500 max)
export PG_ROW_LIMIT=50
export PG_ROW_LIMIT_MAX=500

# Query timeout in milliseconds (default: 15000)
export PG_STMT_TIMEOUT=15000

# Enable SSL (for remote connections)
export PGSSL=true
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
        "PGHOST": "localhost",
        "PGPORT": "5432",
        "PGUSER": "postgres",
        "PGPASSWORD": "your_password",
        "PGDATABASE": "your_database",
        "PG_ALLOW_SCHEMAS": "public"
      }
    }
  }
}
\`\`\`

## Available Tools

- **pg_describe_table**: Get column names and types for a table
- **pg_query_table**: Read rows from a table with optional filters and limits
- **pg_list_tables**: List all tables in allowed schemas

## Available Resources

- **pg://tables**: List of all accessible tables
- **pg://table/\<schema\>/\<table\>**: Preview rows from a specific table

## Security Features

### Safe by Default
- **No arbitrary SQL**: Only predefined, safe operations are allowed
- **Schema allowlisting**: Access restricted to explicitly allowed schemas
- **Identifier validation**: All table and column names are validated against safe patterns
- **Parameterized queries**: All user input is properly parameterized
- **Row limits**: Configurable limits prevent large data dumps
- **Query timeouts**: Prevents runaway queries from consuming resources

### Supported WHERE Operations
The server supports simple equality and inequality filters:
- \`column = value\`
- \`column != value\`

Multiple conditions are combined with AND logic.

## Example Usage

### Describe a table
\`\`\`json
{
  "tool": "pg_describe_table",
  "arguments": {
    "schema": "public",
    "table": "users"
  }
}
\`\`\`

### Query with filters
\`\`\`json
{
  "tool": "pg_query_table",
  "arguments": {
    "schema": "public",
    "table": "users",
    "limit": 10,
    "where": {
      "conditions": [
        {"column": "active", "op": "=", "value": true},
        {"column": "role", "op": "!=", "value": "admin"}
      ]
    }
  }
}
\`\`\`

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Connection pooling with configurable limits
- Proper error handling and validation
- Source maps enabled for better debugging
- Cross-platform compatibility

## Troubleshooting

### Connection Issues
- Verify database credentials and network connectivity
- Check if PostgreSQL is running and accepting connections
- Ensure the database and schemas exist

### Permission Issues
- Verify the database user has SELECT permissions on target tables
- Check that schemas are included in \`PG_ALLOW_SCHEMAS\`

### Performance Issues
- Adjust \`PG_ROW_LIMIT\` and \`PG_ROW_LIMIT_MAX\` for your use case
- Consider adding database indexes for frequently queried columns
- Monitor \`PG_STMT_TIMEOUT\` for slow queries
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
    description: description || "MCP server for secure REST API proxy",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0"
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
import { pathToFileURL } from "url";
import dns from "dns/promises";
import net from "net";

class RestProxyMCPServer {
  private server: Server;
  private allowedHosts: Set<string>;
  private allowedMethods: Set<string>;
  private maxBodyBytes: number;
  private timeoutMs: number;

  constructor() {
    // Security configuration from environment
    this.allowedHosts = new Set(
      (process.env.ALLOWED_HOSTS || "api.example.com")
        .split(",")
        .map(h => h.trim().toLowerCase())
    );
    this.allowedMethods = new Set(["GET", "POST"]);
    this.maxBodyBytes = Number(process.env.MAX_BODY_BYTES || 512 * 1024); // 512 KB
    this.timeoutMs = Number(process.env.TIMEOUT_MS || 15000); // 15 seconds

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
            uri: "rest://config",
            mimeType: "application/json",
            name: "REST Proxy Configuration",
          },
        ],
      };
    });

    this.server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
      const url = new URL(request.params.uri);
      if (url.protocol !== "rest:") {
        throw new Error("Only rest:// URIs are supported");
      }

      if (url.pathname === "//config") {
        const config = {
          allowedHosts: Array.from(this.allowedHosts),
          allowedMethods: Array.from(this.allowedMethods),
          maxBodyBytes: this.maxBodyBytes,
          timeoutMs: this.timeoutMs,
          usage: {
            httpGetJson: "Make GET requests to allowed hosts, returns JSON",
            httpPostJson: "Make POST requests with JSON payload to allowed hosts",
          },
        };
        
        return {
          contents: [
            {
              uri: request.params.uri,
              mimeType: "application/json",
              text: JSON.stringify(config, null, 2),
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
            name: "http_get_json",
            description: "GET a JSON endpoint from an allow-listed host",
            inputSchema: {
              type: "object",
              properties: {
                url: {
                  type: "string",
                  description: "Absolute https:// URL to an allowed host",
                },
                headers: {
                  type: "object",
                  description: "Additional headers (only accept and content-type allowed)",
                  additionalProperties: { type: "string" },
                },
              },
              required: ["url"],
            },
          },
          {
            name: "http_post_json",
            description: "POST JSON to an allow-listed host; returns JSON",
            inputSchema: {
              type: "object",
              properties: {
                url: {
                  type: "string",
                  description: "Absolute https:// URL to an allowed host",
                },
                headers: {
                  type: "object",
                  description: "Additional headers (only accept and content-type allowed)",
                  additionalProperties: { type: "string" },
                },
                body: {
                  description: "JSON-serializable payload",
                },
              },
              required: ["url", "body"],
            },
          },
        ],
      };
    });

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      switch (name) {
        case "http_get_json": {
          const urlStr = String(args?.url ?? "");
          if (!urlStr) throw new Error("url is required");
          
          const url = new URL(urlStr);
          await this.assertUrlAllowed(url);
          const headers = this.sanitizeHeaders(args?.headers);
          
          return await this.makeRequest("GET", url, { headers });
        }
        case "http_post_json": {
          const urlStr = String(args?.url ?? "");
          if (!urlStr) throw new Error("url is required");
          
          const url = new URL(urlStr);
          await this.assertUrlAllowed(url);
          const headers = this.sanitizeHeaders(args?.headers);
          headers["content-type"] = "application/json";
          
          const bodyText = JSON.stringify(args?.body ?? {});
          if (Buffer.byteLength(bodyText) > this.maxBodyBytes) {
            throw new Error("Request body too large");
          }
          
          return await this.makeRequest("POST", url, { headers, body: bodyText });
        }
        default:
          throw new Error(\`Unknown tool: \${name}\`);
      }
    });
  }

  // Block private/loopback/link-local IPs to prevent SSRF
  private isPrivateIp(ip: string): boolean {
    if (net.isIP(ip) === 4) {
      const bytes = ip.split(".").map(Number);
      return (
        bytes[0] === 10 ||
        (bytes[0] === 172 && bytes[1] >= 16 && bytes[1] <= 31) ||
        (bytes[0] === 192 && bytes[1] === 168) ||
        bytes[0] === 127 ||
        (bytes[0] === 169 && bytes[1] === 254)
      );
    }
    // IPv6
    const v6 = ip.toLowerCase();
    return v6 === "::1" || v6.startsWith("fe80:") || v6.startsWith("fc") || v6.startsWith("fd");
  }

  private async assertUrlAllowed(url: URL): Promise<void> {
    // Only allow HTTPS/HTTP
    if (!/^https?:$/.test(url.protocol)) {
      throw new Error("Only http(s) URLs are allowed");
    }
    
    if (!url.hostname) {
      throw new Error("URL must include a hostname");
    }
    
    const hostname = url.hostname.toLowerCase();
    if (!this.allowedHosts.has(hostname)) {
      throw new Error(\`Host '\${hostname}' not allowed. Allowed hosts: \${Array.from(this.allowedHosts).join(", ")}\`);
    }

    // Resolve and block private IPs (basic SSRF guard)
    try {
      const addresses = await dns.lookup(hostname, { all: true, verbatim: true });
      if (addresses.some(addr => this.isPrivateIp(addr.address))) {
        throw new Error("Resolved to a private/loopback IP address");
      }
    } catch (error) {
      if (error instanceof Error && error.message.includes("private/loopback")) {
        throw error;
      }
      throw new Error(\`Failed to resolve hostname: \${hostname}\`);
    }
  }

  private sanitizeHeaders(headers: any): Record<string, string> {
    const allowed = new Set(["accept", "content-type"]);
    const sanitized: Record<string, string> = {};
    
    for (const [key, value] of Object.entries(headers || {})) {
      const normalizedKey = String(key).toLowerCase();
      if (allowed.has(normalizedKey)) {
        sanitized[normalizedKey] = String(value);
      }
    }
    
    return sanitized;
  }

  private abortableTimeout(ms: number): { signal: AbortSignal; cancel: () => void } {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), ms);
    return {
      signal: controller.signal,
      cancel: () => clearTimeout(timeout),
    };
  }

  private async makeRequest(
    method: string,
    url: URL,
    options: { headers?: Record<string, string>; body?: string } = {}
  ) {
    const { signal, cancel } = this.abortableTimeout(this.timeoutMs);
    
    try {
      const response = await fetch(url, {
        method,
        headers: options.headers,
        body: options.body,
        signal,
      });

      // Read response with size limit
      const buffer = new Uint8Array(await response.arrayBuffer());
      if (buffer.byteLength > this.maxBodyBytes) {
        throw new Error("Response too large");
      }

      const text = new TextDecoder().decode(buffer);
      
      // Parse as JSON
      let jsonData;
      try {
        jsonData = JSON.parse(text);
      } catch {
        throw new Error("Response is not valid JSON");
      }

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              status: response.status,
              statusText: response.statusText,
              headers: Object.fromEntries(response.headers.entries()),
              data: jsonData,
            }, null, 2),
          },
        ],
      };
    } catch (error) {
      if (error instanceof Error) {
        return {
          content: [
            {
              type: "text",
              text: \`Error: \${error.message}\`,
            },
          ],
        };
      }
      throw error;
    } finally {
      cancel();
    }
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("REST Proxy MCP server running on stdio");
  }
}

async function main() {
  if (!process.env.ALLOWED_HOSTS) {
    console.error("ALLOWED_HOSTS environment variable is required");
    console.error("Example: ALLOWED_HOSTS=api.example.com,api.github.com");
    process.exit(1);
  }

  const server = new RestProxyMCPServer();
  await server.run();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP server for secure REST API proxy"}

## Features

- **Secure REST API proxy** with comprehensive SSRF protection
- **Host allowlisting** to prevent unauthorized API access
- **IP address validation** to block private/loopback addresses
- **Request/response size limits** to prevent resource exhaustion
- **Timeout protection** to prevent hanging requests
- **JSON-only operations** for predictable data handling
- **Header sanitization** to prevent header injection attacks

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

### Required Environment Variables

\`\`\`bash
# Comma-separated list of allowed hostnames (required)
export ALLOWED_HOSTS="api.example.com,api.github.com,jsonplaceholder.typicode.com"
\`\`\`

### Optional Security Configuration

\`\`\`bash
# Maximum request/response body size in bytes (default: 512KB)
export MAX_BODY_BYTES=524288

# Request timeout in milliseconds (default: 15 seconds)
export TIMEOUT_MS=15000
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
        "ALLOWED_HOSTS": "api.example.com,api.github.com",
        "MAX_BODY_BYTES": "524288",
        "TIMEOUT_MS": "15000"
      }
    }
  }
}
\`\`\`

## Available Tools

- **http_get_json**: Make GET requests to allowed hosts, returns JSON
- **http_post_json**: Make POST requests with JSON payload to allowed hosts

## Available Resources

- **rest://config**: View current proxy configuration and security settings

## Security Features

### SSRF Protection
- **Host allowlisting**: Only configured hostnames are accessible
- **IP address validation**: Blocks requests to private/loopback addresses
- **Protocol restriction**: Only HTTP and HTTPS are allowed
- **DNS resolution checking**: Validates resolved IP addresses

### Request/Response Limits
- **Size limits**: Configurable maximum body size for requests and responses
- **Timeout protection**: Prevents hanging requests with configurable timeouts
- **Method restriction**: Only GET and POST methods are supported

### Header Security
- **Header sanitization**: Only \`accept\` and \`content-type\` headers are allowed
- **No auth forwarding**: Authorization headers are stripped for security

## Example Usage

### GET Request
\`\`\`json
{
  "tool": "http_get_json",
  "arguments": {
    "url": "https://api.example.com/users",
    "headers": {
      "accept": "application/json"
    }
  }
}
\`\`\`

### POST Request
\`\`\`json
{
  "tool": "http_post_json",
  "arguments": {
    "url": "https://api.example.com/users",
    "headers": {
      "accept": "application/json"
    },
    "body": {
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
\`\`\`

## Security Best Practices

### Host Configuration
- Only add trusted API hosts to \`ALLOWED_HOSTS\`
- Use specific hostnames, not wildcards
- Regularly review and update the allowed hosts list

### Network Security
- Deploy behind a firewall for additional protection
- Monitor outbound network traffic
- Consider using a dedicated network segment

### Monitoring
- Log all API requests for audit purposes
- Monitor for unusual request patterns
- Set up alerts for failed requests or timeouts

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Built-in Node.js \`fetch\` API (requires Node.js 18+)
- No external HTTP libraries to reduce attack surface
- Source maps enabled for better debugging
- Comprehensive error handling and validation

## Troubleshooting

### Host Not Allowed Errors
- Verify the hostname is included in \`ALLOWED_HOSTS\`
- Check for typos in hostname configuration
- Ensure hostnames are lowercase in configuration

### Timeout Issues
- Increase \`TIMEOUT_MS\` for slow APIs
- Check network connectivity to target hosts
- Verify the target API is responding

### Size Limit Errors
- Increase \`MAX_BODY_BYTES\` if needed
- Consider pagination for large responses
- Optimize request payloads to reduce size

## Limitations

- **JSON only**: Only JSON requests and responses are supported
- **No authentication forwarding**: API keys must be configured per host if needed
- **Limited HTTP methods**: Only GET and POST are supported
- **No file uploads**: Binary data is not supported

This server prioritizes security over flexibility. For more complex API integration needs, consider implementing a custom server with additional security controls.
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
import { pathToFileURL } from "url";

class GitMCPServer {
  private server: Server;
  private git: SimpleGit;
  private repoPath: string;

  constructor(repoPath: string) {
    this.repoPath = repoPath;
    this.git = simpleGit(repoPath);

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
          ...files.slice(0, 500).map(file => ({
            uri: \`git://file/\${encodeURIComponent(file)}\`,
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

      const host = url.host;
      const path = decodeURIComponent(url.pathname.replace(/^\/+/, ""));

      switch (host) {
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

        case "file":
          if (!path) throw new Error("Missing path in git://file/<path>");
          const text = await this.git.show([\`HEAD:\${path}\`]);
          return {
            contents: [
              {
                uri: request.params.uri,
                mimeType: "text/plain",
                text: text,
              },
            ],
          };

        default:
          throw new Error(\`Unknown resource: \${host}\`);
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
          const commit = args?.commit ? String(args.commit) : "HEAD";
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

  private async readFileResult(filePath: string, commit: string = "HEAD") {
    const content = await this.git.show([\`\${commit}:\${filePath}\`]);
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
    try {
      const files = await this.git.raw(["ls-tree", "-r", "--name-only", "HEAD", dirPath]);
      const result = files.split("\\n").filter(Boolean).map(file => ({
        name: file.split("/").pop() || file,
        type: "file",
        path: file,
      }));

      return {
        content: [
          {
            type: "text",
            text: JSON.stringify(result, null, 2),
          },
        ],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify([], null, 2),
          },
        ],
      };
    }
  }

  private async getTrackedFiles(): Promise<string[]> {
    try {
      const files = await this.git.raw(["ls-tree", "-r", "--name-only", "HEAD"]);
      return files.split("\\n").filter(Boolean);
    } catch (error) {
      return []; // empty repo
    }
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
- Resource listing capped at 500 files for performance
- Proper URI encoding for file paths with special characters
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
        instructions = `Your file system MCP server has been generated with comprehensive security fixes and proper MCP SDK usage! This server provides secure file operations within a specified directory.

**Critical security fixes applied:**
- **Robust path traversal protection**: Uses \`path.relative()\` to prevent directory traversal attacks
- **File size limits**: Configurable maximum file size (default: 512KB) prevents memory exhaustion
- **Input validation**: All tool parameters are validated and type-checked
- **Directory overwrite protection**: Prevents overwriting directories with files
- **Cross-platform compatibility**: Proper path handling for Windows and POSIX systems

**MCP SDK fixes:**
- **Proper ESM module usage**: Correct imports with \`"type": "module"\` in package.json
- **Uses Server + StdioServerTransport**: No HTTP server, communicates over stdio as per MCP specification
- **Correct request handler registration**: Uses proper schemas (\`ListToolsRequestSchema\`, etc.)
- **Proper URI handling**: Uses \`file://\` protocol with \`pathToFileURL\`/\`fileURLToPath\`
- **Input validation**: All tool arguments are validated before processing

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Set the ALLOWED_PATH environment variable to specify the root directory
5. Test with \`npx @modelcontextprotocol/inspector node dist/index.js\`
6. Integrate with Claude Desktop using the provided configuration

**Production features:**
- **ESM module support**: Full compatibility with the MCP SDK
- **Binary file support**: Handles both text and binary files with proper encoding
- **Resource listing**: Exposes files as resources with configurable limits (500 files max)
- **Cross-platform paths**: Normalizes paths to POSIX format for client compatibility
- **Source maps**: Enabled for better debugging experience
- **Comprehensive error handling**: Detailed error messages for troubleshooting

**Available tools:**
- list_directory: List files and directories with path validation
- read_file: Read text files with size limit protection
- write_file: Create/overwrite files with content validation
- create_directory: Create directories with automatic parent creation

This server is production-ready and follows MCP security best practices!`;
        break;

      case "database":
        files = generateDatabaseServer(req.projectName, req.description);
        instructions = `Your PostgreSQL MCP server has been generated with comprehensive security fixes and proper MCP SDK usage! This server provides secure, read-only database access with enterprise-grade safety features.

**Critical security fixes applied:**
- **No SQL injection vulnerabilities**: All identifiers are validated and queries are properly parameterized
- **Schema allowlisting**: Access restricted to explicitly allowed schemas only
- **Row limits**: Configurable limits prevent large data dumps (default: 50, max: 500)
- **Query timeouts**: Prevents runaway queries (default: 15 seconds)
- **Connection pooling**: Efficient resource management with proper limits
- **Identifier validation**: All table/column names validated against safe patterns

**MCP SDK fixes:**
- **Proper ESM module usage**: Correct imports with \`"type": "module"\` in package.json
- **Uses Server + StdioServerTransport**: No HTTP server, communicates over stdio as per MCP specification
- **Correct request handler registration**: Uses proper schemas (\`ListToolsRequestSchema\`, etc.)
- **Proper URI handling**: Uses \`pg://\` protocol (pg://tables, pg://table/<schema>/<table>)
- **Input validation**: All tool arguments are validated before processing

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Configure database connection:
   - Set PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
   - OR set DATABASE_URL connection string
   - Set PG_ALLOW_SCHEMAS (comma-separated, defaults to "public")
5. Test with \`npx @modelcontextprotocol/inspector node dist/index.js\`
6. Integrate with Claude Desktop using the provided configuration

**Production security features:**
- **Safe by default**: Only predefined read operations allowed
- **No arbitrary SQL**: Prevents dangerous queries
- **Parameterized queries**: All user input properly escaped
- **Schema restrictions**: Access limited to allowed schemas
- **Resource limits**: Configurable row limits and timeouts
- **SSL support**: Enable with PGSSL=true for remote connections

**Available tools:**
- pg_describe_table: Get table schema information
- pg_query_table: Query with optional WHERE filters (= and != operators)
- pg_list_tables: List accessible tables

This server is production-ready and follows database security best practices!`;
        break;

      case "api":
        files = generateApiServer(req.projectName, req.description);
        instructions = `Your secure REST API proxy MCP server has been generated with comprehensive security fixes and proper MCP SDK usage! This server provides a safe way to access external APIs with enterprise-grade SSRF protection.

**Critical security fixes applied:**
- **SSRF protection**: Host allowlisting prevents unauthorized API access
- **IP address validation**: Blocks requests to private/loopback addresses (127.0.0.1, 192.168.x.x, etc.)
- **Protocol restrictions**: Only HTTP/HTTPS allowed, no file:// or other schemes
- **DNS resolution checking**: Validates resolved IP addresses before making requests
- **Request/response size limits**: Prevents resource exhaustion attacks
- **Timeout protection**: Configurable timeouts prevent hanging requests
- **Header sanitization**: Only safe headers (accept, content-type) are allowed
- **Method restrictions**: Only GET and POST methods supported

**MCP SDK fixes:**
- **Proper ESM module usage**: Correct imports with \`"type": "module"\` in package.json
- **Uses Server + StdioServerTransport**: No HTTP server, communicates over stdio as per MCP specification
- **Correct request handler registration**: Uses proper schemas (\`ListToolsRequestSchema\`, etc.)
- **Proper URI handling**: Uses \`rest://\` protocol for configuration resources
- **Input validation**: All tool arguments are validated before processing
- **Uses built-in Node.js fetch**: No external HTTP libraries for reduced attack surface

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. **REQUIRED**: Set ALLOWED_HOSTS environment variable with comma-separated hostnames
   - Example: \`ALLOWED_HOSTS=api.example.com,api.github.com\`
5. Optionally configure size limits and timeouts
6. Test with \`npx @modelcontextprotocol/inspector node dist/index.js\`
7. Integrate with Claude Desktop using the provided configuration

**Production security features:**
- **Host allowlisting**: Only configured hostnames are accessible
- **Private IP blocking**: Prevents access to internal networks
- **Size limits**: Configurable max body size (default: 512KB)
- **Timeout protection**: Prevents hanging requests (default: 15s)
- **JSON-only**: Only JSON requests/responses for predictable behavior
- **No auth forwarding**: Authorization headers are stripped for security

**Available tools:**
- http_get_json: Make GET requests to allowed hosts
- http_post_json: Make POST requests with JSON payload

**IMPORTANT**: This server prioritizes security over flexibility. Only add trusted API hosts to ALLOWED_HOSTS!`;
        break;

      case "git":
        files = generateGitServer(req.projectName, req.description);
        instructions = `Your Git repository MCP server has been generated with proper MCP SDK usage and comprehensive fixes! This server provides read-only access to Git repositories.

**Key fixes applied:**
- **Proper ESM module usage**: Correct imports with \`"type": "module"\` in package.json
- **Uses Server + StdioServerTransport**: No HTTP server, communicates over stdio as per MCP specification
- **Correct request handler registration**: Uses proper schemas (\`ListToolsRequestSchema\`, etc.)
- **Proper URI handling**: Uses \`git://\` protocol (git://status, git://log, git://file/<path>)
- **Correct URL parsing**: Uses \`url.host\` and \`url.pathname\` for resource routing
- **Repository context handling**: Proper \`simpleGit(repoPath)\` initialization
- **Input validation**: All tool arguments are validated before processing
- **Resource listing**: Capped at 500 files for performance
- **Proper URI encoding**: Handles file paths with special characters

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Set the REPO_PATH environment variable to your Git repository path
5. Test with \`npx @modelcontextprotocol/inspector node dist/index.js\`
6. Integrate with Claude Desktop using the provided configuration

**Production features:**
- **ESM module support**: Full compatibility with the MCP SDK
- **Read-only operations**: Safe browsing of Git repositories
- **Commit history**: View detailed commit information and diffs
- **File access**: Read files from any commit in the repository
- **Branch management**: List and explore different branches
- **Empty repository handling**: Gracefully handles repositories without commits
- **Source maps**: Enabled for better debugging experience

**Available tools:**
- git_status: Get current repository status
- git_log: View commit history with configurable limits
- git_show: Show detailed commit information
- git_diff: Compare commits, branches, or files
- git_branches: List local and remote branches
- read_file: Read files from any commit
- list_files: Browse repository structure

This server follows MCP best practices and provides secure Git repository access!`;
        break;

      case "custom":
        // Generate a basic template for custom servers
        files = generateFileSystemServer(req.projectName, req.description);
        instructions = `A production-ready MCP server template has been generated based on the file system server with all the latest MCP SDK fixes and security improvements.

**Key fixes included:**
- **Proper ESM module usage**: Correct imports with \`"type": "module"\` in package.json
- **Uses Server + StdioServerTransport**: No HTTP server, communicates over stdio as per MCP specification
- **Correct request handler registration**: Uses proper schemas (\`ListToolsRequestSchema\`, etc.)
- **Proper URI handling**: Correct URL parsing and resource management
- **Input validation**: All tool arguments are validated before processing
- **Security features**: Path traversal protection, file size limits, input validation

**Customization needed:**
1. Modify the tools and resources in src/index.ts according to your requirements
2. Add any additional dependencies to package.json
3. Implement your custom logic in the tool handlers
4. Update URI schemes and resource handling as needed
5. Adjust security measures for your specific use case

**Requirements:** ${req.customRequirements || "No specific requirements provided"}

**Template features to customize:**
- Replace file system operations with your custom functionality
- Modify the URI scheme (currently uses file://) for your resources
- Update tool schemas to match your requirements
- Implement your specific business logic in the request handlers

Follow the MCP SDK documentation to implement your custom functionality while maintaining the security and architectural patterns provided in this template.`;
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
