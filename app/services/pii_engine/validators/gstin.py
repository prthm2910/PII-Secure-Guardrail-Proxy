"""
GSTIN validation using Luhn Mod 36 algorithm.

Validates 15-character GST Identification Numbers.
"""

from app.services.pii_engine.constants import _GSTIN_CHARS, _GSTIN_CHAR_MAP


def validate_gstin_checksum(gstin: str) -> bool:
    """
    Luhn Mod 36 validation for GSTIN. Optimized with divmod.
    
    Args:
        gstin: The GSTIN string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    # Clean input: remove whitespace and convert to upper
    gstin = "".join(gstin.split()).upper()
    if len(gstin) != 15:
        return False
    
    try:
        data = [_GSTIN_CHAR_MAP[c] for c in gstin[:14]]
        check_char = gstin[14]
        
        total = 0
        for i, val in enumerate(data):
            factor = 2 if (i + 1) % 2 == 0 else 1
            q, r = divmod(val * factor, 36)
            total += q + r
        
        remainder = total % 36
        expected = _GSTIN_CHARS[(36 - remainder) % 36]
        return check_char == expected
    except (KeyError, IndexError):
        return False