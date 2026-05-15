import sys
import os
import re
from unittest.mock import MagicMock

# Add the project root to sys.path
sys.path.append(os.getcwd())

# Mock redis_service for standalone testing
mock_redis = MagicMock()
import app.services.redis_service
app.services.redis_service.redis_service = mock_redis

from app.services.pii_engine import pii_engine
from app.services.sanitization_service import sanitization_service
from app.services.normalization_service import normalization_service

class ChatHarness:
    def __init__(self):
        self.banner = """
============================================================
🛡️  PII MIDDLEWARE INTERACTIVE CHAT HARNESS (v1.0)
============================================================
Instructions:
- Type your message and hit ENTER.
- For MULTI-LINE: Type your text and hit ENTER TWICE to process.
- Use Ctrl+C to terminate the session.
============================================================
"""

    def print_table(self, data):
        """Prints a structured ASCII table for metadata."""
        if not data:
            print("\n[ No PII Detected ]")
            return

        headers = ["Entity Type", "Score", "Raw Text", "Masked (Audit)"]
        # Calculate column widths
        widths = [len(h) for h in headers]
        for row in data:
            for i, val in enumerate(row):
                widths[i] = max(widths[i], len(str(val)))

        # Build separators
        sep = "+" + "+".join(["-" * (w + 2) for w in widths]) + "+"
        
        # Print Header
        print("\n📊 EXTRACTED METADATA:")
        print(sep)
        header_row = "| " + " | ".join([h.ljust(widths[i]) for i, h in enumerate(headers)]) + " |"
        print(header_row)
        print(sep.replace("-", "="))

        # Print Rows
        for row in data:
            row_str = "| " + " | ".join([str(val).ljust(widths[i]) for i, val in enumerate(row)]) + " |"
            print(row_str)
        print(sep)

    def get_input(self):
        """Handles both single and multi-line input logic."""
        print("\n\n💬 INPUT QUERY (Hit Enter twice for multi-line):")
        lines = []
        while True:
            line = input("> ")
            if not line:
                break
            lines.append(line)
            # If only one line is entered and it's not empty, we can process immediately 
            # unless the user keeps typing. Let's wait for a blank line to confirm intent.
            if len(lines) == 1:
                # Small delay/check to allow immediate single-line if preferred, 
                # but "Enter twice" is safer for copy-pasting.
                pass
        
        return "\n".join(lines)

    def run(self):
        print(self.banner)
        try:
            while True:
                text = self.get_input()
                if not text.strip():
                    continue

                # 1. Analyze for metadata (scores)
                # We normalize first just like the service does
                clean_text = normalization_service.normalize(text)
                raw_results = pii_engine.analyze(clean_text)

                # 2. Sanitize for final output
                sanitized, req_id, token_map, summary, masked_entities = sanitization_service.sanitize(text)

                # 3. Prepare table data
                table_data = []
                for res in raw_results:
                    raw_val = clean_text[res.start:res.end]
                    # Find the token associated with this value in the sanitized output if possible
                    # Or just show the masked version from the service logic
                    masked_val = sanitization_service.mask_for_logs(clean_text, res.entity_type, raw_val)
                    
                    table_data.append([
                        res.entity_type,
                        f"{res.score:.2f}",
                        raw_val,
                        masked_val
                    ])

                # 4. Display Results
                self.print_table(table_data)

                print("\n🚀 FINAL SANITIZED OUTPUT (Sent to LLM):")
                print("-" * 40)
                print(sanitized)
                print("-" * 40)

        except KeyboardInterrupt:
            print("\n\n👋 Terminating session. Stay secure!")
            sys.exit(0)

if __name__ == "__main__":
    harness = ChatHarness()
    harness.run()
