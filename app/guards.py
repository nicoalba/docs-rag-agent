
SUSPICIOUS_PATTERNS = [
    "ignore previous", "system prompt", "exfiltrate", "BEGIN_SYSTEM_PROMPT",
    "print the hidden", "reveal instructions", "delete all", "disable guard"
]

def is_suspicious(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in SUSPICIOUS_PATTERNS)
