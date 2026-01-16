"""
HIPAA 18 Identifiers and Entity Type Definitions

The HIPAA Privacy Rule identifies 18 types of information that are considered
Protected Health Information (PHI) when linked to health information.
"""

from enum import Enum
from typing import Dict, List


class EntityType(str, Enum):
    """HIPAA Safe Harbor De-identification - 18 Identifiers"""

    # Direct Identifiers
    NAME = "NAME"                    # Names
    DATE = "DATE"                    # Dates (except year) related to individual
    PHONE = "PHONE"                  # Telephone numbers
    FAX = "FAX"                      # Fax numbers
    EMAIL = "EMAIL"                  # Email addresses
    SSN = "SSN"                      # Social Security numbers
    MRN = "MRN"                      # Medical record numbers
    ACCOUNT = "ACCOUNT"              # Account numbers
    LICENSE = "LICENSE"              # Certificate/license numbers
    VEHICLE = "VEHICLE"              # Vehicle identifiers and serial numbers
    DEVICE = "DEVICE"                # Device identifiers and serial numbers
    URL = "URL"                      # Web URLs
    IP = "IP"                        # IP addresses
    BIOMETRIC = "BIOMETRIC"          # Biometric identifiers
    PHOTO = "PHOTO"                  # Full-face photographs
    AGE = "AGE"                      # Ages over 89
    LOCATION = "LOCATION"            # Geographic data (address, city, zip)
    OTHER_ID = "OTHER_ID"            # Any other unique identifying number

    # Additional clinical entities
    PROVIDER = "PROVIDER"            # Healthcare provider names
    ORGANIZATION = "ORGANIZATION"    # Hospital/clinic names
    PATIENT_ID = "PATIENT_ID"        # Patient identifiers


# Mapping from model labels to our entity types
MODEL_LABEL_MAPPING: Dict[str, EntityType] = {
    # Common model output labels -> HIPAA entities
    "B-NAME": EntityType.NAME,
    "I-NAME": EntityType.NAME,
    "B-DATE": EntityType.DATE,
    "I-DATE": EntityType.DATE,
    "B-PHONE": EntityType.PHONE,
    "I-PHONE": EntityType.PHONE,
    "B-EMAIL": EntityType.EMAIL,
    "I-EMAIL": EntityType.EMAIL,
    "B-SSN": EntityType.SSN,
    "I-SSN": EntityType.SSN,
    "B-ID": EntityType.MRN,
    "I-ID": EntityType.MRN,
    "B-MEDICALRECORD": EntityType.MRN,
    "I-MEDICALRECORD": EntityType.MRN,
    "B-IDNUM": EntityType.OTHER_ID,
    "I-IDNUM": EntityType.OTHER_ID,
    "B-LOCATION": EntityType.LOCATION,
    "I-LOCATION": EntityType.LOCATION,
    "B-ADDRESS": EntityType.LOCATION,
    "I-ADDRESS": EntityType.LOCATION,
    "B-CITY": EntityType.LOCATION,
    "I-CITY": EntityType.LOCATION,
    "B-STATE": EntityType.LOCATION,
    "I-STATE": EntityType.LOCATION,
    "B-ZIP": EntityType.LOCATION,
    "I-ZIP": EntityType.LOCATION,
    "B-COUNTRY": EntityType.LOCATION,
    "I-COUNTRY": EntityType.LOCATION,
    "B-HOSPITAL": EntityType.ORGANIZATION,
    "I-HOSPITAL": EntityType.ORGANIZATION,
    "B-ORGANIZATION": EntityType.ORGANIZATION,
    "I-ORGANIZATION": EntityType.ORGANIZATION,
    "B-DOCTOR": EntityType.PROVIDER,
    "I-DOCTOR": EntityType.PROVIDER,
    "B-PATIENT": EntityType.NAME,
    "I-PATIENT": EntityType.NAME,
    "B-USERNAME": EntityType.OTHER_ID,
    "I-USERNAME": EntityType.OTHER_ID,
    "B-URL": EntityType.URL,
    "I-URL": EntityType.URL,
    "B-IP": EntityType.IP,
    "I-IP": EntityType.IP,
    "B-AGE": EntityType.AGE,
    "I-AGE": EntityType.AGE,
    "B-DEVICE": EntityType.DEVICE,
    "I-DEVICE": EntityType.DEVICE,
    "B-FAX": EntityType.FAX,
    "I-FAX": EntityType.FAX,
    "B-LICENSE": EntityType.LICENSE,
    "I-LICENSE": EntityType.LICENSE,
    "B-ACCOUNT": EntityType.ACCOUNT,
    "I-ACCOUNT": EntityType.ACCOUNT,
    "B-VEHICLE": EntityType.VEHICLE,
    "I-VEHICLE": EntityType.VEHICLE,
    "B-BIOMETRIC": EntityType.BIOMETRIC,
    "I-BIOMETRIC": EntityType.BIOMETRIC,
}


