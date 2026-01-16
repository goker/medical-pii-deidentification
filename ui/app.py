"""
Gradio Web Interface for Medical PII De-identification.

Interactive demo showcasing HIPAA-compliant PII detection and removal.
"""

import os
import sys
import json

import gradio as gr

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pii_detector import PIIDetector, get_detector
from src.deidentify import Deidentifier, ReplacementStrategy
from src.entities import EntityType, HIPAA_ENTITIES

# Sample clinical notes for demonstration
SAMPLE_TEXTS = {
    "Discharge Summary": """DISCHARGE SUMMARY

Patient: John Michael Smith
DOB: March 15, 1985
MRN: 123456789
SSN: 123-45-6789

Date of Admission: January 10, 2024
Date of Discharge: January 15, 2024

Attending Physician: Dr. Sarah Elizabeth Johnson, MD
Department: Internal Medicine
Hospital: Memorial General Hospital
Address: 123 Medical Center Drive, Boston, MA 02101

Contact Information:
Phone: (555) 123-4567
Fax: (555) 123-4568
Email: john.smith@personalmail.com

CHIEF COMPLAINT:
Patient presented with chest pain and shortness of breath.

HOSPITAL COURSE:
The patient was admitted for observation and cardiac workup.
EKG showed normal sinus rhythm. Troponins were negative x3.
Patient was started on aspirin 81mg daily.

DISCHARGE MEDICATIONS:
1. Aspirin 81mg PO daily
2. Metoprolol 25mg PO BID

FOLLOW-UP:
Patient to follow up with Dr. Johnson at Memorial Cardiology Clinic
Phone: 555-987-6543
Appointment scheduled for January 25, 2024 at 2:00 PM

Electronically signed by:
Sarah E. Johnson, MD
License #: MA12345
NPI: 1234567890""",

    "Clinical Note": """PROGRESS NOTE

Date: 02/14/2024
Time: 14:30

Patient: Mary Patricia Williams
DOB: 07/22/1958 (Age: 65)
MRN: MRN-987654321

Seen today for follow-up of Type 2 Diabetes Mellitus.

Current Medications:
- Metformin 1000mg BID
- Lisinopril 10mg daily

Vitals:
BP: 128/82  HR: 72  Temp: 98.6F  Weight: 165 lbs

Assessment:
Diabetes well-controlled. A1C improved to 6.8%.
Continue current regimen.

Plan:
1. Continue current medications
2. Recheck A1C in 3 months
3. Annual eye exam scheduled with Dr. Robert Chen at
   Boston Eye Associates, 456 Vision Lane, Cambridge MA 02139
   Phone: 617-555-7890

Next Appointment: May 14, 2024

Provider: James Michael Anderson, NP
Email: janderson@clinic.org
Pager: 555-PAGE-001""",

    "Lab Report": """LABORATORY REPORT

Patient Name: Robert James Garcia
Date of Birth: 11/30/1972
Patient ID: PID-2024-00123
Account Number: ACC-789456123

Collection Date: 01/20/2024 08:45 AM
Report Date: 01/20/2024 14:22 PM

Ordering Physician: Dr. Emily Chen
Phone: (555) 234-5678
Fax: (555) 234-5679

COMPLETE BLOOD COUNT (CBC)

WBC: 7.2 K/uL (4.5-11.0)
RBC: 4.8 M/uL (4.5-5.5)
Hemoglobin: 14.2 g/dL (13.5-17.5)
Hematocrit: 42.1% (38.8-50.0)
Platelets: 245 K/uL (150-400)

COMPREHENSIVE METABOLIC PANEL

Glucose: 95 mg/dL (70-100)
BUN: 15 mg/dL (7-20)
Creatinine: 1.0 mg/dL (0.7-1.3)
eGFR: >90 mL/min/1.73m2

Specimen collected at:
City Medical Laboratory
789 Lab Way, Suite 100
San Francisco, CA 94102

Results reviewed and approved by:
Lisa Marie Thompson, MD, PhD
Laboratory Director
NPI: 9876543210"""
}


# Initialize detector (will load on first use)
detector = None
deidentifier = None


def get_models():
    """Initialize models on first use."""
    global detector, deidentifier
    if detector is None:
        detector = get_detector()
        deidentifier = Deidentifier(detector=detector)
    return detector, deidentifier


