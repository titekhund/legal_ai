# Deployment Guide

This guide covers deploying the Legal AI application to production environments.

## Table of Contents
- [Frontend Deployment (Vercel)](#frontend-deployment-vercel)
- [Backend Deployment (Railway)](#backend-deployment-railway)
- [Environment Variables](#environment-variables)
- [DNS Configuration](#dns-configuration)
- [Post-Deployment Checklist](#post-deployment-checklist)

---

## Frontend Deployment (Vercel)

The frontend Next.js application is configured for deployment on Vercel.

### Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI** (optional): `npm install -g vercel`
3. **GitHub Repository**: Connected to Vercel

### Automatic Deployment via GitHub Actions

The repository includes a GitHub Actions workflow that automatically deploys to Vercel on every push to `main` or pull request.

#### Required GitHub Secrets

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

| Secret Name | Description | How to Get |
|-------------|-------------|------------|
| `VERCEL_TOKEN` | Vercel API token | [Account Settings > Tokens](https://vercel.com/account/tokens) |
| `VERCEL_ORG_ID` | Your Vercel organization ID | Run `vercel project ls` or check project settings |
| `VERCEL_PROJECT_ID` | Your Vercel project ID | Run `vercel project ls` or check project settings |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API URL | Your backend deployment URL (e.g., Railway) |
| `NEXT_PUBLIC_APP_NAME` | Application name (optional) | Default: "საგადასახადო კოდექსის AI ასისტენტი" |

#### Getting Vercel IDs

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Link your project (from frontend directory)
cd frontend
vercel link

# Get project details
vercel project ls

# The .vercel/project.json file will contain your IDs
cat .vercel/project.json
```

### Manual Deployment via Vercel CLI

```bash
# From the frontend directory
cd frontend

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

### Vercel Environment Variables

Configure these in your Vercel project settings (`Settings > Environment Variables`):

#### Production Environment

| Variable Name | Value | Required |
|---------------|-------|----------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://your-backend.railway.app` | Yes |
| `NEXT_PUBLIC_APP_NAME` | `საგადასახადო კოდექსის AI ასისტენტი` | No |
| `NODE_ENV` | `production` | Auto-set |

#### Preview/Development Environments

Same as production, but you can use different backend URLs for testing:
- Preview: `https://your-backend-staging.railway.app`
- Development: `http://localhost:8000`

### Vercel Configuration

The deployment is configured via `frontend/vercel.json`:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs",
  "regions": ["fra1"],
  "env": {
    "NEXT_PUBLIC_API_BASE_URL": "@api_base_url",
    "NEXT_PUBLIC_APP_NAME": "@app_name"
  }
}
```

**Regions:**
- `fra1`: Frankfurt, Germany (closest to Georgia for optimal latency)
- Alternative: `arn1` (Stockholm, Sweden)

### Custom Domain

1. Go to your Vercel project settings
2. Navigate to `Domains`
3. Add your custom domain (e.g., `legal-ai.ge`)
4. Configure DNS records as instructed by Vercel:
   - Type: `A` or `CNAME`
   - Name: `@` or `www`
   - Value: Provided by Vercel

---

## Backend Deployment (Railway)

(To be completed in Task D.2)

Backend deployment to Railway will be documented separately.

---

## Environment Variables

### Frontend Variables (Next.js)

All frontend environment variables must be prefixed with `NEXT_PUBLIC_` to be accessible in the browser.

#### Required

- **`NEXT_PUBLIC_API_BASE_URL`**: Full URL to the backend API
  - Production example: `https://legal-ai-backend.railway.app`
  - Development: `http://localhost:8000`
  - Used for all API requests from the frontend

#### Optional

- **`NEXT_PUBLIC_APP_NAME`**: Application name displayed in the UI
  - Default: `საგადასახადო კოდექსის AI ასისტენტი`
  - Georgian: Legal AI Tax Code Assistant

### Backend Variables (FastAPI)

(To be completed in Task D.2)

---

## DNS Configuration

### Option 1: Vercel DNS (Recommended)

If using a custom domain with Vercel:

1. **Transfer nameservers to Vercel:**
   - Go to Vercel project > Domains
   - Click "Use Vercel Nameservers"
   - Update your domain registrar with Vercel's nameservers

2. **Vercel handles all DNS records automatically**

### Option 2: External DNS Provider

If keeping your DNS provider:

1. **A Record** (for apex domain):
   ```
   Type: A
   Name: @
   Value: 76.76.21.21 (Vercel IP)
   ```

2. **CNAME Record** (for www subdomain):
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

3. **API Subdomain** (if using):
   ```
   Type: CNAME
   Name: api
   Value: your-backend.railway.app
   ```

---

## Post-Deployment Checklist

### Frontend

- [ ] Verify deployment succeeded in Vercel dashboard
- [ ] Check deployment preview/production URL loads correctly
- [ ] Verify all environment variables are set correctly
- [ ] Test API connectivity to backend
- [ ] Verify all pages load without errors:
  - [ ] Home page (`/`)
  - [ ] Chat page (`/chat`)
  - [ ] Disputes page (`/disputes`)
  - [ ] Documents page (`/documents`)
- [ ] Check browser console for errors
- [ ] Test document generation end-to-end
- [ ] Verify custom domain (if configured)
- [ ] Test SSL certificate (should be automatic via Vercel)

### Backend

- [ ] (To be completed in Task D.2)

### Monitoring

- [ ] Set up Vercel Analytics (optional)
- [ ] Configure error tracking (Sentry, etc.) - optional
- [ ] Monitor API response times
- [ ] Set up uptime monitoring (UptimeRobot, etc.) - optional

---

## Troubleshooting

### Common Issues

#### 1. Build Fails on Vercel

**Symptom:** Build fails with module not found errors

**Solution:**
```bash
# Ensure all dependencies are in package.json
cd frontend
npm install
git add package.json package-lock.json
git commit -m "fix: update dependencies"
git push
```

#### 2. API Requests Fail (404/CORS errors)

**Symptom:** Frontend can't reach backend

**Solutions:**
- Verify `NEXT_PUBLIC_API_BASE_URL` is set correctly in Vercel
- Check backend is deployed and running
- Verify CORS is configured in backend to allow frontend domain
- Check browser console for specific error messages

#### 3. Environment Variables Not Working

**Symptom:** Variables are `undefined` in application

**Solutions:**
- Ensure variables are prefixed with `NEXT_PUBLIC_`
- Redeploy after adding environment variables
- Check Vercel deployment logs for variable values
- Clear browser cache and hard reload

#### 4. Slow Page Loads

**Solutions:**
- Enable Vercel Analytics to identify bottlenecks
- Check Vercel region matches your target audience
- Verify API response times
- Consider implementing caching strategies

---

## Rollback Procedure

### Vercel Rollback

1. Go to Vercel project > Deployments
2. Find the previous working deployment
3. Click the three dots menu
4. Select "Promote to Production"

### Git Rollback

```bash
# Find the last working commit
git log --oneline

# Create a revert commit
git revert <commit-hash>
git push origin main

# Or force rollback (use with caution)
git reset --hard <commit-hash>
git push --force origin main
```

---

## Security Considerations

### Vercel Security Features

- **Automatic HTTPS**: All deployments have SSL certificates
- **DDoS Protection**: Built-in DDoS mitigation
- **Security Headers**: Configured in `next.config.js`
- **Environment Isolation**: Preview deployments use separate environments

### Best Practices

1. **Never commit secrets** to the repository
2. **Use environment variables** for all configuration
3. **Enable Vercel's security features**:
   - Password protection for preview deployments (optional)
   - Trusted domains list
4. **Regular dependency updates**: `npm audit` and update regularly
5. **Monitor deployment logs** for suspicious activity

---

## Support & Resources

### Vercel Documentation
- [Vercel Docs](https://vercel.com/docs)
- [Next.js Deployment](https://nextjs.org/docs/deployment)
- [Environment Variables](https://vercel.com/docs/concepts/projects/environment-variables)

### Project-Specific
- [README.md](../README.md) - Project overview
- [API Contract](./api_contract.md) - API documentation
- [Architecture](./architecture.md) - System architecture

### Getting Help
- GitHub Issues: Report deployment issues
- Vercel Support: For Vercel-specific problems
- Next.js Discord: Community support
