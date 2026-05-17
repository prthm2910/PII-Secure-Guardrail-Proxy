from typing import List
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult, EntityRecognizer, AnalysisExplanation
from presidio_analyzer.recognizer_registry import RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine
import re

from app.core.logging import logger

# Verhoeff Algorithm for Aadhaar Validation
VERHOEFF_TABLE_D = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 2, 3, 4, 0, 6, 7, 8, 9, 5),
    (2, 3, 4, 0, 1, 7, 8, 9, 5, 6),
    (3, 4, 0, 1, 2, 8, 9, 5, 6, 7),
    (4, 0, 1, 2, 3, 9, 5, 6, 7, 8),
    (5, 9, 8, 7, 6, 0, 4, 3, 2, 1),
    (6, 5, 9, 8, 7, 1, 0, 4, 3, 2),
    (7, 6, 5, 9, 8, 2, 1, 0, 4, 3),
    (8, 7, 6, 5, 9, 3, 2, 1, 0, 4),
    (9, 8, 7, 6, 5, 4, 3, 2, 1, 0)
)

VERHOEFF_TABLE_P = (
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9),
    (1, 5, 7, 6, 2, 8, 3, 0, 9, 4),
    (5, 8, 0, 3, 7, 9, 6, 1, 4, 2),
    (8, 9, 1, 6, 0, 4, 3, 5, 2, 7),
    (9, 4, 5, 3, 1, 2, 6, 8, 7, 0),
    (4, 2, 8, 6, 5, 7, 3, 9, 0, 1),
    (2, 7, 9, 3, 8, 0, 6, 4, 1, 5),
    (7, 0, 4, 6, 9, 1, 3, 2, 5, 8)
)

# --- Optimized GSTIN Constants ---
_GSTIN_CHARS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_GSTIN_CHAR_MAP = {c: i for i, c in enumerate(_GSTIN_CHARS)}

def validate_verhoeff(number: str) -> bool:
    """Validate a 12-digit Aadhaar number using the Verhoeff algorithm."""
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

def validate_gstin_checksum(gstin: str) -> bool:
    """Luhn Mod 36 validation for GSTIN. Optimized with divmod."""
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

# --- Custom Presidio Recognizer Classes ---

class AadhaarRecognizer(EntityRecognizer):
    """Custom Recognizer for Aadhaar with Verhoeff validation."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_AADHAAR"],
            supported_language="en",
            name="AadhaarRecognizer",
            context=["aadhaar", "uid", "aadhaar card"]
        )
        # Ultra-flexible regex to handle any 12 digits with separators like space, dash, dot, underscore        
        self.pattern = re.compile(r"\b(?:\d[-.\s_]*){11}\d\b(?![-\.\s_]*\d)")

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_AADHAAR" not in entities:
            return results

        for match in self.pattern.finditer(text):
            match_str = match.group()
            if validate_verhoeff(match_str):
                explanation = AnalysisExplanation(
                    recognizer=self.name,
                    original_score=0.85,
                    textual_explanation="Validated using Verhoeff algorithm."
                )

                res = RecognizerResult(
                    entity_type="IN_AADHAAR",
                    start=match.start(),
                    end=match.end(),
                    score=0.85,
                    analysis_explanation=explanation,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                    }
                )
                results.append(res)
        return results

class PanRecognizer(EntityRecognizer):
    """Custom Recognizer for PAN with structural validation."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_PAN"],
            supported_language="en",
            name="PanRecognizer",
            context=["pan", "tax id"]
        )
        self.pattern = re.compile(r"\b[a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}\b", re.IGNORECASE)

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_PAN" not in entities:
            return results

        # PAN Pattern: 5 letters, 4 digits, 1 letter
        for match in self.pattern.finditer(text):
            match_str = match.group()
            # 4th character (index 3) is the Status of the Holder
            status_char = match_str[3].upper()
            
            # Official Status Codes: P, C, H, F, A, T, B, L, J, G
            if status_char in "PCHFABTLJG":
                explanation = AnalysisExplanation(
                    recognizer=self.name,
                    original_score=0.9,
                    textual_explanation=f"Validated PAN structure with status code '{status_char}'."
                )
                
                res = RecognizerResult(
                    entity_type="IN_PAN",
                    start=match.start(),
                    end=match.end(),
                    score=0.9,
                    analysis_explanation=explanation,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                    }
                )
                results.append(res)
        return results

