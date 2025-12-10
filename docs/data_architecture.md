# Data Architecture

<!-- TODO: Document data architecture and schemas -->

## Vector Database

### Tax Code Collection
Document structure for tax code documents in vector database.

**Metadata Schema:**
```json
{
  "document_id": "string",
  "title": "string",
  "section": "string",
  "source": "string",
  "jurisdiction": "string",
  "effective_date": "date",
  "document_type": "string"
}
```

### Disputes Collection
Document structure for historical disputes.

**Metadata Schema:**
```json
{
  "case_id": "string",
  "case_name": "string",
  "outcome": "string",
  "date": "date",
  "tax_type": "string",
  "amount": "number"
}
```

## Relational Database

### Tables

#### conversations
<!-- TODO: Define schema -->

#### messages
<!-- TODO: Define schema -->

#### documents
<!-- TODO: Define schema -->

#### citations
<!-- TODO: Define schema -->

## Data Ingestion Pipeline
<!-- TODO: Document ingestion process -->

## Data Privacy
<!-- TODO: Document data handling and privacy measures -->
