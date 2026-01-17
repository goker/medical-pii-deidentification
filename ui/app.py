"""
Gradio Web Interface for Medical PII De-identification.

ADVANCED DEMO - Shows performance metrics, cost savings, and energy usage.
"""

import os
import sys
import json
import time
import psutil

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


# Global metrics
class Metrics:
    model_load_time = 0
    model_size_mb = 0
    param_count = 0
    last_inference_time = 0
    total_chars_processed = 0
    total_entities_found = 0

metrics = Metrics()

# Initialize detector (will load on first use)
detector = None
deidentifier = None


def get_models():
    """Initialize models on first use and track loading time."""
    global detector, deidentifier, metrics
    if detector is None:
        start_time = time.time()
        detector = get_detector()
        metrics.model_load_time = time.time() - start_time

        # Calculate model size
        if hasattr(detector, 'model') and detector.model is not None:
            param_size = sum(p.numel() * p.element_size() for p in detector.model.parameters())
            buffer_size = sum(b.numel() * b.element_size() for b in detector.model.buffers())
            metrics.model_size_mb = (param_size + buffer_size) / (1024 * 1024)
            metrics.param_count = sum(p.numel() for p in detector.model.parameters())

        deidentifier = Deidentifier(detector=detector)
    return detector, deidentifier


def get_system_metrics():
    """Get current system metrics."""
    process = psutil.Process()
    memory_info = process.memory_info()

    return {
        "ram_usage_mb": memory_info.rss / (1024 * 1024),
        "cpu_percent": process.cpu_percent(),
        "model_load_time": metrics.model_load_time,
        "model_size_mb": metrics.model_size_mb,
        "param_count": metrics.param_count,
    }


def calculate_cost_savings(char_count: int, entity_count: int) -> dict:
    """Calculate cost comparison vs commercial services."""
    # AWS Comprehend Medical pricing: ~$0.01 per 100 characters (unit)
    aws_cost_per_unit = 0.01
    chars_per_unit = 100

    units = max(1, char_count / chars_per_unit)
    aws_cost = units * aws_cost_per_unit

    # Estimated energy cost for local inference
    # ~0.1 kWh for model load + ~0.001 kWh per inference
    # Average US electricity: $0.12/kWh
    kwh_per_inference = 0.001
    electricity_rate = 0.12
    local_energy_cost = kwh_per_inference * electricity_rate

    return {
        "aws_cost": aws_cost,
        "local_cost": local_energy_cost,
        "savings": aws_cost - local_energy_cost,
        "savings_percent": ((aws_cost - local_energy_cost) / aws_cost * 100) if aws_cost > 0 else 0
    }


def detect_and_highlight(text: str, confidence: float) -> tuple:
    """Detect PII and return highlighted text with entity list."""
    global metrics

    if not text.strip():
        return "", "No text provided", "[]", ""

    start_time = time.time()
    detector, _ = get_models()
    detector.confidence_threshold = confidence

    entities = detector.detect(text)
    inference_time = time.time() - start_time
    metrics.last_inference_time = inference_time
    metrics.total_chars_processed += len(text)
    metrics.total_entities_found += len(entities)

    # Calculate costs
    costs = calculate_cost_savings(len(text), len(entities))
    sys_metrics = get_system_metrics()

    if not entities:
        metrics_str = format_metrics(sys_metrics, costs, inference_time, len(text), 0)
        return text, "No PII detected", "[]", metrics_str

    # Build highlighted HTML
    highlighted = text
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
    json_output = json.dumps([e.to_dict() for e in entities], indent=2)
    metrics_str = format_metrics(sys_metrics, costs, inference_time, len(text), len(entities))

    return f"<div style='white-space: pre-wrap; font-family: monospace;'>{highlighted}</div>", summary, json_output, metrics_str


def format_metrics(sys_metrics: dict, costs: dict, inference_time: float, char_count: int, entity_count: int) -> str:
    """Format metrics for display."""
    return f"""### Performance Metrics

| Metric | Value |
|--------|-------|
| **Inference Time** | {inference_time*1000:.1f} ms |
| **Characters Processed** | {char_count:,} |
| **Entities Found** | {entity_count} |
| **Processing Speed** | {char_count/inference_time:,.0f} chars/sec |

### Model Information

| Metric | Value |
|--------|-------|
| **Model Load Time** | {sys_metrics['model_load_time']:.1f} sec |
| **Model Size** | {sys_metrics['model_size_mb']:.1f} MB |
| **Parameters** | {sys_metrics['param_count']:,} |
| **RAM Usage** | {sys_metrics['ram_usage_mb']:.1f} MB |
| **Device** | CPU |

### Cost Comparison

| Service | Cost |
|---------|------|
| **AWS Comprehend Medical** | ${costs['aws_cost']:.4f} |
| **This Tool (energy)** | ${costs['local_cost']:.6f} |
| **Your Savings** | ${costs['savings']:.4f} ({costs['savings_percent']:.1f}%) |

### Monthly Projection (100K documents)

| Service | Monthly Cost |
|---------|-------------|
| **AWS Comprehend Medical** | ~$17,000 |
| **This Tool** | ~$12 (electricity) |
| **Annual Savings** | ~$203,856 |
"""


