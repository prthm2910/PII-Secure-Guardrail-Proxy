# CSS and Visual Constants for the PII Proxy UI

TERMINAL_STYLE = """
<style>
    .stApp {
        background-color: #0e1117;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(90deg, #00f2a1, #00bbff);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        color: #8b949e;
        font-size: 1rem;
        margin-bottom: 2rem;
    }
    .block-header {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        margin-bottom: 8px;
        letter-spacing: 0.05rem;
    }
    .terminal-box {
        background-color: #0d1117;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #30363d;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.95rem;
        line-height: 1.5;
        min-height: 200px;
        max-height: 400px;
        overflow-y: auto;
        white-space: pre-wrap;
    }
    .raw-header { color: #8b949e; }
    .sanitized-header { color: #00f2a1; }
    .redacted-header { color: #ff4b4b; }
    .desanitized-header { color: #00bbff; }
    
    .token-highlight {
        color: #00f2a1;
        font-weight: bold;
        background-color: rgba(0,242,161,0.1);
        padding: 0px 4px;
        border-radius: 3px;
    }
</style>
"""
