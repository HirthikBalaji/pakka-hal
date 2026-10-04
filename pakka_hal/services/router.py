import uuid
import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List, Tuple
from pakka_hal.config import city_config
from pakka_hal.models.incident import RoutingDecision, TriageResult
from pakka_hal.storage.db import get_connection

TAU_ABSTAIN = 0.70

class OwnershipRouter:
    """
    Ownership routing with calibrated abstention.
    Routes incident to responsible municipal department or abstains to human queue.
    """

    def __init__(self):
        self.departments = city_config.get("departments", [])
        self.dept_by_code: Dict[str, Dict[str, Any]] = {}
        for d in self.departments:
            for sc in d.get("service_codes", []):
                self.dept_by_code[sc] = d

    def route_incident(self, triage: TriageResult) -> RoutingDecision:
        category = triage.category
        sector = triage.location.sector or "Unknown"

        # Check if category is known
        if category in self.dept_by_code:
            dept = self.dept_by_code[category]
            base_conf = triage.field_confidence.get("category", 0.85)

            # If triage confidence was low, penalize
            if base_conf < TAU_ABSTAIN:
                return self._abstain(
                    triage,
                    f"Category confidence ({base_conf:.2f}) below threshold {TAU_ABSTAIN:.2f}."
                )

            return RoutingDecision(
                department_id=dept["id"],
                department_name=dept["name"],
                confidence=base_conf,
                abstained=False,
                reason=f"Rule-matched '{category}' to {dept['name']} for sector {sector}."
            )
        else:
            return self._abstain(
                triage,
                f"No automated routing rule for category '{category}' in municipal directory."
            )

    def _abstain(self, triage: TriageResult, reason: str) -> RoutingDecision:
        # Save to human triage queue table
        queue_id = f"htq_{uuid.uuid4().hex[:8]}"
        now_iso = datetime.now(timezone.utc).isoformat()

        # Provide top suggestions
        suggestions = [
            {"department_id": d["id"], "name": d["name"]}
            for d in self.departments[:3]
        ]

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO human_triage_queue (queue_id, incident_id, reason, suggested_departments_json, status, created_at)
            VALUES (?, ?, ?, ?, 'pending', ?)
        """, (queue_id, triage.report_id, reason, json.dumps(suggestions), now_iso))
        conn.commit()
        conn.close()

        return RoutingDecision(
            department_id="HUMAN_QUEUE",
            department_name="Central Municipal Grievance Desk (Abstained for Human Review)",
            confidence=0.40,
            abstained=True,
            reason=f"Abstained to Human Review: {reason}",
            alternative_candidates=suggestions
        )