class GstinRecognizer(EntityRecognizer):
    """Custom Recognizer for GSTIN with Luhn-Mod-36 validation."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_GSTIN"],
            supported_language="en",
            name="GstinRecognizer",
            context=["gstin", "gst", "tax id"]
        )
        self.pattern = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b", re.IGNORECASE)

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_GSTIN" not in entities:
            return results

        for match in self.pattern.finditer(text):
            if validate_gstin_checksum(match.group()):
                explanation = AnalysisExplanation(
                    recognizer=self.name,
                    original_score=0.95,
                    textual_explanation="Validated using Luhn-Mod-36 algorithm."
                )
                results.append(
                    RecognizerResult(
                        entity_type="IN_GSTIN",
                        start=match.start(),
                        end=match.end(),
                        score=0.95,
                        analysis_explanation=explanation,
                        recognition_metadata={
                            RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                            RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                        }
                    )
                )
        return results

class TanRecognizer(EntityRecognizer):
    """Custom Recognizer for TAN (Tax Deduction Account Number)."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_TAN"],
            supported_language="en",
            name="TanRecognizer",
            context=["tan", "tax deduction account number"]
        )
        self.pattern = re.compile(r"\b[A-Z]{4}[0-9]{5}[A-Z]{1}\b", re.IGNORECASE)

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_TAN" not in entities:
            return results

        for match in self.pattern.finditer(text):
            explanation = AnalysisExplanation(
                recognizer=self.name,
                original_score=0.9,
                textual_explanation="Matched TAN pattern (4L + 5D + 1L)."
            )
            results.append(
                RecognizerResult(
                    entity_type="IN_TAN",
                    start=match.start(),
                    end=match.end(),
                    score=0.9,
                    analysis_explanation=explanation,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                    }
                )
            )
        return results

class DematRecognizer(EntityRecognizer):
    """Custom Recognizer for Demat ID (CDSL/NSDL)."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_DEMAT"],
            supported_language="en",
            name="DematRecognizer",
            context=["demat", "dp id", "nsdl", "cdsl"]
        )
        self.cdsl_pattern = re.compile(r"\b[0-9]{16}\b")
        self.nsdl_pattern = re.compile(r"\bIN[0-9]{14}\b", re.IGNORECASE)

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_DEMAT" not in entities:
            return results

        for pattern, source in [(self.cdsl_pattern, "CDSL"), (self.nsdl_pattern, "NSDL")]:
            for match in pattern.finditer(text):
                explanation = AnalysisExplanation(
                    recognizer=self.name,
                    original_score=0.85,
                    textual_explanation=f"Identified as {source} Demat ID."
                )
                results.append(
                    RecognizerResult(
                        entity_type="IN_DEMAT",
                        start=match.start(),
                        end=match.end(),
                        score=0.85,
                        analysis_explanation=explanation,
                        recognition_metadata={
                            RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                            RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                        }
                    )
                )
        return results

class BankAccountRecognizer(EntityRecognizer):
    """Custom Recognizer for Bank Account numbers with Hybrid NLP context."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_BANK_ACC"],
            supported_language="en",
            name="BankAccountRecognizer",
            # Presidio's Context-Aware Enhancer will use these to boost scores
            context=["account", "acc", "ifsc", "beneficiary", "savings", "remittance", "dividend"]
        )
        self.pattern = re.compile(r"\b\d{9,18}\b")

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_BANK_ACC" not in entities:
            return results

        # In Hybrid mode, we flag candidates with a LOWER base score.
        # If the LemmaContextAwareEnhancer finds context nearby, it boosts it to 1.0.
        for match in self.pattern.finditer(text):
            explanation = AnalysisExplanation(
                recognizer=self.name,
                original_score=0.4,
                textual_explanation="Found digit sequence (9-18) matching bank account pattern."
            )
            results.append(
                RecognizerResult(
                    entity_type="IN_BANK_ACC",
                    start=match.start(),
                    end=match.end(),
                    score=0.3, # Low base score, needs context boost
                    analysis_explanation=explanation,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                    }
                )
            )
        return results

class FolioRecognizer(EntityRecognizer):
    """Custom Recognizer for Mutual Fund Folio Numbers with Hybrid NLP context."""
    def __init__(self):
        super().__init__(
            supported_entities=["IN_MF_FOLIO"],
            supported_language="en",
            name="FolioRecognizer",
            context=["folio", "mutual fund", "amc", "investment", "portfolio"]
        )
        self.pattern = re.compile(r"\b[a-zA-Z0-9/-]{5,20}\b")

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        if not entities or "IN_MF_FOLIO" not in entities:
            return results

        for match in self.pattern.finditer(text):
            match_str = match.group()
            if not any(char.isdigit() for char in match_str):
                continue
            
            explanation = AnalysisExplanation(
                recognizer=self.name,
                original_score=0.3,
                textual_explanation="Detected Folio pattern, awaiting context boost."
            )
            results.append(
                RecognizerResult(
                    entity_type="IN_MF_FOLIO",
                    start=match.start(),
                    end=match.end(),
                    score=0.3,
                    analysis_explanation=explanation,
                    recognition_metadata={
                        RecognizerResult.RECOGNIZER_IDENTIFIER_KEY: self.id,
                        RecognizerResult.RECOGNIZER_NAME_KEY: self.name
                    }
                )
            )
        return results

