"""
test_app.py — Pytest test suite for ShopEase Chatbot
Tests: regex extraction, intent detection, response handlers,
       fuzzy matching, context awareness, and cart operations.

Run with:
    pytest test_app.py -v
"""

import pytest
from services import (
    extract_order_id,
    detect_intent,
    handle_track_order,
    handle_product_availability,
    handle_payment_methods,
    handle_return_policy,
    handle_refund_process,
    handle_delivery_estimate,
    handle_cart_add,
    handle_cart_view,
    handle_cart_remove,
    handle_cart_clear,
    handle_unknown,
    get_response,
)
from nlp import (
    levenshtein_distance,
    fuzzy_match,
    normalize,
    extract_keywords,
    find_best_product_match,
    suggest_did_you_mean,
)


# ──────────────────────────────────────────────
# Test 1: Regex — Order ID Extraction
# ──────────────────────────────────────────────

class TestOrderIdExtraction:
    """Test the regex-based order ID extractor."""

    def test_extract_id_from_natural_sentence(self):
        """Should extract 4-digit ID embedded in a sentence."""
        result = extract_order_id("Track my order 1001 please")
        assert result == "1001"

    def test_extract_id_standalone(self):
        """Should extract when user just types the number."""
        result = extract_order_id("1002")
        assert result == "1002"

    def test_extract_id_with_hash(self):
        """Should extract ID when written as #1003."""
        result = extract_order_id("My order is #1003")
        assert result == "1003"

    def test_no_id_returns_none(self):
        """Should return None when no 4-digit ID is present."""
        result = extract_order_id("Where is my package?")
        assert result is None

    def test_short_number_not_matched(self):
        """3-digit numbers should NOT be matched as order IDs."""
        result = extract_order_id("I ordered 3 items")
        assert result is None


# ──────────────────────────────────────────────
# Test 2: Intent Detection (Exact Keywords)
# ──────────────────────────────────────────────

class TestIntentDetection:
    """Test keyword-based intent classification."""

    def test_greeting_intent(self):
        assert detect_intent("Hello there") == "greeting"

    def test_farewell_intent(self):
        assert detect_intent("Bye, thanks!") == "farewell"

    def test_track_order_intent(self):
        assert detect_intent("I want to track my order") == "track_order"

    def test_product_availability_intent(self):
        assert detect_intent("Is the webcam available?") == "product_availability"

    def test_delivery_intent(self):
        assert detect_intent("How long does delivery take?") == "delivery_estimate"

    def test_return_intent(self):
        assert detect_intent("What is your return policy?") == "return_policy"

    def test_refund_intent(self):
        assert detect_intent("How do I get a refund?") == "refund_process"

    def test_payment_intent(self):
        assert detect_intent("Do you accept UPI payments?") == "payment_methods"

    def test_help_intent(self):
        assert detect_intent("help me") == "help"

    def test_unknown_intent(self):
        assert detect_intent("asdfghjklqwerty") == "unknown"


# ──────────────────────────────────────────────
# Test 3: Fuzzy Intent Detection (Typo Tolerance)
# ──────────────────────────────────────────────

class TestFuzzyIntentDetection:
    """Test that typos and misspellings still match correct intents."""

    def test_availability_typo(self):
        """'availibility' should still detect product_availability."""
        assert detect_intent("product availibility") == "product_availability"

    def test_delivery_typo(self):
        """'delievry' should still detect delivery_estimate."""
        assert detect_intent("delievry estimate") == "delivery_estimate"

    def test_refund_typo(self):
        """'refnd' should still map to refund_process."""
        assert detect_intent("how to get a refnd") == "refund_process"

    def test_tracking_typo(self):
        """'trak' should still map to track_order."""
        assert detect_intent("trak my order") == "track_order"


# ──────────────────────────────────────────────
# Test 4: Product Name → Implicit Intent
# ──────────────────────────────────────────────

class TestProductNameDetection:
    """Test that typing a product name alone triggers product_availability."""

    def test_product_name_alone(self):
        """'wireless headphones' should infer product_availability."""
        assert detect_intent("wireless headphones") == "product_availability"

    def test_product_name_partial(self):
        """'headphones' alone should match via product key."""
        assert detect_intent("headphones") == "product_availability"

    def test_product_name_mouse(self):
        """'mouse' should match."""
        assert detect_intent("mouse") == "product_availability"

    def test_product_name_laptop_stand(self):
        """'laptop stand' should match."""
        assert detect_intent("laptop stand") == "product_availability"

    def test_product_name_fuzzy(self):
        """'wirless mouse' (typo) should still match via fuzzy."""
        assert detect_intent("wirless mouse") == "product_availability"


# ──────────────────────────────────────────────
# Test 5: NLP Utilities
# ──────────────────────────────────────────────

