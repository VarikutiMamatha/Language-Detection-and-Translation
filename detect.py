"""
detect.py
Language identification with confidence scores, using langdetect.

langdetect supports 55 languages out of the box, which is plenty for the
"20+ languages" requirement, and it needs no internet access or model
download (it's pure Python + trained profiles bundled in the package).
"""

from langdetect import detect_langs, DetectorFactory, LangDetectException
import re

# Make langdetect deterministic (it's probabilistic by default)
DetectorFactory.seed = 0

# Human-readable names for common ISO 639-1 codes returned by langdetect.
LANGUAGE_NAMES = {
    "en": "English", "te": "Telugu", "hi": "Hindi", "ta": "Tamil", "kn": "Kannada",
    "ml": "Malayalam", "mr": "Marathi", "gu": "Gujarati", "bn": "Bengali", "pa": "Punjabi",
    "ur": "Urdu", "fr": "French", "de": "German", "es": "Spanish", "it": "Italian",
    "pt": "Portuguese", "ru": "Russian", "zh-cn": "Chinese (Simplified)", "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese", "ko": "Korean", "ar": "Arabic", "tr": "Turkish", "nl": "Dutch",
    "pl": "Polish", "sv": "Swedish", "fi": "Finnish", "no": "Norwegian", "da": "Danish",
    "el": "Greek", "he": "Hebrew", "th": "Thai", "vi": "Vietnamese", "id": "Indonesian",
    "uk": "Ukrainian", "ro": "Romanian", "cs": "Czech", "hu": "Hungarian", "sw": "Swahili",
}


def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)


def detect_language(text: str):
    """
    Detect the dominant language of `text`.

    Returns:
        dict with keys: code, name, confidence (0-1 float), all_candidates (list)
        Returns None if detection isn't possible (e.g. empty/too-short text).
    """
    if not text or not text.strip():
        return None

    try:
        candidates = detect_langs(text)  # e.g. [en:0.9999, ...], sorted by confidence
    except LangDetectException:
        return None

    if not candidates:
        return None

    top = candidates[0]
    return {
        "code": top.lang,
        "name": language_name(top.lang),
        "confidence": round(top.prob, 4),
        "all_candidates": [
            {"code": c.lang, "name": language_name(c.lang), "confidence": round(c.prob, 4)}
            for c in candidates
        ],
    }


def detect_mixed_language(text: str, min_sentence_len: int = 8):
    """
    (Advanced/optional) Naive code-switching / mixed-language detector.
    Splits text into rough sentence chunks and detects each one separately.
    Good enough to flag e.g. an English+Telugu sentence in the same message;
    not a substitute for a proper token-level language-ID model.

    Returns a list of {segment, code, name, confidence} for each chunk that
    could be independently classified.
    """
    if not text or not text.strip():
        return []

    # Split on sentence punctuation; fall back to the whole string if no splits found.
    chunks = re.split(r"(?<=[.!?।])\s+", text.strip())
    chunks = [c for c in chunks if len(c) >= min_sentence_len] or [text.strip()]

    results = []
    for chunk in chunks:
        d = detect_language(chunk)
        if d:
            results.append({
                "segment": chunk,
                "code": d["code"],
                "name": d["name"],
                "confidence": d["confidence"],
            })
    return results


def is_mixed_language(text: str) -> bool:
    """Quick boolean check: do different segments of this text look like different languages?"""
    results = detect_mixed_language(text)
    codes = {r["code"] for r in results}
    return len(codes) > 1
