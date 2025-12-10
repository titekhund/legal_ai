# API Contract

Complete API documentation for the Georgian Tax Code Legal AI Assistant.

## Base URL
```
Production: https://api.legal-ai.ge/api/v1
Development: http://localhost:8000/api/v1
```

## Authentication

### Admin Endpoints
Admin endpoints require an API key passed via the `X-Admin-Key` header:

```http
X-Admin-Key: your-admin-api-key-here
```

Set the admin API key via environment variable:
```bash
ADMIN_API_KEY=your-secure-key-here
```

### Public Endpoints
Most endpoints are public and do not require authentication. Rate limiting may apply in production.

---

## Tax Code Endpoints

### POST /tax/advice
Get tax advice based on a question with automatic citation extraction.

**Request:**
```json
{
  "question": "რა არის დღგ-ის განაკვეთი საქართველოში?",
  "context": {},
  "language": "ka"
}
```

**Response:**
```json
{
  "answer": "საქართველოში დღგ-ის განაკვეთი არის 18%. მუხლი 168 ...",
  "cited_articles": [
    {
      "article_number": "168",
      "title": null,
      "snippet": null
    }
  ],
  "confidence": 0.95,
  "model_used": "gemini-1.5-pro",
  "processing_time_ms": 1234
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid request body
- `500 Internal Server Error` - Service error

---

### GET /tax/articles
Search tax code articles.

**Query Parameters:**
- `query` (string, required) - Search query
- `limit` (integer, optional) - Maximum results (default: 10, max: 50)

**Request:**
```http
GET /api/v1/tax/articles?query=დღგ&limit=5
```

**Response:**
```json
[
  {
    "article_number": "168",
    "title": "დღგ-ის განაკვეთი",
    "snippet": "დღგ-ის განაკვეთი არის 18%..."
  }
]
```

---

### GET /tax/status
Get tax service status and statistics.

**Response:**
```json
{
  "service": "TaxCodeService",
  "file_upload_status": "ready",
  "tax_code_path": "/app/data/tax_code/georgian_tax_code.pdf",
  "file_exists": true,
  "uploaded_file_name": "georgian_tax_code.pdf",
  "model_name": "gemini-1.5-pro",
  "max_history_messages": 10,
  "cache_stats": {
    "citation_cache_hits": 42,
    "citation_cache_misses": 8,
    "citation_cache_size": 8,
    "citation_cache_maxsize": 256
  }
}
```

---

## Dispute Resolution Endpoints

### POST /disputes/analyze
Analyze a dispute case and provide legal analysis.

**Request:**
```json
{
  "case_description": "საგადასახადო ორგანომ დააკისრა დღგ-ის დავალიანება 10000 ლარის ოდენობით...",
  "taxpayer_info": {
    "name": "შპს ტესტი",
    "tax_id": "123456789",
    "type": "ltd"
  },
  "dispute_type": "tax_assessment",
  "requested_analysis": ["legal_grounds", "recommendations"],
  "language": "ka"
}
```

**Response:**
```json
{
  "summary": "საგადასახადო დავა დღგ-ის შეფასებასთან დაკავშირებით...",
  "legal_grounds": ["მუხლი 168...", "მუხლი 82..."],
  "recommendations": [
    "1. შეაგროვეთ დამადასტურებელი დოკუმენტაცია...",
    "2. მოამზადეთ საჩივარი..."
  ],
  "cited_cases": [
    {
      "case_id": "2023-001",
      "similarity_score": 0.89,
      "outcome": "taxpayer_won"
    }
  ],
  "confidence": 0.85,
  "processing_time_ms": 2345
}
```

---

### GET /disputes/cases
Search for similar dispute cases.

**Query Parameters:**
- `query` (string, required) - Search query
- `limit` (integer, optional) - Maximum results (default: 5, max: 20)

**Request:**
```http
GET /api/v1/disputes/cases?query=დღგ&limit=3
```

**Response:**
```json
[
  {
    "case_id": "2023-001",
    "title": "დღგ-ის შეფასება...",
    "outcome": "taxpayer_won",
    "similarity_score": 0.92
  }
]
```

---

### GET /disputes/status
Get dispute service status.

**Response:**
```json
{
  "service": "DisputeRAGService",
  "initialized": true,
  "cases_count": 42,
  "model_name": "claude-3-sonnet-20240229"
}
```

---

## Document Generation Endpoints

### GET /documents/types
List all available document types.

**Response:**
```json
[
  {
    "id": "nda",
    "name_ka": "კონფიდენციალურობის შეთანხმება",
    "name_en": "Non-Disclosure Agreement",
    "description_ka": "კონფიდენციალურობის შეთანხმება საქმიანი ინფორმაციის დასაცავად",
    "description_en": "Agreement to protect confidential business information",
    "required_fields": ["party_a_name", "party_b_name", "effective_date"],
    "optional_fields": ["confidentiality_period"]
  }
]
```

---

### GET /documents/types/{type_id}
Get details of a specific document type.

**Path Parameters:**
- `type_id` (string) - Document type identifier

**Response:**
```json
{
  "id": "nda",
  "name_ka": "კონფიდენციალურობის შეთანხმება",
  "name_en": "Non-Disclosure Agreement",
  "description_ka": "კონფიდენციალურობის შეთანხმება...",
  "required_fields": ["party_a_name", "party_b_name", "effective_date"],
  "optional_fields": ["confidentiality_period"]
}
```

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Document type not found

---

### GET /documents/templates
List available templates with optional filtering.

**Query Parameters:**
- `document_type` (string, optional) - Filter by document type
- `language` (string, optional) - Filter by language ('ka' or 'en')
- `limit` (integer, optional) - Maximum results

**Request:**
```http
GET /api/v1/documents/templates?document_type=nda&language=ka
```

**Response:**
```json
[
  {
    "id": "nda_ka_standard",
    "type": "nda",
    "name_ka": "კონფიდენციალურობის ხელშეკრულება - სტანდარტული",
    "name_en": "Non-Disclosure Agreement - Standard",
    "language": "ka",
    "category": "ხელშეკრულებები",
    "tags": ["კონფიდენციალურობა", "NDA"],
    "variables": [
      {
        "name": "party_a_name",
        "label_ka": "პირველი მხარის სახელი",
        "label_en": "First Party Name",
        "type": "text",
        "required": true,
        "placeholder_ka": "მაგ: შპს \"კომპანია\""
      }
    ],
    "related_articles": []
  }
]
```

---

### POST /documents/generate
Generate a document from a template.

**Request:**
```json
{
  "document_type": "nda",
  "template_id": "nda_ka_standard",
  "variables": {
    "party_a_name": "შპს კომპანია A",
    "party_b_name": "შპს კომპანია B",
    "effective_date": "2024-12-10",
    "confidentiality_period": "3"
  },
  "language": "ka",
  "include_legal_references": true,
  "format": "markdown"
}
```

**Response:**
```json
{
  "document": {
    "document_type": "nda",
    "template_used": "nda_ka_standard",
    "content": "# კონფიდენციალურობის შეთანხმება\n\n...",
    "format": "markdown",
    "cited_articles": ["168", "82"],
    "warnings": [],
    "disclaimer": "ეს დოკუმენტი გენერირებულია AI-ს მიერ...",
    "processing_time_ms": 1567
  },
  "document_id": "550e8400-e29b-41d4-a716-446655440000",
  "download_links": {
    "markdown": "/api/v1/documents/download/550e8400-e29b-41d4-a716-446655440000?format=markdown",
    "docx": "/api/v1/documents/download/550e8400-e29b-41d4-a716-446655440000?format=docx",
    "pdf": "/api/v1/documents/download/550e8400-e29b-41d4-a716-446655440000?format=pdf"
  }
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid request (missing variables, invalid template)
- `404 Not Found` - Template not found
- `500 Internal Server Error` - Generation error

---

### GET /documents/download/{document_id}
Download a generated document in the specified format.

**Path Parameters:**
- `document_id` (string, uuid) - Document identifier

**Query Parameters:**
- `format` (string, optional) - Output format: 'markdown' (default), 'docx', or 'pdf'

**Request:**
```http
GET /api/v1/documents/download/550e8400-e29b-41d4-a716-446655440000?format=docx
```

**Response:**
- Content-Type: `text/markdown` (markdown), `application/vnd.openxmlformats-officedocument.wordprocessingml.document` (docx), or `application/pdf` (pdf)
- Content-Disposition: `attachment; filename="document_{id}.{ext}"`
- Body: Binary file content

**Status Codes:**
- `200 OK` - Success
- `404 Not Found` - Document not found or expired
- `400 Bad Request` - Invalid format

**Notes:**
- Documents are stored for 1 hour after generation
- Maximum 100 documents stored at a time (FIFO eviction)

---

## Admin Endpoints

All admin endpoints require the `X-Admin-Key` header.

### POST /admin/templates
Upload a new YAML template.

**Headers:**
```http
X-Admin-Key: your-admin-key
Content-Type: multipart/form-data
```

**Request:**
```http
POST /api/v1/admin/templates
Content-Type: multipart/form-data

file: <template.yaml>
```

**Response:**
```json
{
  "status": "success",
  "template_id": "custom_nda_ka",
  "message": "Template uploaded successfully"
}
```

**Status Codes:**
- `200 OK` - Success
- `400 Bad Request` - Invalid YAML or validation error
- `401 Unauthorized` - Invalid or missing admin key

---

### POST /admin/disputes
Upload a dispute document (PDF or JSON).

**Headers:**
```http
X-Admin-Key: your-admin-key
Content-Type: multipart/form-data
```

**Request:**
```http
POST /api/v1/admin/disputes
Content-Type: multipart/form-data

file: <dispute.pdf>
metadata: {"case_id": "2024-001", "outcome": "taxpayer_won"}
```

**Response:**
```json
{
  "status": "success",
  "case_id": "2024-001",
  "message": "Dispute document uploaded and indexed"
}
```

---

### GET /admin/stats
Get system statistics.

**Headers:**
```http
X-Admin-Key: your-admin-key
```

**Response:**
```json
{
  "tax_service": {
    "file_upload_status": "ready",
    "cache_hits": 42,
    "cache_misses": 8
  },
  "dispute_service": {
    "cases_count": 156,
    "initialized": true
  },
  "document_service": {
    "templates_count": 6,
    "types_count": 6,
    "cache_stats": {
      "search_cache_size": 15,
      "type_cache_size": 6
    }
  },
  "storage": {
    "stored_documents": 23,
    "max_documents": 100
  }
}
```

---

### GET /admin/health
Admin-specific health check with detailed service status.

**Headers:**
```http
X-Admin-Key: your-admin-key
```

**Response:**
```json
{
  "status": "healthy",
  "services": {
    "tax_service": "ready",
    "dispute_service": "ready",
    "document_service": "ready"
  },
  "timestamp": "2024-12-10T10:30:00Z"
}
```

---

## System Endpoints

### GET /health
Basic system health check (no authentication required).

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-12-10T10:30:00Z"
}
```

**Status Codes:**
- `200 OK` - System healthy
- `503 Service Unavailable` - System unhealthy

---

## Error Response Format

All endpoints use a consistent error format:

```json
{
  "detail": {
    "error": "Error type or message",
    "message": "Human-readable error description",
    "details": {
      "field": "Additional context"
    }
  }
}
```

**Common Error Codes:**
- `400 Bad Request` - Invalid input, validation error
- `401 Unauthorized` - Missing or invalid admin key
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Request validation failed
- `500 Internal Server Error` - Server-side error
- `503 Service Unavailable` - Service not initialized or unavailable

---

## Rate Limiting

Currently not implemented. Future versions will include:
- Public endpoints: 100 requests/minute per IP
- Admin endpoints: 1000 requests/minute per API key
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Both provide interactive API exploration with request/response examples.
