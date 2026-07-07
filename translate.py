"""
translate.py

Fixes the classic error:
    "No translation model available for 'en' -> 'te' (direct or via English pivot)"

That error happens with MarianMT/Helsinki-NLP because those are hundreds of
SEPARATE models, one per language pair (or pivot pair), and many pairs
(especially into lower-resource languages like Telugu) simply don't have a
published checkpoint. If a pair is missing, MarianMT has nothing to fall
back on.

Fix used here: translate via Google Translate (through `deep-translator`).
No model downloads, works immediately, covers 100+ languages including
Telugu, Kannada, Malayalam, etc. Requires internet access.
"""


class TranslationError(Exception):
    pass


class GoogleBackend:
    """
    Lightweight, no model download, broad language coverage.
    pip install deep-translator
    """

    # deep-translator's GoogleTranslator wants 'auto' for unknown source,
    # and its own language codes are ISO 639-1, which matches langdetect's
    # output closely enough for our supported language list.
    _CODE_FIXUPS = {
        "zh-cn": "zh-CN",
        "zh-tw": "zh-TW",
    }

    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        from deep_translator import GoogleTranslator
        from deep_translator.exceptions import LanguageNotSupportedException

        src = self._CODE_FIXUPS.get(source_lang, source_lang)
        tgt = self._CODE_FIXUPS.get(target_lang, target_lang)

        try:
            return GoogleTranslator(source=src, target=tgt).translate(text)
        except LanguageNotSupportedException as e:
            raise TranslationError(f"Language pair '{src}' -> '{tgt}' not supported: {e}")
        except Exception as e:
            raise TranslationError(f"Translation failed for '{src}' -> '{tgt}': {e}")


def get_backend() -> GoogleBackend:
    return GoogleBackend()
