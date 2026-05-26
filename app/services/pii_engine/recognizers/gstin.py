"""
Custom Presidio Recognizer for GSTIN with Luhn-Mod-36 validation.

Detects Goods and Services Tax Identification Numbers.
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation

from app.services.pii_engine.validators import validate_gstin_checksum


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