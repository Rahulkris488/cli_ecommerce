import pytest
from services import extract_order_id, get_response

def test_extract_order_id_valid():
    """Test regex extraction for a valid ID"""
    assert extract_order_id("Track order 1234") == "1234"

def test_extract_order_id_none():
    """Test regex extraction when no ID is present"""
    assert extract_order_id("Track my order") is None

def test_track_order_response():
    """Test response logic for tracking an existing order"""
    response = get_response("Track 1001")
    assert "Shipped" in response
    assert "1001" in response

def test_product_inquiry():
    """Test keyword matching for product price"""
    response = get_response("Price of iPhone")
    assert "iPhone" in response
    assert "79999" in response

def test_policy_query():
    """Test return policy query"""
    response = get_response("What is return policy?")
    assert "return products within 7 days" in response

def test_unknown_command():
    """Test fallback response"""
    response = get_response("blabla random text")
    assert "I didn't understand" in response
