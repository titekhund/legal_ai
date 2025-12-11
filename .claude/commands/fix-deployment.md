---
description: Fetch latest Google Cloud deployment errors and automatically fix them
---

# Automated Deployment Error Fixer

I'm fetching the latest deployment errors from Google Cloud...

## Step 1: Fetching Cloud Build Logs

```bash
echo "=== Setting Project ==="
gcloud config set project tax-code-ai-backend 2>&1

echo ""
echo "=== CLOUD BUILD LOGS ==="
gcloud builds list --limit=5 --format="table(id,status,createTime,logUrl)" 2>&1 || echo "Failed to fetch build list"

# Get the latest build ID
LATEST_BUILD=$(gcloud builds list --limit=1 --format="value(id)" 2>&1)
echo ""
echo "Latest Build ID: $LATEST_BUILD"
echo ""

if [ ! -z "$LATEST_BUILD" ]; then
  echo "=== LATEST BUILD LOG ==="
  gcloud builds log $LATEST_BUILD 2>&1 | tail -100
fi
```

## Step 2: Fetching Cloud Run Deployment Status

```bash
echo ""
echo "=== CLOUD RUN SERVICE STATUS ==="
gcloud config set project tax-code-ai-backend 2>&1
gcloud run services describe legal-ai-backend --region=us-central1 --format="yaml(status)" 2>&1 || echo "Failed to fetch Cloud Run status"
```

## Step 3: Fetching Recent Cloud Run Logs

```bash
echo ""
echo "=== CLOUD RUN ERROR LOGS (Last 5 minutes) ==="
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=legal-ai-backend AND severity>=ERROR" --limit=50 --format="table(timestamp,severity,jsonPayload.message)" 2>&1 || echo "Failed to fetch logs"
```

## Task

Now analyze all the errors above and:
1. Identify the root cause of any deployment failures
2. Fix the issues in the codebase
3. Commit the changes with a descriptive message
4. Provide a summary of what was fixed

Focus on:
- Build errors (Docker, dependencies, etc.)
- Runtime errors (missing env vars, startup crashes)
- Configuration issues (Cloud Run settings, memory, timeout)
- Application errors (code bugs, import issues)

Start fixing now!
