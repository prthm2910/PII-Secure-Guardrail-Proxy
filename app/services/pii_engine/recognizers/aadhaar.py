"""
Custom Presidio Recognizer for Aadhaar with Verhoeff validation.

Detects Indian Aadhaar unique identification numbers.
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation

from app.services.pii_engine.validators import validate_verhoeff


class AadhaarRecognizer(EntityRecognizer):
    """Custom Recognizer for Aadhaar with Verhoeff validation."""
    
    def __init__(self):
        super().__init__(
            supported_entities=["IN_AADHAAR"],
            supported_language="en",
            name="AadhaarRecognizer",
            context=["aadhaar", "uid", "aadhaar card"]
        )
        # Ultra-flexible regex to handle any 12 digits with separators
        self.pattern = re.compile(r"\b(?:\(?\d\)?[ -.\s_]*){11}\(?\d\)?\b(?![-\.\s_]*\d)")

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