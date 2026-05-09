import sys
import os
from datetime import datetime
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock redis_service BEFORE importing sanitization_service
mock_redis = MagicMock()
mock_redis.store_tokens.return_value = True
mock_redis.get_tokens.return_value = {}

# Mock the module in sys.modules
import app.services.redis_service
app.services.redis_service.redis_service = mock_redis

from app.services.sanitization_service import sanitization_service
from app.services.pii_engine import pii_engine

class EdgeCaseTester:
    def __init__(self):
        self.test_cases = [
            # --- FALSE NEGATIVES (Obfuscation) ---
            {
                "category": "False Negatives (Obfuscation)",
                "description": "Aadhaar with mixed separators",
                "input": "My Aadhaar is 3662- 1548_5509",
                "expected_entities": ["IN_AADHAAR"]
            },
            {
                "category": "False Negatives (Obfuscation)",
                "description": "Mixed-case PAN (Valid Status 'P')",
                "input": "PAN: abcpk1234d", # Valid status 'p'
                "expected_entities": ["IN_PAN"]
            },
            {
                "category": "False Negatives (Obfuscation)",
                "description": "Mixed-case IFSC",
                "input": "Bank IFSC is hdfc0000123",
                "expected_entities": ["IN_IFSC"]
            },
            {
                "category": "False Negatives (Obfuscation)",
                "description": "Email with spaces (common in LLM errors)",
                "input": "Contact me at test @ example . com",
                "expected_entities": ["EMAIL_ADDRESS"],
                "note": "Custom ResilientEmailRecognizer catches this."
            },
            
            # --- FALSE POSITIVES (Lookalikes) ---
            {
                "category": "False Positives (Lookalikes)",
                "description": "12-digit number failing Verhoeff",
                "input": "Order number 123412341234",
                "expected_entities": [],
                "avoid_entities": ["IN_AADHAAR"]
            },
            {
                "category": "False Positives (Lookalikes)",
                "description": "10-digit quantity (non-mobile)",
                "input": "The total count is 1234567890 units",
                "expected_entities": [],
                "avoid_entities": ["IN_MOBILE"]
            },
            {
                "category": "False Positives (Lookalikes)",
                "description": "Random Alphanumeric (PAN lookalike - Invalid status 'X')",
                "input": "Model serial: GHIXX9999L", # 'X' is invalid status
                "expected_entities": [],
                "avoid_entities": ["IN_PAN"],
                "note": "PAN regex should ignore this as 'X' is not a valid status."
            },

            # --- NAIVE QUERIES (Direct disclosure) ---
            {
                "category": "Naive Queries",
                "description": "Direct Aadhaar disclosure without keywords",
                "input": "My ID is 366215485509",
                "expected_entities": ["IN_AADHAAR"]
            },
            {
                "category": "Naive Queries",
                "description": "Direct mobile disclosure without keywords",
                "input": "Reach me at 9876543210",
                "expected_entities": ["IN_MOBILE"]
            },
            {
                "category": "Naive Queries",
                "description": "UPI ID in sentence",
                "input": "Send money to receiver@okaxis",
                "expected_entities": ["IN_UPI"]
            }
        ]
        self.report_file = "PII_TEST_REPORT.txt"

    def run_tests(self):
        results = []
        print(f"Starting PII Edge Case Testing... ({len(self.test_cases)} cases)")
        
        for case in self.test_cases:
            print(f"Testing: {case['description']}...")
            
            # Use pii_engine to get raw analysis results
            analysis_results = pii_engine.analyze(case['input'])
            detected_entities = list(set([res.entity_type for res in analysis_results]))
            
            # Use sanitization_service for full flow
            try:
                sanitized_text, request_id, token_map, entity_summary, masked_entities = sanitization_service.sanitize(case['input'])
            except Exception as e:
                sanitized_text = f"ERROR: {str(e)}"
                entity_summary = {}

            # Evaluate Pass/Fail
            passed = True
            
            # Check expected entities
            for exp in case.get("expected_entities", []):
                if exp not in detected_entities:
                    passed = False
                    break
            
            # Check avoid entities
            for avoid in case.get("avoid_entities", []):
                if avoid in detected_entities:
                    passed = False
                    break
            
            results.append({
                "case": case,
                "detected": detected_entities,
                "sanitized": sanitized_text,
                "passed": passed
            })

        self.generate_report(results)
        print(f"Tests complete. Report generated at {self.report_file}")

    def generate_report(self, results):
        with open(self.report_file, "w") as f:
            f.write("====================================================\n")
            f.write("PII MIDDLEWARE EDGE-CASE TEST REPORT\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("====================================================\n\n")
            
            current_category = ""
            for res in results:
                case = res["case"]
                if case["category"] != current_category:
                    current_category = case["category"]
                    f.write(f"\n### CATEGORY: {current_category}\n")
                    f.write("-" * 40 + "\n")
                
                status = "PASS" if res["passed"] else "FAIL"
                f.write(f"Description: {case['description']}\n")
                f.write(f"Input      : {case['input']}\n")
                f.write(f"Expected   : {case.get('expected_entities', []) or 'None (Avoid ' + str(case.get('avoid_entities', [])) + ')'}\n")
                f.write(f"Actual     : {res['detected']}\n")
                f.write(f"Sanitized  : {res['sanitized']}\n")
                if "note" in case:
                    f.write(f"Note       : {case['note']}\n")
                f.write(f"Status     : [{status}]\n")
                f.write("\n")

            f.write("\n====================================================\n")
            f.write("SUMMARY\n")
            total = len(results)
            passed_count = sum(1 for r in results if r["passed"])
            f.write(f"Total Cases: {total}\n")
            f.write(f"Passed     : {passed_count}\n")
            f.write(f"Failed     : {total - passed_count}\n")
            f.write("====================================================\n")

if __name__ == "__main__":
    tester = EdgeCaseTester()
    tester.run_tests()
