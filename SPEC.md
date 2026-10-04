# Pakka Hal: Verified-Resolution Rails for Chandigarh's Civic Services

> Build spec for **Code for Communities, Chandigarh**. Theme: **AI for Digital Public Infrastructure of Chandigarh**.
>
> HOW TO USE: paste this whole file into your AI coding agent (Claude Code, Gemini / Antigravity, Cursor) as the first message, or save it as `SPEC.md` in an empty repo and say: "Read SPEC.md fully, then execute Section 12 (Build Plan) one step at a time. Obey Section 16 (Agent Rules)."

**Pitch line:** *Every city has a way to complain. None can prove it got fixed.*

---

## 0. Event facts

Official tracks (as listed on the hackathon page, pasted by the team):
1. Innovative Solution for AI for Digital Public Infrastructure of Chandigarh (open track)
2. Traffic Optimisation for the city
3. Urban Safety for Chandigarh
4. Civic Services
5. Waste & Sustainability

Focus areas (judging lens): **user experience optimisation, technology integration, scalability and performance, real-world impact.**
Bonus for every track: **Best Open-Source AI Project.**

From public listings: the Code for Communities day is **23 Oct 2026 at Chandigarh University** (GDG Cloud Chandigarh, alongside Cloud Community Days; DevFest is 24 Oct).

NOT verified, so CHECK before building: judging weights, team size, build duration, submission format, whether you may enter more than one track, whether pre-built code is allowed before kickoff, and what exactly the open-source bonus rewards (licence, repo quality, model openness?).

**Recommended registration:** Civic Services (primary fit). If you may only enter once and the organisers treat cross-cutting platforms as the open track, enter track 1 instead. Ask on the official channel.

---

## 1. Grounding: what the public record says

- An audit report on Chandigarh Municipal Corporation (reported 3 May 2025, covering 2022-2024) found that the engineering wing kept no comprehensive record of complaints received, pending, or forwarded to other departments, and no control register. It also flagged missing fixed-asset inventory records. Residents file through the MC's online portal, email, or post.
- Chandigarh's Integrated Command and Control Centre (ICCC), set up under the Smart Cities Mission, is described by an ADB Institute publication as integrating 25+ services (traffic management to air-quality monitoring).
- **Open311 GeoReport v2** is an open standard for civic issue reporting (`/services`, `/requests`, `/requests/{id}`, `/tokens/{id}`). Its base status values are only `open` and `closed`. It has **no notion of verified resolution.**

**Implication:** the gap is not another complaint form. It is a missing *accountability layer*: a tamper-evident record of what was reported, who owns it, and whether it was **verifiably** fixed, built on an open standard and sitting *beside* the systems departments already use.

Use these as context in the pitch, paraphrased and constructive. Do not blame individuals or imply the Administration endorses this project.

---

## 2. Problem statement

**Build:** an open-source, Open311-compatible **resolution layer** for Chandigarh that:
1. **Understands** messy multilingual reports (voice + photo + text in Hindi / Punjabi / English / Hinglish) into structured incidents,
2. **Merges** duplicates into one canonical incident,
3. **Routes** to the likely owner, or **abstains** and sends it to a human when unsure,
4. **Verifies closure** with evidence (was it really fixed, at the right place?),
5. **Publishes** a tamper-evident, privacy-preserving public record with honest uncertainty, and
6. (Stretch) **Corrects for reporting bias**, so areas that complain less are not served less.

---

## 3. Track coverage and focus-area mapping

| Track | How this project covers it |
|---|---|
| Civic Services (primary) | Intake, routing, service delivery tracking, verified closure, citizen transparency |
| Waste & Sustainability | Incident types: overflowing bin, litter spot, blocked drain; verified pickup/clearing |
| Traffic Optimisation | Incident types: pothole, signal fault, damaged signage (infrastructure faults, not enforcement) |
| Urban Safety | Incident types: streetlight outage, open manhole; **emergencies are redirected to 112, never queued**; infrastructure only, no surveillance |
| Open track | The platform itself as a DPI building block |

