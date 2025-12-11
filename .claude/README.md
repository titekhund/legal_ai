# Claude Code Custom Commands

This directory contains custom slash commands for automating common tasks.

## Available Commands

### `/fix-deployment`
Automatically fetches the latest Google Cloud deployment errors and fixes them.

**What it does:**
- Fetches latest Cloud Build logs
- Checks Cloud Run service status
- Retrieves error logs from the last 5 minutes
- Analyzes all errors
- Fixes issues in the codebase
- Commits changes

**Usage:**
```bash
/fix-deployment
```

**Use when:**
- Deployment failed and you want automatic fixes
- Build errors need to be resolved
- Cloud Run service is unhealthy

---

### `/deployment-status`
Checks deployment status and shows recent errors (read-only).

**What it does:**
- Shows recent build history
- Displays Cloud Run service status
- Lists recent error/warning logs
- Provides status summary and recommendations

**Usage:**
```bash
/deployment-status
```

**Use when:**
- You want to check current deployment health
- Need to review errors before fixing
- Want to see build history

---

## Prerequisites

These commands require:
1. `gcloud` CLI installed and authenticated
2. Project ID configured: `gcloud config set project YOUR_PROJECT_ID`
3. Proper IAM permissions for:
   - Cloud Build (read logs)
   - Cloud Run (read/describe services)
   - Cloud Logging (read logs)

## Setup

If you haven't configured gcloud yet:

```bash
# Install gcloud CLI
# https://cloud.google.com/sdk/docs/install

# Login
gcloud auth login

# Set your project
export GCP_PROJECT_ID="your-project-id"
gcloud config set project $GCP_PROJECT_ID
```

## Examples

### Quick fix workflow
```bash
# Check what's wrong
/deployment-status

# Fix it automatically
/fix-deployment
```

### Manual workflow
```bash
# Review errors first
/deployment-status

# Make manual fixes...
# Then deploy
cd backend
./deploy-gcp.sh
```

## Customization

You can edit the commands in `.claude/commands/*.md` to:
- Change the region (currently `us-central1`)
- Modify the service name (currently `legal-ai-backend`)
- Adjust log limits and filters
- Add additional checks or fix patterns
