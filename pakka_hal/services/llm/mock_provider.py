import re
import math
import hashlib
import uuid
import io
from PIL import Image
from pakka_hal.services.llm.base import LLMProvider
from pakka_hal.models.incident import TriageResult, LocationInfo, EvidenceItem
from pakka_hal.config import city_config
from pakka_hal.services.emergency import check_emergency_safety_net

# Comprehensive Emergency keywords across English, Hindi (Deva/Latn), and Punjabi (Guru/Latn)
EMERGENCY_KEYWORDS = [
    "fire", "aag", "accident", "ambulance", "police", "khoon", "blood",
    "cylinder blast", "blast", "attack", "emergency", "janleva", "hazard",
    "collapsed", "gir gaya", "khatarnak", "bhaari aag", "current lag gaya",
    "ਅੱਗ", "ਹਾਦਸਾ", "ਐਂਬੂਲੈਂਸ", "ਪੁਲਿਸ", "ਬਲਾਸਟ", "ਸਿਲੰਡਰ", "ਖੂਨ", "ਜਾਨਲੇਵਾ", "agg", "hadsa",
    "आग", "हादसा", "दुर्घटना", "सिलेंडर", "एम्बुलेंस", "करंट"
]

SECTOR_MAP = {
    "17": ("SEC-17", 30.7414, 76.7845),
    "sec 17": ("SEC-17", 30.7414, 76.7845),
    "sector 17": ("SEC-17", 30.7414, 76.7845),
    "ਸੈਕਟਰ 17": ("SEC-17", 30.7414, 76.7845),
    "सेक्टर 17": ("SEC-17", 30.7414, 76.7845),

    "22": ("SEC-22", 30.7333, 76.7725),
    "sec 22": ("SEC-22", 30.7333, 76.7725),
    "sector 22": ("SEC-22", 30.7333, 76.7725),
    "ਸੈਕਟਰ 22": ("SEC-22", 30.7333, 76.7725),
    "सेक्टर 22": ("SEC-22", 30.7333, 76.7725),
    "sector bais": ("SEC-22", 30.7333, 76.7725),
    "sector byee": ("SEC-22", 30.7333, 76.7725),

    "35": ("SEC-35", 30.7225, 76.7621),
    "sec 35": ("SEC-35", 30.7225, 76.7621),
    "sector 35": ("SEC-35", 30.7225, 76.7621),
    "ਸੈਕਟਰ 35": ("SEC-35", 30.7225, 76.7621),
    "सेक्टर 35": ("SEC-35", 30.7225, 76.7621),

    "43": ("SEC-43", 30.7180, 76.7450),
    "sec 43": ("SEC-43", 30.7180, 76.7450),
    "sector 43": ("SEC-43", 30.7180, 76.7450),
    "ਸੈਕਟਰ 43": ("SEC-43", 30.7180, 76.7450),
    "सेक्टर 43": ("SEC-43", 30.7180, 76.7450),
    "isbt": ("SEC-43", 30.7180, 76.7450),

    "it park": ("IT-PARK", 30.7250, 76.8400),
    "chandigarh it park": ("IT-PARK", 30.7250, 76.8400),
}

