import streamlit as st

def render_desanitized_output(content: str, is_loading: bool = False):
    st.markdown("<div class='block-header desanitized-header'>4. De-Sanitized LLM Output (Final User View)</div>", unsafe_allow_html=True)
    
    if is_loading:
        st.markdown(f"<div class='terminal-box'><i>{content}</i></div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='terminal-box'>{content}</div>", unsafe_allow_html=True)
