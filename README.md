# Legal AI - Georgian Tax Code Assistant

## Overview
AI-powered legal assistant for Georgian tax code research, dispute resolution, and document generation. Built with Gemini AI and modern web technologies.

## Features

### Tax Code Consultation (Phase 1-2)
- **NotebookLM-Style Reasoning**: Query Georgian Tax Code with conversational AI
- **Automatic Citation Extraction**: Identifies and references specific tax code articles
- **Contextual Understanding**: Maintains conversation history for follow-up questions
- **Confidence Scoring**: Provides reliability indicators based on citation count
- **Georgian Language Support**: Native Georgian language interface and responses

### Dispute Resolution (Phase 2)
- **RAG-Based Analysis**: Retrieval-augmented generation over historical dispute cases
- **Similar Case Discovery**: Find precedents using semantic search
- **Legal Ground Identification**: Extract legal basis from submitted disputes
- **Recommendation Engine**: AI-generated recommendations based on case analysis
- **Multi-Document Support**: Upload PDFs and JSON dispute documents

### Document Generation (Phase 3)
- **YAML Template System**: 6 Georgian legal document templates
  - Non-Disclosure Agreements (NDA)
  - Employment Contracts
  - Board Resolutions
  - Service Agreements
  - Loan Agreements
  - Shareholder Agreements
- **Dynamic Forms**: Auto-generated forms based on template variables
- **Multi-Format Export**: Download as Markdown, DOCX, or PDF
- **Legal References**: Automatic inclusion of relevant tax code articles
- **Document Preview**: Live markdown rendering with syntax highlighting
- **TTL-Based Storage**: Temporary document storage with 1-hour expiration

### Performance Optimizations
- **Template Caching**: LRU cache for frequently accessed templates (100 entry limit)
- **Citation Caching**: Cached regex extraction for tax article citations (256 entry limit)
- **Gemini File API Caching**: Automatic caching of uploaded tax code documents
- **Type-Based Lookups**: Cached document type filtering

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

#### Backend Unit Tests
```bash
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_document_service.py

# Run with verbose output
pytest -v
```

#### End-to-End Tests
```bash
# Start the backend server first
cd backend
uvicorn app.main:app --reload

# In another terminal, run E2E tests
python scripts/e2e_test.py
```

#### Golden Tests
The project includes comprehensive golden tests in `docs/golden_tests.yaml`:
- Tax query tests (10+ scenarios)
- Dispute analysis tests (8+ cases)
- Document generation tests (6 document types)

#### Frontend Tests
```bash
cd frontend
npm test

# Run with coverage
npm test -- --coverage
```

## Data Management

### Tax Code
The Georgian Tax Code PDF is automatically uploaded to Gemini File API on service initialization. The file is cached for efficient querying.

Place your tax code PDF at: `backend/data/tax_code/georgian_tax_code.pdf`

### Dispute Documents
Upload dispute documents via the Admin API:

```bash
# Upload PDF dispute case
curl -X POST "http://localhost:8000/api/v1/admin/disputes" \
  -H "X-Admin-Key: your-admin-key" \
  -F "file=@dispute_case.pdf" \
  -F "metadata={\"case_id\":\"2024-001\"}"

# Upload JSON dispute case
curl -X POST "http://localhost:8000/api/v1/admin/disputes" \
  -H "X-Admin-Key: your-admin-key" \
  -F "file=@dispute_case.json"
```

### Document Templates
Templates are stored as YAML files in `backend/data/templates/`. Each template includes:
- Document metadata (type, language, category)
- Template content with variable placeholders
- Variable definitions with types and validation
- Related tax code articles

Upload templates via Admin API:
```bash
curl -X POST "http://localhost:8000/api/v1/admin/templates" \
  -H "X-Admin-Key: your-admin-key" \
  -F "file=@my_template.yaml"
```

See existing templates in `backend/data/templates/` for examples.

## Technology Stack

### Frontend
- **Next.js 14**: React framework with App Router
- **React 18**: UI component library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS**: Utility-first CSS framework
- **react-markdown**: Markdown rendering for document preview
- **Radix UI**: Accessible component primitives

### Backend
- **FastAPI**: Modern Python web framework
- **Python 3.11**: Programming language
- **Gemini AI**: Google's multimodal AI for tax code reasoning
- **Anthropic Claude**: Advanced LLM for dispute analysis and document generation
- **python-docx**: DOCX document generation
- **PyYAML**: YAML template parsing
- **Pydantic**: Data validation and settings management

### AI & ML
- **Gemini File API**: Document upload and caching
- **RAG Pipeline**: Retrieval-augmented generation for disputes
- **Vector Embeddings**: Semantic search over dispute cases
- **LRU Caching**: Performance optimization for frequent queries

### Data & Storage
- **In-Memory Storage**: OrderedDict with TTL for generated documents
- **File System**: YAML templates and uploaded documents
- **Gemini File Cache**: Automatic caching of tax code PDF

## API Endpoints

### Tax Code Endpoints
- `POST /api/v1/tax/advice` - Get tax advice with citations
- `GET /api/v1/tax/articles` - Search tax code articles
- `GET /api/v1/tax/status` - Get tax service status

### Dispute Resolution Endpoints
- `POST /api/v1/disputes/analyze` - Analyze dispute case
- `GET /api/v1/disputes/cases` - Search similar cases
- `GET /api/v1/disputes/status` - Get dispute service status

### Document Generation Endpoints
- `GET /api/v1/documents/types` - List document types
- `GET /api/v1/documents/types/{type_id}` - Get specific document type
- `GET /api/v1/documents/templates` - List templates with filters
- `POST /api/v1/documents/generate` - Generate document
- `GET /api/v1/documents/download/{document_id}` - Download document (MD/DOCX/PDF)

### Admin Endpoints (Requires X-Admin-Key header)
- `POST /api/v1/admin/templates` - Upload YAML template
- `POST /api/v1/admin/disputes` - Upload dispute document
- `GET /api/v1/admin/stats` - Get system statistics
- `GET /api/v1/admin/health` - Admin health check

### System Endpoints
- `GET /health` - System health check
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation (ReDoc)

For detailed API specifications, see:
- Interactive Docs: http://localhost:8000/docs
- API Contract: [docs/api_contract.md](docs/api_contract.md)

## Deployment

The application is configured for easy deployment to production platforms.

### Frontend Deployment (Vercel)

The frontend is configured for automatic deployment to Vercel via GitHub Actions.

**Quick Setup:**
1. Create a Vercel account and connect your GitHub repository
2. Add required GitHub secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`
3. Configure environment variables in Vercel:
   - `NEXT_PUBLIC_API_BASE_URL` - Your backend URL
   - `NEXT_PUBLIC_APP_NAME` - Application name (optional)
4. Push to `main` branch - automatic deployment triggers

**Manual Deployment:**
```bash
cd frontend
npm install -g vercel
vercel --prod
```

See [Deployment Guide](docs/deployment.md) for complete instructions.

### Backend Deployment (Railway)

Backend deployment to Railway will be configured in a future update.

### Configuration Files

- `frontend/vercel.json` - Vercel deployment configuration
- `frontend/next.config.js` - Next.js production settings
- `.github/workflows/deploy-frontend.yml` - CI/CD workflow

## Contributing
<!-- TODO: Add contribution guidelines -->

## License
<!-- TODO: Add license information -->

## Support
<!-- TODO: Add support information -->
# T 
