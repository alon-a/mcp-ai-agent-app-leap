# Getting Started

This project consists of an Encore application. Follow the steps below to get the app running locally.

## Prerequisites

If this is your first time using Encore, you need to install the CLI that runs the local development environment. Use the appropriate command for your system:

- **macOS:** `brew install encoredev/tap/encore`
- **Linux:** `curl -L https://encore.dev/install.sh | bash`
- **Windows:** `iwr https://encore.dev/install.ps1 | iex`

You also need to have bun installed for package management. If you don't have bun installed, you can install it by running:

```bash
npm install -g bun
```

## Environment Setup

Before running the application, you need to set up your environment variables:

1. **OpenAI API Key**: The application requires an OpenAI API key for AI-powered features. Set the environment variable:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```
   
   You can get an API key from [OpenAI's platform](https://platform.openai.com/api-keys).

2. **Python API Configuration** (Optional): If you're using the Python bridge service, you can configure:
   ```bash
   export PYTHON_API_URL="http://localhost:8000"  # Default if not set
   export PYTHON_API_KEY="your-python-api-key"    # Optional
   ```

### Setting Environment Variables

**On macOS/Linux:**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
export PYTHON_API_URL="http://localhost:8000"
export PYTHON_API_KEY="your-python-api-key"
```

**On Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=your-openai-api-key-here
set PYTHON_API_URL=http://localhost:8000
set PYTHON_API_KEY=your-python-api-key
```

**On Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="your-openai-api-key-here"
$env:PYTHON_API_URL="http://localhost:8000"
$env:PYTHON_API_KEY="your-python-api-key"
```

**Using a .env file** (recommended for development):
Copy the example environment file and customize it:
```bash
cp .env.example .env
```

Then edit the `.env` file with your actual values:
```env
OPENAI_API_KEY=your-openai-api-key-here
PYTHON_API_URL=http://localhost:8000
PYTHON_API_KEY=your-python-api-key
```

## Running the Application

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Make sure your environment variables are set (see Environment Setup above)

3. Start the Encore development server:
   ```bash
   encore run
   ```

The backend will be available at the URL shown in your terminal (typically `http://localhost:4000`).



### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install the dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npx vite dev
   ```

The frontend will be available at `http://localhost:5173` (or the next available port).


### Generate Frontend Client
To generate the frontend client, run the following command in the `backend` directory:

```bash
encore gen client --target leap
```

## Deployment

### Netlify Deployment

The application can be easily deployed to Netlify with proper environment variable configuration.

> 📖 **Detailed Guide**: See [NETLIFY_DEPLOYMENT.md](NETLIFY_DEPLOYMENT.md) for a comprehensive step-by-step guide.

#### Method 1: Netlify Dashboard (Recommended)

1. **Connect Your Repository**:
   - Go to [Netlify Dashboard](https://app.netlify.com/)
   - Click "New site from Git"
   - Connect your GitHub/GitLab/Bitbucket repository

2. **Configure Build Settings**:
   - **Build command**: `npm run build` (or your specific build command)
   - **Publish directory**: `dist` (or your build output directory)
   - **Base directory**: Leave empty or specify if needed

3. **Set Environment Variables**:
   - Go to Site settings → Environment variables
   - Add the following variables:
     ```
     OPENAI_API_KEY = your-openai-api-key-here
     PYTHON_API_URL = https://your-python-api-url.com
     PYTHON_API_KEY = your-python-api-key-here
     ```

4. **Deploy**:
   - Click "Deploy site"
   - Netlify will automatically build and deploy your application

#### Method 2: Netlify CLI

1. **Install Netlify CLI**:
   ```bash
   npm install -g netlify-cli
   ```

2. **Login to Netlify**:
   ```bash
   netlify login
   ```

3. **Initialize your site**:
   ```bash
   netlify init
   ```

4. **Set environment variables**:
   ```bash
   netlify env:set OPENAI_API_KEY "your-openai-api-key-here"
   netlify env:set PYTHON_API_URL "https://your-python-api-url.com"
   netlify env:set PYTHON_API_KEY "your-python-api-key-here"
   ```

5. **Deploy**:
   ```bash
   netlify deploy --prod
   ```

#### Method 3: netlify.toml Configuration

Create a `netlify.toml` file in your project root:

```toml
[build]
  command = "npm run build"
  publish = "dist"

[build.environment]
  NODE_VERSION = "18"

# Redirect all requests to index.html for SPA routing
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200

# Security headers
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
    Referrer-Policy = "strict-origin-when-cross-origin"
```

Then set environment variables through the Netlify dashboard as described in Method 1.

#### Environment Variables Security

- **Never commit API keys**: Environment variables are securely stored by Netlify
- **Use different keys for different environments**: Consider separate keys for staging/production
- **Rotate keys regularly**: Update your API keys periodically for security

#### Troubleshooting Netlify Deployment

1. **Build fails**: Check the build logs in Netlify dashboard
2. **Environment variables not working**: Ensure they're set in Site settings → Environment variables
3. **API calls failing**: Verify your API endpoints are accessible from Netlify's servers
4. **CORS issues**: Configure your backend to allow requests from your Netlify domain

### Self-hosting
See the [self-hosting instructions](https://encore.dev/docs/self-host/docker-build) for how to use encore build docker to create a Docker image and
configure it.

### Encore Cloud Platform

#### Step 1: Login to your Encore Cloud Account

Before deploying, ensure you have authenticated the Encore CLI with your Encore account (same as your Leap account)

```bash
encore auth login
```

#### Step 2: Set Up Git Remote

Add Encore's git remote to enable direct deployment:

```bash
git remote add encore encore://mcp-ai-agent-app-gbni
```

#### Step 3: Deploy Your Application

Deploy by pushing your code:

```bash
git add -A .
git commit -m "Deploy to Encore Cloud"
git push encore
```

Monitor your deployment progress in the [Encore Cloud dashboard](https://app.encore.dev/mcp-ai-agent-app-gbni/deploys).

## GitHub Integration (Recommended for Production)

For production applications, we recommend integrating with GitHub instead of using Encore's managed git:

### Connecting Your GitHub Account

1. Open your app in the **Encore Cloud dashboard**
2. Navigate to Encore Cloud [GitHub Integration settings](https://app.encore.cloud/mcp-ai-agent-app-gbni/settings/integrations/github)
3. Click **Connect Account to GitHub**
4. Grant access to your repository

Once connected, pushing to your GitHub repository will automatically trigger deployments. Encore Cloud Pro users also get Preview Environments for each pull request.

### Deploy via GitHub

After connecting GitHub, deploy by pushing to your repository:

```bash
git add -A .
git commit -m "Deploy via GitHub"
git push origin main
```

## Additional Resources

- [Encore Documentation](https://encore.dev/docs)
- [Deployment Guide](https://encore.dev/docs/platform/deploy/deploying)
- [GitHub Integration](https://encore.dev/docs/platform/integrations/github)
- [Encore Cloud Dashboard](https://app.encore.dev)



