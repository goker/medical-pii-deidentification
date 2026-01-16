# API Reference

Complete reference for the Medical PII De-identification REST API.

**Base URL**: `http://localhost:8000/api/v1`

---

## Endpoints

### POST /detect

Detect PII entities in text.

**Request Body:**
```json
{
  "text": "string (required, 1-100000 chars)",
  "confidence_threshold": "number (optional, 0.0-1.0, default: 0.5)"
}
```

**Response:**
```json
{
  "entities": [
    {
      "entity_type": "string",
      "text": "string",
      "start": "integer",
      "end": "integer",
      "confidence": "number"
    }
  ],
  "entity_count": "integer",
  "text_length": "integer"
}
```

**Example:**
```bash
curl -X POST 'http://localhost:8000/api/v1/detect' \
  -H 'Content-Type: application/json' \
  -d '{"text": "John Smith SSN 123-45-6789", "confidence_threshold": 0.5}'
```

---

### POST /deidentify

Replace PII with placeholders or other strategies.

**Request Body:**
```json
{
  "text": "string (required)",
  "strategy": "string (optional: placeholder|consistent|redact|hash)",
  "entity_types": ["string"] (optional, filter by type),
  "confidence_threshold": "number (optional, 0.0-1.0)"
}
```

**Response:**
```json
{
  "deidentified_text": "string",
  "entities_found": [...],
  "replacements_made": {"original": "replacement"},
  "entity_count": "integer"
}
```

**Example:**
```bash
curl -X POST 'http://localhost:8000/api/v1/deidentify' \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Patient John Smith (SSN: 123-45-6789)",
    "strategy": "placeholder",
    "entity_types": ["NAME", "SSN"]
  }'
```

---

### POST /batch

Process multiple documents.

**Request Body:**
```json
{
  "texts": ["string", "string", ...] (1-100 items),
  "strategy": "string (optional)",
  "confidence_threshold": "number (optional)"
}
```

**Response:**
```json
{
  "results": [
    {
      "original_text": "string",
      "deidentified_text": "string",
      "entity_count": "integer"
    }
  ],
  "total_entities": "integer",
  "documents_processed": "integer"
}
```

---

### GET /health

Check API health status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1",
  "version": "1.0.0"
}
```

---

### GET /entities

List all supported entity types.

**Response:**
```json
{
  "entity_types": [
    {
      "name": "NAME",
      "description": "Names of patients, doctors, and other individuals",
      "examples": ["John Smith", "Dr. Sarah Johnson"],
      "replacement": "[NAME]"
    }
  ],
  "total_types": 21
}
```

---

## Entity Types

| Type | Description |
|------|-------------|
| `NAME` | Patient, doctor, and other individual names |
| `DATE` | Dates (DOB, admission, discharge, etc.) |
| `PHONE` | Telephone numbers |
| `FAX` | Fax numbers |
| `EMAIL` | Email addresses |
| `SSN` | Social Security numbers |
| `MRN` | Medical record numbers |
| `ACCOUNT` | Account/beneficiary numbers |
| `LICENSE` | License/certificate numbers |
| `VEHICLE` | Vehicle identifiers |
| `DEVICE` | Device identifiers/serial numbers |
| `URL` | Web URLs |
| `IP` | IP addresses |
| `BIOMETRIC` | Biometric identifiers |
| `PHOTO` | Photos/images |
| `AGE` | Ages over 89 |
| `LOCATION` | Geographic data (address, city, ZIP) |
| `OTHER_ID` | Other unique identifiers |
| `PROVIDER` | Healthcare provider names |
| `ORGANIZATION` | Healthcare organization names |
| `PATIENT_ID` | Patient identifiers |

---

## Replacement Strategies

### placeholder (default)
Replaces with generic labels.
```
Input:  "John Smith"
Output: "[NAME]"
```

### consistent
Same entity always maps to same fake value.
```
Input:  "John Smith" (appears twice)
Output: "John Smith_1" (both times)
```

### redact
Replaces with block characters.
```
Input:  "John Smith"
Output: "██████████"
```

### hash
Creates deterministic pseudonyms.
```
Input:  "John Smith"
Output: "[NAME_a1b2c3d4]"
```

---

## Error Responses

**400 Bad Request:**
```json
{
  "error": "Validation error",
  "detail": "Text cannot be empty",
  "status_code": 400
}
```

**500 Internal Server Error:**
```json
{
  "error": "Internal server error",
  "detail": "An unexpected error occurred",
  "status_code": 500
}
```

---

## Rate Limits

Default limits (configurable):
- **Requests**: No default limit
- **Text length**: 100,000 characters max
- **Batch size**: 100 documents max

---

## OpenAPI/Swagger

Interactive API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`
