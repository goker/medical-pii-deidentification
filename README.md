# Medical PII Removal - Local-First, Open Source

**State-of-the-art medical PII detection that runs on any laptop. No cloud required.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![HuggingFace](https://img.shields.io/badge/🤗-OpenMed_Models-orange)](https://huggingface.co/collections/OpenMed/pii-and-de-identification)
[![Local First](https://img.shields.io/badge/Local_First-CPU_Only-green.svg)]()

---

## Why I Built This

OpenMed just released [34 state-of-the-art PII detection models](https://huggingface.co/collections/OpenMed/pii-and-de-identification) - the best open-source medical NER models available.

**But here's the problem:** Most hospitals and clinics can't use them.

- Enterprise PII solutions cost $10,000-$20,000/month
- Cloud APIs require sending patient data to third parties
- ML expertise is needed to deploy transformer models
- Small healthcare facilities are left behind

**My mission:** Make SOTA medical AI accessible to every hospital, clinic, and healthcare developer - regardless of budget or ML expertise.

This tool runs **100% locally** on a basic laptop. Your patient data never leaves your machine. No GPU required. No cloud subscription. No ML knowledge needed.

**Local hospital in rural areas? Small clinic? Medical startup? This is for you.**

---

## The Problem

Companies charge a fortune for medical PII removal:

| Provider | 100K Records/Month |
|----------|-------------------|
| Amazon Comprehend Medical | ~$17,000 |
| Google Healthcare API | Enterprise $$ |
| John Snow Labs | "Contact Sales" |
| Azure Health Services | Per-GB $$ |

**This tool: $0**

---

## What It Does

**Input:**
```
Patient John Smith (DOB: 03/15/1985, MRN: 123456789)
SSN: 123-45-6789, Phone: 555-123-4567
Email: john.smith@email.com
Dr. Sarah Johnson at Memorial Hospital, 123 Main St, Boston MA
```

**Output:**
```
Patient [NAME] (DOB: [DATE], MRN: [MRN])
SSN: [SSN], Phone: [PHONE]
Email: [EMAIL]
Dr. [NAME] at [ORGANIZATION], [LOCATION]
```

**All 18 HIPAA identifiers. Automatically. In milliseconds.**

---

## Deployment Options

Choose your deployment method:

| Option | RAM Needed | Cost | Best For |
|--------|-----------|------|----------|
| **Local (Native)** | 2 GB | $0 | Development, HIPAA-strict environments |
| **Local (Docker)** | 1 GB | $0 | Consistent environments |
| **AWS Lambda** | 1 GB | Free tier | Sporadic usage, serverless |
| **GCP Cloud Run** | 1 GB | Free tier | Auto-scaling, serverless |
| **Azure Container** | 2 GB | Free tier | Azure ecosystem |

---

## Option 1: Local Deployment (Recommended for PHI)

**Data never leaves your machine. Full HIPAA control.**

### Requirements
- **CPU**: 2+ cores (no GPU needed!)
- **RAM**: 2 GB minimum
- **Disk**: 1 GB
- **Python**: 3.9+

### Quick Start (3 Steps)

```bash
# Step 1: Clone
git clone https://github.com/goker/medical-pii-deidentification.git
cd medical-pii-deidentification

# Step 2: Install
pip install -r requirements.txt

# Step 3: Run
python -m ui.app          # Web UI at http://localhost:7860
# OR
uvicorn api.main:app      # API at http://localhost:8000
```

### Docker (Local)

```bash
# Build
docker build -t medical-pii-removal .

# Run with resource limits
docker run -p 8000:8000 --memory="1g" --cpus="1" medical-pii-removal
```

**Performance on CPU:**
| Hardware | Speed |
|----------|-------|
| Apple M1/M2 | 30-50 ms/doc |
| Intel i7 | 50-100 ms/doc |
| Intel i5 | 100-150 ms/doc |

---

## Option 2: Cloud Free Tier Deployment

**Zero cost for 10,000+ documents/month on any provider.**

### AWS Lambda
```bash
./deploy/aws/deploy.sh
```
- **Free tier**: 1M requests/month, 400K GB-seconds
- **Config**: 1 GB RAM, 60s timeout
- **Cold start**: 10-15 seconds

### Google Cloud Run
```bash
./deploy/gcp/deploy.sh
```
- **Free tier**: 2M requests/month, 180K vCPU-seconds
- **Config**: 1 GB RAM, 1 vCPU
- **Cold start**: 8-12 seconds

### Azure Container Apps
```bash
./deploy/azure/deploy.sh
```
- **Free tier**: 2M requests/month, 180K vCPU-seconds
- **Config**: 2 GB RAM, 1 vCPU
- **Cold start**: 10-15 seconds

**All deployments: One command. Free tier eligible. No GPU required.**

See [Resource Requirements](docs/RESOURCE_REQUIREMENTS.md) for detailed specs.

---

## API Usage

### Detect PII
```bash
curl -X POST 'http://localhost:8000/api/v1/detect' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith SSN 123-45-6789"}'
```

### De-identify Text
```bash
curl -X POST 'http://localhost:8000/api/v1/deidentify' \
  -H 'Content-Type: application/json' \
  -d '{"text": "Patient John Smith SSN 123-45-6789"}'
```

**Response:**
```json
{
  "deidentified_text": "Patient [NAME] SSN [SSN]",
  "entity_count": 2
}
```

---

## Replacement Strategies

| Strategy | Example | Use Case |
|----------|---------|----------|
| `placeholder` | `[NAME]`, `[SSN]` | Sharing, reports |
| `consistent` | Same name → same fake | Analysis |
| `redact` | `████████` | Maximum privacy |
| `hash` | `[NAME_a1b2c3d4]` | Pseudonymization |

---

## HIPAA 18 Identifiers ✅

All covered:

- Names ✅
- Dates ✅
- Phone numbers ✅
- Fax numbers ✅
- Email addresses ✅
- Social Security numbers ✅
- Medical record numbers ✅
- Account numbers ✅
- License numbers ✅
- Vehicle identifiers ✅
- Device identifiers ✅
- Web URLs ✅
- IP addresses ✅
- Biometric IDs ✅
- Photos ✅
- Ages over 89 ✅
- Geographic data ✅
- Other unique IDs ✅

---

## The Model

**OpenMed-PII-SuperClinical-Small-44M-v1**

- Parameters: 44 million (runs on CPU, fits in free tier!)
- F1 Score: 95.4% on clinical text
- Precision: 95.5% | Recall: 95.3%
- Entity Types: 54 across 7 categories
- License: Apache 2.0

[View all 33 models](https://huggingface.co/collections/OpenMed/pii-and-de-identification)

---

## The Vision

**Healthcare data protection shouldn't be a luxury only large enterprises can afford.**

Every small clinic deserves the same SOTA AI that big hospital chains use. Every rural healthcare facility should be able to protect patient privacy. Every medical startup should have access to production-grade tools.

This project proves that:
- **SOTA models can run on commodity hardware** - No $10K GPU servers needed
- **Local-first is possible** - PHI never needs to leave your premises
- **Open source can match enterprise** - 95%+ accuracy, zero cost

I want to see this running in:
- Community health centers
- Rural hospitals
- Medical research labs
- Healthcare startups
- Anywhere patient privacy matters

---

## Project Structure

```
medical-pii-deidentification/
├── src/                    # Core library
│   ├── pii_detector.py     # Model inference
│   ├── deidentify.py       # Replacement strategies
│   └── entities.py         # HIPAA definitions
├── api/                    # REST API
│   ├── main.py             # FastAPI app
│   └── routes.py           # Endpoints
├── ui/                     # Web interface
│   └── app.py              # Gradio UI
├── deploy/                 # Cloud scripts
│   ├── aws/                # Lambda
│   ├── gcp/                # Cloud Run
│   └── azure/              # Container Apps
├── examples/               # Usage examples
└── docs/                   # Documentation
```

---

## Resource Requirements

| Resource | Local | Cloud Free Tier |
|----------|-------|-----------------|
| **CPU** | 2+ cores | 1 vCPU |
| **RAM** | 2 GB | 1-2 GB |
| **GPU** | Not needed | Not needed |
| **Disk** | 1 GB | Included |

| Metric | Value |
|--------|-------|
| Model Size | 44M params (~180 MB) |
| Runtime Memory | ~500-600 MB |
| Inference Speed | 30-150 ms/doc (CPU) |
| Cold Start | 5-15 sec |
| F1 Score | 95.4% |

**Key point: Runs on CPU only. No expensive GPU required.**

See [detailed requirements](docs/RESOURCE_REQUIREMENTS.md) for optimization tips.

---

## Privacy & Security

- **No logging** - Input text is never logged
- **Local processing** - Data never leaves your system
- **No external calls** - Model runs entirely locally
- **Open source** - Inspect every line of code

---

## Contributing

PRs welcome! Ideas:

- [ ] More languages (Spanish, French, German)
- [ ] Specialty models (radiology, pathology)
- [ ] VS Code extension
- [ ] Jupyter integration
- [ ] Training pipeline

---

## License

MIT License - use it however you want.

Commercial use? Go ahead.
Modify it? Please do.
Sell products built on it? Sure.

Just give the repo a ⭐ if it helps you.

---

## Links

- **Models**: [OpenMed PII Collection](https://huggingface.co/collections/OpenMed/pii-and-de-identification)
- **API Docs**: [API Reference](docs/API_REFERENCE.md)
- **HIPAA Guide**: [Compliance Notes](docs/HIPAA_COMPLIANCE.md)
- **Resources**: [Resource Requirements](docs/RESOURCE_REQUIREMENTS.md)

---

## Star History

If this helps you, star the repo. It helps others find it.

---

**Built with ❤️ using [OpenMed](https://huggingface.co/OpenMed) models**