class TestNLPUtilities:
    """Test core NLP functions."""

    def test_levenshtein_identical(self):
        assert levenshtein_distance("hello", "hello") == 0

    def test_levenshtein_one_edit(self):
        assert levenshtein_distance("hello", "helo") == 1

    def test_levenshtein_different(self):
        assert levenshtein_distance("cat", "dog") == 3

    def test_fuzzy_match_exact(self):
        assert fuzzy_match("mouse", ["mouse", "keyboard", "webcam"]) == "mouse"

    def test_fuzzy_match_typo(self):
        assert fuzzy_match("mous", ["mouse", "keyboard", "webcam"]) == "mouse"

    def test_fuzzy_match_no_match(self):
        assert fuzzy_match("xyz", ["mouse", "keyboard", "webcam"]) is None

    def test_normalize(self):
        assert normalize("  HELLO   World  ") == "hello world"

    def test_extract_keywords(self):
        words = extract_keywords("Is the wireless mouse available?")
        assert "wireless" in words
        assert "mouse" in words
        assert "is" not in words
        assert "the" not in words

    def test_find_product_exact(self):
        from services import DB
        products = DB.get("products", {})
        assert find_best_product_match("mouse", products) == "mouse"

    def test_find_product_fuzzy(self):
        from services import DB
        products = DB.get("products", {})
        result = find_best_product_match("headphone", products)
        assert result == "headphones"

    def test_find_product_full_name(self):
        from services import DB
        products = DB.get("products", {})
        result = find_best_product_match("wireless headphones", products)
        assert result == "headphones"


# ──────────────────────────────────────────────
# Test 6: Order Tracking Handler
# ──────────────────────────────────────────────

class TestOrderTracking:
    """Test order tracking responses."""

    def test_valid_shipped_order(self):
        response, ctx = handle_track_order("track order 1001", {})
        assert "1001" in response
        assert "Shipped" in response or "shipped" in response.lower()

    def test_valid_delivered_order(self):
        response, ctx = handle_track_order("Where is 1003?", {})
        assert "1003" in response
        assert "Delivered" in response or "delivered" in response.lower()

    def test_cancelled_order(self):
        response, ctx = handle_track_order("status of order 1004", {})
        assert "1004" in response
        assert "Cancelled" in response or "cancelled" in response.lower()

    def test_invalid_order_id(self):
        response, ctx = handle_track_order("track order 9999", {})
        assert "9999" in response
        assert "couldn't find" in response.lower() or "not found" in response.lower()

    def test_missing_id_asks_for_it(self):
        response, ctx = handle_track_order("track my order", {})
        assert ctx.get("awaiting_order_id") is True
        assert "order ID" in response or "order id" in response.lower()

    def test_follow_up_with_id(self):
        """After bot asks for ID, user replies with just the number."""
        context = {"awaiting_order_id": True}
        response, ctx = handle_track_order("1002", context)
        assert "1002" in response
        assert ctx.get("awaiting_order_id") is False


# ──────────────────────────────────────────────
# Test 7: Product Availability (Smart Matching)
# ──────────────────────────────────────────────

class TestProductAvailability:
    """Test product stock lookups with smart matching."""

    def test_in_stock_product(self):
        response, ctx = handle_product_availability("Is the webcam available?", {})
        assert "IN STOCK" in response or "in stock" in response.lower()

    def test_out_of_stock_product(self):
        response, ctx = handle_product_availability("Do you have a keyboard?", {})
        assert "OUT OF STOCK" in response or "out of stock" in response.lower()

    def test_unknown_product_lists_options(self):
        response, ctx = handle_product_availability("Do you have a drone?", {})
        assert "couldn't identify" in response.lower() or "in stock" in response.lower()

    def test_product_name_alone(self):
        """Just typing 'wireless headphones' should show stock info."""
        response, ctx = handle_product_availability("wireless headphones", {})
        assert "Wireless Headphones" in response
        assert "IN STOCK" in response

    def test_remembers_last_product(self):
        """Should store last_product in context."""
        _, ctx = handle_product_availability("webcam", {})
        assert ctx.get("last_product") == "webcam"

    def test_fuzzy_product_match(self):
        """'headphone' (singular) should match 'headphones'."""
        response, ctx = handle_product_availability("headphone", {})
        assert "Wireless Headphones" in response


# ──────────────────────────────────────────────
# Test 8: Cart Operations
# ──────────────────────────────────────────────