class InCreditCardRecognizer(PatternRecognizer):
    """Custom Credit Card Recognizer to replace built-in functionality."""
    def __init__(self):
        patterns = [Pattern(name="credit_card", regex=r"\b(?:\d[ -]*?){13,16}\b", score=0.8)]
        super().__init__(supported_entity="CREDIT_CARD", patterns=patterns, context=["credit card", "card number"], name="InCreditCardRecognizer")

class InEmailRecognizer(PatternRecognizer):
    """Custom Email Recognizer with Lookahead to distinguish from UPI."""
    def __init__(self):
        # Must have a .xxx suffix to be an email (e.g. .com, .in)
        patterns = [Pattern(
            name="email_with_tld", 
            regex=r"\b[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b", 
            score=0.85
        )]
        super().__init__(supported_entity="EMAIL_ADDRESS", patterns=patterns, context=["email", "contact"], name="InEmailRecognizer")

class InUpiRecognizer(PatternRecognizer):
    """Custom UPI Recognizer with Negative Lookahead for TLDs."""
    def __init__(self):
        # Must NOT have a .xxx suffix (e.g. @okaxis but not @okaxis.com)
        patterns = [Pattern(
            name="upi_without_tld", 
            regex=r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{3,64}(?!\.[a-zA-Z]{2,})\b", 
            score=0.9
        )]
        super().__init__(supported_entity="IN_UPI", patterns=patterns, context=["upi", "vpa"], name="InUpiRecognizer")

# --- Engine Implementation ---

class PIIEngine:
    def __init__(self):
        logger.info("Initializing PIIEngine with Presidio and Spacy (en_core_web_sm)")
        # 1. Initialize Hybrid NLP Engine (spaCy)
        configuration = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": "en", "model_name": "en_core_web_sm"}],
        }
        nlp_engine = SpacyNlpEngine(models=configuration["models"])
        nlp_engine.load()
        
        # 2. Setup Registry with Hybrid Recognizers
        # Load default recognizers (includes PERSON via Spacy, etc.)
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        
        # Add custom classes
        registry.add_recognizer(AadhaarRecognizer())
        registry.add_recognizer(PanRecognizer())
        registry.add_recognizer(GstinRecognizer())
        registry.add_recognizer(TanRecognizer())
        registry.add_recognizer(DematRecognizer())
        registry.add_recognizer(BankAccountRecognizer())
        registry.add_recognizer(FolioRecognizer())
        registry.add_recognizer(InUpiRecognizer())
        registry.add_recognizer(InEmailRecognizer())
        registry.add_recognizer(InCreditCardRecognizer())
        
        # Add pattern-based custom recognizers
        registry.add_recognizer(PatternRecognizer(
            supported_entity="IN_MOBILE",
            patterns=[Pattern(name="mobile", regex=r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b", score=0.75)],
            context=["mobile"],
            name="MobileRecognizer"
        ))
        
        registry.add_recognizer(PatternRecognizer(
            supported_entity="IN_IFSC",
            patterns=[Pattern(name="ifsc", regex=r"\b[a-zA-Z]{4}0[a-zA-Z0-9]{6}\b", score=0.9)],
            context=["ifsc"],
            name="IfscRecognizer"
        ))
        
        # 3. Initialize Analyzer with NLP Engine and Context-Aware Support
        self.analyzer = AnalyzerEngine(
            nlp_engine=nlp_engine, 
            registry=registry,
            default_score_threshold=0.35 # Slightly lower to catch context candidates
        )

    def analyze(self, text: str) -> List[RecognizerResult]:
        logger.debug(f"PIIEngine analyzing text (len={len(text)})")
        return self.analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "IN_PAN", "IN_AADHAAR", "IN_UPI", "IN_MOBILE", "IN_IFSC", "PERSON",
                "EMAIL_ADDRESS", "CREDIT_CARD", "IN_GSTIN", "IN_TAN", 
                "IN_DEMAT", "IN_BANK_ACC", "IN_MF_FOLIO"
            ]
        )

pii_engine = PIIEngine()
