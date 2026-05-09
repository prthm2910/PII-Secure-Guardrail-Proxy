import unicodedata
import re

class NormalizationService:
    """
    Handles pre-processing of text to prevent common PII obfuscation bypasses.
    Focus: Invisible characters, Full-width Unicode, and basic Normalization.
    """
    def __init__(self):
        # Regex for invisible/control characters (Zero-width space, non-joiners, etc.)
        self.invisible_chars = re.compile(r"[\u200B-\u200D\uFEFF\u00AD]")

    def normalize(self, text: str) -> str:
        if not text:
            return text

        # 1. Strip invisible characters that break \b word boundaries
        text = self.invisible_chars.sub("", text)

        # 2. Convert Full-width Unicode to standard ASCII (e.g., ＰＡＮ -> PAN)
        # NFKC (Normalization Form Compatibility Composition) is perfect for this.
        text = unicodedata.normalize("NFKC", text)

        return text

normalization_service = NormalizationService()