def detect_and_highlight(text: str, confidence: float) -> tuple:
    """Detect PII and return highlighted text with entity list."""
    if not text.strip():
        return "", "No text provided", "[]"

    detector, _ = get_models()
    detector.confidence_threshold = confidence

    entities = detector.detect(text)

    if not entities:
        return text, "No PII detected", "[]"

    # Build highlighted HTML
    highlighted = text
    # Sort by position (reverse) for replacement
    sorted_entities = sorted(entities, key=lambda e: e.start, reverse=True)

    colors = {
        EntityType.NAME: "#ff6b6b",
        EntityType.DATE: "#4ecdc4",
        EntityType.PHONE: "#45b7d1",
        EntityType.EMAIL: "#96ceb4",
        EntityType.SSN: "#ff8c42",
        EntityType.MRN: "#a8e6cf",
        EntityType.LOCATION: "#dda0dd",
        EntityType.LICENSE: "#f7dc6f",
        EntityType.PROVIDER: "#bb8fce",
        EntityType.ORGANIZATION: "#85c1e9",
    }

    for entity in sorted_entities:
        color = colors.get(entity.entity_type, "#ffeaa7")
        highlighted = (
            highlighted[:entity.start] +
            f'<mark style="background-color: {color}; padding: 2px 4px; border-radius: 3px;" '
            f'title="{entity.entity_type.value}: {entity.confidence:.2%}">{entity.text}</mark>' +
            highlighted[entity.end:]
        )

    # Build entity summary
    entity_summary = []
    for entity in entities:
        entity_summary.append(
            f"- **{entity.entity_type.value}**: `{entity.text}` "
            f"(confidence: {entity.confidence:.2%})"
        )

    summary = f"### Found {len(entities)} PII Entities\n\n" + "\n".join(entity_summary)

    # JSON output
    json_output = json.dumps([e.to_dict() for e in entities], indent=2)

    return f"<div style='white-space: pre-wrap; font-family: monospace;'>{highlighted}</div>", summary, json_output


def deidentify_text(text: str, strategy: str, confidence: float) -> tuple:
    """De-identify text and return result."""
    if not text.strip():
        return "", "No text provided"

    _, deidentifier = get_models()

    # Map strategy
    strategy_map = {
        "Placeholder [NAME]": ReplacementStrategy.PLACEHOLDER,
        "Consistent Fakes": ReplacementStrategy.CONSISTENT,
        "Redact (████)": ReplacementStrategy.REDACT,
        "Hash-based": ReplacementStrategy.HASH,
    }
    strat = strategy_map.get(strategy, ReplacementStrategy.PLACEHOLDER)

    deidentifier.strategy = strat
    deidentifier.detector.confidence_threshold = confidence

    if strat == ReplacementStrategy.CONSISTENT:
        deidentifier.reset_mappings()

    result = deidentifier.deidentify(text)

    # Build summary
    if result.entity_count == 0:
        summary = "No PII detected - text unchanged"
    else:
        summary = f"### Replaced {result.entity_count} PII Entities\n\n"
        for original, replacement in result.replacements_made.items():
            summary += f"- `{original}` → `{replacement}`\n"

    return result.deidentified_text, summary


def load_sample(sample_name: str) -> str:
    """Load a sample text."""
    return SAMPLE_TEXTS.get(sample_name, "")


