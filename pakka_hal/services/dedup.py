import math
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from pakka_hal.models.incident import CanonicalIncident, TriageResult
from pakka_hal.storage.db import get_connection
from pakka_hal.services.llm import get_llm_provider

# Calibrated decision thresholds
TAU_MERGE = 0.80
TAU_SPLIT = 0.45

def haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Computes great-circle distance between two GPS coordinates in meters."""
    R = 6371000.0  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    a, b = np.array(v1), np.array(v2)
    norm_a, norm_b = np.linalg.norm(a), np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

class DedupService:
    def __init__(self, provider_type: Optional[str] = None):
        self.llm = get_llm_provider(provider_type)

    async def compute_similarity_score(
        self,
        triage: TriageResult,
        existing: CanonicalIncident,
        triage_embedding: Optional[List[float]] = None
    ) -> float:
        # 1. Category check
        if triage.category == existing.service_code:
            cat_score = 1.0
        else:
            # Different primary category -> very low chance of merging unless generic
            return 0.0

        # 2. Spatial score
        t_lat = triage.location.lat or 30.7333
        t_lon = triage.location.lon or 76.7794
        dist_m = haversine_distance_m(t_lat, t_lon, existing.lat, existing.lon)

        if dist_m <= 25.0:
            spatial_score = 1.0
        elif dist_m <= 100.0:
            spatial_score = 1.0 - ((dist_m - 25.0) / 75.0) * 0.5
        elif dist_m <= 250.0:
            spatial_score = 0.3
        else:
            return 0.0  # Outside spatial candidate radius for same incident

        # 3. Text semantic similarity
        if not triage_embedding:
            triage_embedding = await self.llm.get_embedding(triage.summary_en)
        existing_embedding = await self.llm.get_embedding(existing.description)
        text_sim = max(0.0, cosine_similarity(triage_embedding, existing_embedding))

        # 4. Temporal decay (incidents older than 14 days decay in merge likelihood)
        time_score = 1.0  # Default within active period

        # 5. Calibrated logistic combination
        # z = w1*spatial + w2*text + w3*cat - bias
        z = (3.5 * spatial_score) + (2.5 * text_sim) + (1.5 * cat_score) - 3.8
        prob = 1.0 / (1.0 + math.exp(-z))
        return float(prob)

    async def find_merge_candidate(
        self,
        triage: TriageResult
    ) -> Tuple[str, Optional[CanonicalIncident], float]:
        """
        Queries open incidents in spatial vicinity and evaluates merge probability.
        Returns:
            decision: "merge" | "suggest_merge" | "new"
            matched_incident: Optional[CanonicalIncident]
            match_score: float
        """
        t_lat = triage.location.lat if (triage.location and triage.location.lat is not None) else 30.7333
        t_lon = triage.location.lon if (triage.location and triage.location.lon is not None) else 76.7794

        # Spatial candidate bounding box (~350m radius) to utilize SQLite spatial indexes
        lat_delta = 0.0035
        lon_delta = 0.0040
        lat_min, lat_max = t_lat - lat_delta, t_lat + lat_delta
        lon_min, lon_max = t_lon - lon_delta, t_lon + lon_delta

        conn = get_connection()
        cur = conn.cursor()

        if triage.category and triage.category != "OTHER":
            cur.execute("""
                SELECT incident_id, service_code, service_name, title, description,
                       status, resolution_state, lat, lon, sector, reports_count,
                       assigned_department, routing_confidence, routing_abstained,
                       verification_score, before_media_url, after_media_url,
                       latest_ledger_hash, created_at, updated_at
                FROM canonical_incidents
                WHERE status = 'open'
                  AND service_code = ?
                  AND lat BETWEEN ? AND ?
                  AND lon BETWEEN ? AND ?
            """, (triage.category, lat_min, lat_max, lon_min, lon_max))
        else:
            cur.execute("""
                SELECT incident_id, service_code, service_name, title, description,
                       status, resolution_state, lat, lon, sector, reports_count,
                       assigned_department, routing_confidence, routing_abstained,
                       verification_score, before_media_url, after_media_url,
                       latest_ledger_hash, created_at, updated_at
                FROM canonical_incidents
                WHERE status = 'open'
                  AND lat BETWEEN ? AND ?
                  AND lon BETWEEN ? AND ?
            """, (lat_min, lat_max, lon_min, lon_max))

        rows = cur.fetchall()
        conn.close()

        if not rows:
            return "new", None, 0.0

        triage_embedding = await self.llm.get_embedding(triage.summary_en)
        best_incident = None
        best_score = 0.0

        for r in rows:
            inc = CanonicalIncident(
                incident_id=r["incident_id"],
                service_code=r["service_code"],
                service_name=r["service_name"],
                title=r["title"],
                description=r["description"],
                status=r["status"],
                resolution_state=r["resolution_state"],
                lat=r["lat"],
                lon=r["lon"],
                sector=r["sector"],
                reports_count=r["reports_count"],
                assigned_department=r["assigned_department"],
                routing_confidence=r["routing_confidence"],
                routing_abstained=bool(r["routing_abstained"]),
                verification_score=r["verification_score"],
                before_media_url=r["before_media_url"],
                after_media_url=r["after_media_url"],
                latest_ledger_hash=r["latest_ledger_hash"],
                created_at=r["created_at"],
                updated_at=r["updated_at"]
            )
            score = await self.compute_similarity_score(triage, inc, triage_embedding)
            if score > best_score:
                best_score = score
                best_incident = inc

        if best_score >= TAU_MERGE:
            return "merge", best_incident, best_score
        elif best_score >= TAU_SPLIT:
            return "suggest_merge", best_incident, best_score
        else:
            return "new", None, best_score