# Entity descriptions for documentation
HIPAA_ENTITIES: Dict[EntityType, Dict] = {
    EntityType.NAME: {
        "description": "Names of patients, doctors, and other individuals",
        "examples": ["John Smith", "Dr. Sarah Johnson", "Jane Doe"],
        "replacement": "[NAME]"
    },
    EntityType.DATE: {
        "description": "Dates related to an individual (birth, admission, discharge, death)",
        "examples": ["03/15/1985", "January 10, 2024", "1985-03-15"],
        "replacement": "[DATE]"
    },
    EntityType.PHONE: {
        "description": "Telephone numbers",
        "examples": ["555-123-4567", "(555) 123-4567", "+1-555-123-4567"],
        "replacement": "[PHONE]"
    },
    EntityType.FAX: {
        "description": "Fax numbers",
        "examples": ["555-123-4568 (fax)", "Fax: 555-123-4568"],
        "replacement": "[FAX]"
    },
    EntityType.EMAIL: {
        "description": "Email addresses",
        "examples": ["john.smith@email.com", "patient@hospital.org"],
        "replacement": "[EMAIL]"
    },
    EntityType.SSN: {
        "description": "Social Security numbers",
        "examples": ["123-45-6789", "123456789"],
        "replacement": "[SSN]"
    },
    EntityType.MRN: {
        "description": "Medical record numbers",
        "examples": ["MRN: 123456789", "Patient ID: ABC123"],
        "replacement": "[MRN]"
    },
    EntityType.ACCOUNT: {
        "description": "Health plan beneficiary numbers and account numbers",
        "examples": ["Account #: 12345", "Policy: HMO-123456"],
        "replacement": "[ACCOUNT]"
    },
    EntityType.LICENSE: {
        "description": "Certificate/license numbers (medical, driver's)",
        "examples": ["License: D1234567", "NPI: 1234567890"],
        "replacement": "[LICENSE]"
    },
    EntityType.VEHICLE: {
        "description": "Vehicle identifiers including license plates",
        "examples": ["VIN: 1HGCM82633A123456", "Plate: ABC-1234"],
        "replacement": "[VEHICLE]"
    },
    EntityType.DEVICE: {
        "description": "Device identifiers and serial numbers",
        "examples": ["Pacemaker SN: 12345", "Implant ID: ABC123"],
        "replacement": "[DEVICE]"
    },
    EntityType.URL: {
        "description": "Web Universal Resource Locators (URLs)",
        "examples": ["https://patient-portal.example.com", "www.hospital.org/patient/123"],
        "replacement": "[URL]"
    },
    EntityType.IP: {
        "description": "Internet Protocol (IP) addresses",
        "examples": ["192.168.1.1", "10.0.0.1"],
        "replacement": "[IP]"
    },
    EntityType.BIOMETRIC: {
        "description": "Biometric identifiers (fingerprints, retinal scans, voice prints)",
        "examples": ["Fingerprint ID: FP-12345", "Voice signature verified"],
        "replacement": "[BIOMETRIC]"
    },
    EntityType.PHOTO: {
        "description": "Full-face photographs and comparable images",
        "examples": ["[Photo attached]", "Patient photo on file"],
        "replacement": "[PHOTO]"
    },
    EntityType.AGE: {
        "description": "Ages over 89 (grouped as 90+)",
        "examples": ["92 years old", "Age: 95"],
        "replacement": "[AGE>89]"
    },
    EntityType.LOCATION: {
        "description": "Geographic subdivisions smaller than a State",
        "examples": ["123 Main St", "Boston, MA 02101", "Memorial Hospital"],
        "replacement": "[LOCATION]"
    },
    EntityType.OTHER_ID: {
        "description": "Any other unique identifying number or code",
        "examples": ["Employee ID: E12345", "Badge #: 9876"],
        "replacement": "[ID]"
    },
    EntityType.PROVIDER: {
        "description": "Healthcare provider names",
        "examples": ["Dr. Smith", "Nurse Johnson"],
        "replacement": "[PROVIDER]"
    },
    EntityType.ORGANIZATION: {
        "description": "Healthcare organization names",
        "examples": ["Memorial Hospital", "City Medical Center"],
        "replacement": "[ORGANIZATION]"
    },
    EntityType.PATIENT_ID: {
        "description": "Patient identifiers",
        "examples": ["Patient #12345", "Case ID: ABC-789"],
        "replacement": "[PATIENT_ID]"
    },
}


def get_replacement_text(entity_type: EntityType) -> str:
    """Get the replacement text for a given entity type."""
    return HIPAA_ENTITIES.get(entity_type, {}).get("replacement", f"[{entity_type.value}]")


def map_model_label(label: str) -> EntityType:
    """Map a model output label to our EntityType enum."""
    return MODEL_LABEL_MAPPING.get(label, EntityType.OTHER_ID)


def get_all_entity_types() -> List[EntityType]:
    """Return all supported entity types."""
    return list(EntityType)
