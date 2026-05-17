import streamlit as st

def render_raw_query(content: str):
    st.markdown("<div class='block-header raw-header'>1. Raw User Query</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='terminal-box'>{content}</div>", unsafe_allow_html=True)
