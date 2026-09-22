"""Conservative PII scrubbing for review text before it is analysed or displayed."""

import re

PATTERNS = (
    (re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I), "[EMAIL REDACTED]"),
    (re.compile(r"(?<!\w)(?:\+?\d{1,3}[ .-]?)?(?:\(?\d{2,4}\)?[ .-]?)?\d{3,5}[ .-]?\d{4}(?!\w)"), "[PHONE REDACTED]"),
    (re.compile(r"\b(?:\d[ -]*?){12,19}\b"), "[CARD REDACTED]"),
    (re.compile(r"\b(?:https?://|www\.)\S+", re.I), "[URL REDACTED]"),
)

def redact_pii(text: str) -> str:
    """Replace direct identifiers while retaining the customer feedback itself."""
    cleaned = str(text)
    for pattern, replacement in PATTERNS:
        cleaned = pattern.sub(replacement, cleaned)
    return cleaned
