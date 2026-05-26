"""
Custom Presidio Recognizers for Indian PII entities.

Provides entity recognizers for Aadhaar, PAN, GSTIN, TAN, Demat,
Bank Accounts, Mutual Fund Folios, Credit Cards, Emails, and UPI.
"""

# Entity recognizers (custom classes)
from app.services.pii_engine.recognizers.aadhaar import AadhaarRecognizer
from app.services.pii_engine.recognizers.pan import PanRecognizer
from app.services.pii_engine.recognizers.gstin import GstinRecognizer
from app.services.pii_engine.recognizers.tan import TanRecognizer
from app.services.pii_engine.recognizers.demat import DematRecognizer
from app.services.pii_engine.recognizers.bank_account import BankAccountRecognizer
from app.services.pii_engine.recognizers.folio import FolioRecognizer
from app.services.pii_engine.recognizers.financial import (
    InCreditCardRecognizer,
    InEmailRecognizer,
    InUpiRecognizer,
)

__all__ = [
    # Entity recognizers
    "AadhaarRecognizer",
    "PanRecognizer",
    "GstinRecognizer",
    "TanRecognizer",
    "DematRecognizer",
    "BankAccountRecognizer",
    "FolioRecognizer",
    # Financial recognizers
    "InCreditCardRecognizer",
    "InEmailRecognizer",
    "InUpiRecognizer",
]