#!/bin/bash
# Medical PII De-identification API - cURL Examples
#
# Usage: ./curl_examples.sh [API_URL]
# Default API_URL: http://localhost:8000

API_URL="${1:-http://localhost:8000}"

echo "========================================"
echo "Medical PII De-identification API"
echo "Base URL: $API_URL"
echo "========================================"

# 1. Health Check
echo ""
echo "1. Health Check"
echo "----------------------------------------"
curl -s "$API_URL/api/v1/health" | python3 -m json.tool

# 2. List Entity Types
echo ""
echo "2. List Supported Entity Types"
echo "----------------------------------------"
curl -s "$API_URL/api/v1/entities" | python3 -m json.tool | head -30
echo "... (truncated)"

# 3. Detect PII
echo ""
echo "3. Detect PII Entities"
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/v1/detect" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith (DOB: 03/15/1985, SSN: 123-45-6789) was admitted. Contact: john.smith@email.com, 555-123-4567.",
    "confidence_threshold": 0.5
  }' | python3 -m json.tool

# 4. De-identify with Placeholder
echo ""
echo "4. De-identify (Placeholder Strategy)"
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/v1/deidentify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith (DOB: 03/15/1985, SSN: 123-45-6789) was admitted. Contact: john.smith@email.com, 555-123-4567.",
    "strategy": "placeholder"
  }' | python3 -m json.tool

# 5. De-identify with Redaction
echo ""
echo "5. De-identify (Redaction Strategy)"
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/v1/deidentify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith (DOB: 03/15/1985, SSN: 123-45-6789) was admitted.",
    "strategy": "redact"
  }' | python3 -m json.tool

# 6. De-identify with Consistent Fakes
echo ""
echo "6. De-identify (Consistent Strategy)"
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/v1/deidentify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith mentioned John Smith needs follow-up.",
    "strategy": "consistent"
  }' | python3 -m json.tool

# 7. De-identify Specific Entity Types Only
echo ""
echo "7. De-identify Only Names and SSN"
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/v1/deidentify" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Patient John Smith (DOB: 03/15/1985, SSN: 123-45-6789) was admitted.",
    "strategy": "placeholder",
    "entity_types": ["NAME", "SSN"]
  }' | python3 -m json.tool

# 8. Batch Processing
echo ""
echo "8. Batch Processing (Multiple Documents)"
echo "----------------------------------------"
curl -s -X POST "$API_URL/api/v1/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "texts": [
      "Patient Jane Doe visited on 02/15/2024.",
      "Dr. Robert Brown called 555-999-8888.",
      "Email from mary@hospital.org about James Wilson."
    ],
    "strategy": "placeholder"
  }' | python3 -m json.tool

echo ""
echo "========================================"
echo "Examples complete!"
echo "========================================"
