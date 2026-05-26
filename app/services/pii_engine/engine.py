"""
PII Engine implementation using Microsoft Presidio.

Main analyzer engine for detecting Indian PII entities in text.
"""

import base64
import re
from typing import List

from presidio_analyzer import AnalyzerEngine, PatternRecognizer, Pattern
from presidio_analyzer.recognizer_registry import RecognizerRegistry
from presidio_analyzer.nlp_engine import SpacyNlpEngine

from app.core.logging import logger

# Import recognizers
from app.services.pii_engine.recognizers import (
    AadhaarRecognizer,
    PanRecognizer,
    GstinRecognizer,
    TanRecognizer,
    DematRecognizer,
    BankAccountRecognizer,
    FolioRecognizer,
    InUpiRecognizer,
    InEmailRecognizer,
    InCreditCardRecognizer,
)


class PIIEngine:
    """PII Detection Engine using Presidio and spaCy."""
    
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
        
        # Add custom recognizers
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
            default_score_threshold=0.35  # Slightly lower to catch context candidates
        )

    def analyze(self, text: str) -> List:
        """
        Analyze text for PII entities.
        
        Args:
            text: Input text to analyze.
            
        Returns:
            List of RecognizerResult objects.
        """
        from presidio_analyzer import RecognizerResult
        
        logger.debug(f"PIIEngine analyzing text (len={len(text)})")

        # Main analysis
        results = self.analyzer.analyze(
            text=text,
            language="en",
            entities=[
                "IN_PAN", "IN_AADHAAR", "IN_UPI", "IN_MOBILE", "IN_IFSC", "PERSON",
                "EMAIL_ADDRESS", "CREDIT_CARD", "IN_GSTIN", "IN_TAN",
                "IN_DEMAT", "IN_BANK_ACC", "IN_MF_FOLIO"
            ]
        )

        # Recursive analysis for encoded payloads (Base64/URL)
        # Improved regex for Base64 (captures most encoded alphanumeric strings)
        b64_pattern = re.compile(r'[A-Za-z0-9+/]{8,}={0,2}')
        for b64_match in b64_pattern.finditer(text):
            b64_str = b64_match.group()
            try:
                # Add padding if needed
                padding = len(b64_str) % 4
                if padding:
                    b64_str += "=" * (4 - padding)
                
                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                # If decoded text is long enough and contains alphanumeric data
                if len(decoded) >= 5 and any(c.isalnum() for c in decoded):
                    d_results = self.analyzer.analyze(
                        text=decoded,
                        language="en",
                        entities=[
                            "IN_PAN", "IN_AADHAAR", "IN_UPI", "IN_MOBILE", "IN_IFSC",
                            "IN_GSTIN", "IN_TAN", "IN_DEMAT", "IN_BANK_ACC", "IN_MF_FOLIO"
                        ]
                    )
                    
                    if d_results:
                        for dr in d_results:
                            # Flag the entire encoded block as the entity
                            results.append(RecognizerResult(
                                entity_type=dr.entity_type,
                                start=b64_match.start(),
                                end=b64_match.end(),
                                score=dr.score * 0.95 
                            ))
            except Exception:
                continue

        return results