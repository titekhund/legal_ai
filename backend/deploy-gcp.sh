#!/bin/bash

# Google Cloud Run Deployment Script for Legal AI Backend

set -e

echo "🚀 Deploying Legal AI Backend to Google Cloud Run..."

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"tax-code-ai-backend"}
REGION="us-central1"
SERVICE_NAME="legal-ai-backend"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ Error: gcloud CLI is not installed"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Step 1: Set the project
echo "📋 Setting GCP project to: ${PROJECT_ID}"
gcloud config set project ${PROJECT_ID}

# Step 2: Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com

# Step 3: Build the Docker image
echo "🐳 Building Docker image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Step 4: Deploy to Cloud Run
echo "☁️  Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME} \
    --platform managed \
    --region ${REGION} \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --max-instances 10 \
    --set-env-vars "ENVIRONMENT=production"

# Step 5: Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo ""
echo "✅ Deployment complete!"
echo "🌐 Your backend is live at: ${SERVICE_URL}"
echo ""
echo "Next steps:"
echo "1. Set environment variables in Cloud Run console:"
echo "   - GEMINI_API_KEY"
echo "   - CORS_ORIGINS"
echo "   - CLAUDE_API_KEY (optional)"
echo ""
echo "2. Update your frontend NEXT_PUBLIC_API_BASE_URL to: ${SERVICE_URL}"
