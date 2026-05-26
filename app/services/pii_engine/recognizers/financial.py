"""
Pattern-based recognizers for financial identifiers.

Credit Card, Email, and UPI recognizers using Presidio's PatternRecognizer.
"""

from presidio_analyzer import PatternRecognizer, Pattern


class InCreditCardRecognizer(PatternRecognizer):
    """Custom Credit Card Recognizer to replace built-in functionality."""
    
    def __init__(self):
        patterns = [Pattern(name="credit_card", regex=r"\b(?:\d[ -]*?){13,16}\b", score=0.8)]
        super().__init__(
            supported_entity="CREDIT_CARD",
            patterns=patterns,
            context=["credit card", "card number"],
            name="InCreditCardRecognizer"
        )


class InEmailRecognizer(PatternRecognizer):
    """Custom Email Recognizer with Lookahead to distinguish from UPI."""
    
    def __init__(self):
        # Must have a .xxx suffix to be an email (e.g. .com, .in)
        patterns = [Pattern(
            name="email_with_tld", 
            regex=r"\b[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b", 
            score=0.85
        )]
        super().__init__(
            supported_entity="EMAIL_ADDRESS",
            patterns=patterns,
            context=["email", "contact"],
            name="InEmailRecognizer"
        )


class InUpiRecognizer(PatternRecognizer):
    """Custom UPI Recognizer with Negative Lookahead for TLDs."""
    
    def __init__(self):
        # Must NOT have a .xxx suffix (e.g. @okaxis but not @okaxis.com)
        patterns = [Pattern(
            name="upi_without_tld", 
            regex=r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{3,64}(?!\.[a-zA-Z]{2,})\b", 
            score=0.9
        )]
        super().__init__(
            supported_entity="IN_UPI",
            patterns=patterns,
            context=["upi", "vpa"],
            name="InUpiRecognizer"
        )