# Build Gradio interface
with gr.Blocks(
    title="Medical PII De-identification",
    theme=gr.themes.Soft(),
    css="""
    .container { max-width: 1200px; margin: auto; }
    .highlight mark { cursor: help; }
    """
) as demo:
    gr.Markdown("""
    # Medical PII De-identification Demo

    **HIPAA-compliant PII detection and removal** using OpenMed's clinical NLP models.

    This tool detects and removes Protected Health Information (PHI) including:
    Names, Dates, Phone/Fax, Email, SSN, MRN, Locations, and 18+ HIPAA identifiers.

    ---
    """)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Load Sample")
            sample_dropdown = gr.Dropdown(
                choices=list(SAMPLE_TEXTS.keys()),
                label="Select Sample Clinical Note",
                value="Discharge Summary"
            )
            load_btn = gr.Button("Load Sample", variant="secondary")

    with gr.Tabs():
        # Tab 1: Detection
        with gr.TabItem("Detect PII"):
            with gr.Row():
                with gr.Column():
                    detect_input = gr.Textbox(
                        label="Input Clinical Text",
                        placeholder="Paste clinical notes here...",
                        lines=15,
                        max_lines=30
                    )
                    detect_confidence = gr.Slider(
                        minimum=0.1,
                        maximum=0.99,
                        value=0.5,
                        step=0.05,
                        label="Confidence Threshold"
                    )
                    detect_btn = gr.Button("Detect PII", variant="primary")

                with gr.Column():
                    detect_output = gr.HTML(label="Highlighted Text")
                    detect_summary = gr.Markdown(label="Entity Summary")

            with gr.Accordion("JSON Output", open=False):
                detect_json = gr.Code(language="json", label="Detected Entities (JSON)")

        # Tab 2: De-identification
        with gr.TabItem("De-identify"):
            with gr.Row():
                with gr.Column():
                    deid_input = gr.Textbox(
                        label="Input Clinical Text",
                        placeholder="Paste clinical notes here...",
                        lines=15,
                        max_lines=30
                    )
                    deid_strategy = gr.Radio(
                        choices=[
                            "Placeholder [NAME]",
                            "Consistent Fakes",
                            "Redact (████)",
                            "Hash-based"
                        ],
                        value="Placeholder [NAME]",
                        label="Replacement Strategy"
                    )
                    deid_confidence = gr.Slider(
                        minimum=0.1,
                        maximum=0.99,
                        value=0.5,
                        step=0.05,
                        label="Confidence Threshold"
                    )
                    deid_btn = gr.Button("De-identify Text", variant="primary")

                with gr.Column():
                    deid_output = gr.Textbox(
                        label="De-identified Text",
                        lines=15,
                        max_lines=30,
                        show_copy_button=True
                    )
                    deid_summary = gr.Markdown(label="Replacement Summary")

        # Tab 3: About
        with gr.TabItem("About"):
            gr.Markdown("""
            ## About This Tool

            This demo uses the **OpenMed SuperClinical PII Detection Model** (44M parameters),
            specifically designed for clinical text de-identification.

            ### HIPAA Safe Harbor - 18 Identifiers

            | Category | Examples |
            |----------|----------|
            | Names | Patient names, Doctor names |
            | Dates | DOB, Admission dates, Appointment dates |
            | Contact | Phone, Fax, Email |
            | IDs | SSN, MRN, Account numbers, License numbers |
            | Location | Addresses, City, State, ZIP |
            | Other | URLs, IP addresses, Device IDs |

            ### Replacement Strategies

            - **Placeholder**: Generic labels like `[NAME]`, `[DATE]`
            - **Consistent Fakes**: Same entity → same fake value (useful for analysis)
            - **Redact**: Black bars `████████`
            - **Hash-based**: Deterministic pseudonyms `[NAME_a1b2c3d4]`

            ### Model Information

            - **Model**: OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1
            - **Architecture**: Transformer (BERT-based)
            - **Parameters**: 44 million
            - **Optimized for**: Clinical discharge notes, progress notes, lab reports

            ### Privacy Notice

            This demo processes text **in-memory only**. No data is logged or stored.
            For production use, deploy on your own infrastructure.

            ---

            **GitHub**: [medical-pii-removal](https://github.com/yourusername/medical-pii-removal)
            """)

    # Event handlers
    load_btn.click(
        fn=load_sample,
        inputs=[sample_dropdown],
        outputs=[detect_input]
    ).then(
        fn=load_sample,
        inputs=[sample_dropdown],
        outputs=[deid_input]
    )

    detect_btn.click(
        fn=detect_and_highlight,
        inputs=[detect_input, detect_confidence],
        outputs=[detect_output, detect_summary, detect_json]
    )

    deid_btn.click(
        fn=deidentify_text,
        inputs=[deid_input, deid_strategy, deid_confidence],
        outputs=[deid_output, deid_summary]
    )


# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_PORT", 7860)),
        share=os.getenv("GRADIO_SHARE", "false").lower() == "true"
    )
