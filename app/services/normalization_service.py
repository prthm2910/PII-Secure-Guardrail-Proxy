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
        
        # Homoglyph map: Cyrillic/Greek -> ASCII
        # Targets common characters used in PAN/GSTIN bypasses
        self.homoglyph_map = str.maketrans({
            # Cyrillic
            '\u0410': 'A', '\u0430': 'a',
            '\u0412': 'B',
            '\u0421': 'C', '\u0441': 'c',
            '\u0415': 'E', '\u0435': 'e',
            '\u041d': 'H',
            '\u041a': 'K', '\u043a': 'k',
            '\u041c': 'M', '\u043c': 'm',
            '\u041e': 'O', '\u043e': 'o',
            '\u0420': 'P', '\u0440': 'p',
            '\u0422': 'T',
            '\u0425': 'X', '\u0445': 'x',
            '\u0423': 'Y', '\u0443': 'y',
            # Greek
            '\u0391': 'A', '\u03b1': 'a',
            '\u0392': 'B', '\u03b2': 'b',
            '\u0395': 'E', '\u03b5': 'e',
            '\u0396': 'Z',
            '\u0397': 'H', '\u03b7': 'h',
            '\u0399': 'I', '\u03b9': 'i',
            '\u039a': 'K', '\u03ba': 'k',
            '\u039c': 'M', '\u03bc': 'm',
            '\u039d': 'N', '\u03bd': 'n',
            '\u039f': 'O', '\u03bf': 'o',
            '\u03a1': 'P', '\u03c1': 'p',
            '\u03a4': 'T', '\u03c4': 't',
            '\u03a5': 'Y', '\u03c5': 'y',
            '\u03a7': 'X', '\u03c7': 'x',
        })

    def normalize(self, text: str) -> str:
        if not text:
            return text

        # 1. Strip invisible characters that break \b word boundaries
        text = self.invisible_chars.sub("", text)

        # 2. Convert Full-width Unicode to standard ASCII (e.g., ＰＡＮ -> PAN)
        text = unicodedata.normalize("NFKC", text)
        
        # 3. Translate Homoglyphs
        text = text.translate(self.homoglyph_map)

        return text

normalization_service = NormalizationService()
