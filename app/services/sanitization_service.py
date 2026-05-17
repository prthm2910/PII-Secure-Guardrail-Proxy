import uuid
from typing import Tuple, Dict, List
import re

from app.services.pii_engine import pii_engine
from app.services.redis_service import redis_service
from app.services.normalization_service import normalization_service
from app.core.logging import logger

class SanitizationService:
    def mask_for_logs(self, text: str, entity_type: str, original_value: str) -> str:
        """Statically mask PII for permanent audit logs."""
        if entity_type == "IN_PAN":
            # ABCPX****Z
            return original_value[:5] + "****" + original_value[-1]
        elif entity_type == "IN_AADHAAR":
            # XXXX-XXXX-1234
            return "XXXX-XXXX-" + original_value[-4:]
        elif entity_type == "IN_GSTIN":
            # 27AAAAA****A1Z2
            return original_value[:7] + "****" + original_value[-4:]
        elif entity_type == "IN_TAN":
            # ABCD****G
            return original_value[:4] + "****" + original_value[-1]
        elif entity_type == "IN_DEMAT":
            # CDSL: 1234**********56, NSDL: IN12**********34
            return original_value[:4] + "*" * 10 + original_value[-2:]
        elif entity_type == "IN_BANK_ACC":
            # **********1234
            return "*" * (len(original_value) - 4) + original_value[-4:]
        elif entity_type == "IN_MF_FOLIO":
            # 123/*****/0
            parts = original_value.split("/")
            if len(parts) > 1:
                return f"{parts[0]}/*****/{parts[-1]}"
            return original_value[:3] + "*****"
        elif entity_type == "EMAIL_ADDRESS":
            # a*****@gmail.com
            parts = original_value.split("@")
            if len(parts) == 2:
                return parts[0][0] + "*****@" + parts[1]
            return "*****"
        elif entity_type == "IN_UPI":
            # *****@ybl
            parts = original_value.split("@")
            if len(parts) == 2:
                return "*****@" + parts[1]
            return "*****"
        elif entity_type == "CREDIT_CARD":
            # 123456******1234
            return original_value[:6] + "******" + original_value[-4:]
        
        return "[MASKED]"

    def sanitize(self, text: str, request_id: str = None) -> Tuple[str, str, Dict[str, str], Dict[str, int], Dict[str, str]]:
        """
        Sanitize text by replacing PII with reversible tokens and generating masked versions for logs.
        Handles overlaps by prioritizing longest matches first.
        Returns: (sanitized_text, request_id, token_map, entity_summary, masked_entities)
        """
        request_id = request_id or str(uuid.uuid4())
        logger.debug(f"Req: {request_id} | Sanitization started")
        
        # Pre-process text to handle obfuscation (Homoglyphs, Unicode, Invisible chars)
        clean_text = normalization_service.normalize(text)
        
        # We analyze the clean text
        results = pii_engine.analyze(clean_text)
        
        token_map = {}
        entity_summary = {}
        masked_entities = {}
        
        # 1. Deduplicate/Filter overlaps: Sort by length (descending)
        # If two entities overlap, the longer one (more specific) wins.
        sorted_results = sorted(results, key=lambda x: (x.end - x.start), reverse=True)
        
        filtered_results = []
        occupied_ranges = set()
        
        for res in sorted_results:
            # Check if this range is already occupied
            is_overlap = False
            for start, end in occupied_ranges:
                if (res.start < end and res.end > start):
                    is_overlap = True
                    break
            
            if not is_overlap:
                filtered_results.append(res)
                occupied_ranges.add((res.start, res.end))
        
        # 2. Sort by start position (reverse) to replace in text safely
        final_results = sorted(filtered_results, key=lambda x: x.start, reverse=True)
        
        sanitized_text = clean_text
        for res in final_results:
            entity_type = res.entity_type
            original_value = clean_text[res.start:res.end]
            
            # Update entity summary for audit logs
            entity_summary[entity_type] = entity_summary.get(entity_type, 0) + 1
            
            # Create a unique token for this specific occurrence
            token_index = entity_summary[entity_type]
            token = f"[{entity_type}_{token_index}]"
            
            # Store in token map for Redis
            token_map[token] = original_value
            
            # Create masked version for logs
            masked_entities[token] = self.mask_for_logs(clean_text, entity_type, original_value)
            
            # Replace in text
            sanitized_text = sanitized_text[:res.start] + token + sanitized_text[res.end:]
            
        # Store tokens in Redis with TTL
        if token_map:
            logger.debug(f"Req: {request_id} | {len(token_map)} tokens generated")
            redis_service.store_tokens(request_id, token_map)
            
        return sanitized_text, request_id, token_map, entity_summary, masked_entities

    def desanitize(self, sanitized_text: str, request_id: str) -> str:
        """Restore original PII values using tokens stored in Redis.
        Handles cases where LLM might add spaces inside brackets like '[ IN_PAN_1 ]'.
        """
        logger.debug(f"Req: {request_id} | Desanitization started")
        token_map = redis_service.get_tokens(request_id)
        if not token_map:
            logger.warning(f"Req: {request_id} | No token map found for desanitization")
            return sanitized_text
            
        desanitized_text = sanitized_text
        # Sort tokens by length (longest first) to avoid partial replacement issues
        sorted_tokens = sorted(token_map.keys(), key=len, reverse=True)
        
        for token in sorted_tokens:
            original_value = token_map[token]
            # Resilient replacement: handles [TOKEN], [ TOKEN ], [TOKEN ], etc.
            token_content = token.strip("[]")
            # Using a simplified word-boundary or bracket-match regex
            pattern = re.compile(rf"\[\s*{re.escape(token_content)}\s*\]")
            desanitized_text = pattern.sub(original_value, desanitized_text)
            
        logger.debug(f"Req: {request_id} | Desanitization complete")
        return desanitized_text

sanitization_service = SanitizationService()
