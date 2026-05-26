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
                "input": "\uff13\uff16\uff16\uff12\uff11\uff15\uff14\uff18\uff15\uff15\uff10\uff19", # ３６６２ １５４８ ５５０９
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
            {
                "category": "Obfuscation",
                "description": "Aadhaar with parentheses formatting",
                "input": "(3662) (1548) (5509)",
                "expected": ["IN_AADHAAR"]
            },
            {
                "category": "Obfuscation",
                "description": "GSTIN with non-breaking spaces (NBSP)",
                "input": "07\u00A0AAAAA\u00A00000\u00A0A1\u00A0Z4",
                "expected": ["IN_GSTIN"]
            },
            {
                "category": "Obfuscation",
                "description": "Mobile number with excessive separators",
                "input": "+91--98765--43210",
                "expected": ["IN_MOBILE"]
            },
            {
                "category": "Obfuscation",
                "description": "IFSC with dot separators",
                "input": "H.D.F.C.0.0.0.0.1.2.3",
                "expected": ["IN_IFSC"]
            },
            {
                "category": "Obfuscation",
                "description": "PAN with HTML tags injection",
                "input": "The ID is A<b>B</b>CPK1234D",
                "expected": ["IN_PAN"]
            },
            {
                "category": "Obfuscation",
                "description": "Aadhaar with soft hyphen",
                "input": "3662\u00AD1548\u00AD5509",
                "expected": ["IN_AADHAAR"]
            },
            {
                "category": "Obfuscation",
                "description": "GSTIN with Zero-Width Non-Joiner (ZWNJ)",
                "input": "07\u200CAAAAA\u200C0000\u200CA1\u200CZ4",
                "expected": ["IN_GSTIN"]
            },
            {
                "category": "Obfuscation",
                "description": "Email with [at] and [dot] obfuscation",
                "input": "john.doe [at] example [dot] com",
                "expected": ["EMAIL_ADDRESS"]
            },
            {
                "category": "Obfuscation",
                "description": "PAN with invisible tab characters",
                "input": "A\tB\tC\tP\tK\t1\t2\t3\t4\tD",
                "expected": ["IN_PAN"]
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
            {
                "category": "Encoding/Wrappers",
                "description": "Hex encoded Aadhaar",
                "input": "333636323135343835353039", # 366215485509 in hex
                "expected": ["IN_AADHAAR"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "HTML Entity encoded PAN",
                "input": "&#65;&#66;&#67;&#80;&#75;&#49;&#50;&#51;&#52;&#68;", # ABCPK1234D
                "expected": ["IN_PAN"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "PII in YAML format",
                "input": "user:\n  pan: ABCPK1234D\n  aadhaar: '366215485509'",
                "expected": ["IN_PAN", "IN_AADHAAR"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "PII in CSV with varied quotes",
                "input": '"ABCPK1234D","366215485509",\'9876543210\'',
                "expected": ["IN_PAN", "IN_AADHAAR", "IN_MOBILE"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "PII in XML CDATA section",
                "input": "<data><![CDATA[The PAN is ABCPK1234D and Aadhaar is 366215485509]]></data>",
                "expected": ["IN_PAN", "IN_AADHAAR"]
            },
            {
                "category": "Encoding/Wrappers",
                "description": "Double URL encoded PAN",
                "input": "%2541%2542%2543%2550%254b%2531%2532%2533%2534%2544", # ABCPK1234D
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
            {
                "category": "Collisions/Ambiguity",
                "description": "Random 12-digit number (Invalid Aadhaar checksum)",
                "input": "The random seed is 123456789012.",
                "expected": [],
                "avoid": ["IN_AADHAAR"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "Random 10-digit number (Not a mobile number)",
                "input": "The count is 1000000000.",
                "expected": [],
                "avoid": ["IN_MOBILE"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "15-digit random string (Invalid GSTIN checksum)",
                "input": "Reference: 27AAAAA0000A1ZA.",
                "expected": [],
                "avoid": ["IN_GSTIN"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "Date looking like Aadhaar fragment",
                "input": "Date: 2023-10-27 15:30",
                "expected": [],
                "avoid": ["IN_AADHAAR"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "PIN code vs Mobile fragment",
                "input": "My PIN code is 400001.",
                "expected": [],
                "avoid": ["IN_MOBILE"]
            },
            {
                "category": "Collisions/Ambiguity",
                "description": "Price vs Bank Account fragment",
                "input": "Total Price: 1,23,456.78",
                "expected": [],
                "avoid": ["IN_BANK_ACC"]
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
            },
            {
                "category": "Contextual Bypasses",
                "description": "PII in a list of mixed technical items",
                "input": "Inventory:\n1. Server: 192.168.1.1\n2. Admin: 9876543210\n3. Port: 8080",
                "expected": ["IN_MOBILE"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "PII inside a technical log message",
                "input": "DEBUG [Session: 366215485509] Processing request for user ABCPK1234D",
                "expected": ["IN_AADHAAR", "IN_PAN"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "PII in code comments",
                "input": "// TODO: Reach out to secondary contact at +91 98765 43210",
                "expected": ["IN_MOBILE"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "PII masked with common patterns (partial)",
                "input": "My PAN is ABCXXXX234D",
                "expected": ["IN_PAN"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "Multiple PII in tight proximity",
                "input": "PAN:ABCPK1234D,AADHAAR:366215485509,MOBILE:9876543210",
                "expected": ["IN_PAN", "IN_AADHAAR", "IN_MOBILE"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "PII in non-English context (Hinglish)",
                "input": "Mera Aadhaar number 3662 1548 5509 hai.",
                "expected": ["IN_AADHAAR"]
            },
            {
                "category": "Contextual Bypasses",
                "description": "PII in a highly formatted table",
                "input": "| Name | ID Type | ID Value |\n| --- | --- | --- |\n| John | PAN | ABCPK1234D |",
                "expected": ["IN_PAN"]
            },

            # --- CATEGORY: COMPLEX SEMANTIC BYPASSES ---
            {
                "category": "Semantic",
                "description": "PII spread across semantic boundaries",
                "input": "The first part of my PAN is ABCPK and the second part is 1234D.",
                "expected": ["IN_PAN"]
            },
            {
                "category": "Semantic",
                "description": "PII disguised as other data (Phone as Serial)",
                "input": "The serial number of the device is +91-98765-43210.",
                "expected": ["IN_MOBILE"]
            },
            {
                "category": "Semantic",
                "description": "PII in a natural conversation (Asking for help)",
                "input": "I am unable to login. My registered email is john.doe@example.com and mobile is 9876543210. Help!",
                "expected": ["EMAIL_ADDRESS", "IN_MOBILE"]
            },
            {
                "category": "Semantic",
                "description": "PII in a signature block",
                "input": "Regards,\nJohn Doe\nMob: 9876543210\nPAN: ABCPK1234D",
                "expected": ["IN_MOBILE", "IN_PAN"]
            },
            {
                "category": "Semantic",
                "description": "PII in a URL path as resource ID",
                "input": "GET /api/users/366215485509/profile",
                "expected": ["IN_AADHAAR"]
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