| Focus area | What we build and measure (targets are hypotheses to test, not claims) |
|---|---|
| UX | Report in <= 45 s median with a voice note + photo, in 3 languages, low-bandwidth friendly, accessible. Test with >= 5 non-team users; report completion times honestly. |
| Technology integration | Open311 GeoReport v2-compatible API; pluggable department adapters (email / CSV / webhook); multimodal LLM + embeddings behind a swappable provider interface (hosted default, open-weights option). |
| Scalability and performance | Event-driven pipeline, spatial bucketing for dedup, load test with synthetic reports; report p50/p95 latency and cost per 1,000 reports. |
| Real-world impact | Verified Resolution Rate, median time to *verified* fix, duplicate reduction, silent-area detection; a concrete pilot plan with one RWA/sector and one department. Do not claim a pilot until it happens. |

---

## 4. Why this is hard (the real technical core)

1. **Multimodal, multilingual intake.** Code-mixed Hinglish/Punjabi, Gurmukhi / Devanagari / Roman scripts, blurry photos, noisy voice notes, fuzzy addresses ("Sec 22 market ke peeche"). Output must be schema-valid with per-field confidence. Punjabi speech quality is a risk: **test it first.**
2. **Incident entity resolution.** Merge errors hide distinct problems; split errors waste crews. Combine GPS noise, sector-grid addressing, time, text semantics and image similarity, and choose thresholds by explicit cost.
3. **Ownership inference with abstention.** The asset registry is incomplete (the audit flagged missing asset records), so ownership must be inferred with uncertainty and the system must say "not sure" and route to a human.
4. **Closure verification.** "Closed" is easy to claim. Confirming *same place, problem gone, no recycled or staged photo* is adversarial and noisy.
5. **Equity under an unobserved denominator.** Complaint counts measure voice, not need. We cannot see problems nobody reports, so estimating bias needs deliberate audit sampling and a validated estimator.
6. **A public record that is trustworthy and safe.** Tamper-evident history, data minimisation, no person-targeting, no mandatory national ID.

---

## 5. What is new compared with typical civic-reporting apps

Typical apps (including open-source ones such as FixMyStreet, and Open311 clients) stop at *ticket creation and status*. This project adds:
- **Verified closure** with an evidence-based posterior and anomaly flags, not a self-declared "closed".
- **Abstaining router** with a published accuracy-vs-coverage curve.
- **AI-native multilingual intake** with an open-weights option so a city can self-host.
- **Equity-aware prioritisation** validated in an open simulator.
- **Open311 compatibility plus clearly-named extension fields** for resolution state.

Run a 15-minute prior-art check (FixMyStreet, SeeClickFix-style apps, Swachhata-style apps, Open311 ecosystem, government grievance portals) and record it in `docs/PRIOR_ART.md`. Individual pieces exist; claim only what you verified is new.

---

## 6. Users and scenarios

| User | Need | Gets |
|---|---|---|
| Citizen | Report fast in my language; know if it was really fixed | Voice+photo report, one confirmation screen, status, one-tap "fixed?" check |
| Field worker | Clear job, easy proof of work | Job card with location, in-app capture of "after" evidence |
| Department supervisor | Fewer duplicates, wrong-department tickets | Merged incidents, routing with reasons, closure-quality flags |
| Command-centre / city official | City-wide truth | Dashboard: verified resolution rate per sector/department/category, with intervals |
| RWA / journalist / auditor | Trust the numbers | Public ledger, method page, eval results, open data |
| Another city's team | Reuse this | `city.yaml` + `docs/FORKING.md` |

---

## 7. Architecture

```
 Citizen PWA (voice + photo + text) ─┐
 Department adapters (email/CSV/webhook) ┤──> Intake API (Open311-compatible) ──> queue
                                          │                                        │
          ┌───────────────────────────────┴────────────────────────────────────────┤
          ▼                                                                        ▼
  Triage (multimodal LLM -> JSON) -> Dedup / entity resolution -> Ownership router (abstain -> human queue)
          │                                                                        │
          └────────────> Canonical Incident store <── Closure verifier <── Field capture app
                                   │                          │
                          Hash-chained ledger        Citizen re-confirm (1-tap)
                                   │
              Transparency dashboard + Equity module (audit bandit) + Open311 read API
```

