# Legal AI - Tax Code Assistant

<!-- TODO: Expand README with comprehensive documentation -->

## Overview
AI-powered legal assistant for tax code research, dispute resolution, and document generation.

## Features
- **Tax Code Search**: Semantic search over Internal Revenue Code and related regulations
- **Dispute Resolution Support**: Analysis of historical tax disputes and outcomes
- **Document Generation**: Templates for legal documents and filings
- **RAG Pipeline**: Advanced retrieval-augmented generation for accurate, cited responses
- **Citation Extraction**: Automatic extraction and validation of legal citations

## Project Structure
```
legal_ai/
├── frontend/          # Next.js frontend application
├── backend/           # FastAPI backend service
├── data/             # Tax code, disputes, and templates
├── scripts/          # Data ingestion scripts
├── docs/             # Documentation
├── infra/            # Docker and infrastructure config
└── .github/          # CI/CD workflows
```

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

#### Using Docker (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd legal_ai
```

2. **Create environment file**
```bash
# Create .env file in the root directory
cat > .env << EOF
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Environment
API_ENV=development
LOG_LEVEL=INFO
NODE_ENV=production

# URLs
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=საგადასახადო კოდექსის AI ასისტენტი

# Database (default values for development)
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/legal_ai
REDIS_URL=redis://redis:6379
EOF

# Edit .env with your actual API keys
nano .env  # or use your preferred editor
```

3. **Start all services with Docker Compose**
```bash
# Build and start all services (backend, frontend, postgres, redis)
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

4. **Access the application**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- PostgreSQL: localhost:5432
- Redis: localhost:6379

5. **View logs**
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

6. **Stop services**
```bash
# Stop containers
docker-compose down

# Stop and remove volumes (WARNING: deletes database data)
docker-compose down -v
```

## Documentation
- [Architecture](docs/architecture.md)
- [API Contract](docs/api_contract.md)
- [Data Architecture](docs/data_architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Golden Tests](docs/golden_tests.yaml)

## Development

### Backend Development (Local)

For local development without Docker:

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env  # Edit with your API keys

# Run development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with specific log level
uvicorn app.main:app --reload --log-level debug
```

**Backend Environment Variables:**
```bash
GEMINI_API_KEY=your_gemini_api_key
ANTHROPIC_API_KEY=your_anthropic_api_key
API_ENV=development
LOG_LEVEL=INFO
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/legal_ai
REDIS_URL=redis://localhost:6379
```

### Frontend Development (Local)

For local development without Docker:

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Create .env.local file
cat > .env.local << EOF
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_APP_NAME=საგადასახადო კოდექსის AI ასისტენტი
EOF

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

**Access the applications:**
- Frontend: http://localhost:3000
- Backend: http://localhost:8000
- API Docs: http://localhost:8000/docs

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Data Ingestion
```bash
# TODO: Add data ingestion instructions
# Ingest tax code documents
python scripts/ingest_tax_code.py --source data/tax_code/

# Ingest dispute documents
python scripts/ingest_disputes.py --source data/disputes/

# Ingest templates
python scripts/ingest_templates.py --source data/templates/
```

## Technology Stack

### Frontend
- Next.js 14
- React 18
- TypeScript
- Tailwind CSS

### Backend
- FastAPI
- Python 3.11
- LangChain
- Anthropic Claude API

### Data & Storage
- PostgreSQL (relational data)
- Pinecone/Weaviate (vector database)
- Redis (caching)

## Contributing
<!-- TODO: Add contribution guidelines -->

## License
<!-- TODO: Add license information -->

## Support
<!-- TODO: Add support information -->
