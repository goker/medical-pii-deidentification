# HIPAA Compliance Notes

This document outlines how this tool supports HIPAA compliance for de-identification of Protected Health Information (PHI).

## HIPAA Safe Harbor Method

The HIPAA Privacy Rule provides two methods for de-identification:

1. **Expert Determination** (§164.514(b)(1)) - Statistical/scientific assessment
2. **Safe Harbor** (§164.514(b)(2)) - Removal of 18 specific identifiers

**This tool implements the Safe Harbor method.**

---

## 18 HIPAA Identifiers

The Safe Harbor method requires removal of the following identifiers:

| # | Identifier | This Tool |
|---|------------|-----------|
| 1 | Names | ✅ NAME entity |
| 2 | Geographic data smaller than State | ✅ LOCATION entity |
| 3 | Dates (except year) | ✅ DATE entity |
| 4 | Phone numbers | ✅ PHONE entity |
| 5 | Fax numbers | ✅ FAX entity |
| 6 | Email addresses | ✅ EMAIL entity |
| 7 | Social Security numbers | ✅ SSN entity |
| 8 | Medical record numbers | ✅ MRN entity |
| 9 | Health plan beneficiary numbers | ✅ ACCOUNT entity |
| 10 | Account numbers | ✅ ACCOUNT entity |
| 11 | Certificate/license numbers | ✅ LICENSE entity |
| 12 | Vehicle identifiers | ✅ VEHICLE entity |
| 13 | Device identifiers/serial numbers | ✅ DEVICE entity |
| 14 | Web URLs | ✅ URL entity |
| 15 | IP addresses | ✅ IP entity |
| 16 | Biometric identifiers | ✅ BIOMETRIC entity |
| 17 | Full-face photographs | ⚠️ Flagged as PHOTO |
| 18 | Any other unique identifier | ✅ OTHER_ID entity |

---

## Important Disclaimers

### This Tool is NOT a Guarantee of Compliance

1. **No tool can guarantee 100% detection** - ML models may miss some identifiers or generate false positives
2. **Human review recommended** - For sensitive use cases, have trained reviewers verify output
3. **Context matters** - Some identifiers require context to detect (e.g., "Memorial Hospital" vs "memorial")
4. **Not a covered entity** - This tool itself is not a HIPAA covered entity

### Recommended Workflow

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  Original   │────▶│ Automated   │────▶│   Human     │────▶│  De-ID'd    │
│    Text     │     │ Detection   │     │   Review    │     │    Text     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

---

## Configuration for Different Risk Levels

### High Sensitivity (Maximum Caution)

```python
# Lower confidence threshold = more entities detected
detector = PIIDetector(confidence_threshold=0.3)

# Use redaction for maximum obscurity
deidentifier = Deidentifier(strategy=ReplacementStrategy.REDACT)
```

### Standard Clinical Use

```python
# Balanced threshold
detector = PIIDetector(confidence_threshold=0.5)

# Placeholder replacement
deidentifier = Deidentifier(strategy=ReplacementStrategy.PLACEHOLDER)
```

### Research/Analysis (Maintain Linkability)

```python
# Higher threshold = fewer false positives
detector = PIIDetector(confidence_threshold=0.7)

# Consistent replacement for entity linking
deidentifier = Deidentifier(strategy=ReplacementStrategy.CONSISTENT)
```

---

## Data Handling Best Practices

### Do

- ✅ Run de-identification on isolated, secure systems
- ✅ Delete original PHI after de-identification
- ✅ Log de-identification actions (not the data itself)
- ✅ Use TLS/HTTPS for API communications
- ✅ Implement access controls
- ✅ Conduct periodic audits

### Don't

- ❌ Log or store input text containing PHI
- ❌ Send PHI to third-party services
- ❌ Store de-identification mappings with PHI
- ❌ Use public/shared compute for PHI processing
- ❌ Assume de-identification equals anonymization

---

## Deployment Considerations

### On-Premises (Recommended for PHI)

For environments with strict PHI handling requirements:

```bash
# Run locally
docker run -p 8000:8000 --network none medical-pii-deidentification
```

Benefits:
- Data never leaves your infrastructure
- Full audit trail
- Meets data residency requirements

### Cloud Deployment

If using cloud services:

1. **AWS**: Consider HIPAA-eligible services, sign BAA
2. **GCP**: Use Healthcare API, sign BAA
3. **Azure**: Use Azure Healthcare APIs, sign BAA

**Important**: Free tiers may not be HIPAA-eligible. Consult your cloud provider.

---

## Audit Trail

For compliance, maintain logs of:

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "deidentify",
  "document_id": "DOC-12345",
  "entities_detected": 15,
  "strategy_used": "placeholder",
  "user_id": "analyst-001",
  "model_version": "OpenMed-PII-SuperClinical-Small-44M-v1"
}
```

**Never log the actual text or detected PII values.**

---

## Related Regulations

This tool may also support compliance with:

- **GDPR** (EU) - Personal data protection
- **CCPA** (California) - Consumer privacy
- **PIPEDA** (Canada) - Personal information protection
- **LGPD** (Brazil) - General data protection

---

## Resources

- [HHS HIPAA De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)
- [NIST De-identification Guidelines](https://csrc.nist.gov/publications/detail/sp/800-188/final)
- [OCR HIPAA FAQs](https://www.hhs.gov/hipaa/for-professionals/faq/index.html)

---

## Legal Notice

**This tool is provided as-is without warranty.** Users are responsible for:

1. Validating de-identification output
2. Ensuring compliance with applicable regulations
3. Implementing appropriate security controls
4. Obtaining necessary legal/compliance review

**Consult with a qualified HIPAA compliance officer before using this tool with real PHI.**
