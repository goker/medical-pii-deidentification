#!/usr/bin/env python3
"""
Example: Using the Medical PII De-identification API

This script demonstrates how to use the REST API for PII detection
and de-identification of clinical text.
"""

import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000/api/v1"


def detect_pii(text: str, confidence: float = 0.5) -> dict:
    """Detect PII entities in text."""
    response = requests.post(
        f"{BASE_URL}/detect",
        json={"text": text, "confidence_threshold": confidence}
    )
    response.raise_for_status()
    return response.json()


def deidentify(text: str, strategy: str = "placeholder") -> dict:
    """De-identify text using specified strategy."""
    response = requests.post(
        f"{BASE_URL}/deidentify",
        json={"text": text, "strategy": strategy}
    )
    response.raise_for_status()
    return response.json()


def batch_deidentify(texts: list, strategy: str = "placeholder") -> dict:
    """Process multiple documents."""
    response = requests.post(
        f"{BASE_URL}/batch",
        json={"texts": texts, "strategy": strategy}
    )
    response.raise_for_status()
    return response.json()


def health_check() -> dict:
    """Check API health status."""
    response = requests.get(f"{BASE_URL}/health")
    response.raise_for_status()
    return response.json()


def main():
    # Sample clinical text
    sample_text = """
    Patient John Smith (DOB: 03/15/1985, MRN: 123456789) was admitted on
    01/10/2024. Contact: john.smith@email.com, 555-123-4567.
    SSN: 123-45-6789. Dr. Sarah Johnson performed the procedure at
    Memorial Hospital, 123 Main St, Boston MA.
    """

    print("=" * 60)
    print("Medical PII De-identification API Examples")
    print("=" * 60)

    # 1. Health Check
    print("\n1. Health Check")
    print("-" * 40)
    health = health_check()
    print(f"Status: {health['status']}")
    print(f"Model: {health['model_name']}")
    print(f"Loaded: {health['model_loaded']}")

    # 2. Detect PII
    print("\n2. Detect PII Entities")
    print("-" * 40)
    print(f"Input text:\n{sample_text.strip()}\n")

    result = detect_pii(sample_text)
    print(f"Found {result['entity_count']} entities:\n")
    for entity in result['entities']:
        print(f"  - {entity['entity_type']}: '{entity['text']}' "
              f"(confidence: {entity['confidence']:.2%})")

    # 3. De-identify with Placeholder Strategy
    print("\n3. De-identify (Placeholder Strategy)")
    print("-" * 40)

    result = deidentify(sample_text, strategy="placeholder")
    print(f"De-identified text:\n{result['deidentified_text']}")

    # 4. De-identify with Redaction Strategy
    print("\n4. De-identify (Redaction Strategy)")
    print("-" * 40)

    result = deidentify(sample_text, strategy="redact")
    print(f"Redacted text:\n{result['deidentified_text']}")

    # 5. De-identify with Consistent Fakes
    print("\n5. De-identify (Consistent Fakes)")
    print("-" * 40)

    result = deidentify(sample_text, strategy="consistent")
    print(f"With fake values:\n{result['deidentified_text']}")
    print(f"\nReplacements made:")
    for original, replacement in result['replacements_made'].items():
        print(f"  '{original}' -> '{replacement}'")

    # 6. Batch Processing
    print("\n6. Batch Processing")
    print("-" * 40)

    documents = [
        "Patient Jane Doe (SSN: 111-22-3333) visited on 02/15/2024.",
        "Dr. Robert Brown called 555-999-8888 regarding MRN 987654321.",
        "Email from mary.smith@hospital.org about patient James Wilson."
    ]

    result = batch_deidentify(documents)
    print(f"Processed {result['documents_processed']} documents")
    print(f"Total entities: {result['total_entities']}\n")

    for i, doc_result in enumerate(result['results'], 1):
        print(f"Document {i}:")
        print(f"  Original: {doc_result['original_text']}")
        print(f"  De-ID'd:  {doc_result['deidentified_text']}")
        print(f"  Entities: {doc_result['entity_count']}\n")

    print("=" * 60)
    print("Examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
