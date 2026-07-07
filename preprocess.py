"""
preprocess.py
Text cleaning / normalization utilities used before language detection
and translation.
"""

import re
import unicodedata


def normalize_unicode(text: str) -> str:
    """Normalize unicode form (NFC) so accented/combined characters are consistent."""
    return unicodedata.normalize("NFC", text)


def clean_text(text: str) -> str:
    """
    Basic cleanup:
    - normalize unicode
    - collapse repeated whitespace
    - strip leading/trailing whitespace
    - remove control characters
    """
    if not text:
        return ""

    text = normalize_unicode(text)

    # Remove non-printable control characters (keep normal punctuation/unicode letters)
    text = "".join(ch for ch in text if ch == "\n" or ch == "\t" or not unicodedata.category(ch).startswith("C"))

    # Collapse multiple spaces/newlines into a single space
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def is_effectively_empty(text: str) -> bool:
    """Check whether, after cleaning, there's actually anything left to process."""
    return len(clean_text(text)) == 0
