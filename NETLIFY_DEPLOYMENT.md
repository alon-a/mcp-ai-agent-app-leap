# Netlify Deployment Guide

This guide walks you through deploying the MCP AI Agent App to Netlify with proper environment variable configuration.

## Quick Start

1. **Fork/Clone this repository** to your GitHub account
2. **Connect to Netlify**:
   - Go to [Netlify Dashboard](https://app.netlify.com/)
   - Click "New site from Git"
   - Select your repository

3. **Configure Build Settings**:
   - Build command: `cd frontend && npm install && npm run build`
   - Publish directory: `frontend/dist`
   - Base directory: (leave empty)

4. **Set Environment Variables**:
   - Go to Site settings → Environment variables
   - Add: `OPENAI_API_KEY` = `your-openai-api-key-here`
   - (Optional) Add: `PYTHON_API_URL` and `PYTHON_API_KEY`

5. **Deploy**: Click "Deploy site"

## Detailed Setup

### 1. Environment Variables

The application requires these environment variables:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `OPENAI_API_KEY` | ✅ Yes | OpenAI API key for AI features | `sk-...` |
| `PYTHON_API_URL` | ❌ Optional | Python service URL | `https://api.example.com` |
| `PYTHON_API_KEY` | ❌ Optional | Python service API key | `your-key` |

### 2. Getting Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-`)
5. Add it to Netlify environment variables

### 3. Build Configuration

The project includes a `netlify.toml` file with optimized settings:

- **Build command**: Installs dependencies and builds the frontend
- **Publish directory**: Points to the built frontend assets
- **Redirects**: Handles SPA routing
- **Headers**: Includes security headers and CSP
- **Caching**: Optimizes static asset caching

### 4. Backend Integration

This frontend connects to an Encore backend. You have two options:

#### Option A: Deploy Backend to Encore Cloud
1. Follow the Encore deployment instructions in `DEVELOPMENT.md`
2. Update the frontend API calls to use your Encore backend URL
3. Configure CORS on your backend to allow your Netlify domain

#### Option B: Use Netlify Functions (Advanced)
1. Convert backend endpoints to Netlify Functions
2. Move environment variables to Netlify Functions
3. Update frontend to call Netlify Functions instead

### 5. Custom Domain (Optional)

1. Go to Site settings → Domain management
2. Click "Add custom domain"
3. Follow DNS configuration instructions
4. Enable HTTPS (automatic with Netlify)

### 6. Continuous Deployment

Once connected to GitHub:
- **Automatic deploys**: Push to main branch triggers deployment
- **Deploy previews**: Pull requests get preview URLs
- **Branch deploys**: Other branches can be configured for staging

### 7. Monitoring and Debugging

#### Build Logs
- Check the "Deploys" tab for build logs
- Look for npm install or build errors
- Verify environment variables are set

#### Runtime Issues
- Use browser dev tools to check console errors
- Verify API calls are reaching the correct endpoints
- Check network tab for failed requests

#### Common Issues

| Issue | Solution |
|-------|----------|
| Build fails | Check Node.js version, dependencies |
| API calls fail | Verify backend URL, CORS settings |
| Environment variables not working | Check they're set in Site settings |
| 404 on refresh | Ensure SPA redirects are configured |

### 8. Performance Optimization

The `netlify.toml` includes:
- **Asset caching**: 1-year cache for static assets
- **Compression**: Automatic gzip/brotli compression
- **CDN**: Global edge network delivery
- **Security headers**: XSS protection, CSP, etc.

### 9. Security Best Practices

- ✅ Environment variables are encrypted at rest
- ✅ API keys are not exposed in client code
- ✅ Security headers prevent common attacks
- ✅ HTTPS is enforced automatically
- ✅ CSP restricts resource loading

### 10. Cost Considerations

Netlify Free Tier includes:
- 100GB bandwidth/month
- 300 build minutes/month
- 1 concurrent build
- Custom domains with SSL

For production apps, consider Netlify Pro for:
- More bandwidth and build minutes
- Deploy previews
- Advanced security features
- Priority support

## Troubleshooting

### Build Errors

```bash
# If you see Node.js version errors
# Update netlify.toml to specify Node version:
[build.environment]
  NODE_VERSION = "18"
```

### Environment Variable Issues

```bash
# Test environment variables are set:
# Add this to your build command temporarily:
echo "OPENAI_API_KEY is set: $OPENAI_API_KEY"
```

### API Connection Issues

1. Check browser network tab for failed requests
2. Verify backend CORS configuration
3. Ensure API endpoints are accessible from Netlify's servers
4. Check for mixed content issues (HTTP vs HTTPS)

## Support

- [Netlify Documentation](https://docs.netlify.com/)
- [Netlify Community](https://community.netlify.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Project Issues](https://github.com/your-repo/issues)

---

**Need help?** Open an issue in the repository or check the troubleshooting section above.