# Multilingual keywords including Gurmukhi and Devanagari script stems
SERVICE_KEYWORDS = {
    "STREETLIGHT_OUT": [
        "batti", "light", "channi", "streetlight", "roshni", "bijli", "pole", "bulb", "dark", "street light", "hanera",
        "ਬੱਤੀ", "ਸਟ੍ਰੀਟ ਲਾਈਟ", "ਖੰਭਾ", "ਹਨੇਰਾ", "ਲਾਈਟ",
        "स्ट्रीट लाइट", "बत्ती", "अंधेरा", "लाइट", "बिजली"
    ],
    "POTHOLE": [
        "khadda", "gaddha", "sarak", "road", "pothole", "asphalt", "tooti", "tuti", "gaddhe", "crater",
        "ਖੱਡਾ", "ਖੱਡੇ", "ਸੜਕ", "ਟੁੱਟੀ", "ਟੁੱਟਿਆ",
        "गड्ढा", "गड्ढे", "सड़क", "टूटी"
    ],
    "GARBAGE_OVERFLOW": [
        "kuda", "koora", "kachra", "dustbin", "dumpster", "dhalav", "safai", "garbage", "trash", "gandagi", "litter",
        "ਕੂੜਾ", "ਕੂੜੇ", "ਕਚਰਾ", "ਡਸਟਬਿਨ", "ਸਫਾਈ",
        "कूड़ा", "कचरा", "कूड़ेदान", "सफाई"
    ],
    "DRAIN_BLOCKED": [
        "nala", "naali", "drain", "waterlogging", "paani", "overflow", "gutter", "block", "sewage", "clog",
        "ਨਾਲਾ", "ਨਾਲੀ", "ਗਟਰ", "ਪਾਣੀ ਭਰ",
        "नाली", "नाला", "सीवर", "जलभराव", "पानी भर"
    ],
    "MANHOLE_COVER": [
        "dhakkan", "cover", "manhole", "chamber", "gutter cover", "open manhole",
        "ਢੱਕਣ", "ਮੈਨਹੋਲ", "ਗਟਰ ਦਾ ਢੱਕਣ",
        "ढक्कन", "मैनहोल", "गटर का ढक्कन"
    ],
    "SIGNAL_FAULT": [
        "traffic light", "signal", "chowk", "red light", "traffic signal",
        "ਟ੍ਰੈਫਿਕ ਲਾਈਟ", "ਸਿਗਨਲ", "ਚੌਂਕ",
        "ट्रैफिक लाइट", "सिग्नल", "चौराहा", "रेड लाइट"
    ],
    "DAMAGED_SIGNAGE": [
        "board", "sign", "sector sign", "signboard", "direction board", "arrow",
        "ਸਾਈਨ ਬੋਰਡ", "ਦਿਸ਼ਾ ਬੋਰਡ",
        "साइन बोर्ड", "दिशा बोर्ड"
    ],
    "WATER_LEAK": [
        "paani leak", "water leak", "pipeline", "supply", "jal", "leaking pipe", "pipe burst",
        "ਪਾਣੀ ਦੀ ਪਾਈਪ", "ਲੀਕ", "ਪਾਈਪ",
        "पानी की पाइप", "लीक", "पाइपलाइन"
    ]
}

