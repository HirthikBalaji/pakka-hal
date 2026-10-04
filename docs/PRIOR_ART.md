# Prior Art & Novelty Analysis: Pakka Hal

> Date: 2026-10-04  
> Project: Pakka Hal (Verified-Resolution Rails for Chandigarh's Civic Services)  
> Track: AI for Digital Public Infrastructure / Civic Services  

---

## 1. Landscape Overview

Cities around the world and across India have deployed various civic grievance systems. Below is an objective analysis of existing systems and standards, identifying their strengths and their architectural gaps.

| System / Platform | Primary Architecture & Scope | How Status is Handled | Key Gaps Addressed by Pakka Hal |
|---|---|---|---|
| **FixMyStreet** (mySociety, UK / Global) | Open-source Perl/Ruby platform. Web/mobile reporting of street problems, routed to local councils via email/API. | Citizen or council marks status as "fixed", "in progress", or "closed". Relies entirely on trust. | No multimodal AI triage; no spatial-semantic-visual deduplication; no evidence-based visual verification of closure; no tamper-evident audit ledger; no Indic multilingual voice support. |
| **SeeClickFix** (CivicPlus, US) | Proprietary commercial civic SaaS. Used by hundreds of US municipalities with GIS integration. | Staff updates status in CRM. Occasional upload of completion photo. | Closed-source commercial software; no self-hosting for Indian DPI; no open-weights model option; lack of cryptographic proof or verification posterior; no equity-aware silent-area sampling. |
| **Swachhata App** (MoHUA & Janaagraha, India) | Pan-India sanitation reporting mobile application for Swachh Bharat Mission. | Municipal sanitary inspector uploads an "after" photo and marks "resolved". | Vulnerable to false closures: workers upload blank/irrelevant photos or photos of unrelated clean streets without automated perceptual/scene cross-matching. Citizens report low trust in closure declarations. Proprietary backend. |
| **Chandigarh MC Grievance Portal & ICCC** | Municipal Corporation Chandigarh online portals, email, post, and Smart City ICCC integration. | Closed by internal departmental action tickets. | 2025 official audit rapped the MC engineering wing for maintaining no comprehensive register of complaints, pending items, or inter-department transfers. No public Open311 API, no voice intake, no verifiable public ledger. |
| **Open311 GeoReport v2** (Standard) | Open REST specification (`/services`, `/requests`, `/tokens`) implemented by Boston, San Francisco, Chicago, Helsinki. | Base specification only defines binary status: `open` and `closed`. | **No notion of verified resolution.** Does not model evidence, verification posterior, spatial-semantic deduplication confidence, or equity audit adjustments. |

---

## 2. What is Verifiably Novel in Pakka Hal

Pakka Hal does **not** re-invent the complaint submission interface. It provides an interoperable **Accountability & Resolution Layer** that sits beside existing city systems:

1. **Evidence-Based Closure Verification Posterior ($P(\text{fixed} \mid \text{evidence})$):**
   - Closure is not a binary toggle or an unverified photo upload.
   - Combines (a) in-app geofenced worker photo capture, (b) multimodal AI scene matching (verifying same background landmarks, problem gone, no photo re-use via pHash), and (c) 1-tap citizen confirmation weighted by reporter reliability.
   - Outputs calibrated states: `fixed_verified`, `fixed_unverified`, `disputed`, `reopened`.

2. **Multilingual, Code-Mixed Indic Voice Triage:**
   - Handles Punjabi (Gurmukhi & Latin script), Hindi (Devanagari & Latin script), and English.
   - Converts unstructured voice notes, photos, and messy text into structured Open311 schemas with per-field confidence scores.
   - Dedicated emergency detection with strict keyword + classifier fallback directly redirecting to Emergency 112 (never queued).

3. **Spatial-Semantic Deduplication with Cost-Calibrated Thresholds:**
   - Combines spatial distance (H3/geohash indexing), text semantic cosine similarity, category hierarchies, and perceptual image hashing.
   - Cost-calibrated: $\text{cost}(\text{wrong merge}) > \text{cost}(\text{duplicate})$, with an explicit human-in-the-loop "suggested merge" band.

4. **Ownership Router with Calibrated Abstention:**
   - Routes complaints to the responsible municipal department (Public Health, Roads/Bridges, Horticulture, Electrical, etc.) using OSM-derived asset layers and rules.
   - **Abstains when uncertain:** If confidence falls below threshold $\tau_{\text{abstain}}$, it routes to a human triage queue with explicit explanations rather than misdirecting municipal crews.

5. **Tamper-Evident Hash-Chained Public Ledger:**
   - Every state transition (`report_received` $\to$ `merged` $\to$ `routed` $\to$ `closure_attempt` $\to$ `verification_result`) is hashed into a SHA-256 linear chain.
   - Daily root hashes can be committed to public Git repos or transparency portals.

6. **Equity-Aware Silent Area Correction (Bandit-Driven Audit Sampling):**
   - Addresses the unobserved denominator: areas with fewer complaints often suffer from digital exclusion rather than having zero problems.
   - Uses Thompson sampling over an audit bandit to suggest physical inspection routes in silent sectors, correcting municipal resource allocation.

---

## 3. Summary

Pakka Hal builds on Open311 GeoReport v2, extending it with backward-compatible extension fields (`resolution_state`, `verification_score`, `ledger_hash`). It provides the missing digital public infrastructure bridge between citizen dissatisfaction and verified municipal accountability.
