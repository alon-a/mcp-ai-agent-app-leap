# MCP Assistant

A comprehensive AI-powered assistant for building Model Context Protocol (MCP) servers and clients. This application provides an interactive chat interface, code generators, and expert guidance for MCP development.

⭐ If you find this project helpful or useful, please give it a star in the upper right hand corner! It helps others discover MCP-Assistant

## Features

### 🤖 AI Chat Assistant
- Expert AI assistant specialized in MCP development
- Interactive chat interface with example prompts
- Comprehensive knowledge of MCP concepts, best practices, and implementation patterns
- Real-time assistance for troubleshooting and optimization

### 🛠️ Code Generators
- **MCP Server Generator**: Create complete server projects with boilerplate code
- **MCP Client Generator**: Generate client applications with CLI and programmatic interfaces
- Support for multiple server/client types:
  - File System operations
  - Database integration (PostgreSQL)
  - REST API proxying
  - Git repository access
  - Multi-server clients
  - Custom implementations

### 📁 Project Management
- View and download generated files
- Copy individual files or entire projects
- Comprehensive setup instructions
- Ready-to-use TypeScript projects with proper configuration

## Architecture

### Backend (Encore.ts)
- **AI Service**: OpenAI-powered chat assistant with MCP expertise
- **Code Generation**: Server and client boilerplate generators
- **REST API**: Type-safe endpoints for all functionality

### Frontend (React + TypeScript)
- **Chat Interface**: Interactive conversation with the AI assistant
- **Code Generators**: Forms for creating servers and clients
- **File Viewer**: Browse and download generated project files
- **Responsive Design**: Works on desktop and mobile devices

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mcp-assistant
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   
   Create a `.env` file or set the OpenAI API key:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

5. **Access the application**
   
   Open your browser to the URL shown in the terminal (typically `http://localhost:3000`)

## Usage Guide

### Chat Assistant

1. **Start a conversation**: Click on the chat interface or use one of the example prompts
2. **Ask questions**: Get help with MCP concepts, implementation details, or troubleshooting
3. **Get code examples**: Request specific code snippets or explanations

Example questions:
- "How do I create an MCP server that reads files?"
- "What's the difference between resources and tools in MCP?"
- "Show me how to implement authentication in an MCP server"

### Generate MCP Servers

1. **Click "Generate Server"** in the chat interface
2. **Select server type**:
   - **File System**: Secure file operations within a directory
   - **Database**: PostgreSQL query interface with read-only safety
   - **API Integration**: Proxy for external REST APIs
   - **Git Repository**: Browse Git history and files
   - **Custom**: Basic template for custom functionality

3. **Fill in project details**:
   - Project name (required)
   - Description (optional)
   - Custom requirements (for custom servers)

4. **Generate and download**: Get a complete TypeScript project with:
   - Source code with MCP SDK integration
   - Package.json with dependencies
   - TypeScript configuration
   - Comprehensive README with setup instructions

### Generate MCP Clients

1. **Click "Generate Client"** in the chat interface
2. **Select client type**:
   - **File System Client**: Connect to file system servers
   - **Database Client**: Interactive database query interface
   - **API Client**: Make HTTP requests through MCP servers
   - **Git Client**: Browse repositories via MCP servers
   - **Multi-Server Client**: Connect to multiple servers simultaneously
   - **Custom Client**: Basic template for custom functionality

3. **Configure the client**:
   - Project name (required)
   - Description (optional)
   - Server endpoints (for multi-server clients)
   - Custom requirements (for custom clients)

4. **Generate and download**: Get a complete client project with:
   - Command-line interface
   - Interactive mode
   - Programmatic API
   - Configuration files
   - Setup documentation

## Generated Project Structure

### MCP Server Projects
```
my-mcp-server/
├── src/
│   └── index.ts          # Main server implementation
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── README.md            # Setup and usage instructions
```

### MCP Client Projects
```
my-mcp-client/
├── src/
│   └── index.ts          # Main client implementation
├── config.json          # Server configuration (multi-server)
├── package.json          # Dependencies and scripts
├── tsconfig.json         # TypeScript configuration
└── README.md            # Setup and usage instructions
```

## MCP Server Types

### File System Server
- **Purpose**: Secure file operations within a specified directory
- **Features**: Read, write, list files and directories
- **Security**: Path validation prevents directory traversal
- **Configuration**: Set `ALLOWED_PATH` environment variable

### Database Server
- **Purpose**: Safe PostgreSQL database querying
- **Features**: Execute SELECT queries, list tables, describe schemas
- **Security**: Read-only operations, no INSERT/UPDATE/DELETE
- **Configuration**: Set `DATABASE_URL` environment variable

### API Integration Server
- **Purpose**: Proxy requests to external REST APIs
- **Features**: GET, POST, PUT, DELETE requests with authentication
- **Security**: API key management, request/response filtering
- **Configuration**: Set `API_BASE_URL` and `API_KEY` environment variables

### Git Repository Server
- **Purpose**: Browse Git repositories and history
- **Features**: View commits, diffs, branches, read files from any commit
- **Security**: Read-only access, no write operations
- **Configuration**: Set `REPO_PATH` environment variable

