# BarberX Legal Tech — Frequently Asked Questions

## General

### What is BarberX Legal Tech?

BarberX Legal Tech is an AI-powered eDiscovery and forensic analysis platform designed for legal professionals. It specializes in processing body-worn camera (BWC) footage, police reports, and legal documents with industry-leading accuracy.

### Who is BarberX designed for?

BarberX is built for:
- **Defense Attorneys** - Analyze evidence and find discrepancies
- **Law Firms** - Streamline eDiscovery workflows
- **Public Defenders** - Process large case volumes efficiently
- **Investigators** - Extract entities and build timelines
- **Compliance Teams** - Maintain chain of custody documentation

### Is BarberX cloud-based or local?

Both! Standard users access BarberX through our secure web platform at [barberx.info](https://barberx.info). Enterprise customers can deploy a fully local, air-gapped installation for maximum privacy and compliance.

---

## Getting Started

### How do I create an account?

1. Visit [barberx.info/register](/register)
2. Enter your email and create a password
3. Verify your email address
4. Start your free trial — no credit card required

### What is included in the free tier?

Free accounts include:
- 5 evidence uploads per month
- Basic transcription and entity extraction
- Standard processing speed
- 7-day data retention
- Email support

### How do I upgrade my account?

Visit [Pricing](/pricing) to compare plans. Professional, Premium, and Enterprise tiers unlock unlimited uploads, faster processing, API access, and priority support.

---

## Features & Capabilities

### What file formats does BarberX support?

**Video:** MP4, MOV, AVI, MKV, WEBM  
**Audio:** MP3, WAV, M4A, FLAC, OGG  
**Documents:** PDF, DOCX, DOC, TXT, RTF  
**Images:** JPG, PNG, TIFF, BMP, HEIC  
**Data:** CSV, JSON, XML

### How accurate is the transcription?

BarberX uses Whisper AI for transcription, achieving **99%+ accuracy** on clear audio. Accuracy may vary with background noise, overlapping speech, or poor recording quality. All transcripts include confidence scores.

### What is speaker diarization?

Speaker diarization automatically identifies **who spoke when** in multi-person recordings. BarberX labels speakers (SPEAKER_00, SPEAKER_01, etc.) and allows you to rename them for clarity in reports.

### What entities does BarberX extract?

Our AI extracts:
- **People:** Names, roles, relationships
- **Organizations:** Companies, agencies, departments
- **Locations:** Addresses, landmarks, jurisdictions
- **Dates & Times:** Timestamps, deadlines, schedules
- **Legal Terms:** Case numbers, statutes, citations
- **Evidence IDs:** Badge numbers, serial numbers, vehicle plates

### What is discrepancy detection?

BarberX compares multiple evidence sources (e.g., BWC footage vs. police report) and flags inconsistencies in:
- Timeline of events
- Quoted statements
- Named individuals
- Described actions

---

## Security & Privacy

### Is my data secure?

Yes. BarberX employs:
- **AES-256 encryption** at rest and in transit
- **SOC 2 Type II** compliance (Enterprise tier)
- **Role-based access control** for team accounts
- **Audit logging** of all user actions
- **Automatic data purging** based on retention policies

### Does BarberX access my files?

BarberX processes files only for the features you use. We never sell, share, or use your data for training AI models. Enterprise customers can deploy fully local installations where data never leaves their network.

### How does chain of custody work?

Every uploaded file receives:
- **SHA-256 hash** for integrity verification
- **Timestamp** of upload and all modifications
- **User attribution** for every action
- **Export-ready custody reports** for court admissibility

---

## Technical

### What are the system requirements for local installation?

**Minimum:**
- Windows 10/11, macOS 11+, or Linux (Ubuntu 20.04+)
- Python 3.8+
- 8GB RAM
- 50GB free disk space

**Recommended:**
- 16GB+ RAM
- NVIDIA GPU with CUDA support
- SSD storage

### How do I install local AI tools?

See our [Installation Guide](/docs/installation/) for step-by-step instructions, or run:

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Does BarberX require an internet connection?

The web platform requires internet access. Enterprise local installations can operate fully offline (air-gapped) after initial setup.

### Is there an API?

Yes! Professional, Premium, and Enterprise tiers include REST API access. See our [API Reference](/api) for documentation.

---

## Billing & Support

### What payment methods do you accept?

We accept all major credit cards (Visa, Mastercard, American Express, Discover) and ACH bank transfers for annual Enterprise contracts.

### Can I cancel anytime?

Yes. Monthly subscriptions can be canceled at any time with no penalty. You will retain access until the end of your billing period.

### How do I get support?

- **Email:** support@barberx.info
- **In-app chat:** Available for Professional+ tiers
- **Phone:** Enterprise customers only
- **Documentation:** [docs.barberx.info](/docs/)

### Do you offer training?

Yes! Enterprise customers receive onboarding training. We also offer webinars and video tutorials for all users.

---

*Have a question not answered here? [Contact us](/contact) or email support@barberx.info.*