Suggested stack (swap freely): Python 3.11 + FastAPI; Postgres/PostGIS (or SQLite + SpatiaLite for the hackathon); H3 or geohash for spatial bucketing; React PWA + MapLibre GL; Cloud Run for deploy; optional Pub/Sub, Firestore, BigQuery; **an `LLMProvider` interface with a hosted Gemini implementation and an open-weights implementation** (for example a Gemma-family model served locally); a multilingual embedding model (hosted or open-weights); speech-to-text via Gemini audio understanding or Cloud Speech-to-Text (verify Punjabi support and quality).

---

## 8. Algorithm spec

### 8.1 Intake: report to structured incident
Taxonomy aligned to Open311 `service_code`s: `STREETLIGHT_OUT, POTHOLE, GARBAGE_OVERFLOW, DRAIN_BLOCKED, SIGNAL_FAULT, DAMAGED_SIGNAGE, MANHOLE_COVER, WATER_LEAK, OTHER, EMERGENCY_REDIRECT`. **No category targets a person or group.**

```json
{
  "report_id": "r_000123",
  "language_detected": "pa-Guru | pa-Latn | hi-Deva | hi-Latn | en",
  "summary_en": "…",
  "category": "STREETLIGHT_OUT",
  "severity": "low | medium | high",
  "emergency": false,
  "location": {"lat": null, "lon": null, "accuracy_m": null, "sector": "…", "landmark_text": "…", "geo_confidence": 0.0},
  "evidence": [{"type": "photo", "id": "m_1", "quality": "ok | blurry | dark"}],
  "field_confidence": {"category": 0.0, "location": 0.0},
  "needs_clarification": null
}
```
(Values are schema placeholders. Never ship placeholders to the UI.) If confidence is low, ask **one** short follow-up question instead of guessing. Use the model's structured-output mode with schema validation and a retry/fallback.

### 8.2 Dedup / entity resolution
```
candidates = open incidents in same spatial bucket(s) + category family + time window
score(pair) = logistic( w1*spatial(d, acc1, acc2) + w2*text_cos + w3*image_cos + w4*time_decay )
if p >= tau_merge: merge
elif p <= tau_split: new incident
else: "suggest merge" to human
```
Learn weights on labelled pairs. Avoid transitive over-merging (constrained agglomerative clustering). Choose thresholds by cost: cost(wrong merge) > cost(duplicate). Report pairwise precision/recall and B-cubed F1 with a threshold sweep.

### 8.3 Ownership router with abstention
- Inputs: `assets.geojson` (seeded from OpenStreetMap, then corrected), `ownership_rules.yaml` (category x area -> owner), and a classifier trained on triage outcomes.
- Output: ranked owners + confidence + a human-readable reason. Below threshold: **abstain to the human queue.**
- Publish the accuracy-at-coverage curve. Department names live in config and are marked "verify"; never hardcode contacts you have not confirmed.

### 8.4 Closure verification
1. A closure attempt requires **in-app capture** of an "after" photo with live location within R metres of the incident (no gallery uploads for closure).
2. Visual check: a vision model compares before/after and returns `{same_location: p, problem_present_after: p, evidence_quality, reasons[]}` in structured form; add an embedding similarity check on the scene and a perceptual-hash check against reuse of old photos.
3. Citizen re-confirmation: a one-tap "Fixed / Not fixed / Can't tell" to original reporters after N hours, weighted by reporter history.
4. Combine into a **verification posterior** (logistic or simple Bayesian). States: `fixed_verified`, `fixed_unverified`, `disputed`, `reopened`.
5. Anomaly flags: closed unusually fast, no evidence, reused photo, worker far from site, repeated closure of the same cell.
6. Public metric: **Verified Resolution Rate** per sector / department / category, with **Wilson confidence intervals** and a small-n warning.

