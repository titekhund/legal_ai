# Docker Setup Guide

This guide provides detailed instructions for running the Legal AI application using Docker.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)
- [Production Deployment](#production-deployment)

## Prerequisites

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **System Requirements**:
  - 4GB RAM minimum (8GB recommended)
  - 10GB free disk space

Verify your installation:
```bash
docker --version
docker-compose --version
```

## Quick Start

1. **Clone and navigate to the project**
```bash
git clone <repository-url>
cd legal_ai
```

2. **Create environment file**
```bash
cat > .env << EOF
# Required: API Keys
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional: Override defaults
API_ENV=development
LOG_LEVEL=INFO
NODE_ENV=production
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=бРТРУРбРоРУЭ ЩЭУФебШб AI РбШбвФЬвШ
EOF
```

3. **Start all services**
```bash
docker-compose up --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

## Architecture

The Docker setup consists of four main services:

### 1. Backend (FastAPI)
- **Image**: Python 3.11-slim
- **Port**: 8000
- **Dependencies**: PostgreSQL, Redis
- **Health Check**: HTTP check on `/health` endpoint every 30s
- **Volumes**:
  - `./backend/app` ’ `/app/app` (hot reload)
  - `./backend/data` ’ `/app/data` (tax code data)

### 2. Frontend (Next.js)
- **Image**: Node 20-alpine
- **Port**: 3000
- **Dependencies**: Backend
- **Build**: Multi-stage build for optimized image size
- **Output**: Standalone server for production

### 3. PostgreSQL
- **Image**: postgres:15-alpine
- **Port**: 5432
- **Database**: `legal_ai`
- **Credentials**: postgres/postgres (development only)
- **Volumes**: `postgres_data` (persistent storage)
- **Health Check**: pg_isready every 10s

### 4. Redis
- **Image**: redis:7-alpine
- **Port**: 6379
- **Purpose**: Caching and rate limiting
- **Volumes**: `redis_data` (persistent storage)
- **Persistence**: AOF (Append-Only File) enabled

## Configuration

### Environment Variables

Create a `.env` file in the root directory with the following variables:

#### Required Variables
```bash
# LLM API Keys
GEMINI_API_KEY=<your-gemini-api-key>
ANTHROPIC_API_KEY=<your-anthropic-api-key>
```

#### Optional Variables
```bash
# Backend Configuration
API_ENV=development              # development, staging, production
LOG_LEVEL=INFO                   # DEBUG, INFO, WARNING, ERROR
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/legal_ai
REDIS_URL=redis://redis:6379

# Frontend Configuration
NODE_ENV=production
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=бРТРУРбРоРУЭ ЩЭУФебШб AI РбШбвФЬвШ

# CORS (comma-separated origins)
CORS_ORIGINS=http://localhost:3000,http://frontend:3000
```

### Port Mapping

Default ports can be changed in `docker-compose.yml`:

```yaml
services:
  backend:
    ports:
      - "8000:8000"  # Change left side: "8001:8000"

  frontend:
    ports:
      - "3000:3000"  # Change left side: "3001:3000"
```

## Development Workflow

### Starting Services

```bash
# Start all services
docker-compose up

# Start in detached mode (background)
docker-compose up -d

# Start specific services
docker-compose up backend postgres redis

# Rebuild and start (after code changes)
docker-compose up --build
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Executing Commands

```bash
# Backend: Run database migrations
docker-compose exec backend alembic upgrade head

# Backend: Access Python shell
docker-compose exec backend python

# Backend: Run tests
docker-compose exec backend pytest

# Frontend: Access Node shell
docker-compose exec frontend sh

# Frontend: Run linter
docker-compose exec frontend npm run lint

# PostgreSQL: Access database
docker-compose exec postgres psql -U postgres -d legal_ai

# Redis: Access CLI
docker-compose exec redis redis-cli
```

### Hot Reload / Live Development

Both backend and frontend support hot reload in development:

**Backend**: Changes to `./backend/app/**/*.py` automatically reload the server
**Frontend**: Run frontend in development mode separately for faster hot reload:

```bash
# Stop frontend container
docker-compose stop frontend

# Run frontend locally
cd frontend
npm install
npm run dev
```

### Stopping Services

```bash
# Stop containers (preserves data)
docker-compose stop

# Stop and remove containers (preserves data)
docker-compose down

# Stop and remove containers + volumes (deletes all data)
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

### Database Management

```bash
# Create database backup
docker-compose exec postgres pg_dump -U postgres legal_ai > backup.sql

# Restore database from backup
cat backup.sql | docker-compose exec -T postgres psql -U postgres legal_ai

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec postgres psql -U postgres -c "CREATE DATABASE legal_ai;"
```

## Troubleshooting

### Port Already in Use

If you get "port already in use" errors:

```bash
# Find process using port 8000
lsof -i :8000
# or on Windows
netstat -ano | findstr :8000

# Kill the process or change ports in docker-compose.yml
```

### Out of Memory

If containers crash due to memory issues:

```bash
# Check Docker memory limits
docker stats

# Increase Docker Desktop memory allocation:
# Docker Desktop ’ Settings ’ Resources ’ Memory ’ Increase to 8GB
```

### Backend Health Check Failing

```bash
# Check backend logs
docker-compose logs backend

# Verify environment variables
docker-compose exec backend env | grep API

# Test health endpoint manually
curl http://localhost:8000/health

# Restart backend
docker-compose restart backend
```

### Database Connection Issues

```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check PostgreSQL logs
docker-compose logs postgres

# Test connection manually
docker-compose exec postgres psql -U postgres -d legal_ai -c "SELECT 1;"

# Verify DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://postgres:postgres@postgres:5432/legal_ai
```

### Frontend Build Failures

```bash
# Clear Next.js cache
docker-compose exec frontend rm -rf .next

# Rebuild with no cache
docker-compose build --no-cache frontend

# Check Node version in Dockerfile (should be 20-alpine)
```

### Volume Permission Issues

On Linux, you may encounter permission issues:

```bash
# Option 1: Change ownership
sudo chown -R $USER:$USER ./backend ./frontend

# Option 2: Run with current user
docker-compose exec --user $(id -u):$(id -g) backend bash
```

### Clearing All Docker Data

  **WARNING: This will delete ALL Docker data, not just this project**

```bash
# Stop all containers
docker-compose down -v

# Remove all unused containers, networks, images
docker system prune -a --volumes

# Rebuild from scratch
docker-compose up --build
```

## Production Deployment

For production deployment, consider these changes:

### 1. Use Production Environment Variables

```bash
# .env.production
API_ENV=production
LOG_LEVEL=WARNING
NODE_ENV=production
DATABASE_URL=postgresql://prod_user:secure_password@prod_host:5432/legal_ai
REDIS_URL=redis://prod_host:6379
```

### 2. Use Secrets Management

Don't commit `.env` files. Use Docker secrets or cloud provider secrets:

```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    secrets:
      - anthropic_api_key

secrets:
  anthropic_api_key:
    external: true
```

### 3. Add Resource Limits

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 1G
```

### 4. Use External Database

Don't run PostgreSQL in Docker for production. Use managed services:
- AWS RDS
- Google Cloud SQL
- Azure Database for PostgreSQL
- Digital Ocean Managed Databases

### 5. Enable HTTPS

Use a reverse proxy (Nginx, Traefik) or cloud load balancer:

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
```

### 6. Set Up Monitoring

Add health checks and monitoring:

```yaml
services:
  backend:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### 7. Use Docker Compose Profiles

Separate development and production configs:

```bash
# docker-compose.override.yml for development
# docker-compose.prod.yml for production

# Run production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

## Additional Resources

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Next.js Docker Documentation](https://nextjs.org/docs/deployment#docker-image)
- [FastAPI Docker Documentation](https://fastapi.tiangolo.com/deployment/docker/)

## Support

For issues specific to Docker setup, check:
1. Docker logs: `docker-compose logs`
2. System resources: `docker stats`
3. Network connectivity: `docker network ls`
4. GitHub Issues: [Report an issue](https://github.com/your-org/legal_ai/issues)
