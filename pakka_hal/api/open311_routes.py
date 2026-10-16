import uuid
import json
import base64
import io
from PIL import Image
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Body, Request
from pakka_hal.config import city_config, BASE_DIR
from pakka_hal.models.open311 import (
    Open311Service, Open311RequestCreate, Open311RequestResponse, Open311RequestDetail
)
from pakka_hal.models.incident import CanonicalIncident
from pakka_hal.storage.db import get_connection
from pakka_hal.services.triage import TriageService
from pakka_hal.services.dedup import DedupService
from pakka_hal.services.router import OwnershipRouter
from pakka_hal.services.ledger import append_ledger_entry

router = APIRouter(tags=["Open311 GeoReport v2"])

triage_service = TriageService()
dedup_service = DedupService()
ownership_router = OwnershipRouter()

@router.get("/services.json", response_model=List[Open311Service])
def get_services():
    """Returns the list of civic service types supported by Chandigarh."""
    services = []
    for s in city_config.get("service_types", []):
        services.append(Open311Service(
            service_code=s["service_code"],
            service_name=s["service_name"],
            description=s.get("description"),
            metadata=s.get("metadata", True),
            type=s.get("type", "realtime"),
            keywords=s.get("keywords", []),
            group="Civic Infrastructure"
        ))
    return services

@router.get("/services/{service_code}.json", response_model=Open311Service)
def get_service_detail(service_code: str):
    for s in city_config.get("service_types", []):
        if s["service_code"].upper() == service_code.upper():
            return Open311Service(
                service_code=s["service_code"],
                service_name=s["service_name"],
                description=s.get("description"),
                metadata=s.get("metadata", True),
                type=s.get("type", "realtime"),
                keywords=s.get("keywords", []),
                group="Civic Infrastructure"
            )
    raise HTTPException(status_code=404, detail=f"Service code '{service_code}' not found.")

from urllib.parse import parse_qs

