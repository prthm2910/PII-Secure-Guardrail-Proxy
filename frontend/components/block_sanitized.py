import streamlit as st
import re

def render_sanitized_input(content: str):
    st.markdown("<div class='block-header sanitized-header'>2. Sanitized Raw Input (To LLM)</div>", unsafe_allow_html=True)
    
    # Highlight tokens using the same regex pattern
    san_content_hl = re.sub(r"(\[.*?_\d+\])", r"<span class='token-highlight'>\1</span>", content)
    
    st.markdown(f"<div class='terminal-box'>{san_content_hl}</div>", unsafe_allow_html=True)
