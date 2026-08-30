import streamlit as st
from datetime import datetime

def render(state):
    """Render a vertical timeline of ledger events."""
    ledger = state.get("ledger", [])
    if not ledger:
        st.write("No timeline events.")
        return
    
    # Sort by timestamp
    ledger_sorted = sorted(ledger, key=lambda x: x.get("timestamp", ""))
    for entry in ledger_sorted:
        ts = entry.get("timestamp", "")
        action = entry.get("action", "")
        detail = entry.get("detail", {})
        cost = entry.get("cost", 0.0)
        col1, col2 = st.columns([1, 3])
        with col1:
            st.write(ts)
        with col2:
            st.write(f"**{action}**")
            if detail:
                st.write(detail)
            if cost:
                st.write(f"Cost: ₹{cost:.2f}")
        st.markdown("---")