@router.post("/requests.json", response_model=List[Open311RequestResponse])
async def create_request(request: Request):
    """
    Open311 GeoReport v2 endpoint for reporting civic issues.
    Supports both JSON and application/x-www-form-urlencoded (standard Open311 GeoReport v2).
    Enhanced by Pakka Hal:
    1. Multilingual Triage (text/voice transcript)
    2. Emergency Safety-Net Detection (redirects if danger to life)
    3. Spatial-Semantic Deduplication
    4. Ownership Routing with Abstention
    5. Hash-Chained Public Ledger Audit Entry
    """
    ct = request.headers.get("content-type", "")
    if "application/x-www-form-urlencoded" in ct:
        raw_body = await request.body()
        parsed = {k: v[0] for k, v in parse_qs(raw_body.decode("utf-8")).items()}
        if "latitude" in parsed and "lat" not in parsed:
            parsed["lat"] = parsed["latitude"]
        if "longitude" in parsed and "long" not in parsed:
            parsed["long"] = parsed["longitude"]
        for num_field in ["lat", "long"]:
            if num_field in parsed and parsed[num_field]:
                try:
                    parsed[num_field] = float(parsed[num_field])
                except ValueError:
                    pass
        payload = Open311RequestCreate(**parsed)
    else:
        body = await request.json()
        payload = Open311RequestCreate(**body)
    raw_desc = payload.description or ""
    req_id = f"req_{uuid.uuid4().hex[:10]}"
    token = f"tok_{uuid.uuid4().hex[:8]}"
    now_iso = datetime.now(timezone.utc).isoformat()

    # 1. Process and persist intake evidence photo (if provided)
    image_bytes = None
    stored_media_url = payload.media_url
    if payload.media_url:
        try:
            if payload.media_url.startswith("data:image") or len(payload.media_url) > 100:
                b64_str = payload.media_url.split(",")[-1]
                image_bytes = base64.b64decode(b64_str)
                # Verify valid image
                img = Image.open(io.BytesIO(image_bytes))
                media_dir = BASE_DIR / "static" / "media"
                media_dir.mkdir(parents=True, exist_ok=True)
                file_name = f"{req_id}_before.jpg"
                img.convert("RGB").save(media_dir / file_name, "JPEG")
                stored_media_url = f"/static/media/{file_name}"
        except Exception:
            image_bytes = None

    # 2. Run Triage
    triage_res = await triage_service.process_report(
        description=raw_desc,
        image_bytes=image_bytes,
        audio_transcript=payload.description if payload.language else None,
        sector_hint=payload.sector
    )

    # 3. Emergency check
    if triage_res.emergency:
        return [Open311RequestResponse(
            service_request_id=req_id,
            token=token,
            service_notice="CRITICAL_EMERGENCY_REDIRECT: Immediate threat detected. Please dial 112 directly. Not queued as a civic ticket.",
            account_id="EMERGENCY_112"
        )]

    # 4. Deduplication check
    decision, matched_inc, sim_score = await dedup_service.find_merge_candidate(triage_res)

    lat = payload.lat or triage_res.location.lat or 30.7333
    lon = payload.long or triage_res.location.lon or 76.7794
    sector = payload.sector or triage_res.location.sector or "SEC-17"
    category = triage_res.category if triage_res.category != "OTHER" else (payload.service_code or "OTHER")

    # 5. Routing
    routing_decision = ownership_router.route_incident(triage_res)

    conn = get_connection()
    cur = conn.cursor()

    if decision == "merge" and matched_inc:
        # Merge into existing canonical incident
        canon_id = matched_inc.incident_id
        is_dup = 1
        new_count = matched_inc.reports_count + 1

        cur.execute("""
            UPDATE canonical_incidents
            SET reports_count = ?, updated_at = ?
            WHERE incident_id = ?
        """, (new_count, now_iso, canon_id))

        cur.execute("""
            INSERT INTO incident_reports (incident_id, report_id, merged_at, similarity_score)
            VALUES (?, ?, ?, ?)
        """, (canon_id, req_id, now_iso, sim_score))

        notice = f"Merged into canonical incident {canon_id} (Similarity: {sim_score:.2f})."
        event_type = "merged"
    else:
        # Create brand new canonical incident
        canon_id = f"inc_{uuid.uuid4().hex[:8]}"
        is_dup = 0

        # Find service name
        s_name = category.replace("_", " ").title()
        for st in city_config.get("service_types", []):
            if st["service_code"] == category:
                s_name = st["service_name"]
                break

        cur.execute("""
            INSERT INTO canonical_incidents (
                incident_id, service_code, service_name, title, description,
                status, resolution_state, lat, lon, sector, reports_count,
                assigned_department, routing_confidence, routing_abstained,
                verification_score, before_media_url, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, 'open', 'open', ?, ?, ?, 1, ?, ?, ?, 0.0, ?, ?, ?)
        """, (
            canon_id, category, s_name, f"{s_name} at {sector}", raw_desc,
            lat, lon, sector, routing_decision.department_name,
            routing_decision.confidence, int(routing_decision.abstained),
            stored_media_url, now_iso, now_iso
        ))

        cur.execute("""
            INSERT INTO incident_reports (incident_id, report_id, merged_at, similarity_score)
            VALUES (?, ?, ?, 1.0)
        """, (canon_id, req_id, now_iso))

        notice = f"Incident created and routed to {routing_decision.department_name}."
        if routing_decision.abstained:
            notice += " (Abstained to Human Review Desk)"
        event_type = "report_received"

    # Save raw intake record
    cur.execute("""
        INSERT INTO service_requests (
            service_request_id, token, service_code, description, lat, long,
            address_string, sector, language, media_url, voice_note_url,
            status, status_notes, canonical_incident_id, is_duplicate,
            triage_json, requested_datetime, updated_datetime
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'open', ?, ?, ?, ?, ?, ?)
    """, (
        req_id, token, category, raw_desc, lat, lon, payload.address_string or sector,
        sector, triage_res.language_detected, payload.media_url, payload.voice_note_url,
        notice, canon_id, is_dup, json.dumps(triage_res.model_dump()), now_iso, now_iso
    ))

    conn.commit()
    conn.close()

    # Append to SHA-256 Ledger
    append_ledger_entry(
        incident_id=canon_id,
        event_type=event_type,
        payload={
            "report_id": req_id,
            "category": category,
            "sector": sector,
            "description": raw_desc[:120],
            "is_duplicate": bool(is_dup)
        },
        metadata={"similarity_score": sim_score}
    )

    return [Open311RequestResponse(
        service_request_id=req_id,
        token=token,
        service_notice=notice,
        account_id=canon_id
    )]

