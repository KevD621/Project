# Sandbox Project
# PhishSandbox – Automated Phishing Link Analysis with Ephemeral Isolation

**PhishSandbox** is a defensive cybersecurity tool that allows employees or analysts to safely verify suspicious URLs without risking the host system. It launches an isolated, ephemeral Docker container that opens the link in a headless browser, captures forensic evidence (screenshots, redirect chains, fake credential submissions), then automatically determines whether the link is safe, suspicious, or malicious – all in under 30 seconds.

## Why This Exists

Phishing remains the top initial access vector. Traditional link scanners often leak the user’s IP or environment, while manual investigation is slow and risky. PhishSandbox:

- **Completely isolates** browsing from the host (no shared filesystem, no network access to internal resources).
- **Destroys the container** after each analysis, leaving zero forensic trace on the user’s machine.
- **Provides immediate, evidence-backed verdicts** without exposing the user to live threats.

## Key Features

- **One‑click analysis** – Submit any URL via a REST API; receive a verdict in seconds.
- **Ephemeral browser sandbox** – Playwright + Chromium inside a read‑only, capability‑dropped Docker container.
- **Automated credential submission** – Fills fake credentials into detected login forms and records POST destinations (useful for tracking credential harvesters).
- **Multi‑factor detection engine**:
  - **Threat intelligence** – Real‑time PhishTank lookups.
  - **Lexical heuristics** – Typosquatting, IP‑as‑domain, excessive subdomains.
  - **Brand spoofing** – Perceptual hash comparison of screenshots against known brand logos.
  - **Redirect & form mismatch** – Flags when a login form appears on a different domain than the original link.
- **Structured JSON reports** – Ready for SIEM/SOAR ingestion, with indicators, reasons, and raw sandbox data.

## Technology Stack

| Layer            | Technology                          |
|------------------|-------------------------------------|
| API              | Flask (Python)                      |
| Containerisation | Docker + `docker-py`                |
| Browser Automation | Playwright (Node.js, headless Chromium) |
| Image Analysis   | Pillow, imagehash (perceptual hashing) |
| Threat Intel     | PhishTank API (free)                |

## Quick Start

```bash
# 1. Clone and enter the project
git clone <your-repo-url>
cd phish-sandbox

# 2. Set up Python environment
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 3. Add known brand logos to known_brands/ (optional for brand detection)
# 4. Add your free PhishTank API key in config.py (optional for intel checks)

# 5. Build sandbox image and start the API
python api.py

# 6. Test with a URL
curl -X POST http://localhost:5000/check \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example-phish.com/login"}'
