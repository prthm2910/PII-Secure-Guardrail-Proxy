"""
Custom Presidio Recognizer for Demat ID (CDSL/NSDL).

Detects Depository participant IDs for Indian trading accounts.
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation


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