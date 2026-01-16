"""
Tests for PII detection functionality.

Run with: pytest tests/test_detector.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pii_detector import PIIDetector, PIIEntity
from src.entities import EntityType


class TestPIIDetector:
    """Tests for the PIIDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a detector instance."""
        return PIIDetector(confidence_threshold=0.3)

    def test_detector_initialization(self, detector):
        """Test detector initializes correctly."""
        assert detector.model_name == PIIDetector.DEFAULT_MODEL
        assert detector.confidence_threshold == 0.3
        assert detector._pipeline is None  # Not loaded yet

    def test_empty_text(self, detector):
        """Test handling of empty text."""
        result = detector.detect("")
        assert result == []

        result = detector.detect("   ")
        assert result == []

    def test_no_pii_text(self, detector):
        """Test text with no PII."""
        text = "The weather is nice today."
        result = detector.detect(text)
        # May or may not detect entities, but should not crash
        assert isinstance(result, list)

    @pytest.mark.slow
    def test_detect_name(self, detector):
        """Test name detection."""
        text = "Patient John Smith was admitted."
        result = detector.detect(text)

        # Should find at least one name
        names = [e for e in result if e.entity_type == EntityType.NAME]
        assert len(names) >= 1

    @pytest.mark.slow
    def test_detect_ssn(self, detector):
        """Test SSN detection."""
        text = "SSN: 123-45-6789"
        result = detector.detect(text)

        # Should find SSN
        ssns = [e for e in result if e.entity_type == EntityType.SSN]
        assert len(ssns) >= 1

    @pytest.mark.slow
    def test_detect_date(self, detector):
        """Test date detection."""
        text = "DOB: 03/15/1985"
        result = detector.detect(text)

        dates = [e for e in result if e.entity_type == EntityType.DATE]
        assert len(dates) >= 1

    @pytest.mark.slow
    def test_detect_multiple_entities(self, detector):
        """Test detection of multiple entity types."""
        text = "Patient John Smith (SSN: 123-45-6789) was admitted on 01/10/2024."
        result = detector.detect(text)

        # Should find multiple entities
        assert len(result) >= 2

    def test_entity_to_dict(self):
        """Test PIIEntity serialization."""
        entity = PIIEntity(
            entity_type=EntityType.NAME,
            text="John Smith",
            start=8,
            end=18,
            confidence=0.95
        )
        d = entity.to_dict()

        assert d["entity_type"] == "NAME"
        assert d["text"] == "John Smith"
        assert d["start"] == 8
        assert d["end"] == 18
        assert d["confidence"] == 0.95

    def test_confidence_threshold(self, detector):
        """Test confidence threshold filtering."""
        detector.confidence_threshold = 0.99  # Very high

        text = "Patient John Smith was admitted."
        result = detector.detect(text)

        # With very high threshold, may filter out most entities
        for entity in result:
            assert entity.confidence >= 0.99

    def test_get_model_info(self, detector):
        """Test model info retrieval."""
        info = detector.get_model_info()

        assert "model_name" in info
        assert "device" in info
        assert "confidence_threshold" in info
        assert "loaded" in info


class TestBatchDetection:
    """Tests for batch detection."""

    @pytest.fixture
    def detector(self):
        return PIIDetector(confidence_threshold=0.3)

    @pytest.mark.slow
    def test_batch_detect(self, detector):
        """Test batch detection."""
        texts = [
            "Patient John Smith.",
            "SSN: 123-45-6789",
            "Email: test@email.com"
        ]

        results = detector.detect_batch(texts)

        assert len(results) == 3
        assert all(isinstance(r, list) for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
