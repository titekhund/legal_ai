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
```bash
# TODO: Add setup instructions

# 1. Clone the repository
git clone <repository-url>
cd legal_ai

# 2. Copy environment variables
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys

# 3. Start services with Docker Compose
docker-compose -f infra/docker-compose.dev.yml up

# 4. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Documentation: http://localhost:8000/docs
```

## Documentation
- [Architecture](docs/architecture.md)
- [API Contract](docs/api_contract.md)
- [Data Architecture](docs/data_architecture.md)
- [Deployment Guide](docs/deployment.md)
- [Golden Tests](docs/golden_tests.yaml)

## Development

### Backend Development
```bash
# TODO: Add backend development instructions
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development
```bash
# TODO: Add frontend development instructions
cd frontend
npm install
npm run dev
```

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