@router.get("/requests/{service_request_id}.json", response_model=List[Open311RequestDetail])
def get_request_status(service_request_id: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT r.*, c.resolution_state, c.verification_score, c.latest_ledger_hash,
               c.assigned_department, c.reports_count, c.after_media_url
        FROM service_requests r
        LEFT JOIN canonical_incidents c ON r.canonical_incident_id = c.incident_id
        WHERE r.service_request_id = ? OR r.canonical_incident_id = ?
    """, (service_request_id, service_request_id))
    rows = cur.fetchall()
    conn.close()

    if not rows:
        raise HTTPException(status_code=404, detail=f"Request '{service_request_id}' not found.")

    results = []
    for r in rows:
        results.append(Open311RequestDetail(
            service_request_id=r["service_request_id"],
            status=r["status"],
            status_notes=r["status_notes"],
            service_name=r["service_code"].replace("_", " ").title(),
            service_code=r["service_code"],
            description=r["description"],
            agency_responsible=r["assigned_department"],
            service_notice=r["status_notes"],
            requested_datetime=r["requested_datetime"],
            updated_datetime=r["updated_datetime"],
            lat=r["lat"],
            long=r["long"],
            media_url=r["media_url"],
            extended_attributes={
                "canonical_incident_id": r["canonical_incident_id"],
                "resolution_state": r["resolution_state"] or "open",
                "verification_score": r["verification_score"] or 0.0,
                "reports_count": r["reports_count"] or 1,
                "latest_ledger_hash": r["latest_ledger_hash"],
                "after_media_url": r["after_media_url"],
                "is_duplicate": bool(r["is_duplicate"])
            }
        ))
    return results

@router.get("/requests.json", response_model=List[Open311RequestDetail])
def list_requests(
    service_code: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50
):
    conn = get_connection()
    cur = conn.cursor()
    query = """
        SELECT r.*, c.resolution_state, c.verification_score, c.latest_ledger_hash,
               c.assigned_department, c.reports_count, c.after_media_url
        FROM service_requests r
        LEFT JOIN canonical_incidents c ON r.canonical_incident_id = c.incident_id
        WHERE 1=1
    """
    params = []
    if service_code:
        query += " AND r.service_code = ?"
        params.append(service_code)
    if status:
        query += " AND r.status = ?"
        params.append(status)
    query += " ORDER BY r.requested_datetime DESC LIMIT ?"
    params.append(limit)

    cur.execute(query, tuple(params))
    rows = cur.fetchall()
    conn.close()

    results = []
    for r in rows:
        results.append(Open311RequestDetail(
            service_request_id=r["service_request_id"],
            status=r["status"],
            status_notes=r["status_notes"],
            service_name=r["service_code"].replace("_", " ").title(),
            service_code=r["service_code"],
            description=r["description"],
            agency_responsible=r["assigned_department"],
            service_notice=r["status_notes"],
            requested_datetime=r["requested_datetime"],
            updated_datetime=r["updated_datetime"],
            lat=r["lat"],
            long=r["long"],
            media_url=r["media_url"],
            extended_attributes={
                "canonical_incident_id": r["canonical_incident_id"],
                "resolution_state": r["resolution_state"] or "open",
                "verification_score": r["verification_score"] or 0.0,
                "reports_count": r["reports_count"] or 1,
                "latest_ledger_hash": r["latest_ledger_hash"],
                "is_duplicate": bool(r["is_duplicate"])
            }
        ))
    return results