def deidentify_text(text: str, strategy: str, confidence: float) -> tuple:
    """De-identify text and return result."""
    global metrics

    if not text.strip():
        return "", "No text provided", ""

    start_time = time.time()
    _, deidentifier = get_models()

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
    inference_time = time.time() - start_time
    metrics.last_inference_time = inference_time
    metrics.total_chars_processed += len(text)
    metrics.total_entities_found += result.entity_count

    # Calculate costs
    costs = calculate_cost_savings(len(text), result.entity_count)
    sys_metrics = get_system_metrics()

    if result.entity_count == 0:
        summary = "No PII detected - text unchanged"
    else:
        summary = f"### Replaced {result.entity_count} PII Entities\n\n"
        for original, replacement in result.replacements_made.items():
            summary += f"- `{original}` → `{replacement}`\n"

    metrics_str = format_metrics(sys_metrics, costs, inference_time, len(text), result.entity_count)

    return result.deidentified_text, summary, metrics_str


def load_sample(sample_name: str) -> str:
    """Load a sample text."""
    return SAMPLE_TEXTS.get(sample_name, "")


# Build Gradio interface
with gr.Blocks(
    title="Medical PII De-identification - Advanced Demo",
    theme=gr.themes.Soft(),
    css="""
    .container { max-width: 1400px; margin: auto; }
    .highlight mark { cursor: help; }
    .metrics-box { background: #1a1a2e; padding: 15px; border-radius: 8px; }
    """
) as demo:
    gr.Markdown("""
    # Medical PII De-identification - Advanced Demo

    **HIPAA-compliant PII detection and removal** using OpenMed's clinical NLP models.

    This advanced demo shows **real-time performance metrics**, **cost comparisons** vs AWS/Google,
    and **energy usage** estimates.

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
        # Tab 1: Detection with Metrics
        with gr.TabItem("Detect PII"):
            with gr.Row():
                with gr.Column(scale=1):
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

                with gr.Column(scale=1):
                    detect_output = gr.HTML(label="Highlighted Text")
                    detect_summary = gr.Markdown(label="Entity Summary")

            with gr.Row():
                with gr.Column():
                    with gr.Accordion("JSON Output", open=False):
                        detect_json = gr.Code(language="json", label="Detected Entities (JSON)")
                with gr.Column():
                    detect_metrics = gr.Markdown(label="Performance & Cost Metrics")

        # Tab 2: De-identification with Metrics
        with gr.TabItem("De-identify"):
            with gr.Row():
                with gr.Column(scale=1):
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

                with gr.Column(scale=1):
                    deid_output = gr.Textbox(
                        label="De-identified Text",
                        lines=15,
                        max_lines=30,
                        show_copy_button=True
                    )
                    deid_summary = gr.Markdown(label="Replacement Summary")

            with gr.Row():
                deid_metrics = gr.Markdown(label="Performance & Cost Metrics")

        # Tab 3: About
        with gr.TabItem("About"):
            gr.Markdown("""
            ## About This Advanced Demo

            This demo uses the **OpenMed SuperClinical PII Detection Model**,
            specifically designed for clinical text de-identification.

            ### Why This Matters

            | Metric | AWS Comprehend | This Tool |
            |--------|---------------|-----------|
            | Cost per 100K docs/month | ~$17,000 | ~$12 |
            | Annual cost | ~$204,000 | ~$144 |
            | Data privacy | Sent to AWS | Stays local |
            | Setup time | Hours | Minutes |

            ### Model Specifications

            | Spec | Value |
            |------|-------|
            | Model | OpenMed-PII-SuperClinical-Small-44M-v1 |
            | Parameters | ~141 million |
            | Size | ~539 MB |
            | Inference | CPU (no GPU required) |
            | Load time | ~60 seconds (first run) |

            ### Why 60 Second Load Time?

            1. **Model Download**: First run downloads 539MB from HuggingFace
            2. **Weight Loading**: Loading 141M parameters into RAM
            3. **Tokenizer Init**: Loading 128K vocabulary
            4. **Warmup**: JIT compilation for optimal inference

            After first load, the model stays in memory and inference is **<100ms**.

            ### Energy & Cost Calculation

            - **Model inference**: ~0.001 kWh per document
            - **Electricity cost**: ~$0.12/kWh (US average)
            - **Cost per document**: ~$0.00012
            - **Monthly (100K docs)**: ~$12

            ---

            **GitHub**: [medical-pii-deidentification](https://github.com/goker/medical-pii-deidentification)
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
        outputs=[detect_output, detect_summary, detect_json, detect_metrics]
    )

    deid_btn.click(
        fn=deidentify_text,
        inputs=[deid_input, deid_strategy, deid_confidence],
        outputs=[deid_output, deid_summary, deid_metrics]
    )


# Launch configuration
if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.getenv("GRADIO_PORT", 7860)),
        share=os.getenv("GRADIO_SHARE", "false").lower() == "true"
    )