class MockLLMProvider(LLMProvider):
    """
    Deterministic offline provider.
    Ensures unit tests, benchmarks, and offline demos run without network keys.
    """

    async def triage_report(
        self,
        text: str,
        image_bytes: Optional[bytes] = None,
        audio_transcript: Optional[str] = None,
        hint_sector: Optional[str] = None
    ) -> TriageResult:
        full_text = f"{text} {audio_transcript or ''}".strip().lower()

        # 1. Emergency safety-net check
        emergency_hit = check_emergency_safety_net(full_text)
        is_emergency = bool(emergency_hit)
        emergency_details = emergency_hit

        # 2. Language detection
        has_gurmukhi = any('\u0A00' <= char <= '\u0A7F' for char in full_text)
        has_devanagari = any('\u0900' <= char <= '\u097F' for char in full_text)
        if has_gurmukhi:
            lang = "pa-Guru"
        elif has_devanagari:
            lang = "hi-Deva"
        elif any(w in full_text for w in ["hai", "nahi", "raha", "bahut", "deva", "kuda", "gaddha"]):
            lang = "hi-Latn"
        elif any(w in full_text for w in ["vich", "kol", "te", "kitho", "haan", "da", "di"]):
            lang = "pa-Latn"
        else:
            lang = "en"

        # 3. Category classification
        category = "OTHER"
        max_matches = 0
        cat_conf = 0.5
        for cat, kws in SERVICE_KEYWORDS.items():
            matches = sum(1 for kw in kws if kw.lower() in full_text)
            if matches > max_matches:
                max_matches = matches
                category = cat
                cat_conf = min(0.95, 0.70 + 0.10 * matches)

        # If emergency was detected, set category to EMERGENCY_REDIRECT
        if is_emergency:
            category = "EMERGENCY_REDIRECT"
            cat_conf = 1.0

        # 4. Location parsing
        loc_sector = hint_sector or "SEC-17"
        lat, lon = 30.7414, 76.7845
        loc_conf = 0.6

        for key, (s_name, s_lat, s_lon) in SECTOR_MAP.items():
            if key.lower() in full_text:
                loc_sector = s_name
                lat, lon = s_lat, s_lon
                loc_conf = 0.95
                break

        summary_en = f"Reported {category.replace('_', ' ').lower()} near {loc_sector}."

        report_id = f"rep_{uuid.uuid4().hex[:8]}"
        evidence = []
        if image_bytes:
            evidence.append(EvidenceItem(
                id=f"img_{uuid.uuid4().hex[:6]}",
                quality="ok",
                phash=hashlib.md5(image_bytes).hexdigest()
            ))

        return TriageResult(
            report_id=report_id,
            language_detected=lang,
            summary_en=summary_en,
            category=category,
            severity="high" if is_emergency or category in ["MANHOLE_COVER", "SIGNAL_FAULT"] else "medium",
            emergency=is_emergency,
            emergency_details=emergency_details,
            location=LocationInfo(
                lat=lat,
                lon=lon,
                accuracy_m=10.0,
                sector=loc_sector,
                landmark_text=f"Detected near {loc_sector}",
                geo_confidence=loc_conf
            ),
            evidence=evidence,
            field_confidence={"category": cat_conf, "location": loc_conf},
            needs_clarification="Location is ambiguous" if loc_conf < 0.7 else None
        )

    async def verify_closure(
        self,
        before_image_bytes: Optional[bytes],
        after_image_bytes: bytes,
        category: str,
        context: Dict[str, Any]
    ) -> Tuple[float, float, str, List[str]]:
        reasons = []
        quality = "ok"

        # 1. Evaluate image quality via PIL pixel analysis
        try:
            img_after = Image.open(io.BytesIO(after_image_bytes)).convert("L")
            pixels_after = list(img_after.getdata())
            if pixels_after:
                brightness = sum(pixels_after) / len(pixels_after)
                variance = sum((p - brightness) ** 2 for p in pixels_after) / len(pixels_after)
                if variance < 20.0:
                    quality = "blurry"
                    reasons.append("Image lacks high-frequency spatial detail (blurry or uniform).")
                elif brightness < 20.0:
                    quality = "dark"
                    reasons.append("Image is severely underexposed (dark).")
                elif brightness > 245.0:
                    quality = "poor"
                    reasons.append("Image is overexposed / washed out.")
        except Exception:
            quality = "ok"

        # 2. Geofence evaluation
        dist = context.get("distance_m", 0.0)
        if dist > 100.0:
            reasons.append(f"Worker location ({dist:.1f}m) exceeds 100m geofence radius.")
            return 0.20, 0.25, quality, reasons

        # 3. Visual correspondence and resolution evaluation
        from pakka_hal.services.verifier import compute_image_phash, hamming_distance

        if before_image_bytes:
            phash_before = compute_image_phash(before_image_bytes)
            phash_after = compute_image_phash(after_image_bytes)
            h_dist = hamming_distance(phash_before, phash_after)

            # Reused photo check (exact duplicate or identical scene with no repair)
            if h_dist <= 2 or hashlib.md5(before_image_bytes).hexdigest() == hashlib.md5(after_image_bytes).hexdigest():
                reasons.append("Identical photo submitted for after-state. Fraudulent closure flagged.")
                return 1.0, 0.0, quality, reasons

            # Substantial scene shift (different location entirely)
            if h_dist > 30:
                reasons.append(f"Visual discrepancy: High perceptual difference ({h_dist} bits). Unrelated location photographed.")
                return 0.35, 0.20, quality, reasons

            # Same location with confirmed defect resolution
            reasons.append("AI Vision: Scene background alignment verified and defect resolution confirmed.")
            return 0.90, 0.92, quality, reasons

        # Single after-image mode
        if quality in ["blurry", "dark", "poor"]:
            return 0.60, 0.45, quality, reasons

        reasons.append("AI Vision: Defect resolution verified on site.")
        return 0.88, 0.90, "ok", reasons

    async def get_embedding(self, text: str) -> List[float]:
        words = re.findall(r'\w+', text.lower())
        vec = [0.0] * 128
        for w in words:
            h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
            for i in range(128):
                if (h >> (i % 32)) & 1:
                    vec[i] += 1.0
                else:
                    vec[i] -= 0.5
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
