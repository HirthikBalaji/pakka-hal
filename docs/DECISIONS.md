# Architectural Decision Records (ADRs)

> Project: Pakka Hal (Verified-Resolution Rails for Chandigarh's Civic Services)  
> Repository: GDG Cloud Chandigarh Hackathon  

---

## ADR-001: Indic Multilingual & Punjabi Audio Intake Strategy

### Context
Section 16 Rule 2 mandates testing Punjabi speech-to-text and vision on real samples and documenting the adaptation strategy.
Chandigarh is a tri-lingual Union Territory where civic grievances are articulated in:
1. **Punjabi** (Gurmukhi `pa-Guru` and Romanized `pa-Latn`, often mixed with Hindi: "ਸੈਕਟਰ 22 ਵਿੱਚ ਬੱਤੀ ਖਰਾਬ ਹੈ", "Sector 22 vich batti band hai")
2. **Hindi** (Devanagari `hi-Deva` and Hinglish `hi-Latn`: "सड़क पर गहरा गड्ढा है", "Road pe bohot bada khadda hai")
3. **English** ("Streetlight pole damaged near Sector 35 market")
4. **Code-mixed colloquialisms** ("Light nahi chal rahi round-about de kol")

Speech-to-Text on localized Punjabi can suffer from acoustic errors on noisy street recordings, specifically regarding sector numbers, landmark names, and colloquial terms for municipal problems ("khadda", "batti", "nala").

### Decision
1. **Multi-Stage Audio Pipeline:**
   - Primary: Gemini audio understanding / Cloud STT with Indic acoustic models.
   - Normalizer: Rule-based and embedding-assisted entity extraction mapping colloquial terms and phonetic variants (e.g., "sector byee", "sector bais", "sec 22") to standard Chandigarh sector identifiers (`SEC-22`).
2. **Citizen-in-the-Loop Confirmation:**
   - In the PWA intake screen, after voice note recording or audio upload, the system immediately presents the transcribed text alongside structured extraction in under 2 seconds. The citizen can tap once to edit or confirm.
3. **Deterministic Fixtures for Testing & Offline Dev:**
   - In unit tests and network-isolated environments, test against recorded transcripts across Hindi, Punjabi, Hinglish, and English with double-labelled ground truth.

---

## ADR-002: Dual-Gate Evidence-Based Closure Verification & Posterior

### Context
Typical civic apps allow municipal crews to close tickets by clicking "Resolved" or uploading an unverified picture. This leads to high rates of fraudulent closure (photographing the sky, shoes, clean sections of other streets, or reusing stock images).

### Decision
Pakka Hal implements an evidence-based closure posterior:
1. **Spatial Geofencing:** Worker must capture the "after" photo in-app with GPS coordinates within $R = 50\text{m}$ of the original report. File picker uploads are restricted in field worker mode.
2. **Perceptual Image Hashing (pHash):** Prevents duplicate or recycled photo submissions across tickets.
3. **Multimodal AI Scene Verification:**
   - Compares the "before" incident photo and "after" resolution photo.
   - Evaluates:
     - $P(\text{same\_location})$: Background building, street fixtures, road angle.
     - $P(\text{problem\_resolved})$: Defect (pothole, garbage, dark light) visibly remedied.
     - Evidence quality score (lighting, sharpness).
4. **Bayesian Posterior Fusion:**
   $$P(\text{Verified} \mid E) = \sigma\left( w_1 \cdot P_{\text{loc}} + w_2 \cdot P_{\text{res}} + w_3 \cdot \text{CitizenConfirm} - w_4 \cdot \text{Anomalies} \right)$$
5. **Calibrated States:**
   - `fixed_verified` (Score $\ge 0.80$)
   - `fixed_unverified` ($0.50 \le \text{Score} < 0.80$)
   - `disputed` (Citizen marks unresolved or score $< 0.50$)
   - `reopened` (Confirmed false closure)
6. **Wilson Confidence Intervals:** Every reported resolution rate per sector displays Wilson score 95% confidence intervals, alerting when sample sizes ($n$) are too small.

---

## ADR-003: Model-Agnostic LLMProvider Architecture

### Context
To qualify for the **Best Open-Source AI Project** bonus and guarantee self-hostability for Indian municipalities, the platform cannot be locked to a single proprietary cloud API.

### Decision
Define a clean abstract base class `LLMProvider`:
```python
class LLMProvider(ABC):
    async def triage_report(self, text: str, image_bytes: bytes | None) -> TriageResult: ...
    async def verify_closure(self, before_img: bytes, after_img: bytes, context: dict) -> VerificationResult: ...
    async def get_embedding(self, text: str) -> list[float]: ...
```
Implement three providers:
1. `GeminiProvider`: Uses Google's `google-genai` / Vertex AI models (`gemini-1.5-flash`).
2. `OpenWeightsProvider`: Uses local or remote open-weights models (`gemma2:9b`, `paligemma`) via Ollama or vLLM OpenAI-compatible endpoints.
3. `MockFixtureProvider`: Completely network-isolated, high-performance mock with recorded test cases for CI/CD and offline demonstrations.

---

## ADR-004: Tamper-Evident SHA-256 Ledger

### Context
Municipal audits (such as the 2025 Chandigarh MC audit) reveal lost, altered, or unregistered complaints. The system must guarantee data integrity without requiring high-latency distributed consensus.

### Decision
Implement a linear cryptographic hash chain:
$$H_0 = \text{Genesis Hash}$$
$$H_i = \text{SHA256}(H_{i-1} \parallel \text{Timestamp}_i \parallel \text{IncidentID}_i \parallel \text{EventType}_i \parallel \text{PayloadHash}_i)$$
- Provides mathematical tamper-evidence: modifying any historical record invalidates all subsequent block hashes.
- Exposes a public endpoint `/api/v1/ledger/verify` and daily root hash commits.
- Privacy-preserving: the public ledger stores hashes of payloads; PII is excluded.

---

## ADR-005: Emergency Detection Keyword Safety Net

### Context
Safety incidents (e.g. active fires, armed violence, medical emergencies) must **never** be queued as civic infrastructure tickets. LLM classification alone cannot guarantee 100% recall.

### Decision
Implement a two-stage filter:
1. Deterministic high-recall keyword scanner (checking terms like "fire", "aag", "accident", "ambulance", "khoon", "police", "attack", "emergency") in Hindi, Punjabi, and English.
2. If triggered or if model confidence $\ge 0.5$, flag `emergency: true`, reject ticket queueing, and immediately render a high-visibility Emergency 112 redirect banner in all three languages.
