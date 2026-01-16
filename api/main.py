"""
FastAPI Application for Medical PII De-identification.

HIPAA-compliant PII detection and de-identification API
using OpenMed's clinical NLP models.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi

from .routes import router, get_pii_detector

# Configure logging (no PII in logs!)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle handler - pre-load model for faster first request."""
    logger.info("Starting Medical PII Removal API...")

    # Pre-load model on startup (reduces cold start latency)
    if os.getenv("PRELOAD_MODEL", "true").lower() == "true":
        logger.info("Pre-loading PII detection model...")
        detector = get_pii_detector()
        detector.load_model()
        logger.info("Model loaded successfully")

    yield

    logger.info("Shutting down API...")


# Create FastAPI application
app = FastAPI(
    title="Medical PII De-identification API",
    description="""
## HIPAA-Compliant PII Detection and De-identification

This API provides clinical text de-identification using state-of-the-art
NLP models from the OpenMed project.

### Features
- **Detect**: Find PII entities (names, dates, SSN, MRN, etc.)
- **De-identify**: Replace PII with placeholders, consistent fakes, or redaction
- **Batch Processing**: Handle multiple documents efficiently
- **HIPAA 18 Identifiers**: Full coverage of Safe Harbor requirements

### Supported Entity Types
Names, Dates, Phone/Fax, Email, SSN, MRN, Account Numbers, License Numbers,
Vehicle IDs, Device IDs, URLs, IP Addresses, Biometric IDs, Photos,
Ages over 89, Geographic Locations, and Other Unique IDs.

### Replacement Strategies
- `placeholder`: Generic labels like [NAME], [DATE]
- `consistent`: Same entity → same fake value (for analysis)
- `redact`: Black bars (████████)
- `hash`: Deterministic hash-based pseudonyms

### Security Note
This API does NOT log any input text or detected PII to ensure data privacy.
    """,
    version="1.0.0",
    contact={
        "name": "Medical PII De-identification Project",
        "url": "https://github.com/goker/medical-pii-deidentification",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    lifespan=lifespan
)

# CORS middleware (configure for your deployment)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler (no PII in error responses!)
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {type(exc).__name__}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred. Please try again.",
            "status_code": 500
        }
    )


# Include routes
app.include_router(router, prefix="/api/v1", tags=["PII Detection"])


# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "Medical PII De-identification API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/v1/health"
    }


# Custom OpenAPI schema
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Medical PII De-identification API",
        version="1.0.0",
        description=app.description,
        routes=app.routes,
    )

    # Add security note
    openapi_schema["info"]["x-security-note"] = (
        "This API is designed with privacy in mind. No input text or "
        "detected PII is logged or stored. All processing happens in memory."
    )

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


# For running directly
if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=os.getenv("ENVIRONMENT", "development") == "development"
    )
