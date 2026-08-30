import pytest
from core.decision_engine import compute_ev, select_optimal_action, generate_decision_explanation

def test_compute_ev_basic():
    # probability 0.5, amount 1000 paise = ₹10, cost ₹1
    ev = compute_ev(0.5, 1000, 1.0)
    assert ev == pytest.approx(4.0)  # 0.5*10 - 1 = 5 - 1 = 4

def test_select_optimal_action_chooses_positive_ev():
    state = {"amount_paise": 100000}  # ₹1000
    allowed = ["silent_retry", "text_nudge", "voice_call"]
    # silent_retry cost 0, text cost 0.1, voice cost 5
    result = select_optimal_action(state, allowed, 0.4)
    assert result["selected_action"] == "silent_retry"  # highest EV due to zero cost

def test_select_optimal_action_stops_if_no_positive_ev():
    state = {"amount_paise": 100}  # ₹1
    allowed = ["text_nudge", "voice_call"]
    result = select_optimal_action(state, allowed, 0.01)  # very low prob
    assert result["selected_action"] == "stop"

def test_generate_decision_explanation_contains_why():
    state = {"amount_paise": 50000, "do_not_contact": False, "attempts_contact": 0}
    allowed = ["text_nudge", "voice_call"]
    decision = select_optimal_action(state, allowed, 0.5)
    explanation = generate_decision_explanation(decision, state, allowed)
    assert "why" in explanation
    assert len(explanation["why"]) > 0