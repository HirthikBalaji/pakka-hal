import hashlib
import json
from datetime import datetime, timezone
import uuid
from typing import Dict, Any, List, Optional, Tuple
from pakka_hal.config import HASH_CHAIN_SEED
from pakka_hal.storage.db import get_connection
from pakka_hal.models.ledger import LedgerEntry, LedgerChainStatus

GENESIS_HASH = hashlib.sha256(HASH_CHAIN_SEED.encode("utf-8")).hexdigest()

def compute_payload_hash(payload: Dict[str, Any]) -> str:
    """Computes deterministic SHA-256 hash of a JSON-serializable dictionary."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()

def compute_entry_hash(prev_hash: str, timestamp: str, incident_id: str, event_type: str, payload_hash: str) -> str:
    """Computes SHA-256 hash linking entry to previous hash."""
    message = f"{prev_hash}|{timestamp}|{incident_id}|{event_type}|{payload_hash}"
    return hashlib.sha256(message.encode("utf-8")).hexdigest()

def append_ledger_entry(incident_id: str, event_type: str, payload: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> LedgerEntry:
    """Appends an event to the linear cryptographic hash chain."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT seq, entry_hash FROM ledger ORDER BY seq DESC LIMIT 1")
    last_row = cur.fetchone()

    if last_row:
        prev_seq = last_row["seq"]
        prev_hash = last_row["entry_hash"]
        seq = prev_seq + 1
    else:
        seq = 1
        prev_hash = GENESIS_HASH

    now_iso = datetime.now(timezone.utc).isoformat()
    entry_id = f"led_{uuid.uuid4().hex[:12]}"
    payload_hash = compute_payload_hash(payload)
    entry_hash = compute_entry_hash(prev_hash, now_iso, incident_id, event_type, payload_hash)

    metadata_dict = metadata or {}
    cur.execute("""
        INSERT INTO ledger (entry_id, seq, timestamp, incident_id, event_type, payload_hash, prev_hash, entry_hash, metadata_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (entry_id, seq, now_iso, incident_id, event_type, payload_hash, prev_hash, entry_hash, json.dumps(metadata_dict)))

    # Update canonical incident's latest_ledger_hash
    cur.execute("""
        UPDATE canonical_incidents SET latest_ledger_hash = ?, updated_at = ? WHERE incident_id = ?
    """, (entry_hash, now_iso, incident_id))

    conn.commit()
    conn.close()

    return LedgerEntry(
        entry_id=entry_id,
        timestamp=now_iso,
        incident_id=incident_id,
        event_type=event_type,
        payload_hash=payload_hash,
        prev_hash=prev_hash,
        entry_hash=entry_hash,
        metadata=metadata_dict
    )

def verify_ledger_chain() -> LedgerChainStatus:
    """Validates the entire ledger from genesis to head."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT entry_id, seq, timestamp, incident_id, event_type, payload_hash, prev_hash, entry_hash FROM ledger ORDER BY seq ASC")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        return LedgerChainStatus(
            total_entries=0,
            genesis_hash=GENESIS_HASH,
            latest_hash=GENESIS_HASH,
            is_valid=True
        )

    expected_prev_hash = GENESIS_HASH
    for r in rows:
        # Verify prev_hash link
        if r["prev_hash"] != expected_prev_hash:
            return LedgerChainStatus(
                total_entries=len(rows),
                genesis_hash=GENESIS_HASH,
                latest_hash=rows[-1]["entry_hash"],
                is_valid=False,
                tampered_entry_id=r["entry_id"]
            )
        # Recompute entry hash
        computed_hash = compute_entry_hash(
            r["prev_hash"], r["timestamp"], r["incident_id"], r["event_type"], r["payload_hash"]
        )
        if computed_hash != r["entry_hash"]:
            return LedgerChainStatus(
                total_entries=len(rows),
                genesis_hash=GENESIS_HASH,
                latest_hash=rows[-1]["entry_hash"],
                is_valid=False,
                tampered_entry_id=r["entry_id"]
            )
        expected_prev_hash = r["entry_hash"]

    return LedgerChainStatus(
        total_entries=len(rows),
        genesis_hash=GENESIS_HASH,
        latest_hash=rows[-1]["entry_hash"],
        is_valid=True
    )

def get_incident_ledger_trail(incident_id: str) -> List[Dict[str, Any]]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT entry_id, seq, timestamp, incident_id, event_type, payload_hash, prev_hash, entry_hash, metadata_json
        FROM ledger WHERE incident_id = ? ORDER BY seq ASC
    """, (incident_id,))
    rows = cur.fetchall()
    conn.close()
    return [
        {
            "entry_id": r["entry_id"],
            "seq": r["seq"],
            "timestamp": r["timestamp"],
            "event_type": r["event_type"],
            "payload_hash": r["payload_hash"],
            "prev_hash": r["prev_hash"],
            "entry_hash": r["entry_hash"],
            "metadata": json.loads(r["metadata_json"]) if r["metadata_json"] else {}
        }
        for r in rows
    ]
