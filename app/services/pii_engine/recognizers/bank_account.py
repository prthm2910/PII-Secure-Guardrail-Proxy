"""
Custom Presidio Recognizer for Bank Account numbers with Hybrid NLP context.

Detects Indian bank account numbers (9-18 digits).
"""

import re
from typing import List

from presidio_analyzer import EntityRecognizer, RecognizerResult, AnalysisExplanation


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
        # Fuzzy regex for 9-18 digits with dot, dash, or space separators
        self.pattern = re.compile(r"\b(?:\d[ -.]*){8,17}\d\b")

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