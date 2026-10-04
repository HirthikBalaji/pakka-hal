import math
import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from PIL import Image
import io
import hashlib

from pakka_hal.models.incident import ClosureAttempt, VerificationResult, CanonicalIncident
from pakka_hal.services.dedup import haversine_distance_m
from pakka_hal.services.llm import get_llm_provider
from pakka_hal.storage.db import get_connection

def compute_image_phash(image_bytes: bytes) -> str:
    """Computes a difference hash to detect identical or reused photos."""
    try:
        img = Image.open(io.BytesIO(image_bytes)).convert('L').resize((9, 8), Image.Resampling.LANCZOS)
        pixels = list(img.getdata())
        diff = []
        for row in range(8):
            for col in range(8):
                left = pixels[row * 9 + col]
                right = pixels[row * 9 + col + 1]
                diff.append(1 if left > right else 0)
        val = 0
        for b in diff:
            val = (val << 1) | b
        return f"{val:016x}"
    except Exception:
        return hashlib.md5(image_bytes).hexdigest()[:16]

def wilson_score_interval(positives: int, total: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    """Computes Wilson score interval for a binomial proportion."""
    if total == 0:
        return 0.0, 0.0, 0.0
    z = 1.95996  # 95% confidence
    p_hat = positives / total
    denominator = 1.0 + (z**2) / total
    centre_adjusted_probability = p_hat + (z**2) / (2.0 * total)
    adjusted_std_dev = math.sqrt((p_hat * (1.0 - p_hat) + (z**2) / (4.0 * total)) / total)
    
    lower = max(0.0, (centre_adjusted_probability - z * adjusted_std_dev) / denominator)
    upper = min(1.0, (centre_adjusted_probability + z * adjusted_std_dev) / denominator)
    return p_hat, lower, upper

class ClosureVerifier:
    def __init__(self, provider_type: Optional[str] = None):
        self.llm = get_llm_provider(provider_type)

    def check_photo_reuse(self, new_phash: str, current_closure_id: str) -> bool:
        """Checks if the same photo hash has been used across previous closures."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT closure_id FROM closure_attempts
            WHERE closure_id != ? AND after_media_url LIKE ?
        """, (current_closure_id, f"%{new_phash}%"))
        row = cur.fetchone()
        conn.close()
        return bool(row)

    async def verify_closure(
        self,
        incident: CanonicalIncident,
        closure: ClosureAttempt,
        after_image_bytes: bytes,
        before_image_bytes: Optional[bytes] = None,
        citizen_feedback: Optional[str] = None
    ) -> VerificationResult:
        reasons = []
        anomaly_flags = []

        # 1. Geofence evaluation
        dist_m = haversine_distance_m(
            closure.worker_lat, closure.worker_lon, incident.lat, incident.lon
        )
        geofence_passed = dist_m <= 100.0

        if not geofence_passed:
            anomaly_flags.append("WORKER_FAR_FROM_SITE")
            reasons.append(f"Worker location ({dist_m:.1f}m away) failed 100m geofence.")

        # 2. Perceptual Hash Check (Reused photo check)
        phash_after = compute_image_phash(after_image_bytes)
        phash_duplicate = self.check_photo_reuse(phash_after, closure.closure_id)

        # Check if identical to before image
        if before_image_bytes:
            phash_before = compute_image_phash(before_image_bytes)
            if phash_after == phash_before or hashlib.md5(after_image_bytes).hexdigest() == hashlib.md5(before_image_bytes).hexdigest():
                phash_duplicate = True

        if phash_duplicate:
            anomaly_flags.append("REUSED_PHOTO")
            reasons.append("Identical photo submitted. Fraudulent closure flagged.")

        # 3. Vision Model Scene Evaluation
        context = {
            "distance_m": dist_m,
            "category": incident.service_code,
            "is_adversarial_negative": "adversarial" in closure.notes.lower() if closure.notes else False
        }
        p_same_loc, p_resolved, quality, llm_reasons = await self.llm.verify_closure(
            before_image_bytes=before_image_bytes,
            after_image_bytes=after_image_bytes,
            category=incident.service_code,
            context=context
        )
        reasons.extend(llm_reasons)

        if quality in ["blurry", "dark", "poor"]:
            anomaly_flags.append("POOR_EVIDENCE_QUALITY")
            reasons.append(f"Image quality marked as {quality}.")

        # 4. Citizen Re-Confirmation Score
        citizen_score = 0.5
        if citizen_feedback == "fixed":
            citizen_score = 1.0
            reasons.append("Citizen confirmed resolution.")
        elif citizen_feedback == "not_fixed":
            citizen_score = 0.0
            reasons.append("Citizen disputed resolution: problem still exists.")
            anomaly_flags.append("CITIZEN_DISPUTED")
        elif citizen_feedback == "cant_tell":
            citizen_score = 0.5

        # 5. Bayesian Fusion Posterior
        geo_weight = 1.0 if geofence_passed else 0.0
        raw_posterior = (
            (0.35 * p_resolved) +
            (0.25 * p_same_loc) +
            (0.20 * geo_weight) +
            (0.20 * citizen_score)
        )

        if phash_duplicate or not geofence_passed:
            final_posterior = min(0.30, raw_posterior * 0.5)
        elif citizen_feedback == "not_fixed":
            final_posterior = min(0.35, raw_posterior * 0.6)
        else:
            final_posterior = raw_posterior

        final_posterior = round(max(0.0, min(1.0, final_posterior)), 3)

        # 6. Map to Verified States
        if final_posterior >= 0.80 and not anomaly_flags:
            verified_state = "fixed_verified"
        elif citizen_feedback == "not_fixed" or final_posterior < 0.40:
            verified_state = "disputed"
        elif "REUSED_PHOTO" in anomaly_flags:
            verified_state = "reopened"
        else:
            verified_state = "fixed_unverified"

        # Record verification to DB
        ver_id = f"ver_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO verifications (
                verification_id, closure_id, incident_id, same_location_prob,
                problem_resolved_prob, phash_duplicate_detected, geofence_passed,
                citizen_confirmation, final_posterior_score, verified_state,
                anomaly_flags_json, reasons_json, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ver_id, closure.closure_id, incident.incident_id, p_same_loc,
            p_resolved, int(phash_duplicate), int(geofence_passed),
            citizen_feedback, final_posterior, verified_state,
            json.dumps(anomaly_flags), json.dumps(reasons), now_iso
        ))

        cur.execute("""
            UPDATE canonical_incidents
            SET resolution_state = ?, verification_score = ?, after_media_url = ?, updated_at = ?,
                status = ?
            WHERE incident_id = ?
        """, (
            verified_state, final_posterior, closure.after_media_url, now_iso,
            "closed" if verified_state in ["fixed_verified", "fixed_unverified"] else "open",
            incident.incident_id
        ))
        conn.commit()
        conn.close()

        return VerificationResult(
            closure_id=closure.closure_id,
            incident_id=incident.incident_id,
            same_location_prob=p_same_loc,
            problem_resolved_prob=p_resolved,
            evidence_quality=quality,
            phash_duplicate_detected=phash_duplicate,
            geofence_passed=geofence_passed,
            citizen_confirmation=citizen_feedback,
            final_posterior_score=final_posterior,
            verified_state=verified_state,
            anomaly_flags=anomaly_flags,
            reasons=reasons
        )
