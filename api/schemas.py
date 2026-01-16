"""
Pydantic schemas for API request/response validation.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ReplacementStrategyEnum(str, Enum):
    """Available replacement strategies."""
    placeholder = "placeholder"
    consistent = "consistent"
    redact = "redact"
    hash = "hash"


class DetectRequest(BaseModel):
    """Request body for PII detection."""
    text: str = Field(
        ...,
        description="Clinical text to analyze for PII",
        min_length=1,
        max_length=100000,
        examples=["Patient John Smith (DOB: 03/15/1985) was admitted on 01/10/2024."]
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0-1) to include an entity"
    )


class DetectedEntity(BaseModel):
    """A detected PII entity."""
    entity_type: str = Field(..., description="Type of PII (NAME, DATE, SSN, etc.)")
    text: str = Field(..., description="The detected PII text")
    start: int = Field(..., description="Start character position")
    end: int = Field(..., description="End character position")
    confidence: float = Field(..., description="Confidence score (0-1)")


class DetectResponse(BaseModel):
    """Response from PII detection."""
    entities: List[DetectedEntity] = Field(
        default_factory=list,
        description="List of detected PII entities"
    )
    entity_count: int = Field(..., description="Total number of entities detected")
    text_length: int = Field(..., description="Length of input text")


class DeidentifyRequest(BaseModel):
    """Request body for text de-identification."""
    text: str = Field(
        ...,
        description="Clinical text to de-identify",
        min_length=1,
        max_length=100000,
        examples=["Patient John Smith (DOB: 03/15/1985, MRN: 123456789) was admitted."]
    )
    strategy: ReplacementStrategyEnum = Field(
        default=ReplacementStrategyEnum.placeholder,
        description="Replacement strategy: placeholder, consistent, redact, or hash"
    )
    entity_types: Optional[List[str]] = Field(
        default=None,
        description="Only replace these entity types (e.g., ['NAME', 'SSN']). None = all types."
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score (0-1) to include an entity"
    )


class DeidentifyResponse(BaseModel):
    """Response from text de-identification."""
    deidentified_text: str = Field(..., description="De-identified text with PII replaced")
    entities_found: List[DetectedEntity] = Field(
        default_factory=list,
        description="List of detected PII entities"
    )
    replacements_made: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of original text to replacement"
    )
    entity_count: int = Field(..., description="Total number of entities replaced")


class BatchRequest(BaseModel):
    """Request body for batch processing."""
    texts: List[str] = Field(
        ...,
        description="List of texts to process",
        min_length=1,
        max_length=100
    )
    strategy: ReplacementStrategyEnum = Field(
        default=ReplacementStrategyEnum.placeholder,
        description="Replacement strategy"
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score"
    )


class BatchResult(BaseModel):
    """Result for a single text in batch processing."""
    original_text: str
    deidentified_text: str
    entity_count: int


class BatchResponse(BaseModel):
    """Response from batch processing."""
    results: List[BatchResult]
    total_entities: int
    documents_processed: int


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(default="healthy")
    model_loaded: bool
    model_name: str
    version: str


class EntityTypeInfo(BaseModel):
    """Information about an entity type."""
    name: str
    description: str
    examples: List[str]
    replacement: str


class EntitiesResponse(BaseModel):
    """Response listing supported entity types."""
    entity_types: List[EntityTypeInfo]
    total_types: int


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: Optional[str] = None
    status_code: int
