# Security Policy

## Supported Versions

We actively support the following versions with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |

## Reporting a Vulnerability

We take security vulnerabilities seriously. If you discover a security vulnerability, please follow these steps:

### 1. Do Not Create a Public Issue

Please do not create a public GitHub issue for security vulnerabilities. This could put users at risk.

### 2. Report Privately

Send an email to: **security@mcp-assistant.dev** (or create a private security advisory on GitHub)

Include the following information:
- Description of the vulnerability
- Steps to reproduce the issue
- Potential impact
- Any suggested fixes (if you have them)

### 3. Response Timeline

- **Initial Response**: Within 48 hours
- **Status Update**: Within 7 days
- **Fix Timeline**: Varies based on severity, typically within 30 days

## Security Measures

### Code Generation Security

Our generated MCP servers include multiple security layers:

#### File System Servers
- **Path Traversal Protection**: Prevents access outside allowed directories
- **Symlink Safety**: Uses canonical path resolution
- **File Size Limits**: Configurable limits prevent resource exhaustion
- **Input Validation**: All file paths are validated

#### Database Servers
- **SQL Injection Prevention**: Parameterized queries only
- **Schema Allowlisting**: Access restricted to allowed schemas
- **Read-Only Operations**: No dangerous SQL operations allowed
- **Connection Limits**: Proper connection pooling and timeouts

#### API Servers
- **SSRF Protection**: Host allowlisting and IP validation
- **Request Size Limits**: Prevents large request attacks
- **Header Sanitization**: Only safe headers allowed
- **Timeout Protection**: Prevents hanging requests

#### Git Servers
- **Read-Only Access**: No write operations allowed
- **Repository Boundaries**: Access limited to specified repository
- **Input Validation**: All Git commands are validated

### Application Security

#### Backend (Encore.ts)
- **Type Safety**: Full TypeScript type checking
- **Input Validation**: All API inputs are validated
- **Error Handling**: Secure error messages (no sensitive data leakage)
- **Rate Limiting**: Built-in protection against abuse

#### Frontend (React)
- **XSS Prevention**: Proper input sanitization
- **CSRF Protection**: Secure API communication
- **Content Security Policy**: Implemented where applicable
- **Secure Dependencies**: Regular dependency updates

### Infrastructure Security

#### Environment Variables
- **Secret Management**: Secure handling of API keys
- **No Hardcoded Secrets**: All sensitive data via environment variables
- **Production Separation**: Different keys for different environments

#### Deployment
- **HTTPS Only**: All production deployments use HTTPS
- **Secure Headers**: Security headers implemented
- **Container Security**: Minimal Docker images with non-root users

## Security Best Practices for Users

### API Key Management
- **Rotate Keys Regularly**: Change OpenAI API keys periodically
- **Limit Permissions**: Use API keys with minimal required permissions
- **Monitor Usage**: Track API usage for unusual patterns

### Generated Code Security
- **Review Generated Code**: Always review generated code before deployment
- **Environment Isolation**: Use separate environments for testing
- **Access Controls**: Implement proper access controls in production

### Deployment Security
- **Secure Configuration**: Use secure configuration in production
- **Regular Updates**: Keep dependencies and runtime updated
- **Monitoring**: Implement security monitoring and logging

## Known Security Considerations

### OpenAI API Integration
- **API Key Exposure**: Ensure API keys are not logged or exposed
- **Rate Limiting**: OpenAI API has rate limits that should be respected
- **Data Privacy**: Be aware of data sent to OpenAI's API

### Generated MCP Servers
- **Configuration Required**: Generated servers require proper configuration
- **Environment Specific**: Security settings may need environment-specific tuning
- **Regular Updates**: Keep generated code updated with latest security fixes

## Security Updates

We will:
- **Notify Users**: Security updates will be clearly marked in release notes
- **Provide Patches**: Critical security issues will receive immediate patches
- **Update Documentation**: Security documentation will be kept current

## Responsible Disclosure

We appreciate security researchers who:
- **Report Privately**: Use private channels for vulnerability reports
- **Allow Fix Time**: Give us reasonable time to fix issues before disclosure
- **Provide Details**: Include sufficient detail to reproduce and fix issues

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Node.js Security Best Practices](https://nodejs.org/en/docs/guides/security/)
- [TypeScript Security Guidelines](https://www.typescriptlang.org/docs/)
- [Encore.ts Security Documentation](https://encore.dev/docs/develop/security)

## Contact

For security-related questions or concerns:
- **Email**: security@mcp-assistant.dev
- **GitHub**: Create a private security advisory

Thank you for helping keep MCP Assistant secure! 🔒