### 8.5 Equity module (stretch, high impact)
```
observed_reports_a ~ Poisson( lambda_a * pi_a )     # lambda: true incident rate, pi: reporting propensity (both unknown)
audit_cells chosen by a bandit (Thompson sampling) favouring high-uncertainty, low-report areas
audit results + inclusion probabilities -> unbiased lambda_a estimate (inverse-propensity weighting)
silent_area_score_a = P( lambda_a high | few reports, audit evidence )
```
Output: a "silent areas" map and **suggested audit tasks** for field staff/volunteers. Validate in an open **simulator** (`civic-sim/`) where true rates and reporting bias are known: show that the estimator recovers the truth better than naive reports-per-capita. Everything from the simulator is labelled `simulated`.

### 8.6 Tamper-evident ledger
Events: `report_received, merged, routed, closure_attempt, verification_result, citizen_confirmation`. Each entry `{id, ts, incident_id, type, payload_hash, prev_hash, entry_hash}`. Commit a **daily root hash** to the repo. Tamper-evident, not tamper-proof; say so. The public API exposes hashes and aggregates, not personal data.

---

## 9. Open311 compatibility and DPI posture

- Implement GeoReport v2 endpoints (`/services`, `/requests`, `/requests/{id}`, `/tokens/{id}`) so any Open311 client works. Test with a plain `curl` and one existing Open311 client.
- The standard's base statuses are only `open` / `closed`. Keep those valid and expose richer states through **clearly-named extension fields** (`resolution_state`, `verification_score`). Check the spec's extension mechanism before choosing field names.
- **Beside, not instead of:** department adapters are plugins (email, CSV drop, webhook). Nothing requires replacing an existing portal or the ICCC.
- Privacy by design: purpose limitation, minimisation, retention limits, no mandatory national ID. Align with the principles of India's Digital Personal Data Protection Act, 2023 (verify requirements with the organisers; this is not legal advice).
- Say "compatible with" Open311, never "integrated with" a government system unless you actually integrated it. Do not use official logos or imply endorsement.
- Publish OpenAPI + JSON Schemas + model cards.

---

## 10. Evaluation plan (write it BEFORE running anything)

Create `eval/EVAL_PLAN.md` and **commit it before the first evaluation run.** Disclose dataset sizes and sources everywhere.

| Component | Test data | Metric |
|---|---|---|
| Triage | >= 150 **human-written** multilingual reports (Hindi/Punjabi/English/Hinglish, voice transcripts included), double-labelled | Macro-F1 for category; location-resolution accuracy; emergency **recall** |
| Dedup | >= 40 incidents with 2-5 reports each, hand-clustered | Pairwise P/R, B-cubed F1, threshold sweep |
| Router | Labelled owner for each incident | Accuracy vs coverage (abstention curve) |
| Closure verifier | >= 30 real before/after pairs the team photographs + >= 30 adversarial negatives (wrong place, reused photo, unrelated scene) | AUC, **false-accept rate** at the chosen threshold |
| Equity estimator | Open simulator with known truth | Rank correlation and error vs naive baseline, across bias levels |
| Performance | Synthetic reports (LLM-generated allowed here, labelled synthetic) | p50/p95 intake-to-incident latency, throughput, cost per 1,000 reports |
| UX | >= 5 non-team users | Median time to file a report, error points, accessibility checks |

- Compare hosted vs open-weights model on the same triage set and report the gap.
- LLM-synthetic data is for load tests only, not for quality claims (circularity).
- **Report failures.** A slide with where it breaks is a strength.

---

## 11. Open-source AI bonus checklist

