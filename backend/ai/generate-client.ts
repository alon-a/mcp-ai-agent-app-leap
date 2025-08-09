import { api } from "encore.dev/api";

export type ClientType = "filesystem" | "database" | "api" | "git" | "multi-server" | "custom";

export interface GenerateClientRequest {
  clientType: ClientType;
  projectName: string;
  description?: string;
  serverEndpoints?: string[];
  features?: string[];
  customRequirements?: string;
}

export interface ClientProjectFile {
  path: string;
  content: string;
}

export interface GenerateClientResponse {
  files: ClientProjectFile[];
  instructions: string;
}

const generateFileSystemClient = (projectName: string, description?: string): ClientProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP client for file system operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "commander": "^11.0.0"
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

  const indexTs = `import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Command } from "commander";
import { spawn } from "child_process";
import { pathToFileURL } from "url";

class FileSystemMCPClient {
  private client: Client;
  private transport: StdioClientTransport;

  constructor() {
    this.client = new Client(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );
  }

  async connect(serverCommand: string, serverArgs: string[] = []) {
    // Start the MCP server process
    const serverProcess = spawn(serverCommand, serverArgs, {
      stdio: ["pipe", "pipe", "inherit"],
    });

    this.transport = new StdioClientTransport({
      readable: serverProcess.stdout!,
      writable: serverProcess.stdin!,
    });

    await this.client.connect(this.transport);
    console.log("Connected to MCP server");
  }

  async listResources() {
    try {
      const response = await this.client.request(
        { method: "resources/list" },
        {}
      );
      return response.resources;
    } catch (error) {
      console.error("Error listing resources:", error);
      throw error;
    }
  }

  async readResource(uri: string) {
    try {
      const response = await this.client.request(
        { method: "resources/read" },
        { uri }
      );
      return response.contents;
    } catch (error) {
      console.error(\`Error reading resource \${uri}:\`, error);
      throw error;
    }
  }

  async listTools() {
    try {
      const response = await this.client.request(
        { method: "tools/list" },
        {}
      );
      return response.tools;
    } catch (error) {
      console.error("Error listing tools:", error);
      throw error;
    }
  }

  async callTool(name: string, arguments_: any = {}) {
    try {
      const response = await this.client.request(
        { method: "tools/call" },
        { name, arguments: arguments_ }
      );
      return response.content;
    } catch (error) {
      console.error(\`Error calling tool \${name}:\`, error);
      throw error;
    }
  }

  async readFile(path: string) {
    return await this.callTool("read_file", { path });
  }

  async writeFile(path: string, content: string) {
    return await this.callTool("write_file", { path, content });
  }

  async listDirectory(path: string) {
    return await this.callTool("list_directory", { path });
  }

  async createDirectory(path: string) {
    return await this.callTool("create_directory", { path });
  }

  async disconnect() {
    if (this.transport) {
      await this.transport.close();
    }
  }
}

async function main() {
  const program = new Command();

  program
    .name("${projectName}")
    .description("MCP client for file system operations")
    .version("1.0.0");

  program
    .command("connect")
    .description("Connect to MCP server and start interactive session")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new FileSystemMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        
        // Interactive session
        console.log("\\nMCP Client connected! Available commands:");
        console.log("- list-resources: List all available resources");
        console.log("- list-tools: List all available tools");
        console.log("- read-file <path>: Read a file");
        console.log("- write-file <path> <content>: Write to a file");
        console.log("- list-dir <path>: List directory contents");
        console.log("- create-dir <path>: Create a directory");
        console.log("- quit: Exit the client\\n");

        const readline = await import("readline");
        const rl = readline.createInterface({
          input: process.stdin,
          output: process.stdout,
        });

        const processCommand = async (input: string) => {
          const [command, ...args] = input.trim().split(" ");

          try {
            switch (command) {
              case "list-resources":
                const resources = await client.listResources();
                console.log("Resources:", JSON.stringify(resources, null, 2));
                break;

              case "list-tools":
                const tools = await client.listTools();
                console.log("Tools:", JSON.stringify(tools, null, 2));
                break;

              case "read-file":
                if (args.length === 0) {
                  console.log("Usage: read-file <path>");
                  break;
                }
                const content = await client.readFile(args[0]);
                console.log("File content:", content);
                break;

              case "write-file":
                if (args.length < 2) {
                  console.log("Usage: write-file <path> <content>");
                  break;
                }
                const [path, ...contentParts] = args;
                const fileContent = contentParts.join(" ");
                const result = await client.writeFile(path, fileContent);
                console.log("Write result:", result);
                break;

              case "list-dir":
                if (args.length === 0) {
                  console.log("Usage: list-dir <path>");
                  break;
                }
                const dirContents = await client.listDirectory(args[0]);
                console.log("Directory contents:", dirContents);
                break;

              case "create-dir":
                if (args.length === 0) {
                  console.log("Usage: create-dir <path>");
                  break;
                }
                const createResult = await client.createDirectory(args[0]);
                console.log("Create directory result:", createResult);
                break;

              case "quit":
                await client.disconnect();
                rl.close();
                process.exit(0);
                break;

              default:
                console.log("Unknown command. Type 'quit' to exit.");
            }
          } catch (error) {
            console.error("Error:", error);
          }

          rl.prompt();
        };

        rl.setPrompt("mcp> ");
        rl.prompt();

        rl.on("line", processCommand);
        rl.on("close", async () => {
          await client.disconnect();
          process.exit(0);
        });

      } catch (error) {
        console.error("Failed to connect to MCP server:", error);
        process.exit(1);
      }
    });

  program
    .command("read-file")
    .description("Read a file from the server")
    .argument("<path>", "File path to read")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (path, options) => {
      const client = new FileSystemMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const content = await client.readFile(path);
        console.log(content);
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("write-file")
    .description("Write content to a file")
    .argument("<path>", "File path to write")
    .argument("<content>", "Content to write")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (path, content, options) => {
      const client = new FileSystemMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const result = await client.writeFile(path, content);
        console.log(result);
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("list-dir")
    .description("List directory contents")
    .argument("<path>", "Directory path to list")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (path, options) => {
      const client = new FileSystemMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const contents = await client.listDirectory(path);
        console.log(contents);
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  await program.parseAsync();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP client for file system operations"}

## Features

- Connect to MCP file system servers
- Interactive command-line interface
- Read and write files
- List directory contents
- Create directories
- Programmatic API for integration

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Usage

### Interactive Mode

Connect to an MCP server and start an interactive session:

\`\`\`bash
npm start connect --server node --args path/to/server/dist/index.js
\`\`\`

Available interactive commands:
- \`list-resources\`: List all available resources
- \`list-tools\`: List all available tools
- \`read-file <path>\`: Read a file
- \`write-file <path> <content>\`: Write to a file
- \`list-dir <path>\`: List directory contents
- \`create-dir <path>\`: Create a directory
- \`quit\`: Exit the client

### Command Line Mode

Execute single commands:

\`\`\`bash
# Read a file
npm start read-file README.md --server node --args path/to/server/dist/index.js

# Write a file
npm start write-file test.txt "Hello World" --server node --args path/to/server/dist/index.js

# List directory
npm start list-dir . --server node --args path/to/server/dist/index.js
\`\`\`

### Programmatic Usage

\`\`\`typescript
import { FileSystemMCPClient } from './src/index.js';

const client = new FileSystemMCPClient();
await client.connect('node', ['path/to/server/dist/index.js']);

// Read a file
const content = await client.readFile('README.md');
console.log(content);

// Write a file
await client.writeFile('output.txt', 'Hello from MCP client!');

// List directory
const files = await client.listDirectory('.');
console.log(files);

await client.disconnect();
\`\`\`

## Configuration

The client connects to MCP servers via stdio transport. Make sure your MCP server is properly configured and accessible.

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Source maps enabled for better debugging
- Cross-platform compatibility

## Development

\`\`\`bash
# Development mode
npm run dev

# Build
npm run build
\`\`\`
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateDatabaseClient = (projectName: string, description?: string): ClientProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP client for database operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "commander": "^11.0.0",
      "inquirer": "^9.0.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "@types/inquirer": "^9.0.0",
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

  const indexTs = `import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Command } from "commander";
