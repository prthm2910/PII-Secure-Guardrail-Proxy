import sys
import os
import unittest
from unittest.mock import MagicMock
from typing import List, Dict

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock redis_service before imports
mock_redis = MagicMock()
import app.services.redis_service
app.services.redis_service.redis_service = mock_redis

from app.services.sanitization_service import sanitization_service
from datetime import datetime

class EdgeCaseTester:
    def __init__(self):
        self.test_cases = [
            # --- OBFUSCATION CASES ---
            {
                "category": "False Negatives (Obfuscation)",
                "description": "Aadhaar with mixed separators",
                "input": "My Aadhaar is 3662- 1548_5509",
                "expected_entities": ["IN_AADHAAR"]
            },
            {
                "category": "False Negatives (Obfuscation)",
                "description": "Mixed-case PAN (Valid Status 'P')",
                "input": "PAN: abcpk1234d",
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
            
            # --- LOOKALIE CASES ---
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
                "input": "Model serial: GHIXX9999L",
                "expected_entities": [],
                "avoid_entities": ["IN_PAN"],
                "note": "PAN regex should ignore this as 'X' is not a valid status."
            },

            # --- NAIVE QUERIES ---
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
            },
            # --- FINANCIAL EXPANSION CASES ---
            {
                "category": "Financial Expansion",
                "description": "Valid GSTIN (27AAAAA0000A1Z2)",
                "input": "Our GSTIN is 27AAAAA0000A1Z2",
                "expected_entities": ["IN_GSTIN"]
            },
            {
                "category": "Financial Expansion",
                "description": "Valid TAN (BLRP12345G)",
                "input": "TAN Number: BLRP12345G",
                "expected_entities": ["IN_TAN"]
            },
            {
                "category": "Financial Expansion",
                "description": "Valid CDSL Demat (16 digits)",
                "input": "Demat A/c: 1234567890123456",
                "expected_entities": ["IN_DEMAT"]
            },
            {
                "category": "Financial Expansion",
                "description": "Valid NSDL Demat (IN + 14 digits)",
                "input": "NSDL ID: IN12345678901234",
                "expected_entities": ["IN_DEMAT"]
            },
            {
                "category": "Financial Expansion",
                "description": "Bank Account with Anchor (IFSC)",
                "input": "Account 1234567890 for IFSC HDFC0000123",
                "expected_entities": ["IN_BANK_ACC", "IN_IFSC"]
            },
            {
                "category": "Financial Expansion",
                "description": "MF Folio with Anchor",
                "input": "Folio No: 123/45678/0",
                "expected_entities": ["IN_MF_FOLIO"]
            },
            {
                "category": "False Positives (Financial)",
                "description": "Random 10-digit number (No Bank Anchor)",
                "input": "The total is 1234567890",
                "expected_entities": [],
                "avoid_entities": ["IN_BANK_ACC"]
            }
        ]
        self.report_file = "PII_TEST_REPORT.txt"

    def run_tests(self):
        results = []
        print(f"🕵️ Running PII Edge Case Tests... ({len(self.test_cases)} cases)")
        
        for case in self.test_cases:
            # 1. Sanitize
            sanitized, req_id, tokens, summary, masked = sanitization_service.sanitize(case["input"])
            
            # 2. Extract detected entity types
            detected = list(summary.keys())
            
            # 3. Validate
            passed = True
            # Must find all expected
            for exp in case.get("expected_entities", []):
                if exp not in detected:
                    passed = False
            # Must avoid unwanted
            for av in case.get("avoid_entities", []):
                if av in detected:
                    passed = False
            
            results.append({
                "case": case,
                "detected": detected,
                "sanitized": sanitized,
                "passed": passed
            })
        
        self.generate_report(results)

    def generate_report(self, results):
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write("====================================================\n")
            f.write("PII MIDDLEWARE EDGE-CASE TEST REPORT\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("====================================================\n\n")

            current_cat = ""
            for res in results:
                case = res["case"]
                if case["category"] != current_cat:
                    current_cat = case["category"]
                    f.write(f"\n### CATEGORY: {current_cat}\n")
                    f.write("-" * 40 + "\n")
                
                f.write(f"Description: {case['description']}\n")
                f.write(f"Input      : {case['input']}\n")
                f.write(f"Expected   : {case.get('expected_entities') or 'None (Avoid ' + str(case.get('avoid_entities')) + ')'}\n")
                f.write(f"Actual     : {res['detected']}\n")
                f.write(f"Sanitized  : {res['sanitized']}\n")
                if "note" in case:
                    f.write(f"Note       : {case['note']}\n")
                f.write(f"Status     : [{'PASS' if res['passed'] else 'FAIL'}]\n\n")

            total = len(results)
            passed_count = sum(1 for r in results if r["passed"])
            f.write("\n" + "=" * 52 + "\n")
            f.write("SUMMARY\n")
            f.write(f"Total Cases: {total}\n")
            f.write(f"Passed     : {passed_count}\n")
            f.write(f"Failed     : {total - passed_count}\n")
            f.write("=" * 52 + "\n")

        print(f"Test report generated at {self.report_file}")

if __name__ == "__main__":
    tester = EdgeCaseTester()
    tester.run_tests()
