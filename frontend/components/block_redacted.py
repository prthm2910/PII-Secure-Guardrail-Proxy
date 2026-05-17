import streamlit as st
import re

def render_redacted_output(content: str, is_loading: bool = False):
    st.markdown("<div class='block-header redacted-header'>3. LLM Redacted Output (Raw Response)</div>", unsafe_allow_html=True)
    
    if is_loading:
        st.markdown(f"<div class='terminal-box'><i>{content}</i></div>", unsafe_allow_html=True)
    else:
        # Highlight tokens
        red_content_hl = re.sub(r"(\[.*?_\d+\])", r"<span class='token-highlight'>\1</span>", content)
        st.markdown(f"<div class='terminal-box'>{red_content_hl}</div>", unsafe_allow_html=True)
