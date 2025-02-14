# AI Documentation System API Reference

## Overview
This document provides detailed API documentation for the AI Documentation System.

## Authentication
All API endpoints require authentication using an API key in the header:
```
Authorization: Bearer <your-api-key>
```

## Endpoints

### Content Review
```http
POST /api/review
Content-Type: application/json
```

Reviews content using AI and Acrolinx integration.

**Request Body:**
```json
{
    "content": "string",
    "content_type": "text/html",
    "reference": "string (optional)"
}
```

**Response:**
```json
{
    "quality_score": float,
    "issues": [
        {
            "type": "string",
            "message": "string",
            "severity": "string",
            "suggestions": ["string"]
        }
    ],
    "metadata": {
        "acrolinx": {},
        "ai_review": {}
    }
}
```

### Content Draft
```http
POST /api/draft
Content-Type: application/json
```

Generates content drafts based on provided parameters.

**Request Body:**
```json
{
    "topic": "string",
    "context": {
        "audience": "string",
        "level": "string",
        "template": "string (optional)"
    }
}
```

### Documentation Query
```http
POST /api/query
Content-Type: application/json
```

Queries documentation and returns relevant responses.

**Request Body:**
```json
{
    "query": "string",
    "context": "object (optional)",
    "session_id": "string (optional)"
}
```

## Error Handling

### Error Response Format
```json
{
    "error": {
        "code": "string",
        "message": "string",
        "details": "object (optional)"
    }
}
```

### Common Error Codes
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Rate Limiting
- 100 requests per minute per API key
- Rate limit headers included in responses 