import inquirer from "inquirer";
import { spawn } from "child_process";
import { pathToFileURL } from "url";

class DatabaseMCPClient {
  private client: Client;
  private transport: StdioClientTransport;

  constructor() {
    this.client = new Client(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );
  }

  async connect(serverCommand: string, serverArgs: string[] = []) {
    const serverProcess = spawn(serverCommand, serverArgs, {
      stdio: ["pipe", "pipe", "inherit"],
    });

    this.transport = new StdioClientTransport({
      readable: serverProcess.stdout!,
      writable: serverProcess.stdin!,
    });

    await this.client.connect(this.transport);
    console.log("Connected to MCP database server");
  }

  async listResources() {
    try {
      const response = await this.client.request(
        { method: "resources/list" },
        {}
      );
      return response.resources;
    } catch (error) {
      console.error("Error listing resources:", error);
      throw error;
    }
  }

  async readResource(uri: string) {
    try {
      const response = await this.client.request(
        { method: "resources/read" },
        { uri }
      );
      return response.contents;
    } catch (error) {
      console.error(\`Error reading resource \${uri}:\`, error);
      throw error;
    }
  }

  async listTools() {
    try {
      const response = await this.client.request(
        { method: "tools/list" },
        {}
      );
      return response.tools;
    } catch (error) {
      console.error("Error listing tools:", error);
      throw error;
    }
  }

  async callTool(name: string, arguments_: any = {}) {
    try {
      const response = await this.client.request(
        { method: "tools/call" },
        { name, arguments: arguments_ }
      );
      return response.content;
    } catch (error) {
      console.error(\`Error calling tool \${name}:\`, error);
      throw error;
    }
  }

  async queryDatabase(query: string) {
    return await this.callTool("query_database", { query });
  }

  async listTables() {
    return await this.callTool("list_tables");
  }

  async describeTable(tableName: string) {
    return await this.callTool("describe_table", { table_name: tableName });
  }

  async getTableData(tableName: string, limit: number = 10) {
    return await this.callTool("get_table_data", { table_name: tableName, limit });
  }

  async disconnect() {
    if (this.transport) {
      await this.transport.close();
    }
  }
}

async function startInteractiveSession(client: DatabaseMCPClient) {
  console.log("\\nDatabase MCP Client - Interactive Mode");
  console.log("Type 'help' for available commands or 'quit' to exit\\n");

  while (true) {
    try {
      const { action } = await inquirer.prompt([
        {
          type: "list",
          name: "action",
          message: "What would you like to do?",
          choices: [
            { name: "List all tables", value: "list_tables" },
            { name: "Describe a table", value: "describe_table" },
            { name: "Query database", value: "query" },
            { name: "Get table data", value: "table_data" },
            { name: "List resources", value: "list_resources" },
            { name: "List tools", value: "list_tools" },
            { name: "Exit", value: "quit" },
          ],
        },
      ]);

      if (action === "quit") {
        break;
      }

      switch (action) {
        case "list_tables":
          const tables = await client.listTables();
          console.log("\\nTables:", JSON.stringify(tables, null, 2));
          break;

        case "describe_table":
          const { tableName } = await inquirer.prompt([
            {
              type: "input",
              name: "tableName",
              message: "Enter table name:",
            },
          ]);
          const schema = await client.describeTable(tableName);
          console.log(\`\\nTable '\${tableName}' schema:\`, JSON.stringify(schema, null, 2));
          break;

        case "query":
          const { query } = await inquirer.prompt([
            {
              type: "input",
              name: "query",
              message: "Enter SQL query (SELECT only):",
            },
          ]);
          const result = await client.queryDatabase(query);
          console.log("\\nQuery result:", JSON.stringify(result, null, 2));
          break;

        case "table_data":
          const { dataTableName, limit } = await inquirer.prompt([
            {
              type: "input",
              name: "dataTableName",
              message: "Enter table name:",
            },
            {
              type: "number",
              name: "limit",
              message: "Number of rows to fetch:",
              default: 10,
            },
          ]);
          const data = await client.getTableData(dataTableName, limit);
          console.log(\`\\nData from '\${dataTableName}':\`, JSON.stringify(data, null, 2));
          break;

        case "list_resources":
          const resources = await client.listResources();
          console.log("\\nResources:", JSON.stringify(resources, null, 2));
          break;

        case "list_tools":
          const tools = await client.listTools();
          console.log("\\nTools:", JSON.stringify(tools, null, 2));
          break;
      }

      console.log("\\n" + "=".repeat(50) + "\\n");
    } catch (error) {
      console.error("Error:", error);
    }
  }
}

async function main() {
  const program = new Command();

  program
    .name("${projectName}")
    .description("MCP client for database operations")
    .version("1.0.0");

  program
    .command("connect")
    .description("Connect to MCP server and start interactive session")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new DatabaseMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        await startInteractiveSession(client);
        await client.disconnect();
      } catch (error) {
        console.error("Failed to connect to MCP server:", error);
        process.exit(1);
      }
    });

  program
    .command("query")
    .description("Execute a database query")
    .argument("<query>", "SQL query to execute")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (query, options) => {
      const client = new DatabaseMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const result = await client.queryDatabase(query);
        console.log(JSON.stringify(result, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("list-tables")
    .description("List all database tables")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new DatabaseMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const tables = await client.listTables();
        console.log(JSON.stringify(tables, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("describe")
    .description("Describe a database table")
    .argument("<table>", "Table name to describe")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (table, options) => {
      const client = new DatabaseMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const schema = await client.describeTable(table);
        console.log(JSON.stringify(schema, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  await program.parseAsync();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP client for database operations"}

## Features

- Connect to MCP database servers
- Interactive command-line interface with guided prompts
- Execute SQL queries safely
- List and describe database tables
- Get sample data from tables
- Programmatic API for integration

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Usage

### Interactive Mode

Connect to an MCP database server and start an interactive session:

\`\`\`bash
npm start connect --server node --args path/to/server/dist/index.js
\`\`\`

The interactive mode provides a guided interface with options to:
- List all tables
- Describe table schemas
- Execute SQL queries
- Get sample data from tables
- List available resources and tools

### Command Line Mode

Execute single commands:

\`\`\`bash
# List all tables
npm start list-tables --server node --args path/to/server/dist/index.js

# Describe a table
npm start describe users --server node --args path/to/server/dist/index.js

# Execute a query
npm start query "SELECT * FROM users LIMIT 5" --server node --args path/to/server/dist/index.js
\`\`\`

### Programmatic Usage

\`\`\`typescript
import { DatabaseMCPClient } from './src/index.js';

const client = new DatabaseMCPClient();
await client.connect('node', ['path/to/server/dist/index.js']);

// List tables
const tables = await client.listTables();
console.log('Tables:', tables);

// Describe a table
const schema = await client.describeTable('users');
console.log('Schema:', schema);

// Execute a query
const result = await client.queryDatabase('SELECT COUNT(*) FROM users');
console.log('Result:', result);

// Get sample data
const data = await client.getTableData('users', 10);
console.log('Sample data:', data);

await client.disconnect();
\`\`\`

## Configuration

The client connects to MCP database servers via stdio transport. Ensure your MCP server is configured with the correct database connection string.

## Security

This client only supports SELECT queries for safety. No INSERT, UPDATE, or DELETE operations are permitted through the MCP server.

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Source maps enabled for better debugging
- Interactive prompts for better user experience

## Development

\`\`\`bash
# Development mode
npm run dev

# Build
npm run build
\`\`\`
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateApiClient = (projectName: string, description?: string): ClientProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP client for API integration",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "commander": "^11.0.0",
      "inquirer": "^9.0.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "@types/inquirer": "^9.0.0",
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

  const indexTs = `import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Command } from "commander";
import inquirer from "inquirer";
import { spawn } from "child_process";
import { pathToFileURL } from "url";

class ApiMCPClient {
  private client: Client;
  private transport: StdioClientTransport;

  constructor() {
    this.client = new Client(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );
  }

  async connect(serverCommand: string, serverArgs: string[] = []) {
    const serverProcess = spawn(serverCommand, serverArgs, {
      stdio: ["pipe", "pipe", "inherit"],
    });

    this.transport = new StdioClientTransport({
      readable: serverProcess.stdout!,
      writable: serverProcess.stdin!,
    });

    await this.client.connect(this.transport);
    console.log("Connected to MCP API server");
  }

  async listResources() {
    try {
      const response = await this.client.request(
        { method: "resources/list" },
        {}
      );
      return response.resources;
    } catch (error) {
      console.error("Error listing resources:", error);
      throw error;
    }
  }

  async readResource(uri: string) {
    try {
      const response = await this.client.request(
        { method: "resources/read" },
        { uri }
      );
      return response.contents;
    } catch (error) {
      console.error(\`Error reading resource \${uri}:\`, error);
      throw error;
    }
  }

  async listTools() {
    try {
      const response = await this.client.request(
        { method: "tools/list" },
        {}
      );
      return response.tools;
    } catch (error) {
      console.error("Error listing tools:", error);
      throw error;
    }
  }

  async callTool(name: string, arguments_: any = {}) {
    try {
      const response = await this.client.request(
        { method: "tools/call" },
        { name, arguments: arguments_ }
      );
      return response.content;
    } catch (error) {
      console.error(\`Error calling tool \${name}:\`, error);
      throw error;
    }
  }

  async makeGetRequest(endpoint: string, params?: any, headers?: any) {
    return await this.callTool("get_request", { endpoint, params, headers });
  }

  async makePostRequest(endpoint: string, data?: any, headers?: any) {
    return await this.callTool("post_request", { endpoint, data, headers });
  }

  async makePutRequest(endpoint: string, data?: any, headers?: any) {
    return await this.callTool("put_request", { endpoint, data, headers });
  }

  async makeDeleteRequest(endpoint: string, headers?: any) {
    return await this.callTool("delete_request", { endpoint, headers });
  }

  async disconnect() {
    if (this.transport) {
      await this.transport.close();
    }
  }
}

async function startInteractiveSession(client: ApiMCPClient) {
  console.log("\\nAPI MCP Client - Interactive Mode");
  console.log("Make HTTP requests through the MCP server\\n");

  while (true) {
    try {
      const { action } = await inquirer.prompt([
        {
          type: "list",
          name: "action",
          message: "What would you like to do?",
          choices: [
            { name: "Make GET request", value: "get" },
            { name: "Make POST request", value: "post" },
            { name: "Make PUT request", value: "put" },
            { name: "Make DELETE request", value: "delete" },
            { name: "List available endpoints", value: "endpoints" },
            { name: "List tools", value: "list_tools" },
            { name: "Exit", value: "quit" },
          ],
        },
      ]);

      if (action === "quit") {
        break;
      }

      switch (action) {
        case "get":
          const { getEndpoint, getParams } = await inquirer.prompt([
            {
              type: "input",
              name: "getEndpoint",
              message: "Enter endpoint path (e.g., /users):",
            },
            {
              type: "input",
              name: "getParams",
              message: "Enter query parameters (JSON format, optional):",
            },
          ]);
          
          let params;
          if (getParams.trim()) {
            try {
              params = JSON.parse(getParams);
            } catch (e) {
              console.log("Invalid JSON for parameters, ignoring...");
            }
          }
          
          const getResult = await client.makeGetRequest(getEndpoint, params);
          console.log("\\nGET Response:", JSON.stringify(getResult, null, 2));
          break;

        case "post":
          const { postEndpoint, postData } = await inquirer.prompt([
            {
              type: "input",
              name: "postEndpoint",
              message: "Enter endpoint path (e.g., /users):",
            },
            {
              type: "input",
              name: "postData",
              message: "Enter request body (JSON format):",
            },
          ]);
          
          let data;
          if (postData.trim()) {
            try {
              data = JSON.parse(postData);
            } catch (e) {
              console.log("Invalid JSON for data");
              break;
            }
          }
          
          const postResult = await client.makePostRequest(postEndpoint, data);
          console.log("\\nPOST Response:", JSON.stringify(postResult, null, 2));
          break;

        case "put":
          const { putEndpoint, putData } = await inquirer.prompt([
            {
              type: "input",
              name: "putEndpoint",
              message: "Enter endpoint path (e.g., /users/123):",
            },
            {
              type: "input",
              name: "putData",
              message: "Enter request body (JSON format):",
            },
          ]);
          
          let putDataObj;
          if (putData.trim()) {
            try {
              putDataObj = JSON.parse(putData);
            } catch (e) {
              console.log("Invalid JSON for data");
              break;
            }
          }
          
          const putResult = await client.makePutRequest(putEndpoint, putDataObj);
          console.log("\\nPUT Response:", JSON.stringify(putResult, null, 2));
          break;

        case "delete":
          const { deleteEndpoint } = await inquirer.prompt([
            {
              type: "input",
              name: "deleteEndpoint",
              message: "Enter endpoint path (e.g., /users/123):",
            },
          ]);
          
          const deleteResult = await client.makeDeleteRequest(deleteEndpoint);
          console.log("\\nDELETE Response:", JSON.stringify(deleteResult, null, 2));
          break;

        case "endpoints":
          const endpoints = await client.readResource("api://endpoints");
          console.log("\\nAvailable endpoints:", JSON.stringify(endpoints, null, 2));
          break;

        case "list_tools":
          const tools = await client.listTools();
          console.log("\\nTools:", JSON.stringify(tools, null, 2));
          break;
      }

      console.log("\\n" + "=".repeat(50) + "\\n");
    } catch (error) {
      console.error("Error:", error);
    }
  }
}

async function main() {
  const program = new Command();

  program
    .name("${projectName}")
    .description("MCP client for API integration")
    .version("1.0.0");

  program
    .command("connect")
    .description("Connect to MCP server and start interactive session")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new ApiMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        await startInteractiveSession(client);
        await client.disconnect();
      } catch (error) {
        console.error("Failed to connect to MCP server:", error);
        process.exit(1);
      }
    });

  program
    .command("get")
    .description("Make a GET request")
    .argument("<endpoint>", "API endpoint path")
    .option("-p, --params <params>", "Query parameters (JSON)")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (endpoint, options) => {
      const client = new ApiMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        
        let params;
        if (options.params) {
          params = JSON.parse(options.params);
        }
        
        const result = await client.makeGetRequest(endpoint, params);
        console.log(JSON.stringify(result, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("post")
    .description("Make a POST request")
    .argument("<endpoint>", "API endpoint path")
    .option("-d, --data <data>", "Request body data (JSON)")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (endpoint, options) => {
      const client = new ApiMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        
        let data;
        if (options.data) {
          data = JSON.parse(options.data);
        }
        
        const result = await client.makePostRequest(endpoint, data);
        console.log(JSON.stringify(result, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  await program.parseAsync();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP client for API integration"}

## Features

- Connect to MCP API servers
- Interactive command-line interface
- Make HTTP requests (GET, POST, PUT, DELETE)
- Support for query parameters and request bodies
- JSON formatting for requests and responses
- Programmatic API for integration

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Usage

### Interactive Mode

Connect to an MCP API server and start an interactive session:

\`\`\`bash
npm start connect --server node --args path/to/server/dist/index.js
\`\`\`

The interactive mode provides options to:
- Make GET, POST, PUT, and DELETE requests
- View available endpoints
- List server tools
- Input request data in JSON format

### Command Line Mode

Execute single requests:

\`\`\`bash
# GET request
npm start get /users --params '{"limit": 10}' --server node --args path/to/server/dist/index.js

# POST request
npm start post /users --data '{"name": "John", "email": "john@example.com"}' --server node --args path/to/server/dist/index.js
\`\`\`

### Programmatic Usage

\`\`\`typescript
import { ApiMCPClient } from './src/index.js';

const client = new ApiMCPClient();
await client.connect('node', ['path/to/server/dist/index.js']);

// GET request
const users = await client.makeGetRequest('/users', { limit: 10 });
console.log('Users:', users);

// POST request
const newUser = await client.makePostRequest('/users', {
  name: 'John Doe',
  email: 'john@example.com'
});
console.log('Created user:', newUser);

// PUT request
const updatedUser = await client.makePutRequest('/users/123', {
  name: 'John Smith'
});
console.log('Updated user:', updatedUser);

// DELETE request
const deleteResult = await client.makeDeleteRequest('/users/123');
console.log('Delete result:', deleteResult);

await client.disconnect();
\`\`\`

## Configuration

The client connects to MCP API servers via stdio transport. Ensure your MCP server is configured with the correct API base URL and authentication credentials.

## Request Format

- Query parameters and request bodies should be provided in JSON format
- The server handles authentication automatically if configured
- All responses are returned in JSON format

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Source maps enabled for better debugging
- Interactive prompts for better user experience

## Development

\`\`\`bash
# Development mode
npm run dev

# Build
npm run build
\`\`\`
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateGitClient = (projectName: string, description?: string): ClientProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP client for Git repository operations",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "commander": "^11.0.0",
      "inquirer": "^9.0.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "@types/inquirer": "^9.0.0",
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

  const indexTs = `import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Command } from "commander";
import inquirer from "inquirer";
import { spawn } from "child_process";
import { pathToFileURL } from "url";

class GitMCPClient {
  private client: Client;
  private transport: StdioClientTransport;

  constructor() {
    this.client = new Client(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );
  }

  async connect(serverCommand: string, serverArgs: string[] = []) {
    const serverProcess = spawn(serverCommand, serverArgs, {
      stdio: ["pipe", "pipe", "inherit"],
    });

    this.transport = new StdioClientTransport({
      readable: serverProcess.stdout!,
      writable: serverProcess.stdin!,
    });

    await this.client.connect(this.transport);
    console.log("Connected to MCP Git server");
  }

  async listResources() {
    try {
      const response = await this.client.request(
        { method: "resources/list" },
        {}
      );
      return response.resources;
    } catch (error) {
      console.error("Error listing resources:", error);
      throw error;
    }
  }

  async readResource(uri: string) {
    try {
      const response = await this.client.request(
        { method: "resources/read" },
        { uri }
      );
      return response.contents;
    } catch (error) {
      console.error(\`Error reading resource \${uri}:\`, error);
      throw error;
    }
  }

  async listTools() {
    try {
      const response = await this.client.request(
        { method: "tools/list" },
        {}
      );
      return response.tools;
    } catch (error) {
      console.error("Error listing tools:", error);
      throw error;
    }
  }

  async callTool(name: string, arguments_: any = {}) {
    try {
      const response = await this.client.request(
        { method: "tools/call" },
        { name, arguments: arguments_ }
      );
      return response.content;
    } catch (error) {
      console.error(\`Error calling tool \${name}:\`, error);
      throw error;
    }
  }

  async getGitStatus() {
    return await this.callTool("git_status");
  }

  async getGitLog(maxCount: number = 10) {
    return await this.callTool("git_log", { maxCount });
  }

  async showCommit(commit: string) {
    return await this.callTool("git_show", { commit });
  }

  async getDiff(from?: string, to?: string, file?: string) {
    return await this.callTool("git_diff", { from, to, file });
  }

  async getBranches(remote: boolean = false) {
    return await this.callTool("git_branches", { remote });
  }

  async readFile(path: string, commit?: string) {
    return await this.callTool("read_file", { path, commit });
  }

  async listFiles(path: string = ".") {
    return await this.callTool("list_files", { path });
  }

  async disconnect() {
    if (this.transport) {
      await this.transport.close();
    }
  }
}

async function startInteractiveSession(client: GitMCPClient) {
  console.log("\\nGit MCP Client - Interactive Mode");
  console.log("Explore Git repositories through the MCP server\\n");

  while (true) {
    try {
      const { action } = await inquirer.prompt([
        {
          type: "list",
          name: "action",
          message: "What would you like to do?",
          choices: [
            { name: "Show git status", value: "status" },
            { name: "Show git log", value: "log" },
            { name: "Show commit details", value: "show" },
            { name: "Show diff", value: "diff" },
            { name: "List branches", value: "branches" },
            { name: "Read file", value: "read_file" },
            { name: "List files", value: "list_files" },
            { name: "List resources", value: "list_resources" },
            { name: "Exit", value: "quit" },
          ],
        },
      ]);

      if (action === "quit") {
        break;
      }

      switch (action) {
        case "status":
          const status = await client.getGitStatus();
          console.log("\\nGit Status:", JSON.stringify(status, null, 2));
          break;

        case "log":
          const { logCount } = await inquirer.prompt([
            {
              type: "number",
              name: "logCount",
              message: "Number of commits to show:",
              default: 10,
            },
          ]);
          const log = await client.getGitLog(logCount);
          console.log("\\nGit Log:", JSON.stringify(log, null, 2));
          break;

        case "show":
          const { commit } = await inquirer.prompt([
            {
              type: "input",
              name: "commit",
              message: "Enter commit hash or reference (e.g., HEAD, main):",
            },
          ]);
          const commitDetails = await client.showCommit(commit);
          console.log(\`\\nCommit Details:\`, JSON.stringify(commitDetails, null, 2));
          break;

        case "diff":
          const { from, to, file } = await inquirer.prompt([
            {
              type: "input",
              name: "from",
              message: "From commit/branch (optional):",
            },
            {
              type: "input",
              name: "to",
              message: "To commit/branch (optional):",
            },
            {
              type: "input",
              name: "file",
              message: "Specific file to diff (optional):",
            },
          ]);
          const diff = await client.getDiff(
            from || undefined,
            to || undefined,
            file || undefined
          );
          console.log("\\nDiff:", JSON.stringify(diff, null, 2));
          break;

        case "branches":
          const { includeRemote } = await inquirer.prompt([
            {
              type: "confirm",
              name: "includeRemote",
              message: "Include remote branches?",
              default: false,
            },
          ]);
          const branches = await client.getBranches(includeRemote);
          console.log("\\nBranches:", JSON.stringify(branches, null, 2));
          break;

        case "read_file":
          const { filePath, fileCommit } = await inquirer.prompt([
            {
              type: "input",
              name: "filePath",
              message: "Enter file path:",
            },
            {
              type: "input",
              name: "fileCommit",
              message: "Commit hash (optional, defaults to HEAD):",
            },
          ]);
          const fileContent = await client.readFile(filePath, fileCommit || undefined);
          console.log(\`\\nFile Content:\`, JSON.stringify(fileContent, null, 2));
          break;

        case "list_files":
          const { dirPath } = await inquirer.prompt([
            {
              type: "input",
              name: "dirPath",
              message: "Directory path (optional, defaults to root):",
              default: ".",
            },
          ]);
          const files = await client.listFiles(dirPath);
          console.log("\\nFiles:", JSON.stringify(files, null, 2));
          break;

        case "list_resources":
          const resources = await client.listResources();
          console.log("\\nResources:", JSON.stringify(resources, null, 2));
          break;
      }

      console.log("\\n" + "=".repeat(50) + "\\n");
    } catch (error) {
      console.error("Error:", error);
    }
  }
}

async function main() {
  const program = new Command();

  program
    .name("${projectName}")
    .description("MCP client for Git repository operations")
    .version("1.0.0");

  program
    .command("connect")
    .description("Connect to MCP server and start interactive session")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new GitMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        await startInteractiveSession(client);
        await client.disconnect();
      } catch (error) {
        console.error("Failed to connect to MCP server:", error);
        process.exit(1);
      }
    });

  program
    .command("status")
    .description("Show git status")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new GitMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const status = await client.getGitStatus();
        console.log(JSON.stringify(status, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("log")
    .description("Show git log")
    .option("-n, --count <count>", "Number of commits", "10")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (options) => {
      const client = new GitMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const log = await client.getGitLog(parseInt(options.count));
        console.log(JSON.stringify(log, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("show")
    .description("Show commit details")
    .argument("<commit>", "Commit hash or reference")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (commit, options) => {
      const client = new GitMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const details = await client.showCommit(commit);
        console.log(JSON.stringify(details, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  program
    .command("read")
    .description("Read a file from the repository")
    .argument("<path>", "File path")
    .option("-c, --commit <commit>", "Commit hash")
    .option("-s, --server <command>", "Server command to run", "node")
    .option("-a, --args <args...>", "Server arguments", [])
    .action(async (path, options) => {
      const client = new GitMCPClient();
      
      try {
        await client.connect(options.server, options.args);
        const content = await client.readFile(path, options.commit);
        console.log(JSON.stringify(content, null, 2));
        await client.disconnect();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  await program.parseAsync();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP client for Git repository operations"}

## Features

- Connect to MCP Git servers
- Interactive command-line interface
- View git status, log, and commit details
- Show diffs between commits or branches
- Read files from any commit
- List repository files and directories
- Browse git history and branches

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Usage

### Interactive Mode

Connect to an MCP Git server and start an interactive session:

\`\`\`bash
npm start connect --server node --args path/to/server/dist/index.js
\`\`\`

The interactive mode provides options to:
- Show git status and log
- View commit details and diffs
- List branches (local and remote)
- Read files from any commit
- Browse repository structure

### Command Line Mode

Execute single commands:

\`\`\`bash
# Show git status
npm start status --server node --args path/to/server/dist/index.js

# Show git log (last 5 commits)
npm start log --count 5 --server node --args path/to/server/dist/index.js

# Show commit details
npm start show HEAD --server node --args path/to/server/dist/index.js

# Read a file from a specific commit
npm start read README.md --commit abc123 --server node --args path/to/server/dist/index.js
\`\`\`

### Programmatic Usage

\`\`\`typescript
import { GitMCPClient } from './src/index.js';

const client = new GitMCPClient();
await client.connect('node', ['path/to/server/dist/index.js']);

// Get git status
const status = await client.getGitStatus();
console.log('Status:', status);

// Get commit history
const log = await client.getGitLog(10);
console.log('Recent commits:', log);

// Show commit details
const commit = await client.showCommit('HEAD');
console.log('Latest commit:', commit);

// Read file from specific commit
const content = await client.readFile('README.md', 'abc123');
console.log('File content:', content);

// Get diff between commits
const diff = await client.getDiff('HEAD~1', 'HEAD');
console.log('Changes:', diff);

await client.disconnect();
\`\`\`

## Configuration

The client connects to MCP Git servers via stdio transport. Ensure your MCP server is configured with the correct repository path.

## Features

- **Read-only operations**: Safe browsing of Git repositories
- **Commit history**: View detailed commit information and diffs
- **File access**: Read files from any commit in the repository
- **Branch management**: List and explore different branches
- **Interactive exploration**: Guided interface for repository browsing

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Source maps enabled for better debugging
- Interactive prompts for better user experience

## Development

\`\`\`bash
# Development mode
npm run dev

# Build
npm run build
\`\`\`
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "README.md", content: readme },
  ];
};

const generateMultiServerClient = (projectName: string, description?: string, serverEndpoints?: string[]): ClientProjectFile[] => {
  const packageJson = {
    name: projectName,
    version: "1.0.0",
    description: description || "MCP client for multiple server connections",
    type: "module",
    main: "dist/index.js",
    scripts: {
      build: "tsc",
      start: "node --enable-source-maps dist/index.js",
      dev: "tsx src/index.ts"
    },
    dependencies: {
      "@modelcontextprotocol/sdk": "^1.0.0",
      "commander": "^11.0.0",
      "inquirer": "^9.0.0"
    },
    devDependencies: {
      "@types/node": "^20.0.0",
      "@types/inquirer": "^9.0.0",
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

  const configExample = {
    servers: serverEndpoints?.map((endpoint, index) => ({
      name: `server${index + 1}`,
      command: "node",
      args: [endpoint],
      description: `MCP Server ${index + 1}`
    })) || [
      {
        name: "filesystem",
        command: "node",
        args: ["path/to/filesystem-server/dist/index.js"],
        description: "File System MCP Server"
      },
      {
        name: "database",
        command: "node", 
        args: ["path/to/database-server/dist/index.js"],
        description: "Database MCP Server"
      }
    ]
  };

  const indexTs = `import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { Command } from "commander";
import inquirer from "inquirer";
import { spawn } from "child_process";
import fs from "fs/promises";
import { pathToFileURL } from "url";

interface ServerConfig {
  name: string;
  command: string;
  args: string[];
  description?: string;
}

interface Config {
  servers: ServerConfig[];
}

class MultiServerMCPClient {
  private clients: Map<string, Client> = new Map();
  private transports: Map<string, StdioClientTransport> = new Map();
  private config: Config;

  constructor(config: Config) {
    this.config = config;
  }

  async connectToServer(serverName: string) {
    const serverConfig = this.config.servers.find(s => s.name === serverName);
    if (!serverConfig) {
      throw new Error(\`Server '\${serverName}' not found in configuration\`);
    }

    const client = new Client(
      {
        name: "${projectName}",
        version: "1.0.0",
      },
      {
        capabilities: {},
      }
    );

    const serverProcess = spawn(serverConfig.command, serverConfig.args, {
      stdio: ["pipe", "pipe", "inherit"],
    });

    const transport = new StdioClientTransport({
      readable: serverProcess.stdout!,
      writable: serverProcess.stdin!,
    });

    await client.connect(transport);
    
    this.clients.set(serverName, client);
    this.transports.set(serverName, transport);
    
    console.log(\`Connected to server: \${serverName}\`);
  }

  async connectToAllServers() {
    for (const server of this.config.servers) {
      try {
        await this.connectToServer(server.name);
      } catch (error) {
        console.error(\`Failed to connect to \${server.name}:\`, error);
      }
    }
  }

  getConnectedServers(): string[] {
    return Array.from(this.clients.keys());
  }

  async listResources(serverName: string) {
    const client = this.clients.get(serverName);
    if (!client) {
      throw new Error(\`Not connected to server: \${serverName}\`);
    }

    try {
      const response = await client.request(
        { method: "resources/list" },
        {}
      );
      return response.resources;
    } catch (error) {
      console.error(\`Error listing resources from \${serverName}:\`, error);
      throw error;
    }
  }

  async readResource(serverName: string, uri: string) {
    const client = this.clients.get(serverName);
    if (!client) {
      throw new Error(\`Not connected to server: \${serverName}\`);
    }

    try {
      const response = await client.request(
        { method: "resources/read" },
        { uri }
      );
      return response.contents;
    } catch (error) {
      console.error(\`Error reading resource from \${serverName}:\`, error);
      throw error;
    }
  }

  async listTools(serverName: string) {
    const client = this.clients.get(serverName);
    if (!client) {
      throw new Error(\`Not connected to server: \${serverName}\`);
    }

    try {
      const response = await client.request(
        { method: "tools/list" },
        {}
      );
      return response.tools;
    } catch (error) {
      console.error(\`Error listing tools from \${serverName}:\`, error);
      throw error;
    }
  }

  async callTool(serverName: string, name: string, arguments_: any = {}) {
    const client = this.clients.get(serverName);
    if (!client) {
      throw new Error(\`Not connected to server: \${serverName}\`);
    }

    try {
      const response = await client.request(
        { method: "tools/call" },
        { name, arguments: arguments_ }
      );
      return response.content;
    } catch (error) {
      console.error(\`Error calling tool \${name} on \${serverName}:\`, error);
      throw error;
    }
  }

  async getAllResources() {
    const allResources: { [serverName: string]: any[] } = {};
    
    for (const serverName of this.getConnectedServers()) {
      try {
        allResources[serverName] = await this.listResources(serverName);
      } catch (error) {
        console.error(\`Failed to get resources from \${serverName}:\`, error);
        allResources[serverName] = [];
      }
    }
    
    return allResources;
  }

  async getAllTools() {
    const allTools: { [serverName: string]: any[] } = {};
    
    for (const serverName of this.getConnectedServers()) {
      try {
        allTools[serverName] = await this.listTools(serverName);
      } catch (error) {
        console.error(\`Failed to get tools from \${serverName}:\`, error);
        allTools[serverName] = [];
      }
    }
    
    return allTools;
  }

  async disconnectFromServer(serverName: string) {
    const transport = this.transports.get(serverName);
    if (transport) {
      await transport.close();
      this.transports.delete(serverName);
    }
    this.clients.delete(serverName);
  }

  async disconnectAll() {
    for (const serverName of this.getConnectedServers()) {
      await this.disconnectFromServer(serverName);
    }
  }
}

async function loadConfig(configPath: string): Promise<Config> {
  try {
    const configContent = await fs.readFile(configPath, "utf-8");
    return JSON.parse(configContent);
  } catch (error) {
    console.error("Failed to load config file:", error);
    throw error;
  }
}

async function startInteractiveSession(client: MultiServerMCPClient) {
  console.log("\\nMulti-Server MCP Client - Interactive Mode");
  console.log("Manage multiple MCP server connections\\n");

  while (true) {
    try {
      const connectedServers = client.getConnectedServers();
      
      const { action } = await inquirer.prompt([
        {
          type: "list",
          name: "action",
          message: "What would you like to do?",
          choices: [
            { name: "List all resources (all servers)", value: "all_resources" },
            { name: "List all tools (all servers)", value: "all_tools" },
            { name: "Work with specific server", value: "specific_server" },
            { name: "Show connected servers", value: "show_servers" },
            { name: "Connect to additional server", value: "connect_server" },
            { name: "Disconnect from server", value: "disconnect_server" },
            { name: "Exit", value: "quit" },
          ],
        },
      ]);

      if (action === "quit") {
        break;
      }

      switch (action) {
        case "all_resources":
          const allResources = await client.getAllResources();
          console.log("\\nAll Resources:", JSON.stringify(allResources, null, 2));
          break;

        case "all_tools":
          const allTools = await client.getAllTools();
          console.log("\\nAll Tools:", JSON.stringify(allTools, null, 2));
          break;

        case "specific_server":
          if (connectedServers.length === 0) {
            console.log("No servers connected.");
            break;
          }

          const { serverName } = await inquirer.prompt([
            {
              type: "list",
              name: "serverName",
              message: "Select server:",
              choices: connectedServers,
            },
          ]);

          const { serverAction } = await inquirer.prompt([
            {
              type: "list",
              name: "serverAction",
              message: \`What to do with \${serverName}?\`,
              choices: [
                { name: "List resources", value: "resources" },
                { name: "List tools", value: "tools" },
                { name: "Call tool", value: "call_tool" },
                { name: "Read resource", value: "read_resource" },
              ],
            },
          ]);

          switch (serverAction) {
            case "resources":
              const resources = await client.listResources(serverName);
              console.log(\`\\nResources from \${serverName}:\`, JSON.stringify(resources, null, 2));
              break;

            case "tools":
              const tools = await client.listTools(serverName);
              console.log(\`\\nTools from \${serverName}:\`, JSON.stringify(tools, null, 2));
              break;

            case "call_tool":
              const { toolName, toolArgs } = await inquirer.prompt([
                {
                  type: "input",
                  name: "toolName",
                  message: "Tool name:",
                },
                {
                  type: "input",
                  name: "toolArgs",
                  message: "Tool arguments (JSON format, optional):",
                },
              ]);

              let args = {};
              if (toolArgs.trim()) {
                try {
                  args = JSON.parse(toolArgs);
                } catch (e) {
                  console.log("Invalid JSON for arguments, using empty object");
                }
              }

              const result = await client.callTool(serverName, toolName, args);
              console.log(\`\\nTool result from \${serverName}:\`, JSON.stringify(result, null, 2));
              break;

            case "read_resource":
              const { resourceUri } = await inquirer.prompt([
                {
                  type: "input",
                  name: "resourceUri",
                  message: "Resource URI:",
                },
              ]);

              const content = await client.readResource(serverName, resourceUri);
              console.log(\`\\nResource content from \${serverName}:\`, JSON.stringify(content, null, 2));
              break;
          }
          break;

        case "show_servers":
          console.log("\\nConnected servers:", connectedServers);
          break;

        case "connect_server":
          const { newServerName } = await inquirer.prompt([
            {
              type: "input",
              name: "newServerName",
              message: "Server name (must be in config):",
            },
          ]);

          try {
            await client.connectToServer(newServerName);
          } catch (error) {
            console.error("Failed to connect:", error);
          }
          break;

        case "disconnect_server":
          if (connectedServers.length === 0) {
            console.log("No servers connected.");
            break;
          }

          const { disconnectServerName } = await inquirer.prompt([
            {
              type: "list",
              name: "disconnectServerName",
              message: "Select server to disconnect:",
              choices: connectedServers,
            },
          ]);

          await client.disconnectFromServer(disconnectServerName);
          console.log(\`Disconnected from \${disconnectServerName}\`);
          break;
      }

      console.log("\\n" + "=".repeat(50) + "\\n");
    } catch (error) {
      console.error("Error:", error);
    }
  }
}

async function main() {
  const program = new Command();

  program
    .name("${projectName}")
    .description("MCP client for multiple server connections")
    .version("1.0.0");

  program
    .command("connect")
    .description("Connect to MCP servers and start interactive session")
    .option("-c, --config <path>", "Config file path", "config.json")
    .action(async (options) => {
      try {
        const config = await loadConfig(options.config);
        const client = new MultiServerMCPClient(config);
        
        console.log("Connecting to all configured servers...");
        await client.connectToAllServers();
        
        const connectedServers = client.getConnectedServers();
        console.log(\`Connected to \${connectedServers.length} servers: \${connectedServers.join(", ")}\`);
        
        await startInteractiveSession(client);
        await client.disconnectAll();
      } catch (error) {
        console.error("Failed to start multi-server client:", error);
        process.exit(1);
      }
    });

  program
    .command("list-all")
    .description("List resources and tools from all servers")
    .option("-c, --config <path>", "Config file path", "config.json")
    .action(async (options) => {
      try {
        const config = await loadConfig(options.config);
        const client = new MultiServerMCPClient(config);
        
        await client.connectToAllServers();
        
        const allResources = await client.getAllResources();
        const allTools = await client.getAllTools();
        
        console.log("All Resources:", JSON.stringify(allResources, null, 2));
        console.log("\\nAll Tools:", JSON.stringify(allTools, null, 2));
        
        await client.disconnectAll();
      } catch (error) {
        console.error("Error:", error);
        process.exit(1);
      }
    });

  await program.parseAsync();
}

const isEntry = import.meta.url === pathToFileURL(process.argv[1]).href;
if (isEntry) {
  main().catch(console.error);
}
`;

  const readme = `# ${projectName}

${description || "MCP client for multiple server connections"}

## Features

- Connect to multiple MCP servers simultaneously
- Interactive command-line interface for server management
- Aggregate resources and tools from all connected servers
- Individual server interaction and control
- Configuration-based server management
- Programmatic API for multi-server operations

## Installation

\`\`\`bash
npm install
npm run build
\`\`\`

## Configuration

Create a \`config.json\` file to define your MCP servers:

\`\`\`json
${JSON.stringify(configExample, null, 2)}
\`\`\`

## Usage

### Interactive Mode

Connect to all configured servers and start an interactive session:

\`\`\`bash
npm start connect --config config.json
\`\`\`

The interactive mode provides options to:
- View resources and tools from all servers
- Work with individual servers
- Connect/disconnect servers dynamically
- Call tools and read resources from specific servers

### Command Line Mode

List all resources and tools from all servers:

\`\`\`bash
npm start list-all --config config.json
\`\`\`

### Programmatic Usage

\`\`\`typescript
import { MultiServerMCPClient } from './src/index.js';

const config = {
  servers: [
    {
      name: "filesystem",
      command: "node",
      args: ["path/to/filesystem-server/dist/index.js"],
      description: "File System Server"
    },
    {
      name: "database", 
      command: "node",
      args: ["path/to/database-server/dist/index.js"],
      description: "Database Server"
    }
  ]
};

const client = new MultiServerMCPClient(config);

// Connect to all servers
await client.connectToAllServers();

// Get resources from all servers
const allResources = await client.getAllResources();
console.log('All resources:', allResources);

// Work with specific server
const files = await client.listResources('filesystem');
const tables = await client.listResources('database');

// Call tools on specific servers
const fileContent = await client.callTool('filesystem', 'read_file', { path: 'README.md' });
const queryResult = await client.callTool('database', 'query_database', { query: 'SELECT * FROM users LIMIT 5' });

await client.disconnectAll();
\`\`\`

## Configuration Format

The configuration file should contain a \`servers\` array with the following properties for each server:

- \`name\`: Unique identifier for the server
- \`command\`: Command to start the server (e.g., "node", "python")
- \`args\`: Array of arguments to pass to the command
- \`description\`: Optional description of the server

## Features

- **Multi-server management**: Connect to and manage multiple MCP servers
- **Aggregated views**: See all resources and tools across servers
- **Individual control**: Work with specific servers independently
- **Dynamic connections**: Connect and disconnect servers at runtime
- **Configuration-driven**: Easy setup through JSON configuration
- **Interactive exploration**: Guided interface for multi-server operations

## Technical Notes

- Uses ESM modules for compatibility with the MCP SDK
- Source maps enabled for better debugging
- Interactive prompts for better user experience

## Development

\`\`\`bash
# Development mode
npm run dev

# Build
npm run build
\`\`\`
`;

  return [
    { path: "package.json", content: JSON.stringify(packageJson, null, 2) },
    { path: "tsconfig.json", content: JSON.stringify(tsConfig, null, 2) },
    { path: "src/index.ts", content: indexTs },
    { path: "config.json", content: JSON.stringify(configExample, null, 2) },
    { path: "README.md", content: readme },
  ];
};

// Generates complete MCP client boilerplate code based on user requirements.
export const generateClient = api<GenerateClientRequest, GenerateClientResponse>(
  { expose: true, method: "POST", path: "/generate-client" },
  async (req) => {
    let files: ClientProjectFile[] = [];
    let instructions = "";

    switch (req.clientType) {
      case "filesystem":
        files = generateFileSystemClient(req.projectName, req.description);
        instructions = `Your file system MCP client has been generated with production-ready fixes! This client provides a command-line interface for interacting with MCP file system servers.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Start your MCP file system server
5. Connect using: \`npm start connect --server node --args path/to/server/dist/index.js\`

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Source maps enabled for better debugging
- Cross-platform compatibility
- Features: Interactive mode, command-line operations, and programmatic API for file operations`;
        break;

      case "database":
        files = generateDatabaseClient(req.projectName, req.description);
        instructions = `Your database MCP client has been generated with production-ready fixes! This client provides an interactive interface for querying databases through MCP servers.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Start your MCP database server with proper DATABASE_URL
5. Connect using: \`npm start connect --server node --args path/to/server/dist/index.js\`

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Source maps enabled for better debugging
- Interactive prompts for better user experience
- Features: Interactive query interface, table exploration, and guided database operations`;
        break;

      case "api":
        files = generateApiClient(req.projectName, req.description);
        instructions = `Your API integration MCP client has been generated with production-ready fixes! This client provides tools for making HTTP requests through MCP API servers.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Start your MCP API server with proper API_BASE_URL and API_KEY
5. Connect using: \`npm start connect --server node --args path/to/server/dist/index.js\`

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Source maps enabled for better debugging
- Interactive prompts for better user experience
- Features: Support for GET, POST, PUT, DELETE requests with JSON formatting`;
        break;

      case "git":
        files = generateGitClient(req.projectName, req.description);
        instructions = `Your Git repository MCP client has been generated with production-ready fixes! This client provides tools for exploring Git repositories through MCP servers.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Start your MCP Git server with proper REPO_PATH
5. Connect using: \`npm start connect --server node --args path/to/server/dist/index.js\`

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Source maps enabled for better debugging
- Interactive prompts for better user experience
- Features: Git history exploration, file reading from commits, and repository browsing`;
        break;

      case "multi-server":
        files = generateMultiServerClient(req.projectName, req.description, req.serverEndpoints);
        instructions = `Your multi-server MCP client has been generated with production-ready fixes! This client can connect to and manage multiple MCP servers simultaneously.

**Next steps:**
1. Extract the files to a new directory
2. Run \`npm install\` to install dependencies
3. Run \`npm run build\` to compile TypeScript
4. Edit config.json to configure your MCP servers
5. Start your MCP servers
6. Connect using: \`npm start connect --config config.json\`

**Production improvements:**
- ESM module support for MCP SDK compatibility
- Source maps enabled for better debugging
- Interactive prompts for better user experience
- Features: Multi-server management, aggregated resource views, and dynamic server connections`;
        break;

      case "custom":
        // Generate a basic template for custom clients
        files = generateFileSystemClient(req.projectName, req.description);
        instructions = `A production-ready MCP client template has been generated based on the file system client with all the latest fixes.

**Customization needed:**
1. Modify the client methods in src/index.ts according to your server's tools and resources
2. Add any additional dependencies to package.json
3. Implement custom interaction logic for your specific use case

**Requirements:** ${req.customRequirements || "No specific requirements provided"}

**Production improvements included:**
- ESM module support for MCP SDK compatibility
- Source maps enabled for better debugging
- Cross-platform compatibility

Follow the MCP SDK documentation to implement your custom client functionality.`;
        break;

      default:
        throw new Error(`Unsupported client type: ${req.clientType}`);
    }

    return {
      files,
      instructions
    };
  }
);
