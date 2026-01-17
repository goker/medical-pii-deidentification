# Resource Requirements

This document details the hardware and cloud resources needed to run the Medical PII De-identification tool.

---

## Model Specifications

**Model**: OpenMed-PII-SuperClinical-Small-44M-v1

| Spec | Value |
|------|-------|
| Parameters | 44 million |
| Model Size (disk) | ~180 MB |
| Vocabulary | 30,522 tokens |
| Architecture | BERT-based token classifier |
| Precision | FP32 (can run FP16) |

---

## Local Deployment (Your Machine)

### Minimum Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **CPU** | 2 cores | 4+ cores |
| **RAM** | 2 GB | 4 GB |
| **Disk** | 1 GB | 2 GB |
| **GPU** | Not required | Not required |
| **Python** | 3.9+ | 3.11+ |

### Memory Breakdown

```
Model weights:        ~180 MB
Tokenizer:            ~5 MB
PyTorch runtime:      ~200 MB
Inference overhead:   ~100-200 MB
─────────────────────────────
Total RAM needed:     ~500-600 MB
```

### Performance (CPU-only)

| Hardware | Inference Time | Throughput |
|----------|---------------|------------|
| Apple M1/M2 | 30-50 ms/doc | ~25 docs/sec |
| Intel i7 (10th gen) | 50-100 ms/doc | ~15 docs/sec |
| Intel i5 (8th gen) | 100-150 ms/doc | ~8 docs/sec |
| 2-core VM | 150-300 ms/doc | ~5 docs/sec |

*Document = ~500 characters (typical clinical note paragraph)*

### Local Installation

```bash
# Clone the repo
git clone https://github.com/goker/medical-pii-deidentification.git
cd medical-pii-deidentification

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Run the API
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Or run the Web UI
python -m ui.app
```

### Docker (Local)

```bash
# Build
docker build -t medical-pii-removal .

# Run (API mode)
docker run -p 8000:8000 medical-pii-removal

# Run (UI mode)
docker run -p 7860:7860 -e MODE=ui medical-pii-removal
```

**Docker resource limits:**
```bash
docker run -p 8000:8000 \
  --memory="1g" \
  --cpus="1" \
  medical-pii-removal
```

---

## Cloud Free Tier Deployment

All three major cloud providers offer free tiers that can run this tool.

### AWS Lambda (Free Tier)

| Resource | Free Tier Limit | Our Usage |
|----------|----------------|-----------|
| Requests | 1M/month | Well within |
| Compute | 400,000 GB-sec/month | ~0.1 GB-sec/request |
| Memory | Up to 10 GB | 1 GB configured |
| Storage | 512 MB /tmp | 2 GB ephemeral |

**Configuration:**
```yaml
MemorySize: 1024  # 1 GB RAM
Timeout: 60       # seconds
EphemeralStorage: 2048  # 2 GB for model cache
```

**Cost estimate (beyond free tier):**
- ~$0.0000167 per request
- 100K requests/month = ~$1.67

**Cold start:** 10-15 seconds (model loading)

**Deploy:**
```bash
cd deploy/aws
./deploy.sh
```

---

### Google Cloud Run (Free Tier)

| Resource | Free Tier Limit | Our Usage |
|----------|----------------|-----------|
| Requests | 2M/month | Well within |
| CPU | 180,000 vCPU-sec/month | 1 vCPU per request |
| Memory | 360,000 GB-sec/month | 1 GB per request |
| Networking | 1 GB egress/month | Minimal |

**Configuration:**
```yaml
memory: 1Gi
cpu: 1
timeout: 60s
concurrency: 10
minInstances: 0  # Scale to zero
maxInstances: 5
```

**Cost estimate (beyond free tier):**
- CPU: $0.00002400 per vCPU-second
- Memory: $0.00000250 per GB-second
- ~$0.002 per request

**Cold start:** 8-12 seconds

**Deploy:**
```bash
cd deploy/gcp
./deploy.sh
```

---

### Azure Container Apps (Free Tier)

| Resource | Free Tier Limit | Our Usage |
|----------|----------------|-----------|
| vCPU | 180,000 vCPU-sec/month | 1 vCPU per request |
| Memory | 360,000 GB-sec/month | 2 GB per request |
| Requests | 2M/month | Well within |

**Configuration:**
```json
{
  "cpu": 1,
  "memory": "2Gi"
}
```

**Cost estimate (beyond free tier):**
- ~$0.000024 per vCPU-second
- ~$0.003 per request

**Cold start:** 10-15 seconds

**Deploy:**
```bash
cd deploy/azure
./deploy.sh
```

---

## Comparison Table

| Deployment | RAM | CPU | Cold Start | Cost | Best For |
|------------|-----|-----|------------|------|----------|
| **Local** | 2 GB | 2 cores | 5-10 sec | $0 | Development, HIPAA-strict |
| **Docker** | 1 GB | 1 core | 5-10 sec | $0 | Consistent environments |
| **AWS Lambda** | 1 GB | Auto | 10-15 sec | Free tier | Sporadic usage |
| **GCP Cloud Run** | 1 GB | 1 vCPU | 8-12 sec | Free tier | Scalability |
| **Azure Container** | 2 GB | 1 vCPU | 10-15 sec | Free tier | Azure ecosystem |

---

## Optimization Tips

### Reduce Memory Usage

```python
# Use FP16 (half precision) - reduces memory by ~40%
from src.pii_detector import PIIDetector
detector = PIIDetector(use_fp16=True)
```

### Reduce Cold Start Time

```bash
# Pre-download model before deployment
python -c "from transformers import AutoTokenizer, AutoModelForTokenClassification; \
    AutoModelForTokenClassification.from_pretrained('OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1'); \
    AutoTokenizer.from_pretrained('OpenMed/OpenMed-PII-SuperClinical-Small-44M-v1')"
```

### Batch Processing

```python
# Process multiple documents in one call
texts = ["Patient John Smith...", "Dr. Jane Doe...", ...]
results = detector.detect_batch(texts)  # More efficient
```

---

## Free Tier Limits Summary

| Provider | Requests/Month | Compute/Month | Our Fit |
|----------|---------------|---------------|---------|
| AWS Lambda | 1,000,000 | 400K GB-sec | Excellent |
| GCP Cloud Run | 2,000,000 | 180K vCPU-sec | Excellent |
| Azure Container | 2,000,000 | 180K vCPU-sec | Excellent |

**Bottom line:** You can process **10,000+ documents/month** completely free on any cloud provider.

---

## When to Upgrade

Consider paid tiers when:
- Processing > 50,000 docs/month consistently
- Need < 100ms response times (keep instances warm)
- Require guaranteed uptime SLA
- Need VPC/private networking

---

## Questions?

Open an issue: https://github.com/goker/medical-pii-deidentification/issues