class TestCart:
    """Test shopping cart functionality."""

    def test_add_with_product_name(self):
        """Adding a product by name."""
        response, ctx = handle_cart_add("add headphones", {"cart": {}})
        assert "Added" in response
        assert "Wireless Headphones" in response
        assert "headphones" in ctx["cart"]

    def test_add_with_context(self):
        """Adding using last_product context (user says just 'add')."""
        context = {"cart": {}, "last_product": "mouse"}
        response, ctx = handle_cart_add("add", context)
        assert "Added" in response
        assert "Wireless Mouse" in response

    def test_add_increments_quantity(self):
        """Adding same product twice increases quantity."""
        ctx = {"cart": {}}
        _, ctx = handle_cart_add("add mouse", ctx)
        _, ctx = handle_cart_add("add mouse", ctx)
        assert ctx["cart"]["mouse"]["qty"] == 2

    def test_view_empty_cart(self):
        response, _ = handle_cart_view({"cart": {}})
        assert "empty" in response.lower()

    def test_view_with_items(self):
        context = {"cart": {"mouse": {"name": "Wireless Mouse", "price": 799, "qty": 2}}}
        response, _ = handle_cart_view(context)
        assert "Wireless Mouse" in response
        assert "1598" in response  # 799 * 2

    def test_remove_item(self):
        context = {"cart": {"mouse": {"name": "Wireless Mouse", "price": 799, "qty": 1}}}
        response, ctx = handle_cart_remove("remove mouse", context)
        assert "Removed" in response
        assert "mouse" not in ctx["cart"]

    def test_clear_cart(self):
        context = {"cart": {"mouse": {"name": "Wireless Mouse", "price": 799, "qty": 1}}}
        response, ctx = handle_cart_clear(context)
        assert "cleared" in response.lower() or "empty" in response.lower()
        assert len(ctx["cart"]) == 0

    def test_add_out_of_stock(self):
        """Can't add out-of-stock product."""
        response, ctx = handle_cart_add("add keyboard", {"cart": {}})
        assert "out of stock" in response.lower()


# ──────────────────────────────────────────────
# Test 9: Policy Responses
# ──────────────────────────────────────────────

class TestPolicyResponses:
    """Test that policy handlers return relevant content."""

    def test_return_policy_contains_days(self):
        response = handle_return_policy()
        assert "30" in response  # 30-day window

    def test_refund_mentions_timeline(self):
        response = handle_refund_process()
        assert "5-7" in response or "business days" in response.lower()

    def test_delivery_mentions_standard(self):
        response = handle_delivery_estimate()
        assert "Standard" in response or "standard" in response.lower()

    def test_payment_mentions_upi(self):
        response = handle_payment_methods()
        assert "UPI" in response


# ──────────────────────────────────────────────
# Test 10: Full Conversation via get_response
# ──────────────────────────────────────────────

class TestGetResponse:
    """Integration tests through the main dispatcher."""

    def test_hello_triggers_greeting(self):
        response, ctx = get_response("hi", {})
        assert "Welcome" in response or "Hello" in response

    def test_bye_sets_exit_flag(self):
        response, ctx = get_response("bye", {})
        assert ctx.get("should_exit") is True

    def test_track_without_id_sets_context(self):
        response, ctx = get_response("track my order", {})
        assert ctx.get("awaiting_order_id") is True

    def test_track_with_id_inline(self):
        response, ctx = get_response("track my order 1005", {})
        assert "1005" in response

    def test_unknown_input_graceful(self):
        response, ctx = get_response("xyzabcdef123", {})
        assert "didn't" in response.lower() or "help" in response.lower()

    def test_product_name_alone_works(self):
        """'wireless headphones' should show product info via get_response."""
        response, ctx = get_response("wireless headphones", {"cart": {}})
        assert "Wireless Headphones" in response
        assert "IN STOCK" in response

    def test_add_after_product_query(self):
        """After asking about a product, 'add' should add it to cart."""
        ctx = {"cart": {}, "last_product": None, "last_intent": None}
        # First, ask about headphones
        _, ctx = get_response("wireless headphones", ctx)
        assert ctx.get("last_product") == "headphones"
        # Now say 'add'
        response, ctx = get_response("add", ctx)
        assert "Added" in response
        assert "headphones" in ctx.get("cart", {})

    def test_typo_recovery(self):
        """'product availibility' should not return unknown."""
        response, ctx = get_response("product availibility", {})
        assert "didn't" not in response.lower()

    def test_view_cart_integration(self):
        """'view cart' should work through get_response."""
        ctx = {"cart": {"mouse": {"name": "Wireless Mouse", "price": 799, "qty": 1}}}
        response, _ = get_response("view cart", ctx)
        assert "Wireless Mouse" in response


# ──────────────────────────────────────────────
# Test 11: Did You Mean? Suggestions
# ──────────────────────────────────────────────

class TestDidYouMean:
    """Test the 'Did you mean?' fallback for near-miss inputs."""

    def test_near_miss_product(self):
        from services import DB
        products = DB.get("products", {})
        suggestion = suggest_did_you_mean("webcm", products)
        assert suggestion is not None
        assert "Webcam" in suggestion

    def test_total_nonsense_no_suggestion(self):
        from services import DB
        products = DB.get("products", {})
        suggestion = suggest_did_you_mean("zzzzzzzzzzz", products)
        assert suggestion is None
