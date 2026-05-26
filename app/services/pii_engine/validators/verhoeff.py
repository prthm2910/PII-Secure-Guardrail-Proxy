"""
Verhoeff algorithm implementation for Aadhaar validation.

Validates 12-digit Aadhaar numbers using the Verhoeff checksum algorithm.
"""

from app.services.pii_engine.constants import VERHOEFF_TABLE_D, VERHOEFF_TABLE_P


def validate_verhoeff(number: str) -> bool:
    """
    Validate a 12-digit Aadhaar number using the Verhoeff algorithm.
    
    Args:
        number: The Aadhaar number string (may contain separators).
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        # Strip common separators
        clean_number = "".join(filter(str.isdigit, number))
        if len(clean_number) != 12:
            return False
        # Avoid obvious sequences
        if clean_number == clean_number[0] * 12 or clean_number == "123456789012" or clean_number == "123412341234":
            return False

        c = 0
        ll = [int(x) for x in clean_number]
        for i, x in enumerate(reversed(ll)):
            c = VERHOEFF_TABLE_D[c][VERHOEFF_TABLE_P[i % 8][x]]
        return c == 0
    except ValueError:
        return False