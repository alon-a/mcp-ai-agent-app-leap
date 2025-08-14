# Deployment Guide

This guide covers how to deploy MCP Assistant to various platforms.

## Prerequisites

- Node.js 18+ and npm
- OpenAI API key
- Git repository set up

## Environment Variables

Set the following environment variables for production:

```bash
# Required
OPENAI_API_KEY=your-openai-api-key

# Optional
NODE_ENV=production
PORT=3000
```

## Deployment Options

### 1. Encore.ts Cloud (Recommended)

The easiest way to deploy is using Encore.ts's built-in deployment system:

```bash
# Install Encore CLI if not already installed
npm install -g @encore/cli

# Login to Encore
encore auth login

# Deploy to staging
encore deploy

# Deploy to production
encore deploy --env=prod
```

#### Setting Secrets in Encore Cloud

```bash
# Set OpenAI API key
encore secret set --env=prod OpenAIKey your-openai-api-key
```

### 2. Docker Deployment

Build and run with Docker:

```bash
# Build the Docker image
docker build -t mcp-assistant .

# Run the container
docker run -p 3000:3000 -e OPENAI_API_KEY=your-key mcp-assistant
```

#### Docker Compose

```yaml
version: '3.8'
services:
  mcp-assistant:
    build: .
    ports:
      - "3000:3000"
    environment:
      - OPENAI_API_KEY=your-openai-api-key
      - NODE_ENV=production
    restart: unless-stopped
```

### 3. Traditional VPS/Server

Deploy to any VPS or server:

```bash
# Clone the repository
git clone https://github.com/your-username/mcp-assistant.git
cd mcp-assistant

# Install dependencies
npm install

# Build the application
npm run build

# Set environment variables
export OPENAI_API_KEY=your-openai-api-key
export NODE_ENV=production

# Start the application
npm start
```

#### Using PM2 for Process Management

```bash
# Install PM2 globally
npm install -g pm2

# Start the application with PM2
pm2 start npm --name "mcp-assistant" -- start

# Save PM2 configuration
pm2 save

# Set up PM2 to start on boot
pm2 startup
```

### 4. Vercel Deployment

Deploy the frontend to Vercel:

```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
vercel

# Set environment variables in Vercel dashboard
# OPENAI_API_KEY=your-openai-api-key
```

### 5. Railway Deployment

Deploy to Railway:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Deploy
railway up

# Set environment variables
railway variables set OPENAI_API_KEY=your-openai-api-key
```

## Production Considerations

### Security

1. **Environment Variables**: Never commit API keys to version control
2. **HTTPS**: Always use HTTPS in production
3. **Rate Limiting**: Consider implementing rate limiting for API endpoints
4. **CORS**: Configure CORS appropriately for your domain

### Performance

1. **Caching**: Implement caching for frequently requested data
2. **CDN**: Use a CDN for static assets
3. **Monitoring**: Set up monitoring and logging
4. **Health Checks**: Implement health check endpoints

### Monitoring

Set up monitoring for:
- Application uptime
- API response times
- Error rates
- OpenAI API usage and costs

### Backup and Recovery

1. **Database Backups**: If using a database, set up regular backups
2. **Code Backups**: Ensure code is backed up in version control
3. **Configuration Backups**: Document and backup configuration

## Scaling

### Horizontal Scaling

For high traffic, consider:
- Load balancing across multiple instances
- Database clustering
- Caching layers (Redis)
- CDN for static content

### Vertical Scaling

For moderate traffic increases:
- Increase server resources (CPU, RAM)
- Optimize database queries
- Implement efficient caching

## Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Check API key validity
   - Verify API quota and billing
   - Monitor rate limits

2. **Build Failures**
   - Ensure Node.js version compatibility
   - Check for missing dependencies
   - Verify TypeScript compilation

3. **Runtime Errors**
   - Check environment variables
   - Review application logs
   - Verify network connectivity

### Debugging

Enable debug logging:

```bash
export DEBUG=*
npm start
```

Check application logs:

```bash
# PM2 logs
pm2 logs mcp-assistant

# Docker logs
docker logs container-name

# System logs
journalctl -u mcp-assistant
```

## Maintenance

### Updates

1. **Dependencies**: Regularly update dependencies
2. **Security Patches**: Apply security updates promptly
3. **Encore.ts Updates**: Keep Encore.ts framework updated
4. **OpenAI SDK**: Update OpenAI SDK for new features

### Monitoring

Set up alerts for:
- High error rates
- Slow response times
- API quota exhaustion
- Server resource usage

## Support

For deployment issues:
- Check the GitHub issues
- Review Encore.ts documentation
- Contact support if needed

Remember to test your deployment thoroughly before going live!