## MCP Client Types

### File System Client
- **Purpose**: Interact with file system MCP servers
- **Features**: CLI commands, interactive mode, file operations
- **Usage**: Connect to file system servers for file management

### Database Client
- **Purpose**: Query databases through MCP servers
- **Features**: Interactive query interface, table exploration
- **Usage**: Execute SQL queries safely through MCP servers

### API Client
- **Purpose**: Make HTTP requests via MCP API servers
- **Features**: Support for all HTTP methods, JSON formatting
- **Usage**: Interact with external APIs through MCP proxy servers

### Git Client
- **Purpose**: Browse Git repositories via MCP servers
- **Features**: View history, read files, explore branches
- **Usage**: Git repository exploration without direct access

### Multi-Server Client
- **Purpose**: Connect to multiple MCP servers simultaneously
- **Features**: Aggregate resources, individual server control
- **Usage**: Manage multiple MCP servers from a single interface

## Development

### Project Structure
```
mcp-assistant/
├── backend/              # Encore.ts backend
│   └── ai/              # AI service
│       ├── encore.service.ts
│       ├── chat.ts      # Chat endpoint
│       ├── generate.ts  # Server generator
│       └── generate-client.ts # Client generator
├── frontend/            # React frontend
│   ├── components/      # UI components
│   ├── App.tsx         # Main app component
│   └── ...
├── package.json
└── README.md
```

### Backend Development
The backend uses Encore.ts for type-safe API development:

- **Services**: Each major feature is organized as a service
- **API Endpoints**: Type-safe endpoints with request/response schemas
- **Code Generation**: Template-based project generation
- **AI Integration**: OpenAI GPT-4 for expert assistance

### Frontend Development
The frontend uses React with TypeScript:

- **Components**: Modular, reusable UI components
- **State Management**: React hooks for local state
- **API Client**: Auto-generated client from backend types
- **UI Library**: shadcn/ui components with Tailwind CSS

### Adding New Server Types

1. **Update the backend generator** (`backend/ai/generate.ts`):
   ```typescript
   const generateNewServerType = (projectName: string, description?: string): ProjectFile[] => {
     // Implementation
   };
   ```

2. **Add the new type** to the `ServerType` union and switch statement

3. **Update the frontend form** (`frontend/components/GenerateServerForm.tsx`) with the new option

### Adding New Client Types

1. **Update the backend generator** (`backend/ai/generate-client.ts`):
   ```typescript
   const generateNewClientType = (projectName: string, description?: string): ProjectFile[] => {
     // Implementation
   };
   ```

2. **Add the new type** to the `ClientType` union and switch statement

3. **Update the frontend form** (`frontend/components/GenerateClientForm.tsx`) with the new option

## Configuration

### Environment Variables

#### Required
- `OPENAI_API_KEY`: Your OpenAI API key for the chat assistant

#### Optional
- `PORT`: Server port (default: 3000)
- `NODE_ENV`: Environment (development/production)

### Deployment

The application can be deployed using Encore.ts's built-in deployment system:

1. **Build the application**:
   ```bash
   npm run build
   ```

2. **Deploy with Encore**:
   ```bash
   encore deploy
   ```

## Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/new-feature`
3. **Make your changes** and add tests
4. **Commit your changes**: `git commit -m 'Add new feature'`
5. **Push to the branch**: `git push origin feature/new-feature`
6. **Submit a pull request**

### Development Guidelines

- **Code Style**: Use TypeScript with strict mode
- **Components**: Keep components small and focused
- **Testing**: Add tests for new functionality
- **Documentation**: Update README and code comments

## Troubleshooting

### Common Issues

#### "OpenAI API key not found"
- Ensure `OPENAI_API_KEY` environment variable is set
- Check that the API key is valid and has sufficient credits

#### "Failed to generate files"
- Check network connectivity
- Verify the OpenAI API is accessible
- Try refreshing the page and generating again

#### "Server won't start"
- Ensure all dependencies are installed: `npm install`
- Check that the port is not already in use
- Verify Node.js version is 18 or higher

### Getting Help

1. **Check the documentation**: Review this README and the MCP official docs
2. **Use the chat assistant**: Ask questions directly in the application
3. **Check the console**: Look for error messages in the browser console
4. **File an issue**: Create a GitHub issue with details about the problem

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Acknowledgments

- **Anthropic**: For creating the Model Context Protocol
- **MCP Community**: For examples and best practices
- **Encore.ts**: For the excellent backend framework
- **OpenAI**: For providing the AI capabilities

## Related Resources

- [MCP Official Documentation](https://docs.anthropic.com/en/docs/mcp)
- [MCP TypeScript SDK](https://github.com/modelcontextprotocol/typescript-sdk)
- [MCP Example Servers](https://github.com/modelcontextprotocol/servers)
- [Encore.ts Documentation](https://encore.dev/docs)
- [Claude Desktop Integration](https://docs.anthropic.com/en/docs/mcp/quickstart)
