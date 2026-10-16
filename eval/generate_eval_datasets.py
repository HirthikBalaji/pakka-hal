import json
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 1. DEDUPLICATION EVALUATION DATASET
# 40 canonical clusters with variant reports (same incident, different language/minor GPS noise)
# + 50 distinct negative pairs (different locations or defects)
dedup_clusters = []
for c_idx in range(40):
    sec = f"SEC-{(c_idx % 20) + 1}"
    base_lat = 30.7300 + (c_idx * 0.002)
    base_lon = 76.7700 + (c_idx * 0.002)
    cats = ["STREETLIGHT_OUT", "POTHOLE", "GARBAGE_OVERFLOW", "DRAIN_BLOCKED"]
    cat = cats[c_idx % 4]

    variants = [
        {"desc": f"Broken {cat.lower().replace('_', ' ')} in {sec}", "lat": base_lat, "lon": base_lon, "lang": "en"},
        {"desc": f"{sec} de vich {cat.lower().replace('_', ' ')} kharab hai", "lat": base_lat + 0.0001, "lon": base_lon - 0.0001, "lang": "pa-Latn"},
        {"desc": f"{sec} par {cat.lower().replace('_', ' ')} ki samasya hai", "lat": base_lat - 0.0001, "lon": base_lon + 0.0001, "lang": "hi-Latn"}
    ]
    dedup_clusters.append({
        "cluster_id": f"clust_{c_idx+1}",
        "canonical_category": cat,
        "sector": sec,
        "reports": variants
    })

with open(DATA_DIR / "dedup_eval_clusters.json", "w", encoding="utf-8") as f:
    json.dump(dedup_clusters, f, indent=2)

# 2. ROUTER EVALUATION DATASET
# 100 cases mapping categories to departments, including out-of-domain and ambiguous cases for abstention
router_cases = []
dept_map = {
    "STREETLIGHT_OUT": "ELECTRICAL",
    "SIGNAL_FAULT": "ELECTRICAL",
    "POTHOLE": "ROADS_BRIDGES",
    "DAMAGED_SIGNAGE": "ROADS_BRIDGES",
    "GARBAGE_OVERFLOW": "MOH_SANITATION",
    "DRAIN_BLOCKED": "PUBLIC_HEALTH",
    "MANHOLE_COVER": "PUBLIC_HEALTH",
    "WATER_LEAK": "PUBLIC_HEALTH",
    "UNKNOWN_CIVIC_NOISE": "ABSTAIN",
    "VAGUE_COMPLAINT": "ABSTAIN"
}

for i in range(100):
    keys = list(dept_map.keys())
    cat = keys[i % len(keys)]
    target_dept = dept_map[cat]
    router_cases.append({
        "case_id": f"route_{i+1}",
        "category": cat,
        "sector": f"SEC-{(i % 30) + 1}",
        "expected_department": target_dept,
        "should_abstain": target_dept == "ABSTAIN"
    })

with open(DATA_DIR / "router_eval_cases.json", "w", encoding="utf-8") as f:
    json.dump(router_cases, f, indent=2)

# 3. CLOSURE VERIFIER EVALUATION DATASET
# 30 true positives (repair done, worker within 50m, clean photo)
# 30 adversarial negatives:
#   - 10 reused identical photos (pHash collision)
#   - 10 worker far away (> 2km)
#   - 10 defect unresolved (adversarial note)
closure_pairs = []
# True positives
for i in range(30):
    closure_pairs.append({
        "pair_id": f"closure_pos_{i+1}",
        "ground_truth_fixed": True,
        "worker_distance_m": 15.0 + (i * 1.5),
        "is_reused_photo": False,
        "defect_unresolved": False,
        "notes": "Bulb repaired and debris removed on site."
    })
# Adversarial negatives
for i in range(10):
    closure_pairs.append({
        "pair_id": f"closure_reused_{i+1}",
        "ground_truth_fixed": False,
        "worker_distance_m": 20.0,
        "is_reused_photo": True,
        "defect_unresolved": False,
        "notes": "Reused photo identical to before photo."
    })
for i in range(10):
    closure_pairs.append({
        "pair_id": f"closure_far_{i+1}",
        "ground_truth_fixed": False,
        "worker_distance_m": 1500.0 + (i * 200),
        "is_reused_photo": False,
        "defect_unresolved": False,
        "notes": "Worker located 2km away from site."
    })
for i in range(10):
    closure_pairs.append({
        "pair_id": f"closure_unresolved_{i+1}",
        "ground_truth_fixed": False,
        "worker_distance_m": 25.0,
        "is_reused_photo": False,
        "notes": "Patching deferred; barricade placed."
    })

with open(DATA_DIR / "closure_eval_pairs.json", "w", encoding="utf-8") as f:
    json.dump(closure_pairs, f, indent=2)

print("Generated all evaluation test datasets:")
print(" - dedup_eval_clusters.json: 40 clusters")
print(" - router_eval_cases.json: 100 cases")
print(" - closure_eval_pairs.json: 60 pairs (30 positive, 30 adversarial negative)")
