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

    def _resolve_zonal_office(self, sector: str) -> str:
        """Resolves Chandigarh municipal engineering sub-division based on sector grid."""
        import re
        match = re.search(r"(\d+)", sector)
        if match:
            num = int(match.group(1))
            if num <= 28:
                return "Division 1 (North Zone)"
            elif num <= 47:
                return "Division 2 (South Zone)"
            else:
                return "Division 3 (South-West Zone)"
        if "IT" in sector.upper() or "IND" in sector.upper():
            return "Division 4 (East/Industrial Zone)"
        return "Central Zone"

    def route_incident(self, triage: TriageResult) -> RoutingDecision:
        category = triage.category
        sector = triage.location.sector or "Unknown"
        sub_division = self._resolve_zonal_office(sector)

        # 1. Check if category is known in municipal charter
        if category in self.dept_by_code:
            dept = self.dept_by_code[category]
            base_conf = triage.field_confidence.get("category", 0.85)

            # Check cross-cutting ambiguity in description
            text_lower = (triage.summary_en or "").lower()
            competing_depts = []
            for sc, d in self.dept_by_code.items():
                if d["id"] != dept["id"] and sc.lower().replace("_", " ") in text_lower:
                    competing_depts.append(d)

            if competing_depts and base_conf < 0.80:
                # Borderline jurisdictional ambiguity
                return self._abstain(
                    triage,
                    f"Cross-jurisdictional ambiguity between {dept['name']} and {competing_depts[0]['name']}."
                )

            # If triage confidence was low, penalize and abstain
            if base_conf < TAU_ABSTAIN:
                return self._abstain(
                    triage,
                    f"Category confidence ({base_conf:.2f}) below threshold {TAU_ABSTAIN:.2f}."
                )

            resolved_dept_name = f"{dept['name']} - {sub_division}"
            return RoutingDecision(
                department_id=dept["id"],
                department_name=resolved_dept_name,
                confidence=base_conf,
                abstained=False,
                reason=f"Matched '{category}' to {dept['name']} for sector {sector} ({sub_division})."
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
