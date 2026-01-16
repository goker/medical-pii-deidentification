"""
De-identification utilities for replacing PII with placeholders.

Supports multiple replacement strategies for different use cases.
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
import re
import hashlib

from .pii_detector import PIIDetector, PIIEntity, get_detector
from .entities import EntityType, get_replacement_text


class ReplacementStrategy(str, Enum):
    """Strategy for replacing detected PII."""

    PLACEHOLDER = "placeholder"      # [NAME], [DATE], etc.
    CONSISTENT = "consistent"        # Same entity -> same fake value
    REDACT = "redact"               # Replace with ████████
    HASH = "hash"                   # Replace with hash prefix
    CUSTOM = "custom"               # User-provided mapping


@dataclass
class DeidentificationResult:
    """Result of de-identification process."""
    original_text: str
    deidentified_text: str
    entities_found: List[PIIEntity]
    replacements_made: Dict[str, str]
    entity_count: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_text": self.original_text,
            "deidentified_text": self.deidentified_text,
            "entities_found": [e.to_dict() for e in self.entities_found],
            "replacements_made": self.replacements_made,
            "entity_count": self.entity_count
        }


class Deidentifier:
    """
    De-identifies medical text by replacing PII with placeholders.

    Supports multiple replacement strategies:
    - PLACEHOLDER: Generic labels like [NAME], [DATE]
    - CONSISTENT: Same entity text always maps to same fake value
    - REDACT: Black bars/blocks
    - HASH: Deterministic hash-based pseudonyms
    """

    def __init__(
        self,
        detector: Optional[PIIDetector] = None,
        strategy: ReplacementStrategy = ReplacementStrategy.PLACEHOLDER,
        custom_replacements: Optional[Dict[str, str]] = None
    ):
        """
        Initialize the deidentifier.

        Args:
            detector: PIIDetector instance. Creates default if None.
            strategy: How to replace detected PII.
            custom_replacements: For CUSTOM strategy, mapping of text -> replacement.
        """
        self.detector = detector or get_detector()
        self.strategy = strategy
        self.custom_replacements = custom_replacements or {}

        # For CONSISTENT strategy: track entity -> fake value mapping
        self._consistent_mapping: Dict[str, str] = {}
        self._entity_counters: Dict[EntityType, int] = {}

    def deidentify(
        self,
        text: str,
        entity_types: Optional[List[EntityType]] = None
    ) -> DeidentificationResult:
        """
        De-identify the given text.

        Args:
            text: Clinical text to de-identify.
            entity_types: Only replace these entity types. None = all types.

        Returns:
            DeidentificationResult with original, deidentified text, and metadata.
        """
        if not text:
            return DeidentificationResult(
                original_text=text,
                deidentified_text=text,
                entities_found=[],
                replacements_made={},
                entity_count=0
            )

        # Detect entities
        entities = self.detector.detect(text)

        # Filter by requested entity types
        if entity_types:
            entities = [e for e in entities if e.entity_type in entity_types]

        # Build replacement mapping
        replacements: Dict[str, str] = {}

        # Sort by position (reverse) to replace from end to start
        # This preserves character positions for earlier replacements
        sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

        deidentified = text
        for entity in sorted_entities:
            replacement = self._get_replacement(entity)
            replacements[entity.text] = replacement

            # Replace in text
            deidentified = (
                deidentified[:entity.start] +
                replacement +
                deidentified[entity.end:]
            )

        return DeidentificationResult(
            original_text=text,
            deidentified_text=deidentified,
            entities_found=entities,
            replacements_made=replacements,
            entity_count=len(entities)
        )

    def _get_replacement(self, entity: PIIEntity) -> str:
        """Get the replacement text for an entity based on strategy."""

        if self.strategy == ReplacementStrategy.PLACEHOLDER:
            return get_replacement_text(entity.entity_type)

        elif self.strategy == ReplacementStrategy.REDACT:
            # Replace with blocks matching length
            return "█" * len(entity.text)

        elif self.strategy == ReplacementStrategy.HASH:
            # Create a short hash-based identifier
            hash_val = hashlib.sha256(entity.text.encode()).hexdigest()[:8]
            return f"[{entity.entity_type.value}_{hash_val}]"

        elif self.strategy == ReplacementStrategy.CONSISTENT:
            return self._get_consistent_replacement(entity)

        elif self.strategy == ReplacementStrategy.CUSTOM:
            return self.custom_replacements.get(
                entity.text,
                get_replacement_text(entity.entity_type)
            )

        return get_replacement_text(entity.entity_type)

    def _get_consistent_replacement(self, entity: PIIEntity) -> str:
        """Generate consistent fake values for the same entity text."""

        key = f"{entity.entity_type.value}:{entity.text}"

        if key not in self._consistent_mapping:
            # Generate a new fake value
            entity_type = entity.entity_type

            if entity_type not in self._entity_counters:
                self._entity_counters[entity_type] = 0

            self._entity_counters[entity_type] += 1
            counter = self._entity_counters[entity_type]

            # Generate appropriate fake value based on type
            fake_value = self._generate_fake_value(entity_type, counter)
            self._consistent_mapping[key] = fake_value

        return self._consistent_mapping[key]

    def _generate_fake_value(self, entity_type: EntityType, counter: int) -> str:
        """Generate a fake value for consistent replacement."""

        fake_names = ["Smith", "Johnson", "Williams", "Brown", "Jones",
                      "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]
        fake_first_names = ["John", "Jane", "Robert", "Mary", "Michael",
                           "Patricia", "William", "Linda", "David", "Elizabeth"]

        if entity_type == EntityType.NAME:
            first = fake_first_names[counter % len(fake_first_names)]
            last = fake_names[counter % len(fake_names)]
            return f"{first} {last}"

        elif entity_type == EntityType.DATE:
            # Generate a fake date
            month = (counter % 12) + 1
            day = (counter % 28) + 1
            return f"{month:02d}/{day:02d}/XXXX"

        elif entity_type == EntityType.PHONE:
            return f"555-{counter:03d}-{1000 + counter:04d}"

        elif entity_type == EntityType.EMAIL:
            name = fake_names[counter % len(fake_names)].lower()
            return f"{name}{counter}@example.com"

        elif entity_type == EntityType.SSN:
            return "XXX-XX-XXXX"

        elif entity_type == EntityType.MRN:
            return f"MRN-{counter:08d}"

        elif entity_type == EntityType.LOCATION:
            return f"[LOCATION_{counter}]"

        elif entity_type == EntityType.AGE:
            return "[AGE>89]"

        else:
            return f"[{entity_type.value}_{counter}]"

    def reset_mappings(self) -> None:
        """Reset consistent replacement mappings (for new document set)."""
        self._consistent_mapping.clear()
        self._entity_counters.clear()

    def deidentify_batch(
        self,
        texts: List[str],
        entity_types: Optional[List[EntityType]] = None,
        reset_between_docs: bool = False
    ) -> List[DeidentificationResult]:
        """
        De-identify multiple texts.

        Args:
            texts: List of texts to de-identify.
            entity_types: Only replace these entity types.
            reset_between_docs: If True, reset consistent mappings between documents.

        Returns:
            List of DeidentificationResults.
        """
        results = []

        for text in texts:
            if reset_between_docs and self.strategy == ReplacementStrategy.CONSISTENT:
                self.reset_mappings()

            results.append(self.deidentify(text, entity_types))

        return results


def quick_deidentify(
    text: str,
    strategy: ReplacementStrategy = ReplacementStrategy.PLACEHOLDER
) -> str:
    """
    Convenience function for quick de-identification.

    Args:
        text: Text to de-identify.
        strategy: Replacement strategy.

    Returns:
        De-identified text string.
    """
    deidentifier = Deidentifier(strategy=strategy)
    result = deidentifier.deidentify(text)
    return result.deidentified_text
