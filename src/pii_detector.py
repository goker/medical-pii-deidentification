"""
PII Detector - Core model inference for medical text de-identification.

Uses OpenMed's SuperClinical models for HIPAA-compliant PII detection.
"""

import os
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import logging

from transformers import (
    AutoTokenizer,
    AutoModelForTokenClassification,
    pipeline,
    Pipeline
)
import torch

from .entities import EntityType, map_model_label, get_replacement_text

logger = logging.getLogger(__name__)


@dataclass
class PIIEntity:
    """Represents a detected PII entity in text."""
    entity_type: EntityType
    text: str
    start: int
    end: int
    confidence: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_type": self.entity_type.value,
            "text": self.text,
            "start": self.start,
            "end": self.end,
            "confidence": round(self.confidence, 4)
        }


class PIIDetector:
    """
    Detects PII entities in medical/clinical text using transformer models.

    Default model: OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1
    - Optimized for clinical text
    - HIPAA-compliant entity detection
    - 44M parameters (fits in free tier cloud functions)
    """

    DEFAULT_MODEL = "OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1"

    def __init__(
        self,
        model_name: Optional[str] = None,
        device: Optional[str] = None,
        confidence_threshold: float = 0.5
    ):
        """
        Initialize the PII detector.

        Args:
            model_name: HuggingFace model identifier. Defaults to SuperClinical-Small.
            device: Device to run on ('cpu', 'cuda', 'mps'). Auto-detected if None.
            confidence_threshold: Minimum confidence score to include entity (0-1).
        """
        self.model_name = model_name or os.getenv("PII_MODEL", self.DEFAULT_MODEL)
        self.confidence_threshold = confidence_threshold
        self.device = device or self._detect_device()

        self._pipeline: Optional[Pipeline] = None
        self._tokenizer = None
        self._model = None

    def _detect_device(self) -> str:
        """Detect the best available device."""
        if torch.cuda.is_available():
            return "cuda"
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
        return "cpu"

    def load_model(self) -> None:
        """Load the model and tokenizer. Called automatically on first use."""
        if self._pipeline is not None:
            return

        logger.info(f"Loading model: {self.model_name} on {self.device}")

        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForTokenClassification.from_pretrained(self.model_name)

        self._pipeline = pipeline(
            "token-classification",
            model=self._model,
            tokenizer=self._tokenizer,
            device=0 if self.device == "cuda" else -1 if self.device == "cpu" else self.device,
            aggregation_strategy="simple"  # Merge B-/I- tokens
        )

        logger.info("Model loaded successfully")

    def detect(self, text: str) -> List[PIIEntity]:
        """
        Detect PII entities in the given text.

        Args:
            text: Clinical/medical text to analyze.

        Returns:
            List of detected PII entities with positions and confidence scores.
        """
        if not text or not text.strip():
            return []

        # Lazy load model
        self.load_model()

        # Run inference
        raw_entities = self._pipeline(text)

        # Process and filter results
        entities = []
        for entity in raw_entities:
            confidence = entity.get("score", 0.0)

            # Filter by confidence threshold
            if confidence < self.confidence_threshold:
                continue

            # Map model label to our entity type
            label = entity.get("entity_group", entity.get("entity", "O"))
            if label == "O":  # Outside any entity
                continue

            entity_type = map_model_label(label)

            pii_entity = PIIEntity(
                entity_type=entity_type,
                text=entity.get("word", ""),
                start=entity.get("start", 0),
                end=entity.get("end", 0),
                confidence=confidence
            )
            entities.append(pii_entity)

        # Sort by position
        entities.sort(key=lambda e: e.start)

        # Merge overlapping entities of the same type
        entities = self._merge_overlapping(entities)

        return entities

    def _merge_overlapping(self, entities: List[PIIEntity]) -> List[PIIEntity]:
        """Merge overlapping or adjacent entities of the same type."""
        if not entities:
            return entities

        merged = [entities[0]]

        for current in entities[1:]:
            previous = merged[-1]

            # Check if current overlaps or is adjacent to previous
            if (current.entity_type == previous.entity_type and
                current.start <= previous.end + 1):
                # Merge: extend the previous entity
                merged[-1] = PIIEntity(
                    entity_type=previous.entity_type,
                    text=previous.text + current.text[max(0, previous.end - current.start):],
                    start=previous.start,
                    end=max(previous.end, current.end),
                    confidence=max(previous.confidence, current.confidence)
                )
            else:
                merged.append(current)

        return merged

    def detect_batch(
        self,
        texts: List[str],
        batch_size: int = 8
    ) -> List[List[PIIEntity]]:
        """
        Detect PII entities in multiple texts efficiently.

        Args:
            texts: List of texts to analyze.
            batch_size: Number of texts to process at once.

        Returns:
            List of entity lists, one per input text.
        """
        self.load_model()

        results = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            for text in batch:
                results.append(self.detect(text))

        return results

    def get_model_info(self) -> Dict[str, Any]:
        """Return information about the loaded model."""
        return {
            "model_name": self.model_name,
            "device": self.device,
            "confidence_threshold": self.confidence_threshold,
            "loaded": self._pipeline is not None
        }


# Singleton instance for serverless environments
_detector_instance: Optional[PIIDetector] = None


def get_detector(
    model_name: Optional[str] = None,
    confidence_threshold: float = 0.5
) -> PIIDetector:
    """
    Get or create a PIIDetector instance.

    Uses a singleton pattern for efficient reuse in serverless environments.
    """
    global _detector_instance

    if _detector_instance is None:
        _detector_instance = PIIDetector(
            model_name=model_name,
            confidence_threshold=confidence_threshold
        )

    return _detector_instance
