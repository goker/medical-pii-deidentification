"""
API route handlers for PII detection and de-identification.
"""

from typing import List, Optional
import logging

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

import sys
sys.path.insert(0, '..')

from src.pii_detector import PIIDetector, get_detector
from src.deidentify import Deidentifier, ReplacementStrategy
from src.entities import EntityType, HIPAA_ENTITIES, get_all_entity_types

from .schemas import (
    DetectRequest, DetectResponse, DetectedEntity,
    DeidentifyRequest, DeidentifyResponse,
    BatchRequest, BatchResponse, BatchResult,
    HealthResponse, EntitiesResponse, EntityTypeInfo,
    ErrorResponse, ReplacementStrategyEnum
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton detector instance (warm across requests)
_detector: Optional[PIIDetector] = None


def get_pii_detector() -> PIIDetector:
    """Dependency to get or create the PII detector."""
    global _detector
    if _detector is None:
        _detector = get_detector()
    return _detector


@router.post(
    "/detect",
    response_model=DetectResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Detect PII entities",
    description="Analyze text and return detected PII entities with positions and confidence scores."
)
async def detect_pii(
    request: DetectRequest,
    detector: PIIDetector = Depends(get_pii_detector)
) -> DetectResponse:
    """Detect PII entities in the provided text."""

    try:
        # Update confidence threshold if provided
        original_threshold = detector.confidence_threshold
        detector.confidence_threshold = request.confidence_threshold

        # Detect entities
        entities = detector.detect(request.text)

        # Restore threshold
        detector.confidence_threshold = original_threshold

        # Convert to response format
        detected_entities = [
            DetectedEntity(
                entity_type=e.entity_type.value,
                text=e.text,
                start=e.start,
                end=e.end,
                confidence=round(e.confidence, 4)
            )
            for e in entities
        ]

        return DetectResponse(
            entities=detected_entities,
            entity_count=len(detected_entities),
            text_length=len(request.text)
        )

    except Exception as e:
        logger.error(f"Detection error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/deidentify",
    response_model=DeidentifyResponse,
    responses={400: {"model": ErrorResponse}},
    summary="De-identify text",
    description="Replace PII in text with placeholders or other replacement strategies."
)
async def deidentify_text(
    request: DeidentifyRequest,
    detector: PIIDetector = Depends(get_pii_detector)
) -> DeidentifyResponse:
    """De-identify the provided text by replacing PII."""

    try:
        # Map API strategy enum to internal enum
        strategy_map = {
            ReplacementStrategyEnum.placeholder: ReplacementStrategy.PLACEHOLDER,
            ReplacementStrategyEnum.consistent: ReplacementStrategy.CONSISTENT,
            ReplacementStrategyEnum.redact: ReplacementStrategy.REDACT,
            ReplacementStrategyEnum.hash: ReplacementStrategy.HASH,
        }
        strategy = strategy_map.get(request.strategy, ReplacementStrategy.PLACEHOLDER)

        # Update confidence threshold
        detector.confidence_threshold = request.confidence_threshold

        # Create deidentifier
        deidentifier = Deidentifier(detector=detector, strategy=strategy)

        # Parse entity types if provided
        entity_types = None
        if request.entity_types:
            entity_types = []
            for et_str in request.entity_types:
                try:
                    entity_types.append(EntityType(et_str.upper()))
                except ValueError:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown entity type: {et_str}"
                    )

        # De-identify
        result = deidentifier.deidentify(request.text, entity_types=entity_types)

        # Convert entities to response format
        detected_entities = [
            DetectedEntity(
                entity_type=e.entity_type.value,
                text=e.text,
                start=e.start,
                end=e.end,
                confidence=round(e.confidence, 4)
            )
            for e in result.entities_found
        ]

        return DeidentifyResponse(
            deidentified_text=result.deidentified_text,
            entities_found=detected_entities,
            replacements_made=result.replacements_made,
            entity_count=result.entity_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"De-identification error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/batch",
    response_model=BatchResponse,
    responses={400: {"model": ErrorResponse}},
    summary="Batch process multiple texts",
    description="De-identify multiple documents in a single request."
)
async def batch_deidentify(
    request: BatchRequest,
    detector: PIIDetector = Depends(get_pii_detector)
) -> BatchResponse:
    """Process multiple texts for de-identification."""

    try:
        # Map strategy
        strategy_map = {
            ReplacementStrategyEnum.placeholder: ReplacementStrategy.PLACEHOLDER,
            ReplacementStrategyEnum.consistent: ReplacementStrategy.CONSISTENT,
            ReplacementStrategyEnum.redact: ReplacementStrategy.REDACT,
            ReplacementStrategyEnum.hash: ReplacementStrategy.HASH,
        }
        strategy = strategy_map.get(request.strategy, ReplacementStrategy.PLACEHOLDER)

        detector.confidence_threshold = request.confidence_threshold
        deidentifier = Deidentifier(detector=detector, strategy=strategy)

        # Process all texts
        results = deidentifier.deidentify_batch(request.texts)

        # Build response
        batch_results = [
            BatchResult(
                original_text=r.original_text,
                deidentified_text=r.deidentified_text,
                entity_count=r.entity_count
            )
            for r in results
        ]

        total_entities = sum(r.entity_count for r in results)

        return BatchResponse(
            results=batch_results,
            total_entities=total_entities,
            documents_processed=len(request.texts)
        )

    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check API health and model status."
)
async def health_check(
    detector: PIIDetector = Depends(get_pii_detector)
) -> HealthResponse:
    """Return API health status."""

    model_info = detector.get_model_info()

    return HealthResponse(
        status="healthy",
        model_loaded=model_info["loaded"],
        model_name=model_info["model_name"],
        version="1.0.0"
    )


@router.get(
    "/entities",
    response_model=EntitiesResponse,
    summary="List entity types",
    description="List all supported HIPAA entity types with descriptions."
)
async def list_entities() -> EntitiesResponse:
    """Return list of supported entity types."""

    entity_types = []

    for entity_type in get_all_entity_types():
        info = HIPAA_ENTITIES.get(entity_type, {})
        entity_types.append(
            EntityTypeInfo(
                name=entity_type.value,
                description=info.get("description", ""),
                examples=info.get("examples", []),
                replacement=info.get("replacement", f"[{entity_type.value}]")
            )
        )

    return EntitiesResponse(
        entity_types=entity_types,
        total_types=len(entity_types)
    )