- Permissive licence (Apache-2.0 suggested); credit OpenStreetMap (ODbL attribution) and other data providers.
- Model-agnostic provider interface with a working **open-weights path**, plus a documented benchmark of both.
- **Model cards** for each AI component: purpose, data, metrics, limits, failure cases.
- Public, PII-free eval sets and one-command reproduction (`make eval`); open simulator.
- CI: lint, tests, eval smoke test. `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue templates ("add a service type", "add a city").
- Starter issues to open before the demo:
  1. Add a `city.yaml` for another Indian city.
  2. Native-speaker review of Hindi/Punjabi prompts and UI strings.
  3. Add a new service type with tests.
  4. Improve Gurmukhi address normalisation.
  5. Add a department adapter (CSV / email).
  6. Add a reliability diagram for the verifier.
  7. Low-bandwidth mode for the PWA.
  8. Write `docs/FORKING.md` walkthrough.
- If Hacktoberfest participation matters, add the `hacktoberfest` topic and **check the official rules.**

---

## 12. Build plan (assumes ~24 h; scale down proportionally if shorter; assign a data/eval owner from hour 0)

**Before kickoff:** only if the rules allow. If pre-built code is banned or unclear, limit prep to reading docs, testing Punjabi speech-to-text and vision APIs, writing `eval/EVAL_PLAN.md`, and **writing the human test reports and taking before/after photos.** Start the repo at kickoff and commit continuously.

| Hours | Task | Done when |
|---|---|---|
| 0-1 | Repo, `city.yaml`, licence, deploy hello-world | Public URL responds |
| 1-4 | Open311 intake API + triage to schema + taxonomy | Voice+photo -> valid JSON with confidence |
| 4-8 | Dedup (bucketing, scoring, thresholds) | Pairwise metrics print |
| 8-11 | Router + OSM-seeded asset registry + human queue | Accuracy-at-coverage curve prints |
| 11-15 | Closure verifier + in-app capture + ledger | A good closure verifies; a staged one is flagged |
| 15-19 | Citizen PWA + transparency dashboard (Wilson intervals) | Full flow clickable end to end |
| 19-21 | Eval runs + load test + hosted-vs-open model comparison | Results table committed |
| 21-23 | Equity simulator + module (stretch) / open-source polish | Simulator plot or polished repo |
| 23-24 | README, rehearsal, fallback demo video | 3-minute demo runs twice cleanly |

**Suggested roles (team of 4):** backend/AI, frontend/UX, data/eval (labelling + simulator), pitch/docs/open-source.
**Cut line:** intake -> dedup -> route -> verified closure -> dashboard, with real team-collected test data and the eval table. Equity module, voice polish, adapters and the open-weights benchmark are stretch. **Protect verified closure and the evaluation; they are the novelty.**

---

## 13. Demo script (about 4 minutes)

1. **Report:** a Punjabi voice note + photo of a broken streetlight near a named sector. Show the confirmation screen with the structured incident (~40 s).
2. **Dedup:** two more reports (Hindi text, English) merge into the same incident, with the match confidence shown (~30 s).
3. **Routing:** auto-routed with a reason and confidence, then an ambiguous case **abstains to a human** (~30 s).
4. **Closure:** the field worker captures the "after" photo in-app and it verifies; then a staged closure (wrong place or reused photo) is **flagged** (~50 s).
5. **Transparency:** dashboard of Verified Resolution Rate per sector with intervals; simulated silent-area map (clearly labelled `simulated`) and suggested audits (~40 s).
6. **Interoperability:** a `curl` against the Open311 endpoint; swap `city.yaml` (~20 s).
7. **Honesty slide:** eval table, including where it fails; emergency redirect to 112 (~30 s).

Every screen must say whether data is `live`, `test-collected` or `simulated`.

---

## 14. Pitch and judging alignment

- **UX:** voice-first, three languages, median time to report measured with real users.
- **Technology integration:** open standard, adapters, swappable AI providers including open weights.
- **Scalability and performance:** event-driven design, measured p95 and cost per 1,000 reports.
- **Real-world impact:** a metric the public can verify (Verified Resolution Rate) and a concrete pilot plan.
- **Open-source bonus:** licence, model cards, open eval and simulator, forkable by city.

One-paragraph pitch: "Chandigarh already has ways to complain. What's missing is proof. Pakka Hal is an open, Open311-compatible layer that understands reports in Hindi, Punjabi and English, merges duplicates, routes to the right owner or admits it doesn't know, and verifies that a fix really happened, with a tamper-evident public record and honest error bars. It sits beside existing systems, runs on open models if the city prefers, and any city can fork it."

---

## 15. Risks, ethics and honesty rules (non-negotiable)

- Never present simulated or synthetic data as real; label `live` / `test-collected` / `simulated`.
- **No person-targeting.** No facial recognition, no predictive policing, no categories about people (vendors, individuals, groups). The safety track is infrastructure only.
- **Emergencies:** detect and show 112 prominently in all three languages; never queue an emergency as a civic ticket. State that this is not a replacement for emergency services; test emergency recall.
- Blur faces and number plates, strip EXIF from public media, keep closure-verification metadata internal with a retention limit. Public views show aggregates and moderated incident cards; apply a minimum-count threshold for small areas to prevent re-identification.
- Abuse and spam: rate limits, reporter reputation weighting, dispute flow for contested closures. Brigading is a real risk; mention it in `docs/LIMITATIONS.md`.
- Intervals everywhere; small-n warnings; no claims beyond the evaluated data.
- Cite the audit report as it states, paraphrased. No blame on individuals. No official logos; no implied endorsement.
- Keys in `.env`, never in the repo. Respect data licences and rate limits.

---

## 16. Rules for the coding agent

1. Read this file fully. Before coding, spend at most 15 minutes on the prior-art check and write `docs/PRIOR_ART.md`.
2. **Test Punjabi speech-to-text and vision on real samples in the first hour**; if quality is poor, record it in `docs/DECISIONS.md` and adapt (for example text-first Punjabi, voice for Hindi/English).
3. Build in **vertical slices** with a runnable demo at all times; commit often.
4. Build the **eval harness early** (by hour ~11). Do not tune on the test set.
5. Tests never touch the network; use recorded fixtures. Mock LLM calls with fixtures in unit tests; keep a separate opt-in live test.
6. Never hardcode secrets; use `.env` and `.env.example`.
7. Ask before adding dependencies beyond the suggested stack.
8. If an API, endpoint or capability differs from this spec, **adapt and record it in `docs/DECISIONS.md`**; do not fabricate data or results.
9. If real data for a required input is unavailable, stop and report it rather than silently simulating. If simulation is unavoidable, label it `simulated` everywhere.
10. Keep LLMs out of final decisions that need guarantees (emergency redirect uses a high-recall classifier plus a keyword safety net; verification uses calibrated thresholds).
11. After each milestone, state what works, what is stubbed, and what is next, in 3 lines.

---

## 17. Alternates per track (if you need to pivot)

- **Traffic Optimisation: Green Corridor Planner.** Build a SUMO model of a road segment derived from OpenStreetMap; compute ambulance signal-preemption plans and quantify the delay imposed on cross traffic (fairness). Hard part: calibration without live signal data, so claim only *relative* improvements with sensitivity analysis. All results `simulated`; verify which junctions are actually signalised.
- **Urban Safety: Dark-Spot Audit.** An infrastructure-only night-safety condition index (lighting outages, verified repairs, footpath obstructions) on the same engine. Hard part: validating "safety" without crime data, so define it as an *infrastructure condition index*, never crime prediction. No surveillance.
- **Waste & Sustainability: Hawa Hisaab.** The previously delivered spec: an auditable air-source attribution engine (regional smoke vs local sources vs unexplained, with intervals and a pre-registered hindcast). Fits "environmental monitoring". Alternatively reuse this engine for **verified waste pickup** with collection-vehicle logs.
- **Open track:** this flagship itself.

---

## 18. Sources used to write this spec

- Audit report coverage on Chandigarh MC complaint records (Tribune, May 2025): https://www.tribuneindia.com/news/chandigarh/audit-report-raps-chandigarh-civic-body-for-not-maintaining-public-complaint-record/amp
- ADB Institute on Chandigarh's Integrated Command and Control Centre: https://www.adb.org/adbi/publications/integrated-command-and-control-centre-a-holistic-approach-to-tackling-environmental-challenges-in-chandigarh-india
- Open311 GeoReport v2 (archived wiki): https://webarchive.library.unt.edu/web/20170118233000mp_/http://wiki.open311.org/GeoReport_v2
- GDG Cloud Chandigarh DevFest & Code for Communities 2026: https://sessionize.com/gdg-cloud-chandigarh-devfest
- Hackathon listing: https://hackculture.io/hackathons/code-for-communities-chandigarh
