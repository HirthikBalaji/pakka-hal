# Limitations, Privacy & Ethical Guarantees

> Project: Pakka Hal (Verified-Resolution Rails for Chandigarh's Civic Services)  
> Principles: Privacy by Design, DPDP Act 2023 Alignment, Zero Person-Targeting  

---

## 1. Ethical Red Lines (Non-Negotiable)

1. **Zero Person-Targeting:**
   - Pakka Hal is an infrastructure accountability system, **not a surveillance or enforcement system**.
   - No facial recognition, no automated license plate readers (ALPR), and no categories targeting street vendors, unhoused populations, or demographic groups.
   - Public image uploads are stripped of EXIF metadata (device serial numbers, private GPS timestamps) before storage.

2. **Emergency 112 Hard Separation:**
   - Civic grievance queues are fundamentally asynchronous. Urgent hazards to life (fires, active assaults, structural building collapses, severe road collisions) must **never** wait in a municipal ticket backlog.
   - The platform enforces an un-bypassable deterministic keyword safety net in English, Hindi, and Punjabi redirecting users to **National Emergency Number 112**.

3. **Honest Error Bars & Small-n Disclosures:**
   - Civic dashboards often display deceptive metrics like "100% resolved" for a ward that has received exactly 1 complaint.
   - Pakka Hal computes **Wilson score 95% confidence intervals** and explicitly highlights `Small-n Warning (n < 5)` to prevent statistical manipulation by officials.

---

## 2. Abuse, Spam & Brigading Defense

- **Brigading & Spam Floods:** Coordinated campaigns where groups submit hundreds of identical reports for a single location are mitigated via spatial-semantic deduplication: they merge into a single canonical incident.
- **Worker Fraud (Staged Closures):** Municipal workers photographing clean sections of other streets or reusing identical stock photos are caught via in-app geofencing ($R \le 100\text{m}$) and perceptual image hashing (dHash), with anomalous closures flagged for supervisor audit.

---

## 3. Equity & The Unobserved Denominator

- In every city, affluent sectors report grievances at 5x to 10x the rate of underserved colonies simply due to digital literacy, smartphone access, and higher administrative responsiveness.
- A naive portal that allocates resources based on complaint volume perpetuates spatial inequality.
- The **Equity Module** simulates and estimates this reporting propensity gap, using Thompson sampling to assign proactive physical inspection missions in silent sectors.
