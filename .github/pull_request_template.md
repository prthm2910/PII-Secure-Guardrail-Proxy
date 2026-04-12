## 📝 System Decision Record (SDR)

### 🎯 Objective
*Summarize the core purpose of this change. What specific PII or architectural layer does this address?*

### ⚖️ Technical Trade-offs & Decisions
*Document the "Why" behind the "How". Example: Why use Verhoeff over Regex? Why Redis over local memory?*
- **Decision:** [e.g., Custom EntityRecognizer vs PatternRecognizer]
- **Trade-off:** [e.g., Higher complexity but allows for pre-extraction checksum validation to reduce NLP noise.]

### 🏛️ Architectural Alignment
- [ ] **Decoupled Logic**: Does this change maintain the "Data Loss Prevention API Gateway" separation?
- [ ] **Indian Compliance**: Does this align with DPDP 2023 or RBI Data Localization mandates?
- [ ] **Performance**: Is the latency overhead for this logic minimal (Target < 50ms)?

### 🛡️ Quality Gate & Verification
*Paste snippets of the dry run or test results here to document the state of the system at merge.*
- [ ] **Local Tests**: `uv run pytest` passed.
- [ ] **Redis State**: TTL and ephemeral mapping confirmed.

### 📖 Self-Documentation Note
*This PR acts as a permanent record of the implementation details for future maintenance and scaling. No external review is required for this solo-sprint.*
