# Evaluation Plan: Pakka Hal

> Date: 2026-10-04  
> Pre-registration Status: **COMMITTED PRIOR TO EVALUATION RUNS**  
> Standards Compliance: Section 10, SPEC.md  

---

## 1. Objectives & Principles

1. **Pre-Registration:** All metrics, thresholds, and datasets are defined here before running evaluation scripts.
2. **Zero Data Snooping:** No tuning of model hyperparameters or routing weights on the test partition.
3. **Disclosure of Provenance:** All datasets explicitly distinguish between `human_labelled`, `test_collected`, and `simulated` data. Synthetic data is restricted to performance and load testing.
4. **Honest Reporting of Failures:** Negative results, boundary condition failures, and edge cases will be catalogued in the final evaluation report.

---

## 2. Evaluation Matrix

| Component | Target Dataset Size & Composition | Primary Metrics | Success Thresholds |
|---|---|---|---|
| **Intake Triage** | 150+ multilingual civic reports (Hindi Devanagari/Latin, Punjabi Gurmukhi/Latin, English, Code-mixed Hinglish) with ground-truth categories and emergency labels | • Macro-F1 (Category)<br>• Emergency **Recall**<br>• Sector Location Accuracy | • Macro-F1 $\ge 0.85$<br>• Emergency Recall $= 1.00$ (Zero Misses)<br>• Location Acc $\ge 0.80$ |
| **Deduplication / Entity Resolution** | 40+ canonical incident clusters (each containing 2–5 variant reports across languages, slight coordinate noise, and temporal shifts) + 50 distinct negative pairs | • Pairwise Precision<br>• Pairwise Recall<br>• B-cubed F1 Score<br>• Threshold Sweep curve | • Pairwise Precision $\ge 0.90$<br>• Pairwise Recall $\ge 0.80$<br>• B-cubed F1 $\ge 0.85$ |
| **Ownership Router with Abstention** | 100+ categorized incidents mapped to municipal departments (Public Health, Roads/B&R, Electrical, Sanitation, Horticulture) | • Accuracy at Coverage Curve<br>• Accuracy on non-abstained<br>• Abstention Rate on ambiguous cases | • Accuracy $\ge 0.92$ at $70\%$ coverage<br>• Proper abstention on out-of-domain/ambiguous cases |
| **Closure Verifier** | 30 true before/after resolution pairs + 30 adversarial negative pairs (same defect, wrong angle, unrelated clean scene, reused identical photo) | • ROC-AUC<br>• False Accept Rate (FAR) at calibrated threshold $\tau = 0.80$<br>• pHash collision detection recall | • ROC-AUC $\ge 0.90$<br>• FAR $\le 0.05$ at $\tau = 0.80$<br>• pHash Duplicate Detection $= 1.00$ |
| **Equity Estimator (CivicSim)** | Simulated city grid of 60 sectors with known true Poisson defect rates $\lambda_s$ and uneven reporting propensities $\pi_s$ | • Spearman Rank Correlation vs Truth<br>• Mean Absolute Error (MAE) vs Naive Complaint Count baseline | • Estimator Rank Corr $>$ Naive Corr by $\ge 0.25$<br>• Effective identification of top-5 silent sectors |
| **Performance & Latency** | 1,000 synthetic Open311 intake requests streamed under load | • p50 and p95 End-to-End Latency<br>• Throughput (requests/sec)<br>• Projected Cost per 1,000 requests | • p50 $< 800\text{ms}$ (non-LLM) / $< 2.5\text{s}$ (LLM)<br>• p95 $< 4.0\text{s}$<br>• Cost $< \$0.50$ per 1,000 reports |
| **User Experience (UX)** | 5+ non-team human testers recording voice notes in Hindi/Punjabi/English | • Median Completion Time<br>• Task Success Rate<br>• Language Preference distribution | • Median filing time $\le 45\text{s}$<br>• Task Success Rate $= 100\%$ |

---

## 3. Detailed Component Protocols

### 3.1 Triage & Emergency Recall Protocol
- **Safety Critical:** Emergency reports (accidents, structural collapses, fires, violent attacks) must trigger immediate redirect to Emergency 112.
- Test harness will feed both subtle ("Sector 22 market me aag lag gayi hai") and overt ("Emergency police ambulance needed") inputs.
- Any emergency routed to civic ticket queue counts as a critical failure.

### 3.2 Deduplication Cost-Matrix
In civic grievance management:
$$\text{Cost}(\text{False Merge}) \gg \text{Cost}(\text{False Split})$$
- False Merge merges two distinct potholes on opposite sides of a sector, causing crews to fix one and leave the other forgotten.
- False Split merely creates two tickets for the same issue, which a field worker can quickly spot.
- Thus, the decision threshold $\tau_{\text{merge}}$ is calibrated to enforce high precision ($\ge 90\%$), with intermediate scores ($0.50 \le p < \tau_{\text{merge}}$) flagged as "Suggested Merges" for human review.

### 3.3 Verification Posterior Formula
For each closure attempt $k$:
$$S_{\text{raw}} = 0.35 \cdot S_{\text{geo}} + 0.30 \cdot P(\text{resolved} \mid \text{vision}) + 0.20 \cdot P(\text{same\_site} \mid \text{vision}) + 0.15 \cdot S_{\text{citizen}}$$
Penalties:
- If pHash detects image reuse across tickets: $S_{\text{final}} = 0.0$ (Flag: `REUSED_PHOTO`)
- If distance $> 100\text{m}$: $S_{\text{final}} = 0.0$ (Flag: `OUT_OF_GEOFENCE`)
- If closure duration $< 10$ minutes from creation: Flag `RAPID_CLOSURE_SUSPICION`.

Confidence interval on sector resolution rate:
Wilson Score Interval:
$$w = \frac{\hat{p} + \frac{z^2}{2n} \pm z \sqrt{\frac{\hat{p}(1-\hat{p})}{n} + \frac{z^2}{4n^2}}}{1 + \frac{z^2}{n}}$$
Where $z = 1.96$ for 95% confidence.

---

## 4. Execution Command
The evaluation harness will be executable via a single command:
```bash
python eval/run_eval.py --all
```
Results will be output to `eval/results/summary.json` and formatted as a Markdown report in `eval/RESULTS.md`.
