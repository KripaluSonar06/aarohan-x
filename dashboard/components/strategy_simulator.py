import streamlit as st
import pandas as pd

def render(decision_explanation):
    """
    Render the strategy simulator table.
    Expects decision_explanation dict with keys: selected_action, all_ev, why, why_not, counterfactuals.
    """
    all_ev = decision_explanation.get("all_ev", [])
    if all_ev:
        df = pd.DataFrame(all_ev)
        df.columns = ["Action", "Cost", "EV", "Probability", "Net Positive"]
        st.dataframe(df, use_container_width=True)
    
    st.write("**Why selected?**")
    for reason in decision_explanation.get("why", []):
        st.write(f"- {reason}")
    
    st.write("**Why not others?**")
    for reason in decision_explanation.get("why_not", []):
        st.write(f"- {reason}")
    
    st.write("**Counterfactuals**")
    for cf in decision_explanation.get("counterfactuals", []):
        st.write(f"- {cf}")