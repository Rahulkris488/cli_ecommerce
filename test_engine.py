
import pytest
from engine import IntentEngine

@pytest.fixture
def engine():
    return IntentEngine(data_file="data.json")

def test_levenshtein(engine):
    assert engine.levenshtein_distance("kitten", "sitting") == 3
    assert engine.levenshtein_distance("iphone", "iphone") == 0
    assert engine.levenshtein_distance("", "abc") == 3

def test_fuzzy_match(engine):
    candidates = ["track", "order", "return"]
    assert engine.fuzzy_match("trac", candidates) == "track"
    assert engine.fuzzy_match("retun", candidates) == "return"
    assert engine.fuzzy_match("xyz", candidates) is None

def test_extract_order_id(engine):
    assert engine.extract_order_id("Track order 1234") == "1234"
    assert engine.extract_order_id("Order #567890") == "567890"
    assert engine.extract_order_id("No id here") is None

def test_detect_intent_track(engine):
    ctx = {}
    intent, score, _ = engine.detect_intent("Where is my order?", ctx)
    assert intent == "track_order"
    
def test_detect_intent_cancel_weighted(engine):
    ctx = {}
    # 'cancel' has weight 90, 'order' 10. Should pick cancel.
    intent, score, _ = engine.detect_intent("Cancel my order", ctx)
    assert intent == "cancel_order"

def test_context_awareness(engine):
    ctx = {"last_intent": "track_order", "last_order_id": "1001"}
    # User just says "status"
    intent, score, _ = engine.detect_intent("status", ctx)
    assert intent == "track_order"
