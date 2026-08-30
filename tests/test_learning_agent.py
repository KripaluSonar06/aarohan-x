from models.bandit_model import ContextualBandit

def test_bandit_selects_best_action():
    bandit = ContextualBandit(epsilon=0.0)  # no exploration
    context = {"diagnosed_class": "funds", "amount_paise": 100000}
    allowed = ["text_nudge", "voice_call"]
    # Initially no rewards, should pick first allowed
    action = bandit.select_action(context, allowed)
    assert action in allowed
    # Update rewards to favor voice
    bandit.update(context, "text_nudge", 0.0)
    bandit.update(context, "text_nudge", 0.0)
    bandit.update(context, "voice_call", 1.0)
    bandit.update(context, "voice_call", 1.0)
    # Now should pick voice (higher average)
    action = bandit.select_action(context, allowed)
    assert action == "voice_call"