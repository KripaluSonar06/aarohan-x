"""
Aarohan-X Dashboard - Streamlit frontend.
Displays recovery metrics, case details, and policy configuration.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timezone
from sqlalchemy import func
from config.settings import settings
from models.entities import RecoveryEvent, LedgerEntry
from utils.db import SessionLocal
from dashboard.state_loader import load_events, load_event_detail, load_metrics
from dashboard.components import strategy_simulator, intervention_ladder, timeline

st.set_page_config(page_title="Aarohan-X", page_icon="📈", layout="wide")

# Sidebar navigation
st.sidebar.title("Aarohan-X")
st.sidebar.caption("Autonomous Revenue Recovery")

page = st.sidebar.radio("Navigation", ["Run", "Case Detail", "Money", "Exceptions", "Policy Center"])

# Initialize DB session
db = SessionLocal()

if page == "Run":
    st.title("Run Recovery Agent")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Events Loaded", db.query(RecoveryEvent).count())
    with col2:
        st.metric("Active", db.query(RecoveryEvent).filter(RecoveryEvent.status == "active").count())
    with col3:
        recovered = db.query(func.sum(RecoveryEvent.recovered_amount_paise)).scalar() or 0
        st.metric("Recovered ₹", f"{recovered/100:.2f}")
    
    if st.button("▶️ Run Recovery Batch", type="primary"):
        with st.spinner("Processing events..."):
            # In a real app, we would call the orchestrator here.
            # For demo, we simulate by loading existing results.
            st.success("Batch complete. See Money for results.")
    
    # Show recent events table
    events = db.query(RecoveryEvent).order_by(RecoveryEvent.created_at.desc()).limit(20).all()
    if events:
        df = pd.DataFrame([e.to_dict() for e in events])
        st.dataframe(df, use_container_width=True)

elif page == "Case Detail":
    st.title("Case Detail")
    event_ids = [e.id for e in db.query(RecoveryEvent.id).all()]
    event_id = st.selectbox("Select Event", event_ids)
    if event_id:
        state = load_event_detail(event_id, db)
        if state:
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Diagnosis")
                st.write(f"**Class:** {state.get('diagnosed_class')}")
                st.write(f"**Confidence:** {state.get('diagnosis_confidence')}")
                st.write(f"**Source:** {state.get('diagnosis_source')}")
                st.write("**Gates Passed:**", state.get('gates_passed'))
                st.write("**Gates Blocked:**", state.get('gates_blocked'))
            with col2:
                st.subheader("Action & Value")
                st.write(f"**Playbook Action:** {state.get('playbook_action')}")
                st.write(f"**Recovery Probability:** {state.get('recovery_probability')}")
                st.write(f"**Expected Gross ₹:** {state.get('expected_gross_value')}")
                st.write(f"**Channel Cost ₹:** {state.get('channel_cost')}")
                st.write(f"**Net Expected ₹:** {state.get('net_expected_value')}")
            
            # Timeline
            st.subheader("Recovery Timeline")
            timeline.render(state)
            
            # Strategy simulator (if decision_explanation present)
            if 'decision_explanation' in state:
                st.subheader("Recovery Strategy Simulator")
                strategy_simulator.render(state['decision_explanation'])
            
            # Ledger
            st.subheader("Audit Ledger")
            ledger_df = pd.DataFrame(state.get('ledger', []))
            st.dataframe(ledger_df, use_container_width=True)

elif page == "Money":
    st.title("Money Scoreboard")
    metrics = load_metrics(db)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("₹ At Risk", f"{metrics['total_at_risk']/100:.2f}")
    with col2:
        st.metric("Gross Recovered", f"{metrics['gross_recovered']/100:.2f}")
    with col3:
        st.metric("Net Recovered", f"{metrics['net_recovered']/100:.2f}")
    with col4:
        st.metric("Incremental Lift", f"+{metrics['incremental_lift']/100:.2f}")
    
    st.subheader("Where did the money come from?")
    breakdown = metrics['channel_breakdown']
    if breakdown:
        st.bar_chart(pd.DataFrame(breakdown).set_index('channel'))
    
    st.subheader("Recovery Rate by Class")
    class_rates = metrics['class_rates']
    if class_rates:
        st.bar_chart(pd.DataFrame(class_rates).set_index('class'))

elif page == "Exceptions":
    st.title("Exceptions & Needs Human")
    exceptions = db.query(RecoveryEvent).filter(
        RecoveryEvent.status.in_(["needs_human", "escalated"])
    ).all()
    if exceptions:
        st.dataframe([e.to_dict() for e in exceptions], use_container_width=True)
    else:
        st.write("No exceptions.")

elif page == "Policy Center":
    st.title("Merchant Policy Center")
    st.write("The AI optimizes only inside these boundaries.")
    col1, col2 = st.columns(2)
    with col1:
        max_silent = st.number_input("Max silent retries", min_value=0, max_value=5, value=settings.SYSTEM_MAX_SILENT_RETRIES)
        max_sms = st.number_input("Max SMS attempts", min_value=0, max_value=5, value=settings.SYSTEM_MAX_CUSTOMER_CONTACTS)
        max_voice = st.number_input("Max voice attempts", min_value=0, max_value=3, value=1)
    with col2:
        voice_threshold = st.number_input("Voice threshold (₹)", min_value=0, value=settings.VOICE_MIN_AMOUNT_PAISE//100)
        max_discount = st.number_input("Max discount %", min_value=0, max_value=20, value=int(settings.DISCOUNT_MAX_PERCENT))
        quiet_start = st.time_input("Quiet hours start", value=datetime.strptime("21:00", "%H:%M").time())
        quiet_end = st.time_input("Quiet hours end", value=datetime.strptime("09:00", "%H:%M").time())
    if st.button("Save Policy", type="primary"):
        # Here we would update policy_manager and persist to DB
        st.success("Policy saved (demo only)")

db.close()