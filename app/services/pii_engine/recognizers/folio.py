"""
Custom Presidio Recognizer for Mutual Fund Folio Numbers with Hybrid NLP context.

Detects Indian mutual fund folio numbers.
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation


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