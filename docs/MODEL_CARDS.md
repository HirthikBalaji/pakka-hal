# Model Cards: Pakka Hal Civic AI Pipeline

> Project: Pakka Hal (Verified-Resolution Rails for Chandigarh's Civic Services)  
> Standard: Open-Source AI Model Transparency Guidelines  

---

## 1. Multilingual Civic Triage Model

### Model Details
- **Architecture:** Swappable Provider Interface (`LLMProvider`)
  - Hosted Tier: Google Gemini 1.5 Flash / Pro (`gemini-1.5-flash`)
  - Open-Weights Tier: Google Gemma 2 (`gemma-2-9b-it`) via Ollama / vLLM
  - Offline / Deterministic Tier: `MockLLMProvider`
- **Primary Task:** Multimodal text & speech classification into Open311 civic taxonomy, location entity resolution, and safety-critical emergency filtering.
- **Languages Supported:** Punjabi (`pa-Guru`, `pa-Latn`), Hindi (`hi-Deva`, `hi-Latn`), English (`en`), and code-mixed colloquialisms.

### Intended Use
- Autonomous structuring of citizen voice notes, photos, and messages into standardized Open311 service requests.
- Immediate extraction of sector identifiers (`SEC-17`, `SEC-22`, etc.) and severity scoring.

### Out-of-Scope & Prohibited Uses
- **No Person Identification:** Strictly prohibited from classifying, tracking, or identifying individuals, hawkers, protestors, or socio-economic groups.
- **No Emergency Queuing:** When life hazard is detected, model execution is bypassed or overridden by the deterministic Emergency 112 safety-net redirect.

### Evaluation Metrics
- Category Macro-F1: **0.8538** on 160 double-labelled multilingual test cases.
- Emergency Recall: **1.0000** (Zero misses).
- Average Inference Latency: $< 50\text{ms}$ (Mock/local) / $\sim 1.2\text{s}$ (Hosted API).

---

## 2. Evidence-Based Closure Verification Model

### Model Details
- **Architecture:** PaliGemma / Gemini 1.5 Multimodal Vision paired with 64-bit difference perceptual hashing (dHash).
- **Primary Task:** Cross-examination of before-defect and after-repair photographs to evaluate scene correspondence ($P_{\text{loc}}$) and defect rectification ($P_{\text{res}}$).
- **Inputs:** Pair of JPEG/PNG images, incident category, worker GPS distance offset.
- **Output:** Calibrated posterior score $P(\text{Fixed} \mid \text{Evidence}) \in [0.0, 1.0]$ and anomaly flags (`REUSED_PHOTO`, `WORKER_FAR_FROM_SITE`, `POOR_EVIDENCE_QUALITY`).

### Factors & Performance
- **Adversarial Robustness:** Tested against reused identical photos, 2km+ GPS discrepancies, and staged uncompleted repairs.
- **ROC-AUC:** **1.0000** on 60 positive and adversarial negative test pairs.
- **False Accept Rate (FAR @ 0.80):** **0.0000** (Zero fraudulent closures accepted).
- **Photo Reuse Detection Recall:** **1.0000** (100% of reused photos caught via pHash collision).

### Limitations
- Adverse weather (fog, heavy rain, nighttime darkness) degrades visual confidence. In low-visibility scenarios, the system abstains to `fixed_unverified` until citizen confirmation is recorded.

---

## 3. Equity Audit Bandit (CivicSim)

### Model Details
- **Architecture:** Bayesian Multi-Armed Bandit using Thompson Sampling over Gamma-Poisson conjugate priors.
- **Task:** Estimating unobserved defect generation rates ($\lambda_a$) across 60 city sectors to detect digitally silent communities suffering from low reporting propensity ($\pi_a$).
- **Benchmark Performance:**
  - Rank correlation improvement vs naive complaint counts: **+0.069 to +0.250** gain.
  - Generates top-priority proactive audit missions for municipal ground staff.
