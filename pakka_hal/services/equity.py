import numpy as np
from typing import Dict, Any, List, Tuple
from pakka_hal.config import city_config

class EquityEstimator:
    """
    Equity Module: Corrects for reporting bias (the unobserved denominator).
    Areas with fewer complaints may have lower reporting propensity (pi_a), not zero defects (lambda_a).
    Uses a multi-armed bandit (Thompson Sampling) to suggest proactive municipal audit cells.
    """

    def __init__(self, num_sectors: int = 60):
        self.num_sectors = num_sectors
        self.sectors = [f"SEC-{i}" for i in range(1, num_sectors + 1)]

    def run_simulation_benchmark(
        self,
        seed: int = 42
    ) -> Dict[str, Any]:
        """
        Runs the open simulator comparing naive complaint counts against the Thompson-sampling audit estimator.
        Returns rank correlations, MAE, and identified silent sectors.
        """
        rng = np.random.default_rng(seed)

        # 1. True underlying defect rate lambda_a (unknown to naive municipal portals)
        true_lambda = rng.gamma(shape=3.0, scale=4.0, size=self.num_sectors)

        # 2. Reporting propensity pi_a (higher in affluent/connected sectors, lower in peri-urban sectors)
        propensity = rng.beta(a=2.0, b=4.0, size=self.num_sectors)
        propensity = np.clip(propensity, 0.1, 0.95)

        # 3. Observed citizen reports (Poisson)
        observed_reports = rng.poisson(true_lambda * propensity)

        # 4. Thompson Sampling Bandit for Field Audits (prior: Gamma(alpha=1, beta=1))
        # Prior parameters for each sector
        alphas = np.ones(self.num_sectors) + observed_reports
        betas = np.ones(self.num_sectors) + propensity

        # Draw posterior samples to allocate 15 field audits
        total_audits = 15
        audit_allocations = np.zeros(self.num_sectors, dtype=int)
        for _ in range(total_audits):
            # Sample from Gamma posterior
            samples = rng.gamma(alphas, 1.0 / betas)
            # Prioritize high uncertainty and high ratio of estimated lambda to observed reports
            uncertainty_weights = samples / (observed_reports + 1.0)
            chosen_sector = np.argmax(uncertainty_weights)
            audit_allocations[chosen_sector] += 1
            # Update posterior with simulated audit inspection
            detected_audit_defects = rng.poisson(true_lambda[chosen_sector] * 0.5)
            alphas[chosen_sector] += detected_audit_defects
            betas[chosen_sector] += 0.5

        # 5. Estimated lambda via Bayesian posterior mean
        estimated_lambda = alphas / betas

        # 6. Silent Area Score: P(lambda is in top 20% while observed reports are in bottom 30%)
        lambda_80th = np.percentile(estimated_lambda, 70)
        reports_30th = np.percentile(observed_reports, 40)

        silent_scores = {}
        suggested_audits = []

        for i, s_id in enumerate(self.sectors):
            # High estimated defects, but low reported voice
            is_silent = estimated_lambda[i] >= lambda_80th and observed_reports[i] <= reports_30th
            silent_score = float(max(0.0, (estimated_lambda[i] / (observed_reports[i] + 1.0)) * 0.2))
            silent_scores[s_id] = {
                "observed_reports": int(observed_reports[i]),
                "estimated_true_defects": round(float(estimated_lambda[i]), 2),
                "true_lambda": round(float(true_lambda[i]), 2),
                "silent_area_score": round(min(1.0, silent_score), 3),
                "is_silent_risk": bool(is_silent),
                "audits_conducted": int(audit_allocations[i])
            }
            if is_silent or audit_allocations[i] > 0:
                suggested_audits.append({
                    "sector": s_id,
                    "reason": f"High defect risk ({estimated_lambda[i]:.1f}) vs low reports ({observed_reports[i]}). Recommend ground inspection.",
                    "priority": "HIGH" if is_silent else "MEDIUM"
                })

        # 7. Metrics: Spearman rank correlation with truth
        naive_corr = float(np.corrcoef(observed_reports, true_lambda)[0, 1])
        estimator_corr = float(np.corrcoef(estimated_lambda, true_lambda)[0, 1])
        naive_mae = float(np.mean(np.abs(observed_reports - true_lambda)))
        estimator_mae = float(np.mean(np.abs(estimated_lambda - true_lambda)))

        return {
            "provenance": "simulated",
            "benchmark_metrics": {
                "naive_correlation_with_truth": round(naive_corr, 3),
                "estimator_correlation_with_truth": round(estimator_corr, 3),
                "naive_mae": round(naive_mae, 2),
                "estimator_mae": round(estimator_mae, 2),
                "correlation_gain": round(estimator_corr - naive_corr, 3)
            },
            "suggested_audits": suggested_audits[:8],
            "sector_details": {k: silent_scores[k] for k in list(silent_scores.keys())[:15]}
        }
