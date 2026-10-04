# Forking Pakka Hal for Another City

> Pakka Hal is built as a portable **Digital Public Good (DPG)** under the Apache-2.0 license.  
> Any municipality, Smart City SPV, developer group, or RWA federation can fork and deploy it in under an hour.

---

## 1. Quick Fork Guide (3 Steps)

### Step 1: Clone and Create Your City Config
Copy `config/city.yaml` to create your city profile (e.g. `config/mohali.yaml`, `config/amritsar.yaml`, or `config/delhi.yaml`):

```yaml
city:
  name: "SAS Nagar (Mohali)"
  state: "Punjab"
  country: "IN"
  timezone: "Asia/Kolkata"
  center:
    lat: 30.7046
    lon: 76.7179
  emergency_contacts:
    police_fire_ambulance: "112"
  supported_languages:
    - code: "pa"
    - code: "en"
    - code: "hi"

sectors:
  total_sectors: 45
  sample_anchors:
    - id: "PHASE-7"
      name: "Phase 7 Industrial / Commercial"
      lat: 30.7080
      lon: 76.7200
```

### Step 2: Configure Departments & SLAs
Map your municipal corporation's actual administrative wings:
```yaml
departments:
  - id: "MC_MOHALI_SANITATION"
    name: "Mohali MC Sanitation Wing"
    email: "sanitation@mcmohali.gov.in"
    sla_hours: 24
    service_codes: ["GARBAGE_OVERFLOW"]
```

### Step 3: Run with Custom Config
Point the environment variable to your custom YAML file:
```bash
export CITY_CONFIG_PATH="config/mohali.yaml"
python main.py
```
Your city now has a fully functioning, Open311-compliant, evidence-based verified resolution rail!

---

## 2. Choosing Your AI Execution Tier

1. **Zero-Cost Local Open-Weights Tier (Air-gapped / Local Server):**
   - Install [Ollama](https://ollama.ai) on your municipal server:
     ```bash
     ollama run gemma2:9b
     ```
   - In `.env`, set:
     ```bash
     LLM_PROVIDER=ollama
     OLLAMA_BASE_URL=http://localhost:11434
     OPEN_WEIGHTS_MODEL=gemma2:9b
     ```
2. **Cloud Tier (Google Cloud / Vertex AI):**
   - In `.env`, set:
     ```bash
     LLM_PROVIDER=gemini
     GEMINI_API_KEY=your_key_here
     ```
3. **Offline / CI/CD Benchmark Tier:**
   - Set `LLM_PROVIDER=mock` for deterministic test suites.
