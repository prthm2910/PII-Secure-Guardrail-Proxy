import streamlit as st

def render_sidebar(flow_manager):
    st.sidebar.title("🛡️ Proxy Controls")
    
    if st.sidebar.button("🗑️ Reset UI"):
        flow_manager.reset_state()
        st.rerun()
        
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Test Templates")
    templates = {
        "🇮🇳 Financial PII": "Hi, my name is Rahul. My PAN is BKXPS1234Z. I need help with my account.",
        "🏦 Business ID": "Company GSTIN is 27AAAAA0000A1Z5. Please process this invoice.",
        "🆔 Identity PII": "Registering user with Aadhaar: 1234 5678 9012 and email: test@example.com."
    }
    
    for label, text in templates.items():
        if st.sidebar.button(label):
            st.session_state.pending_input = text
            st.rerun()
