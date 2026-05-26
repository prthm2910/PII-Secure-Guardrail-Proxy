"""
Custom Presidio Recognizer for PAN with structural validation.

Detects Indian Permanent Account Numbers.
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation


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