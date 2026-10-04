import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from pakka_hal.config import DATABASE_URL, BASE_DIR

DB_PATH = Path(DATABASE_URL.replace("sqlite:///", ""))
if not DB_PATH.is_absolute():
    DB_PATH = BASE_DIR / DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Raw intake reports
    cur.execute("""
    CREATE TABLE IF NOT EXISTS service_requests (
        service_request_id TEXT PRIMARY KEY,
        token TEXT,
        service_code TEXT,
        description TEXT,
        lat REAL,
        long REAL,
        address_string TEXT,
        sector TEXT,
        language TEXT,
        media_url TEXT,
        voice_note_url TEXT,
        status TEXT DEFAULT 'open',
        status_notes TEXT,
        canonical_incident_id TEXT,
        is_duplicate INTEGER DEFAULT 0,
        triage_json TEXT,
        requested_datetime TEXT,
        updated_datetime TEXT
    )
    """)

    # Canonical incidents (deduplicated)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS canonical_incidents (
        incident_id TEXT PRIMARY KEY,
        service_code TEXT,
        service_name TEXT,
        title TEXT,
        description TEXT,
        status TEXT DEFAULT 'open',
        resolution_state TEXT DEFAULT 'open',
        lat REAL,
        lon REAL,
        sector TEXT,
        reports_count INTEGER DEFAULT 1,
        assigned_department TEXT,
        routing_confidence REAL DEFAULT 0.0,
        routing_abstained INTEGER DEFAULT 0,
        verification_score REAL DEFAULT 0.0,
        before_media_url TEXT,
        after_media_url TEXT,
        latest_ledger_hash TEXT,
        created_at TEXT,
        updated_at TEXT
    )
    """)

    # Child report link table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS incident_reports (
        incident_id TEXT,
        report_id TEXT,
        merged_at TEXT,
        similarity_score REAL,
        PRIMARY KEY (incident_id, report_id)
    )
    """)

    # Closure attempts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS closure_attempts (
        closure_id TEXT PRIMARY KEY,
        incident_id TEXT,
        worker_id TEXT,
        after_media_url TEXT,
        worker_lat REAL,
        worker_lon REAL,
        distance_to_incident_m REAL,
        timestamp TEXT,
        notes TEXT,
        FOREIGN KEY(incident_id) REFERENCES canonical_incidents(incident_id)
    )
    """)

    # Verifications
    cur.execute("""
    CREATE TABLE IF NOT EXISTS verifications (
        verification_id TEXT PRIMARY KEY,
        closure_id TEXT,
        incident_id TEXT,
        same_location_prob REAL,
        problem_resolved_prob REAL,
        phash_duplicate_detected INTEGER,
        geofence_passed INTEGER,
        citizen_confirmation TEXT,
        final_posterior_score REAL,
        verified_state TEXT,
        anomaly_flags_json TEXT,
        reasons_json TEXT,
        verified_at TEXT
    )
    """)

    # Hash-chained public ledger
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledger (
        entry_id TEXT PRIMARY KEY,
        seq INTEGER,
        timestamp TEXT,
        incident_id TEXT,
        event_type TEXT,
        payload_hash TEXT,
        prev_hash TEXT,
        entry_hash TEXT,
        metadata_json TEXT
    )
    """)

    # Human triage queue (for router abstentions)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS human_triage_queue (
        queue_id TEXT PRIMARY KEY,
        incident_id TEXT,
        reason TEXT,
        suggested_departments_json TEXT,
        status TEXT DEFAULT 'pending', -- pending, resolved
        resolved_by TEXT,
        resolved_at TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()

# Initialize on import
init_db()
