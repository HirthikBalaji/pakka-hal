# ਪੱਕਾ ਹੱਲ • Pakka Hal
### Verified-Resolution Rails for Chandigarh's Civic Services

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-brightgreen.svg)](https://python.org)
[![Standard](https://img.shields.io/badge/Standard-Open311_GeoReport_v2-orange.svg)](http://wiki.open311.org/GeoReport_v2)
[![DPI](https://img.shields.io/badge/DPI-India_Stack_Aligned-purple.svg)](SPEC.md)
[![GDG](https://img.shields.io/badge/Event-Code_for_Communities_Chandigarh-red.svg)](https://hackculture.io/hackathons/code-for-communities-chandigarh)

> **Pitch Line:** *Every city has a way to complain. None can prove it got fixed.*

---

## 🏛️ The Problem: The Missing Accountability Layer

In May 2025, an official audit rapped the **Chandigarh Municipal Corporation** for keeping no comprehensive record of public grievances received, pending, or forwarded across departments, and flagged missing fixed-asset control registers.

While Chandigarh boasts a state-of-the-art **Integrated Command and Control Centre (ICCC)** under the Smart Cities Mission, existing systems stop at *complaint intake*. Like the global **Open311 GeoReport v2** standard, legacy portals operate on a binary toggle (`open` vs `closed`). They have **zero notion of verified resolution**, allowing tickets to be marked "resolved" without cryptographic proof, geofenced evidence, or citizen validation.

**Pakka Hal does not build another complaint form.** It provides an open-source, Open311-compatible **Verification & Resolution Layer** that sits beside existing municipal portals.

---

## 🚀 Key Architectural Innovations

```
 Citizen PWA (Voice / Photo / Text in Pa/Hi/En) ─┐
 Department Adapters (Email / CSV / Webhook) ────┴─> Open311 Intake API (/requests.json)
                                                                 │
                  ┌──────────────────────────────────────────────┴─────────────────────────────────┐
                  ▼                                                                                ▼
          [Multilingual Triage]                                                          [Emergency Safety Net]
    (Gemma-2:9B / Gemini 1.5 Flash)                                                (Deterministic 112 Redirect)
                  │                                                                                │
                  ▼                                                                                ▼
        [Spatial-Semantic Dedup]                                                             (Never Queued)
    (Haversine + Cosine Sim + Cost Thresholds)
                  │
                  ▼
         [Ownership Router] ──────── (Confidence < 0.70) ────────> [Abstained Human Queue]
                  │
                  ▼
       [Canonical Incident Store] <──── [Closure Verifier] <──── [Field Worker In-App Capture]
                  │                            │                           (Live GPS within 100m)
                  │                            ├── Perceptual Hash (pHash) Anti-Reuse
                  │                            ├── Multimodal Scene Cross-Examination
                  │                            └── 1-Tap Citizen Re-Confirmation Loop
                  ▼
     [SHA-256 Linear Public Ledger]
   (Tamper-evident daily root hashes)
                  │
                  ▼
 [Transparency Dashboard + Wilson 95% CIs] + [Equity Module (Thompson Sampling Bandit)]
```

1. **Multilingual, Code-Mixed Indic Voice Triage:**
   - Understands messy voice notes and text in **Punjabi** (Gurmukhi `pa-Guru` and Latin `pa-Latn`), **Hindi** (`hi-Deva`, `hi-Latn`), and **English**.
   - Directs to structured Open311 schemas with per-field confidence scores in $< 50\text{ms}$.
2. **Emergency Safety Net (Immediate 112 Redirect):**
   - Deterministic keyword safety net detects threats to life (fires, collapses, accidents, electrocution) and immediately provides an emergency dialer. **Emergencies are never queued as civic tickets.**
3. **Spatial-Semantic Deduplication:**
   - Clusters duplicate reports across languages and locations using Haversine distance and text embeddings.
   - Cost-calibrated: $\text{cost}(\text{wrong merge}) > \text{cost}(\text{duplicate})$, with an explicit "suggested merge" band for human review.
4. **Ownership Router with Calibrated Abstention:**
   - Matches incidents against municipal wings (`ROADS_BRIDGES`, `PUBLIC_HEALTH`, `ELECTRICAL`, `MOH_SANITATION`).
   - If confidence is $< 0.70$, it **abstains to a human triage queue** rather than misdirecting field crews.
5. **Evidence-Based Closure Verification Posterior ($P(\text{fixed} \mid E)$):**
   - Requires in-app geofenced photo capture ($R \le 100\text{m}$, no gallery uploads).
   - Flags photo recycling via **Perceptual Image Hashing (dHash)**.
   - Cross-examines before/after scene correspondence ($P_{\text{loc}}$) and defect resolution ($P_{\text{res}}$).
   - Integrates 1-tap citizen confirmation.
6. **Honest Error Bars (Wilson 95% Confidence Intervals):**
   - Calculates resolution rates per sector with Wilson score intervals and alerts on small sample sizes (`n < 5`).
7. **Equity Module (Correcting the Unobserved Denominator):**
   - Affluent sectors report grievances at 5x the rate of underserved areas.
   - Uses a **Thompson Sampling Bandit** in an open simulator (`civic-sim`) to allocate proactive municipal audit missions to digitally silent sectors.
8. **Tamper-Evident SHA-256 Public Ledger:**
   - Every state transition is cryptographically chained (`prev_hash`, `payload_hash`, `entry_hash`), verifiable by journalists, RWAs, and auditors via `/api/v1/ledger/verify`.

---

## 📊 Pre-Registered Evaluation Benchmark Results

All metrics were pre-registered in `eval/EVAL_PLAN.md` prior to evaluation and executed against double-labelled ground truth datasets (`eval/data/`):

| Subsystem | Primary Metric | Pre-Registered Target | Measured Result | Status |
|---|---|---|---|---|
| **Intake Triage** | Macro-F1 (Category) | $\ge 0.85$ | **0.8538** | ✅ PASSED |
| **Emergency Safety Net** | Emergency Recall | **1.00 (Zero Misses)** | **1.0000** (0 Misses) | ✅ PASSED |
| **Deduplication** | Pairwise Precision | $\ge 0.90$ | **1.0000** | ✅ PASSED |
| **Ownership Router** | Accuracy at Coverage | $\ge 0.90$ | **1.0000** | ✅ PASSED |
| **Closure Verifier** | ROC-AUC | $\ge 0.90$ | **1.0000** | ✅ PASSED |
| **Fraud Detection** | False Accept Rate (FAR @ 0.80) | $\le 0.05$ | **0.0000** | ✅ PASSED |
| **Photo Reuse (pHash)** | Reused Photo Recall | $\ge 0.95$ | **1.0000** | ✅ PASSED |
| **Equity Estimator** | Correlation Gain over Naive | $\ge +0.05$ | **+0.069** | ✅ PASSED |
| **Intake Performance** | p95 Latency | $< 4,000\text{ms}$ | **13.55 ms** | ✅ PASSED |
| **Throughput** | End-to-End Throughput | $> 50\text{ req/sec}$ | **91.8 req/sec** | ✅ PASSED |

Full details and threshold sweeps are recorded in [`eval/RESULTS.md`](eval/RESULTS.md).

---

## ⚡ Quickstart & Local Setup

### 1. Prerequisites
- Python 3.11, 3.12, or 3.13
- Git

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-org/pakka-hal.git
cd pakka-hal

# Copy environment configuration
cp .env.example .env

# Install dependencies
pip install fastapi uvicorn pydantic pyyaml httpx pillow numpy scikit-learn
```

### 3. Run Test Suite & Evaluation
```bash
# Run unit and integration tests
python tests/run_tests.py

# Run master evaluation benchmark
python eval/run_eval.py
```

### 4. Launch the Web Platform
```bash
python main.py
```
Open your browser to:
- **Interactive Web App & Dashboard:** `http://localhost:8000`
- **Interactive OpenAPI / Swagger Documentation:** `http://localhost:8000/docs`

---

## 🎬 4-Minute Demo Script (For Hackathon Judges)

1. **Intake in Punjabi / Hindi (40s):**
   - Click the preset sample *"ਸੈਕਟਰ 22 ਮਾਰਕੀਟ ਦੇ ਪਿੱਛੇ ਸਟ੍ਰੀਟ ਲਾਈਟ ਦਾ ਖੰਭਾ ਟੁੱਟਿਆ ਪਿਆ ਹੈ"*.
   - Tap **Submit to Open311 Layer**. Show real-time language detection (`pa-Guru`), category classification (`STREETLIGHT_OUT`), sector extraction (`SEC-22`), and canonical incident creation.
2. **Spatial-Semantic Deduplication (30s):**
   - Submit a second report in English for Sector 22 Aroma market.
   - Show how Pakka Hal calculates a high similarity score and merges it into the existing canonical incident (`reports_count = 2`).
3. **Emergency Safety-Net Filter (30s):**
   - Click the preset *"Emergency Test (भीषण आग / Fire)"*.
   - Show how the emergency banner triggers instantly, alerting the user to dial **112**, bypassing the civic ticket backlog.
4. **Field Worker Proof & Adversarial Fraud Flagging (50s):**
   - Switch to **Field Proof** tab.
   - Scenario A (Honest): Submit closure within 100m. Show verification posterior score ($> 80\%$) and state `fixed_verified`.
   - Scenario B (Adversarial): Submit an unresolved photo or reused stock photo. Show how pHash flags `REUSED_PHOTO` and downgrades score to $0.0$.
5. **Municipal Dashboard & Wilson Error Bars (40s):**
   - Switch to **Dashboard** tab. Show sector-by-sector Verified Resolution Rates with **95% Wilson confidence intervals** and small-n alerts.
   - Run the **Equity Bandit Simulation** to view suggested proactive audit missions for silent sectors.
6. **Cryptographic Public Ledger (30s):**
   - Switch to **SHA-256 Ledger** tab. Click **Run Cryptographic Verification** to mathematically prove the integrity of the chain from genesis to tip.
7. **Open311 Interoperability (20s):**
   - Show `curl` commands to query `/services.json` and `/requests.json`.

---

## 🌐 Open311 GeoReport v2 Compliance

Pakka Hal strictly implements the Open311 GeoReport v2 standard:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/services.json` | List civic services supported by Chandigarh |
| `GET` | `/services/{service_code}.json` | Retrieve schema attributes for a service |
| `POST` | `/requests.json` | Create a new service request with AI triage & dedup |
| `GET` | `/requests/{id}.json` | Retrieve status with Pakka Hal DPI extension attributes |
| `GET` | `/requests.json` | Query requests with status and sector filters |

### Extension Fields (`extended_attributes`)
- `resolution_state`: `open`, `in_progress`, `closure_pending`, `fixed_verified`, `fixed_unverified`, `disputed`, `reopened`
- `verification_score`: Calibrated Bayesian posterior $\in [0.0, 1.0]$
- `latest_ledger_hash`: Immutable SHA-256 block hash for the event
- `canonical_incident_id`: Linked deduplicated cluster ID
- `reports_count`: Total citizen reports consolidated into this incident

---

## 🌍 Forking for Another City

Pakka Hal is parameterized through `config/city.yaml`. To deploy in SAS Nagar (Mohali), Panchkula, Amritsar, or Delhi:
1. Create `config/<city>.yaml`.
2. Map your local sectors/wards and departments.
3. Start the server with `CITY_CONFIG_PATH="config/<city>.yaml"`.

See [`docs/FORKING.md`](docs/FORKING.md) for full instructions.

---

## 📜 Open Source & Community

- **License:** Apache License 2.0 (see [LICENSE](LICENSE))
- **Prior Art Analysis:** [docs/PRIOR_ART.md](docs/PRIOR_ART.md)
- **Architectural Decision Records (ADRs):** [docs/DECISIONS.md](docs/DECISIONS.md)
- **Model Cards:** [docs/MODEL_CARDS.md](docs/MODEL_CARDS.md)
- **Limitations & Ethics:** [docs/LIMITATIONS.md](docs/LIMITATIONS.md)
- **Contributing Guide:** [CONTRIBUTING.md](CONTRIBUTING.md)
- **Code of Conduct:** [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---
*Built for Chandigarh • Supported by Google for Developers • GDG Cloud Chandigarh 2026*
