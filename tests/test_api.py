from fastapi.testclient import TestClient
from main import app
from pakka_hal.services.verifier import wilson_score_interval
from pakka_hal.services.ledger import verify_ledger_chain

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["city"] == "Chandigarh"
    assert "Open311" in data["standard"]

def test_open311_services_list():
    response = client.get("/services.json")
    assert response.status_code == 200
    services = response.json()
    assert len(services) >= 7
    codes = [s["service_code"] for s in services]
    assert "STREETLIGHT_OUT" in codes
    assert "POTHOLE" in codes
    assert "GARBAGE_OVERFLOW" in codes

def test_open311_service_detail():
    response = client.get("/services/POTHOLE.json")
    assert response.status_code == 200
    assert response.json()["service_code"] == "POTHOLE"

def test_open311_service_detail_404():
    response = client.get("/services/NON_EXISTENT_SERVICE.json")
    assert response.status_code == 404

def test_emergency_redirect_safety_net():
    # Emergency reports MUST NEVER be queued as civic tickets
    response = client.post("/requests.json", json={
        "service_code": "STREETLIGHT_OUT",
        "description": "Building balcony collapsed fire in Sector 22 emergency 112!",
        "sector": "SEC-22"
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["account_id"] == "EMERGENCY_112"
    assert "CRITICAL_EMERGENCY_REDIRECT" in data[0]["service_notice"]

def test_regular_intake_and_deduplication():
    # 1. Submit initial report
    resp1 = client.post("/requests.json", json={
        "service_code": "STREETLIGHT_OUT",
        "description": "ਸੈਕਟਰ 22 ਮਾਰਕੀਟ ਵਿੱਚ ਬੱਤੀ ਖਰਾਬ ਹੈ",
        "sector": "SEC-22",
        "lat": 30.7333,
        "long": 76.7725
    })
    assert resp1.status_code == 200
    d1 = resp1.json()[0]
    canonical_id = d1["account_id"]
    req1_id = d1["service_request_id"]
    assert canonical_id.startswith("inc_")

    # 2. Submit near duplicate report (same sector, same defect)
    resp2 = client.post("/requests.json", json={
        "service_code": "STREETLIGHT_OUT",
        "description": "Sector 22 market di batti band hai dark spot",
        "sector": "SEC-22",
        "lat": 30.7334,
        "long": 76.7726
    })
    assert resp2.status_code == 200
    d2 = resp2.json()[0]
    # Should merge into the same canonical incident!
    assert d2["account_id"] == canonical_id
    assert "Merged into canonical incident" in d2["service_notice"]

    # 3. Query request details through Open311
    get_resp = client.get(f"/requests/{req1_id}.json")
    assert get_resp.status_code == 200
    detail = get_resp.json()[0]
    assert detail["service_request_id"] == req1_id
    assert detail["extended_attributes"]["canonical_incident_id"] == canonical_id
    assert detail["extended_attributes"]["reports_count"] >= 2

def test_field_worker_closure_and_verification():
    # 1. Create an incident
    create_resp = client.post("/requests.json", json={
        "service_code": "POTHOLE",
        "description": "Road crater in Sector 35 near chowk",
        "sector": "SEC-35",
        "lat": 30.7225,
        "long": 76.7621
    })
    inc_id = create_resp.json()[0]["account_id"]

    # 2. Submit closure with matching GPS
    closure_resp = client.post("/api/v1/closure/submit", json={
        "incident_id": inc_id,
        "worker_id": "WORKER_ROAD_01",
        "worker_lat": 30.7225,
        "worker_lon": 76.7621,
        "after_media_base64": "data:image/jpeg;base64,valid_after_image_repair",
        "notes": "Filled with bitumen and rolled flat."
    })
    assert closure_resp.status_code == 200
    res = closure_resp.json()
    assert res["incident_id"] == inc_id
    assert res["geofence_passed"] is True
    assert res["final_posterior_score"] >= 0.70
    assert res["verified_state"] in ["fixed_verified", "fixed_unverified"]

def test_citizen_reconfirmation_loop():
    # 1. Create and close incident
    create_resp = client.post("/requests.json", json={
        "service_code": "GARBAGE_OVERFLOW",
        "description": "Kuda da dher in Sector 17 plaza",
        "sector": "SEC-17",
        "lat": 30.7414,
        "long": 76.7845
    })
    inc_id = create_resp.json()[0]["account_id"]

    client.post("/api/v1/closure/submit", json={
        "incident_id": inc_id,
        "worker_id": "MOH_SAN_07",
        "worker_lat": 30.7414,
        "worker_lon": 76.7845,
        "after_media_base64": "data:image/jpeg;base64,clean_plaza",
        "notes": "Garbage cleared."
    })

    # 2. Citizen votes 'fixed'
    vote_resp = client.post("/api/v1/closure/citizen-confirm", json={
        "incident_id": inc_id,
        "citizen_feedback": "fixed"
    })
    assert vote_resp.status_code == 200
    v_data = vote_resp.json()
    assert v_data["verified_state"] == "fixed_verified"
    assert v_data["final_posterior_score"] >= 0.80

def test_tamper_evident_ledger_verification():
    verify_resp = client.get("/api/v1/ledger/verify")
    assert verify_resp.status_code == 200
    chain = verify_resp.json()
    assert chain["is_valid"] is True
    assert chain["total_entries"] > 0
    assert chain["tampered_entry_id"] is None

def test_dashboard_metrics_and_wilson_intervals():
    resp = client.get("/api/v1/dashboard/metrics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["city"] == "Chandigarh"
    assert "summary" in data
    assert "sectors" in data

    # Test Wilson interval formula directly
    p_hat, lower, upper = wilson_score_interval(positives=10, total=20, confidence=0.95)
    assert 0.0 < lower < p_hat < upper < 1.0
    assert round(p_hat, 2) == 0.50

def test_equity_bandit_simulation():
    resp = client.get("/api/v1/equity/silent-areas")
    assert resp.status_code == 200
    eq = resp.json()
    assert eq["provenance"] == "simulated"
    assert "benchmark_metrics" in eq
    assert eq["benchmark_metrics"]["correlation_gain"] >= 0.0
    assert len(eq["suggested_audits"]) > 0
