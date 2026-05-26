"""
Custom Presidio Recognizer for TAN (Tax Deduction Account Number).

Detects Tax Deduction and Collection Account Numbers.
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation


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