import streamlit as st
import asyncio
import os
from dotenv import load_dotenv

from styles import TERMINAL_STYLE
from flow_manager import FlowManager, FlowStatus
from components.sidebar import render_sidebar
from components.block_raw import render_raw_query
from components.block_sanitized import render_sanitized_input
from components.block_redacted import render_redacted_output
from components.block_desanitized import render_desanitized_output

# Load .env file
load_dotenv()

# Page Config
st.set_page_config(
    page_title="PII Proxy Quad-Block UI",
    page_icon="🛡️",
    layout="wide"
)

# Inject Global Styles
st.markdown(TERMINAL_STYLE, unsafe_allow_html=True)

# Initialize Flow Manager
fm = FlowManager()

# App Header
st.markdown("<h1 class='main-title'>PII Transformation Lifecycle</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-title'>Modular architecture visualizing eager sanitization and LLM redaction</p>", unsafe_allow_html=True)

# Sidebar
render_sidebar(fm)

# Main Input Logic
input_val = st.chat_input("Type a query with PII...")
if hasattr(st.session_state, "pending_input"):
    input_val = st.session_state.pending_input
    del st.session_state.pending_input

if input_val:
    # Trigger Step 1: Sanitize
    fm.reset_state()
    fm.run_sanitize(input_val)
    st.rerun()

# Layout
query = st.session_state.current_query

# Row 1
col1, col2 = st.columns(2)
with col1:
    render_raw_query(query["raw"])
with col2:
    render_sanitized_input(query["sanitized"])

st.markdown("<div style='margin: 10px 0;'></div>", unsafe_allow_html=True)

# Row 2
col3, col4 = st.columns(2)
with col3:
    is_loading = query["status"] in [FlowStatus.SANITIZING.value, FlowStatus.CHATTING.value, FlowStatus.SANITIZED.value]
    loading_text = "Analyzing..." if query["status"] == FlowStatus.SANITIZING.value else "Waiting for LLM..."
    content = loading_text if is_loading and not query["redacted"] else query["redacted"]
    render_redacted_output(content, is_loading=is_loading and not query["redacted"])

with col4:
    content = loading_text if is_loading and not query["desanitized"] else query["desanitized"]
    render_desanitized_output(content, is_loading=is_loading and not query["desanitized"])

# Footer
if query["request_id"]:
    st.divider()
    st.caption(f"Session ID: {query['request_id']} | Status: {query['status'].upper()}")
    if query["status"] == FlowStatus.ERROR.value:
        st.error(query["error_message"])

# Step 2 Trigger: Background LLM Call
if query["status"] == FlowStatus.SANITIZED.value:
    with st.spinner("LLM is processing..."):
        fm.run_chat()
        st.rerun()
