# Contributing to MCP Assistant

Thank you for your interest in contributing to MCP Assistant! This document provides guidelines and information for contributors.

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Git
- OpenAI API key for testing

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/mcp-assistant.git
   cd mcp-assistant
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   ```

4. **Start the development server**
   ```bash
   npm run dev
   ```

## Project Structure

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

## Development Guidelines

### Code Style

- Use TypeScript with strict mode enabled
- Follow the existing code formatting and naming conventions
- Use 2 spaces for indentation
- Add JSDoc comments for public APIs
- Keep components small and focused

### Backend Development (Encore.ts)

- Each major feature should be organized as a service
- Use type-safe API endpoints with proper request/response schemas
- Follow Encore.ts best practices for service organization
- Add comprehensive error handling

### Frontend Development (React)

- Use functional components with hooks
- Keep components modular and reusable
- Use shadcn/ui components when possible
- Implement proper error boundaries
- Follow accessibility best practices

### Testing

- Write tests for new functionality
- Ensure all tests pass before submitting PRs
- Test both frontend and backend components
- Include integration tests for critical paths

## Contribution Process

### 1. Fork and Branch

1. Fork the repository on GitHub
2. Create a feature branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   ```

### 2. Make Changes

- Make your changes following the development guidelines
- Write or update tests as needed
- Update documentation if necessary
- Ensure your code follows the project's style guidelines

### 3. Test Your Changes

```bash
# Run the development server
npm run dev

# Build the project
npm run build

# Run tests (when available)
npm test
```

### 4. Commit Your Changes

Use clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add new MCP server type for Redis integration"
```

Follow conventional commit format:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding tests
- `chore:` for maintenance tasks

### 5. Submit a Pull Request

1. Push your branch to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

2. Create a pull request on GitHub
3. Provide a clear description of your changes
4. Link any related issues
5. Wait for review and address feedback

## Types of Contributions

### Bug Reports

When reporting bugs, please include:
- Clear description of the issue
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Node.js version, etc.)
- Screenshots or error logs if applicable

### Feature Requests

For new features, please:
- Describe the use case and problem it solves
- Provide examples of how it would be used
- Consider backward compatibility
- Discuss implementation approach if you have ideas

### Code Contributions

We welcome contributions for:
- New MCP server types
- New MCP client types
- UI/UX improvements
- Performance optimizations
- Bug fixes
- Documentation improvements
- Test coverage improvements

### Documentation

Help improve our documentation by:
- Fixing typos or unclear explanations
- Adding examples and use cases
- Improving setup instructions
- Creating tutorials or guides

## Code Review Process

All contributions go through code review:

1. **Automated checks**: PRs must pass all automated checks
2. **Peer review**: At least one maintainer will review your code
3. **Testing**: Changes should be tested thoroughly
4. **Documentation**: Updates to docs should accompany code changes

### Review Criteria

- Code quality and maintainability
- Adherence to project conventions
- Test coverage for new features
- Performance impact
- Security considerations
- Backward compatibility

## Getting Help

If you need help or have questions:

- **GitHub Issues**: For bug reports and feature requests
- **GitHub Discussions**: For general questions and community discussion
- **Documentation**: Check the README and inline code comments

## Recognition

Contributors will be recognized in:
- GitHub contributors list
- Release notes for significant contributions
- Special mentions for outstanding contributions

## License

By contributing to MCP Assistant, you agree that your contributions will be licensed under the same license as the project (MIT License).

## Code of Conduct

Please be respectful and professional in all interactions. We're committed to providing a welcoming and inclusive environment for all contributors.

### Our Standards

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

Thank you for contributing to MCP Assistant! 🚀
