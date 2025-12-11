---
description: Check Google Cloud deployment status and recent errors (view only)
---

# Deployment Status Check

Fetching current deployment status from Google Cloud...

## Cloud Build Status

```bash
echo "=== RECENT BUILDS ==="
gcloud builds list --limit=10 --format="table(id,status,createTime,duration)" 2>&1 || echo "Failed to fetch builds"
```

## Cloud Run Service Status

```bash
echo ""
echo "=== CLOUD RUN SERVICE INFO ==="
gcloud run services describe legal-ai-backend --region=us-central1 2>&1 || echo "Service not found"
```

## Recent Error Logs

```bash
echo ""
echo "=== RECENT ERROR LOGS ==="
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=legal-ai-backend AND severity>=WARNING" --limit=30 --format="table(timestamp,severity,textPayload)" 2>&1 || echo "Failed to fetch logs"
```

---

Based on the information above, provide a summary of:
1. Current deployment status (healthy/failing)
2. Recent build success rate
3. Any critical errors to address
4. Recommendations for next steps
