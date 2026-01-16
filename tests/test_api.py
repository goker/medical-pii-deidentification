"""
Tests for the REST API.

Run with: pytest tests/test_api.py -v
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check(self, client):
        """Test health endpoint returns 200."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "model_name" in data
        assert "version" in data


class TestEntitiesEndpoint:
    """Tests for entities listing endpoint."""

    def test_list_entities(self, client):
        """Test listing supported entities."""
        response = client.get("/api/v1/entities")
        assert response.status_code == 200

        data = response.json()
        assert "entity_types" in data
        assert "total_types" in data
        assert data["total_types"] > 0


class TestDetectEndpoint:
    """Tests for PII detection endpoint."""

    def test_detect_empty_text(self, client):
        """Test detection with empty text."""
        response = client.post(
            "/api/v1/detect",
            json={"text": ""}
        )
        # Should fail validation (min_length=1)
        assert response.status_code == 422

    def test_detect_simple_text(self, client):
        """Test detection with simple text."""
        response = client.post(
            "/api/v1/detect",
            json={"text": "Hello world, no PII here."}
        )
        assert response.status_code == 200

        data = response.json()
        assert "entities" in data
        assert "entity_count" in data
        assert "text_length" in data

    @pytest.mark.slow
    def test_detect_with_pii(self, client):
        """Test detection with actual PII."""
        response = client.post(
            "/api/v1/detect",
            json={
                "text": "Patient John Smith SSN 123-45-6789",
                "confidence_threshold": 0.3
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["entity_count"] >= 1

    def test_detect_invalid_confidence(self, client):
        """Test detection with invalid confidence."""
        response = client.post(
            "/api/v1/detect",
            json={"text": "Test", "confidence_threshold": 1.5}
        )
        # Should fail validation (max=1.0)
        assert response.status_code == 422


class TestDeidentifyEndpoint:
    """Tests for de-identification endpoint."""

    def test_deidentify_simple(self, client):
        """Test basic de-identification."""
        response = client.post(
            "/api/v1/deidentify",
            json={
                "text": "Patient John Smith was admitted.",
                "strategy": "placeholder"
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert "deidentified_text" in data
        assert "entity_count" in data

    def test_deidentify_strategies(self, client):
        """Test different replacement strategies."""
        text = "Patient John Smith."

        for strategy in ["placeholder", "redact", "hash", "consistent"]:
            response = client.post(
                "/api/v1/deidentify",
                json={"text": text, "strategy": strategy}
            )
            assert response.status_code == 200

    def test_deidentify_invalid_strategy(self, client):
        """Test with invalid strategy."""
        response = client.post(
            "/api/v1/deidentify",
            json={"text": "Test", "strategy": "invalid"}
        )
        assert response.status_code == 422

    def test_deidentify_filter_entity_types(self, client):
        """Test filtering by entity types."""
        response = client.post(
            "/api/v1/deidentify",
            json={
                "text": "John Smith SSN 123-45-6789 on 01/10/2024",
                "entity_types": ["NAME"]
            }
        )
        assert response.status_code == 200


class TestBatchEndpoint:
    """Tests for batch processing endpoint."""

    def test_batch_empty(self, client):
        """Test batch with empty list."""
        response = client.post(
            "/api/v1/batch",
            json={"texts": []}
        )
        # Should fail validation (min_length=1)
        assert response.status_code == 422

    def test_batch_single(self, client):
        """Test batch with single document."""
        response = client.post(
            "/api/v1/batch",
            json={"texts": ["Patient John Smith."]}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["documents_processed"] == 1

    def test_batch_multiple(self, client):
        """Test batch with multiple documents."""
        response = client.post(
            "/api/v1/batch",
            json={
                "texts": [
                    "Patient John Smith.",
                    "SSN: 123-45-6789",
                    "Email: test@email.com"
                ]
            }
        )
        assert response.status_code == 200

        data = response.json()
        assert data["documents_processed"] == 3
        assert len(data["results"]) == 3


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200

        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "docs" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
