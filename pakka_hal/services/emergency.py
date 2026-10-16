import re
from typing import Optional

# Contextual emergency regex patterns (English, Hindi Deva/Latn, Punjabi Guru/Latn)
# Designed to avoid false positives on words like 'current status', 'police chowki', or 'blood bank'
EMERGENCY_PATTERNS = [
    # Active Fire / Blasts
    r"\b(?:fire|blaze|massive\s+fire|cylinder\s+blast|gas\s+blast|explosion|building\s+collaps\w*|roof\s+collaps\w*)\b",
    r"\b(?:आग\s+लग\w*|भीषण\s+आग|सिलेंडर\s+ब्लास्ट|धमाका|इमारत\s+गिर\w*|छत\s+गिर\w*)\b",
    r"\b(?:ਅੱਗ\s+ਲੱਗ\w*|ਭਾਰੀ\s+ਅੱਗ|ਸਿਲੰਡਰ\s+ਬਲਾਸਟ|ਧਮਾਕਾ|ਇਮਾਰਤ\s+ਡਿੱਗ\w*)\b",
    r"\b(?:bhaari\s+aag|aag\s+lagi|cylinder\s+phat|blast|dhamaka)\b",
    
    # Severe Accidents & Medical Emergencies
    r"\b(?:major\s+road\s+accident|road\s+accident|fatal\s+accident|serious\s+accident|head-on\s+collision|car\s+crash|vehicle\s+collision|severe\s+bleeding|multiple\s+casualties|person\s+unconscious|loss\s+of\s+life|ambulance\s+needed|urgent\s+(?:police|ambulance))\b",
    r"\b(?:गंभीर\s+हादसा|सड़क\s+दुर्घटना|सड़क\s+हादसा|जानलेवा\s+हादसा|खून\s+बह\s+रहा|एम्बुलेंस\s+भेजो|मौत)\b",
    r"\b(?:ਗੰਭੀਰ\s+ਹਾਦਸਾ|ਸੜਕ\s+ਹਾਦਸਾ|ਜਾਨਲੇਵਾ\s+ਹਾਦਸਾ|ਖੂਨ\s+ਵਹਿ\s+ਰਿਹਾ|ਐਂਬੂਲੈਂਸ\s+ਭੇਜੋ|ਮੌਤ)\b",
    r"\b(?:janleva\s+hadsa|khoon\s+beh\s+raha|ambulance\s+bhejo)\b",
    
    # Electrocution / High Voltage Hazards (Strictly contextual: never standalone 'current')
    r"\b(?:electrocution|electrocuted|electric\s+shock|high\s+voltage\s+shock|live\s+wire\s+sparking)\b",
    r"\b(?:करंट\s+लग\s+गया|बिजली\s+का\s+करंट|करंट\s+आ\s+रहा|करंट\s+लगा)\b",
    r"\b(?:ਕਰੰਟ\s+ਲੱਗ\s+ਗਿਆ|ਬਿਜਲੀ\s+ਦਾ\s+ਕਰੰਟ|ਕਰੰਟ\s+ਆ\s+ਰਿਹਾ)\b",
    r"\b(?:current\s+lag\s+gaya|bijli\s+ka\s+current)\b",
    
    # Explicit 112 / Emergency SOS
    r"\b(?:dial\s+112|emergency\s+112|112\s+emergency|police\s+help\s+needed|attack\s+in\s+progress)\b",
    r"\b(?:ਤੁਰੰਤ\s+ਮਦਦ|ਪੁਲਿਸ\s+ਸੱਦੋ|112\s+ਕਾਲ)\b",
    r"\b(?:पुलिस\s+बुलाओ|112\s+पर\s+कॉल)\b"
]

# Non-emergency landmarks that might otherwise trigger false positives
LANDMARK_EXCLUSIONS = [
    r"\bblood\s+bank\b",
    r"\bpolice\s+(?:station|chowki|post|headquarters|barrier|line)\b",
    r"\bfire\s+(?:station|extinguisher|exit|hydrant|audit)\b",
    r"\bcurrent\s+(?:status|condition|situation|repair|speed|update|work)\b"
]

COMPILED_EMERGENCY = [re.compile(p, re.IGNORECASE) for p in EMERGENCY_PATTERNS]
COMPILED_EXCLUSIONS = [re.compile(p, re.IGNORECASE) for p in LANDMARK_EXCLUSIONS]

def check_emergency_safety_net(text: str) -> Optional[str]:
    """
    Context-aware deterministic safety net.
    Checks regex patterns with word boundaries and excludes common civic landmarks.
    """
    clean_text = text.strip()
    if not clean_text:
        return None

    # Check for direct emergency triggers
    for pattern in COMPILED_EMERGENCY:
        match = pattern.search(clean_text)
        if match:
            trigger_text = match.group(0)
            # Ensure it is not an excluded civic landmark phrase
            is_excluded = any(ex.search(clean_text) and trigger_text.lower() in ex.pattern for ex in COMPILED_EXCLUSIONS)
            if not is_excluded:
                return f"Emergency condition triggered by pattern '{trigger_text}'. Immediate 112 redirect."

    # Direct keyword backup for high-risk single-word emergencies
    for word in ["112", "ਐਮਰਜੈਂਸੀ", "आपातकालीन"]:
        if word in clean_text:
            return f"Emergency condition triggered by explicit keyword '{word}'. Immediate 112 redirect."

    return None
