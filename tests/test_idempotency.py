from utils.idempotency import generate_idempotency_key

def test_idempotency_key_unique_per_attempt():
    key1 = generate_idempotency_key("E1", "silent_retry", 0)
    key2 = generate_idempotency_key("E1", "silent_retry", 1)
    assert key1 != key2

def test_idempotency_key_includes_mandate():
    key = generate_idempotency_key("E1", "silent_retry", 0, mandate_id="M1")
    assert "M1" in key