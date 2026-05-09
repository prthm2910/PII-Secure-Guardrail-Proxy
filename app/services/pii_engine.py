from typing import List
from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern, RecognizerResult, EntityRecognizer, AnalysisExplanation
from presidio_analyzer.recognizer_registry import RecognizerRegistry
import re

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

    def load(self) -> None:
        pass

    def analyze(self, text: str, entities: List[str], nlp_artifacts=None) -> List[RecognizerResult]:
        results = []
        # PAN Pattern: 5 letters, 4 digits, 1 letter
        for match in re.finditer(r"[a-zA-Z]{5}[0-9]{4}[a-zA-Z]{1}", text):
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
                    analysis_explanation=explanation
                )
                results.append(res)
        return results

class EmailRecognizer(PatternRecognizer):
    """Custom Email Recognizer that handles spaces injected by LLMs."""
    def __init__(self):
        # Matches test@example.com and test @ example . com
        patterns = [Pattern(
            name="email_recognizer", 
            regex=r"\b[a-zA-Z0-9._%+-]+\s*@\s*[a-zA-Z0-9.-]+\s*\.\s*[a-zA-Z]{2,}\b", 
            score=0.8
        )]
        super().__init__(supported_entity="EMAIL_ADDRESS", patterns=patterns, context=["email", "contact"], name="ResilientEmailRecognizer")

class UpiRecognizer(PatternRecognizer):
    def __init__(self):
        # Refined UPI regex to avoid catching parts of emails
        patterns = [Pattern(name="upi", regex=r"\b[a-zA-Z0-9.\-_]{2,256}@[a-zA-Z]{3,64}(?!\.[a-zA-Z]{2,})\b", score=0.8)]
        super().__init__(supported_entity="IN_UPI", patterns=patterns, context=["upi", "vpa"], name="UpiRecognizer")

# --- Engine Implementation ---

class PIIEngine:
    def __init__(self):
        # Start with an empty registry to have absolute control
        registry = RecognizerRegistry()
        
        # Add custom classes (Our primary defense)
        registry.add_recognizer(AadhaarRecognizer())
        registry.add_recognizer(PanRecognizer())
        registry.add_recognizer(UpiRecognizer())
        registry.add_recognizer(EmailRecognizer())
        
        # Add a custom Phone/Mobile recognizer to override built-in one
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

        # We can add back only the essential predefined ones manually if needed,
        # but for now, we want strict control over PAN, AADHAAR, EMAIL, and MOBILE.
        # This prevents built-in generic ones from causing false positives.
        
        self.analyzer = AnalyzerEngine(registry=registry)

    def analyze(self, text: str) -> List[RecognizerResult]:
        return self.analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "IN_PAN", "IN_AADHAAR", "IN_UPI", "IN_MOBILE", "IN_IFSC", "EMAIL_ADDRESS"
            ]
        )

pii_engine = PIIEngine()
