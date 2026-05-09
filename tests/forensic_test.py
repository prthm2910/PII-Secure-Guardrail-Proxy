import sys
import os
import base64
import urllib.parse
from datetime import datetime
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock redis_service
mock_redis = MagicMock()
import app.services.redis_service
app.services.redis_service.redis_service = mock_redis

from app.services.pii_engine import pii_engine
from app.services.sanitization_service import sanitization_service

class ForensicTester:
    def __init__(self):
        self.test_cases = [
            # --- CATEGORY: OBFUSCATION (Homoglyphs, Unicode, Injections) ---
            {
                "category": "Obfuscation",
                "description": "PAN with Cyrillic Homoglyphs (A, B, C, P)",
                "input": "\u0410\u0412\u0421D\u04201234F",  # АВСDР1234F
                "expected": ["IN_PAN"]
            },
            {
                "category": "Obfuscation",
                "description": "GSTIN with Cyrillic Homoglyphs (A, O)",
                "input": "07\u0410\u0410\u0410\u0410\u04100000\u04101Z4",  # 07AAAAA0000A1Z4
                "expected": ["IN_GSTIN"]
            },
            {
                "category": "Obfuscation",
                "description": "Full-width Aadhaar Number",
                "input": "\uff13\uff16\uff16\uff12\uff11\uff15\uff14\uff18\uff15\uff15\uff10\uff19", # ３６６２１５４８５５０９
                "expected": ["IN_AADHAAR"]
            },
            {
                "category": "Obfuscation",
                "description": "Aadhaar with Zero-Width Space (ZWSP)",
                "input": "3662\u200B1548\u200B5509",
                "expected": ["IN_AADHAAR"]
            },
            {
                "category": "Obfuscation",
                "description": "GSTIN split across multiple lines",
                "input": "GST Number:\n07\nAAAAA\n0000\nA1\nZ2", # Corrected checksum
                "expected": ["IN_GSTIN"]
            },
            {
                "category": "Obfuscation",
                "description": "Bank Account with mixed dot and dash separators",
                "input": "Beneficiary Acc: 123.456.789-012",
                "expected": ["IN_BANK_ACC"]
            },

            # --- CATEGORY: ENCODING/WRAPPERS ---
            {
                "category": "Encoding/Wrappers",
                "description": "Full Base64 encoded PAN",
                "input": "QUJDUEsxMjM0RA==", # ABCPK1234D
                "expected": ["IN_PAN"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "URL encoded GSTIN in query parameter",
                "input": "https://api.example.in/v2/verify?id=27AAAAA0000A1Z2&type=gstin",
                "expected": ["IN_GSTIN"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "PII nested in raw JSON with escape characters",
                "input": '{"payload": {"metadata": "User ID: ABCPK1234D", "aadhaar_ref": "366215485509"}}',
                "expected": ["IN_PAN", "IN_AADHAAR"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "Markdown bold splitting within PAN",
                "input": "The requested ID is **ABCPK**1234D",
                "expected": ["IN_PAN"]
            },

            # --- CATEGORY: COLLISIONS/AMBIGUITY ---
            {
                "category": "Collisions/Ambiguity",
                "description": "PAN embedded in GSTIN collision",
                "input": "The entity GSTIN is 27ABCPK1234D1Z2.",
                "expected": ["IN_GSTIN"],
                "avoid": ["IN_PAN"] # We prefer GSTIN over the nested PAN
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "Invalid GSTIN checksum ambiguity",
                "input": "Please check invoice 27ABCPK1234D1ZA for errors.",
                "expected": [],
                "avoid": ["IN_GSTIN"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "Invalid PAN status code ambiguity",
                "input": "Serial Number: ABCDE1234F", # 'E' is invalid status
                "expected": [],
                "avoid": ["IN_PAN"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "CDSL Demat ID vs Timestamp ambiguity",
                "input": "Operation completed at 2023102715304512.",
                "expected": [],
                "avoid": ["IN_DEMAT"]
            },

            # --- CATEGORY: CONTEXTUAL BYPASSES ---
            {
                "category": "Contextual Bypasses",
                "description": "Bank Account anchor far beyond proximity window",
                "input": "IFSC code for this branch is HDFC0000123. Please note that the primary identification number for the customer is 9876543210.",
                "expected": ["IN_BANK_ACC"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "Negated Bank Account anchor",
                "input": "This is NOT an account: 1234567890",
                "expected": ["IN_BANK_ACC"] # Engine should be cautious and still detect
            },
            {
                "category": "Contextual Bypasses",
                "description": "Folio surrounded by noisy numeric context",
                "input": "123 456 789 012 345 678 901 234 567 890 Mutual Fund 98765/43/2",
                "expected": ["IN_MF_FOLIO"]
            }
        ]
        self.report_file = "PII_FORENSIC_REPORT.txt"

    def run(self):
        results = []
        print(f"🕵️ Starting Forensic PII Testing (Full Pipeline)... ({len(self.test_cases)} cases)")
        
        for case in self.test_cases:
            # Use the full sanitization pipeline to trigger Normalization
            sanitized_text, request_id, token_map, entity_summary, masked_entities = sanitization_service.sanitize(case['input'])
            
            # Extract detected entities from the summary
            detected = list(entity_summary.keys())
            
            passed = True
            # Check for missing expected entities
            for exp in case.get("expected", []):
                if exp not in detected:
                    passed = False
                    break
            
            # Check for unwanted entities (false positives)
            if passed: # Only check avoid if expectations met
                for av in case.get("avoid", []):
                    if av in detected:
                        passed = False
                        break
            
            results.append({
                "case": case,
                "detected": detected,
                "passed": passed
            })
        
        self.generate_report(results)

    def generate_report(self, results):
        with open(self.report_file, "w", encoding="utf-8") as f:
            f.write("====================================================\n")
            f.write("🕵️ PII ENGINE FORENSIC ANALYSIS REPORT\n")
            f.write(f"Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("====================================================\n\n")
            
            total = len(results)
            passed_count = sum(1 for r in results if r["passed"])
            
            f.write(f"SUMMARY: {passed_count}/{total} Passed\n")
            f.write("Vulnerability Rate: {:.2f}%\n".format((1 - passed_count/total)*100))
            f.write("-" * 40 + "\n\n")

            current_cat = ""
            for res in results:
                case = res["case"]
                if case["category"] != current_cat:
                    current_cat = case["category"]
                    f.write(f"\n### CATEGORY: {current_cat}\n")
                
                status = "✅ PASS" if res["passed"] else "❌ FAIL"
                f.write(f"{status} | {case['description']}\n")
                f.write(f"  Input   : {case['input'].replace('\n', '\\n')}\n")
                f.write(f"  Expected: {case.get('expected') or 'None'}\n")
                f.write(f"  Actual  : {res['detected']}\n")
                f.write("\n")

        print(f"Forensic report generated at {self.report_file}")

if __name__ == "__main__":
    tester = ForensicTester()
    tester.run()
