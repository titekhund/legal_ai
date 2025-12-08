# API Contract

<!-- TODO: Document API endpoints and contracts -->

## Base URL
```
http://localhost:8000/api/v1
```

## Authentication
<!-- TODO: Document authentication mechanism -->

## Endpoints

### Chat

#### POST /chat
Send a message and receive AI response.

**Request:**
```json
{
  "message": "string",
  "conversation_id": "string (optional)"
}
```

**Response:**
```json
{
  "response": "string",
  "citations": [],
  "conversation_id": "string"
}
```

### Conversations

#### GET /conversations
List all conversations.

#### GET /conversations/{id}
Get specific conversation.

#### POST /conversations
Create new conversation.

#### DELETE /conversations/{id}
Delete conversation.

### Health

#### GET /health
Basic health check.

## Error Responses
<!-- TODO: Document error response format -->

## Rate Limiting
<!-- TODO: Document rate limits -->
