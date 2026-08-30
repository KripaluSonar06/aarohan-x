import streamlit as st

def render():
    """Display the intervention ladder graphic."""
    st.markdown("""
    ### Intervention Ladder
    0. No action
    1. Silent retry
    2. Payment link / re-auth
    3. SMS/WhatsApp
    4. Voice call
    5. Merchant escalation
    STOP
    """)