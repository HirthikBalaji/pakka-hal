import os
import sys
from pathlib import Path

# Add root directory to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))
sys.stdout.reconfigure(encoding='utf-8')

# Ensure clean isolated test database
TEST_DB_FILE = ROOT_DIR / "test_pakka.db"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_FILE}"
if TEST_DB_FILE.exists():
    try:
        TEST_DB_FILE.unlink()
    except Exception:
        pass

from pakka_hal.storage.db import init_db
init_db()

import tests.test_api as t

def run():
    tests_list = [
        ("Health Check", t.test_health_check),
        ("Open311 Services List", t.test_open311_services_list),
        ("Open311 Service Detail", t.test_open311_service_detail),
        ("Open311 Service Detail 404", t.test_open311_service_detail_404),
        ("Emergency Redirect Safety Net", t.test_emergency_redirect_safety_net),
        ("Regular Intake & Deduplication", t.test_regular_intake_and_deduplication),
        ("Field Worker Closure & Verification", t.test_field_worker_closure_and_verification),
        ("Citizen Reconfirmation Loop", t.test_citizen_reconfirmation_loop),
        ("Tamper-Evident Ledger Verification", t.test_tamper_evident_ledger_verification),
        ("Dashboard Metrics & Wilson Intervals", t.test_dashboard_metrics_and_wilson_intervals),
        ("Equity Bandit Simulation", t.test_equity_bandit_simulation),
        ("Emergency False-Positive Resistance", t.test_emergency_false_positive_resistance),
        ("Photo Reuse Fraud Rejection", t.test_reused_photo_fraud_rejection),
        ("Open311 Form-Urlencoded Intake", t.test_open311_form_urlencoded_intake)
    ]

    passed = 0
    failed = 0

    print("==================================================")
    print("        PAKKA HAL • TEST SUITE EXECUTION          ")
    print("==================================================")

    for name, func in tests_list:
        try:
            func()
            print(f"  [PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("--------------------------------------------------")
    print(f"Total: {len(tests_list)} | Passed: {passed} | Failed: {failed}")
    for ext in ["", "-wal", "-shm"]:
        f = Path(f"{TEST_DB_FILE}{ext}")
        if f.exists():
            try:
                f.unlink()
            except Exception:
                pass
    if failed == 0:
        print("All tests passed successfully!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run()
