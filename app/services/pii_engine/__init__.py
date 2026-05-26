"""
PII Engine Package for detecting Indian PII entities.

This package provides modular PII detection for Indian financial identifiers
(Aadhaar, PAN, GSTIN, TAN, Demat, Bank Accounts, etc.).

Backward-compatible exports from the old monolithic pii_engine.py.

Usage:
    from app.services.pii_engine import pii_engine, validate_verhoeff, validate_gstin_checksum
    
    results = pii_engine.analyze("My Aadhaar is 366215485509")
"""

# Main engine
from app.services.pii_engine.factory import pii_engine, get_pii_engine
from app.services.pii_engine.engine import PIIEngine

# Validators
from app.services.pii_engine.validators import validate_verhoeff, validate_gstin_checksum

# Recognizers
from app.services.pii_engine.recognizers import (
    AadhaarRecognizer,
    PanRecognizer,
    GstinRecognizer,
    TanRecognizer,
    DematRecognizer,
    BankAccountRecognizer,
    FolioRecognizer,
    InCreditCardRecognizer,
    InEmailRecognizer,
    InUpiRecognizer,
)

__all__ = [
    # Engine
    "PIIEngine",
    "pii_engine",
    "get_pii_engine",
    # Validators
    "validate_verhoeff",
    "validate_gstin_checksum",
    # Recognizers
    "AadhaarRecognizer",
    "PanRecognizer",
    "GstinRecognizer",
    "TanRecognizer",
    "DematRecognizer",
    "BankAccountRecognizer",
    "FolioRecognizer",
    "InCreditCardRecognizer",
    "InEmailRecognizer",
    "InUpiRecognizer",
]