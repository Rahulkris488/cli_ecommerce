"""
services.py — Business logic for ShopEase E-commerce Chatbot
Handles intent detection, order lookup, product search, cart management,
and policy queries.

Intelligence features:
  • Fuzzy intent detection (typo-tolerant via Levenshtein distance)
  • Smart product matching (partial names, fuzzy keywords)
  • Conversational context (remembers last product, last intent)
  • Shopping cart with add / view / remove / clear
  • "Did you mean?" suggestions as fallback
"""

import re
import json
import os
from nlp import (
    normalize,
    extract_keywords,
    check_synonym,
    fuzzy_intent_from_keywords,
    find_best_product_match,
    suggest_did_you_mean,
    SYNONYMS,
)


# ──────────────────────────────────────────────
# Load database
# ──────────────────────────────────────────────

def load_database():
    """Load data from database.json relative to this file."""
    db_path = os.path.join(os.path.dirname(__file__), "database.json")
    with open(db_path, "r") as f:
        return json.load(f)


DB = load_database()


# ──────────────────────────────────────────────
# Regex: Extract Order ID
# ──────────────────────────────────────────────

def extract_order_id(text: str):
    """
    Extract a 4-digit order ID from user input using regex.
    Pattern: one or more digits (captures IDs like 1001, 1002, etc.)
    Returns the matched ID string or None.
    """
    match = re.search(r'\b(\d{4})\b', text)
    if match:
        return match.group(1)
    return None


# ──────────────────────────────────────────────
# Intent Detection (keyword + fuzzy + synonym)
# ──────────────────────────────────────────────

def detect_intent(text: str, context: dict = None) -> str:
    """
    Detect user intent using a multi-layered approach:
      1. Regex keyword matching (fast, exact)
      2. Synonym / phrase matching
      3. Product-name detection (infer product_availability)
      4. Fuzzy keyword matching (typo tolerance)
      5. Context-based inference (last product → implicit actions)
    Returns one of the recognized intent strings.
    """
    if context is None:
        context = {}

    text_lower = text.lower().strip()

    # ── Layer 1: Exact regex keyword matching ──────────────

    # Greeting intent
    if re.search(r'\b(hello|hi|hey|good morning|good evening|howdy)\b', text_lower):
        return "greeting"

    # Farewell intent
    if re.search(r'\b(bye|goodbye|exit|quit|see you)\b', text_lower):
        return "farewell"

    # Thanks (can be farewell or standalone)
    if re.search(r'\b(thanks|thank you)\b', text_lower):
        return "farewell"

    # Help/menu intent
    if re.search(r'\b(help|assist|support|what can you do|options|menu)\b', text_lower):
        return "help"

    # Order tracking intent
    if re.search(r'\b(track|tracking|where is|order status|my order|check order)\b', text_lower):
        return "track_order"

    # Product availability intent
    if re.search(r'\b(available|availability|in stock|stock|do you sell|price|cost)\b', text_lower):
        return "product_availability"

    # Delivery estimate intent
    if re.search(r'\b(delivery|deliver|shipping|ship|how long|when will|arrive|arrival|dispatch)\b', text_lower):
        return "delivery_estimate"

    # Return policy intent
    if re.search(r'\b(return|returning|send back|exchange|replace|replacement)\b', text_lower):
        return "return_policy"

    # Refund process intent
    if re.search(r'\b(refund|money back|reimbursement|credit back|cashback)\b', text_lower):
        return "refund_process"

    # Payment methods intent
    if re.search(r'\b(payment|pay|upi|card|emi|cash on delivery|cod|net banking|wallet)\b', text_lower):
        return "payment_methods"

    # ── Layer 2: Synonym / phrase matching ──────────────

    synonym_action = check_synonym(text)
    if synonym_action:
        if synonym_action == "cart_add":
            return "cart_add"
        elif synonym_action == "cart_view":
            return "cart_view"
        elif synonym_action == "cart_remove":
            return "cart_remove"
        elif synonym_action == "cart_clear":
            return "cart_clear"
        elif synonym_action == "price":
            return "product_availability"
        elif synonym_action == "available":
            return "product_availability"
        elif synonym_action == "delivery":
            return "delivery_estimate"

    # ── Layer 3: Check if it's a product name ──────────────
    # If user just types a product name, infer product_availability.

    products = DB.get("products", {})
    product_match = find_best_product_match(text, products)
    if product_match:
        return "product_availability"

    # ── Layer 4: Fuzzy keyword matching (typo recovery) ────
    fuzzy_intent = fuzzy_intent_from_keywords(text)
    if fuzzy_intent:
        return fuzzy_intent

    return "unknown"


# ──────────────────────────────────────────────
# Response Handlers
# ──────────────────────────────────────────────

def handle_greeting() -> str:
    return (
        "Hello! Welcome to ShopEase Support! 🛍️\n"
        "I can help you with:\n"
        "  • Order tracking\n"
        "  • Product availability\n"
        "  • Delivery estimates\n"
        "  • Return & refund policy\n"
        "  • Payment methods\n"
        "  • Shopping cart\n\n"
        "How can I assist you today?"
    )


def handle_farewell() -> str:
    return "Thank you for contacting ShopEase! Have a great day! 😊 Goodbye!"


def handle_help() -> str:
    return (
        "Here's what I can help you with:\n"
        "  1. Track your order       → 'track my order' or 'where is my order'\n"
        "  2. Product availability   → 'is [product] available?' or just type the product name\n"
        "  3. Delivery estimates     → 'how long does delivery take?'\n"
        "  4. Return policy          → 'what is your return policy?'\n"
        "  5. Refund process         → 'how do I get a refund?'\n"
        "  6. Payment methods        → 'what payment methods do you accept?'\n"
        "  7. Cart                   → 'add to cart', 'view cart', 'remove', 'clear cart'\n"
        "  8. Greeting / Farewell    → say hi or bye anytime\n\n"
        "💡 Tips: I understand typos and partial names!\n"
        "   Try: 'headphones', 'wirless mouse', 'how much is the webcam?'\n\n"
        "Just type your question naturally!"
    )


def handle_track_order(text: str, context: dict) -> tuple:
    """
    Tracks an order. If no order ID in current message, checks context.
    Returns (response_string, updated_context_dict).
    """
    order_id = extract_order_id(text)

    # If no ID found, check if we already asked and user just replied with a number
    if not order_id and context.get("awaiting_order_id"):
        # Try extracting any number from a short reply
        match = re.search(r'\b(\d+)\b', text)
        if match:
            order_id = match.group(1)

    if not order_id:
        context["awaiting_order_id"] = True
        return "Please provide your 4-digit order ID so I can track it for you.", context

    # Clear the awaiting flag
    context["awaiting_order_id"] = False

    orders = DB.get("orders", {})

    if order_id in orders:
        order = orders[order_id]
        status = order["status"].title()
        item = order["item"]
        eta = order["estimated_delivery"]
        courier = order["courier"]
        tracking_num = order["tracking_number"]

        if order["status"] == "delivered":
            response = (
                f"Order #{order_id} ({item}): ✅ Already Delivered.\n"
                f"  Courier: {courier} | Tracking#: {tracking_num}"
            )
        elif order["status"] == "cancelled":
            response = (
                f"Order #{order_id} ({item}): ❌ Cancelled.\n"
                "  If this was unexpected, please contact our support team."
            )
        else:
            response = (
                f"Order #{order_id} ({item}): 📦 {status}\n"
                f"  Estimated delivery: {eta}\n"
                f"  Courier: {courier} | Tracking#: {tracking_num}"
            )
    else:
        response = (
            f"Sorry, I couldn't find order #{order_id}. "
            "Please double-check your order ID or contact support at support@shopease.com."
        )

    return response, context


def handle_product_availability(text: str, context: dict) -> tuple:
    """
    Check product availability using smart matching.
    Stores the matched product in context for follow-up queries.
    Returns (response_string, updated_context).
    """
    products = DB.get("products", {})
    matched_key = find_best_product_match(text, products)

    if matched_key:
        product = products[matched_key]
        name = product["name"]
        price = product["price"]

        # Remember the product for follow-up
        context["last_product"] = matched_key

        if product["available"]:
            stock = product["stock"]
            return (
                f"✅ {name} is currently IN STOCK!\n"
                f"  Price: ₹{price} | Units available: {stock}\n"
                "  You can add it to your cart — just say 'add to cart'."
            ), context
        else:
            return (
                f"❌ Sorry, {name} is currently OUT OF STOCK.\n"
                f"  Price: ₹{price} (when available)\n"
                "  You can click 'Notify Me' on the product page to get an alert."
            ), context
    else:
        # List available products
        available = [p["name"] for p in products.values() if p["available"]]
        return (
            "I couldn't identify a specific product from your message.\n"
            "Here are some products we currently have in stock:\n  " +
            "\n  ".join(f"• {p}" for p in available) +
            "\n\nTry asking: 'Is the webcam available?' or just type 'headphones'"
        ), context


def handle_delivery_estimate() -> str:
    delivery = DB["policies"]["delivery"]
    return (
        "📦 ShopEase Delivery Estimates:\n"
        f"  • Standard Shipping  : {delivery['standard']}\n"
        f"  • Express Shipping   : {delivery['express']}\n"
        f"  • Same-Day Delivery  : {delivery['same_day']}\n"
        f"  • Free Shipping      : {delivery['free_shipping']}\n\n"
        "Delivery times may vary based on your location and product availability."
    )


def handle_return_policy() -> str:
    policy = DB["policies"]["return"]
    return (
        "🔄 ShopEase Return Policy:\n"
        f"  • Return Window  : {policy['window_days']} days from delivery\n"
        f"  • Condition      : {policy['condition']}\n"
        f"  • Process        : {policy['process']}\n"
        f"  • Non-Returnable : {policy['non_returnable']}"
    )


def handle_refund_process() -> str:
    refund = DB["policies"]["refund"]
    return (
        "💰 ShopEase Refund Process:\n"
        f"  • Timeline  : {refund['timeline']}\n"
        f"  • Mode      : {refund['modes']}\n"
        f"  • Partial   : {refund['partial']}\n"
        f"  • Escalate  : {refund['contact']}"
    )


def handle_payment_methods() -> str:
    payment = DB["policies"]["payment"]
    methods = ", ".join(payment["methods"])
    return (
        "💳 ShopEase Payment Options:\n"
        f"  • Accepted Methods : {methods}\n"
        f"  • EMI              : {payment['emi']}\n"
        f"  • Cash on Delivery : {payment['cod']}\n"
        f"  • Security         : {payment['security']}"
    )


# ──────────────────────────────────────────────
# Cart Handlers
# ──────────────────────────────────────────────

def handle_cart_add(text: str, context: dict) -> tuple:
    """
    Add a product to the cart. Tries to identify the product from text;
    falls back to context['last_product'] if no product found in text.
    """
    products = DB.get("products", {})
    cart = context.get("cart", {})

    # Strip action verbs to get just the product part of the text
    action_words = {"add", "buy", "purchase", "order", "get", "cart", "to", "it", "this", "the", "a", "an", "my", "please", "i", "want"}
    cleaned_words = [w for w in normalize(text).split() if w not in action_words]
    cleaned_text = " ".join(cleaned_words)

    # Try to find product in the cleaned text (only if there are meaningful words left)
    product_key = None
    if cleaned_text.strip():
        product_key = find_best_product_match(cleaned_text, products)

    # Fall back to last discussed product
    if not product_key:
        product_key = context.get("last_product")

    if not product_key:
        return (
            "🛒 Which product would you like to add to your cart?\n"
            "Try: 'add headphones' or ask about a product first, then say 'add'."
        ), context

    product = products.get(product_key)
    if not product:
        return "Sorry, I couldn't find that product.", context

    if not product["available"]:
        return f"❌ Sorry, {product['name']} is currently out of stock and can't be added to cart.", context

    # Add to cart (increment quantity)
    if product_key in cart:
        cart[product_key]["qty"] += 1
    else:
        cart[product_key] = {"name": product["name"], "price": product["price"], "qty": 1}

    context["cart"] = cart
    context["last_product"] = product_key

    total = sum(item["price"] * item["qty"] for item in cart.values())
    qty = cart[product_key]["qty"]

    return (
        f"🛒 Added {product['name']} to your cart! (Qty: {qty})\n"
        f"  Cart total: ₹{total}\n"
        "  Say 'view cart' to see all items or keep shopping!"
    ), context


def handle_cart_view(context: dict) -> tuple:
    """Show the current cart contents."""
    cart = context.get("cart", {})

    if not cart:
        return "🛒 Your cart is empty! Browse our products and say 'add to cart'.", context

    lines = ["🛒 Your Cart:\n  ───────────────────────────"]
    total = 0
    for i, (key, item) in enumerate(cart.items(), 1):
        subtotal = item["price"] * item["qty"]
        total += subtotal
        lines.append(f"  {i}. {item['name']} × {item['qty']}  →  ₹{subtotal}")

    lines.append(f"  ───────────────────────────\n  💰 Total: ₹{total}")
    lines.append("\n  Say 'remove [product]' to remove, or 'clear cart' to empty it.")

    return "\n".join(lines), context


def handle_cart_remove(text: str, context: dict) -> tuple:
    """Remove a product from the cart."""
    cart = context.get("cart", {})

    if not cart:
        return "🛒 Your cart is already empty!", context

    products = DB.get("products", {})
    product_key = find_best_product_match(text, products)

    # Fall back to last product if user just says "remove"
    if not product_key:
        product_key = context.get("last_product")

    if product_key and product_key in cart:
        removed = cart.pop(product_key)
        context["cart"] = cart
        total = sum(item["price"] * item["qty"] for item in cart.values())
        return (
            f"🗑️ Removed {removed['name']} from your cart.\n"
            f"  Cart total: ₹{total}"
        ), context
    else:
        items = ", ".join(item["name"] for item in cart.values())
        return f"That item isn't in your cart. Your cart has: {items}", context


def handle_cart_clear(context: dict) -> tuple:
    """Clear the entire cart."""
    context["cart"] = {}
    return "🗑️ Cart cleared! Your cart is now empty.", context


def handle_unknown(text: str) -> str:
    """
    Enhanced unknown handler with 'Did you mean?' suggestions.
    """
    products = DB.get("products", {})
    suggestion = suggest_did_you_mean(text, products)

    if suggestion:
        return (
            f"🤔 I'm not sure what you mean, but did you mean {suggestion}?\n"
            "Type 'help' to see what I can assist you with."
        )
    else:
        return (
            "🤔 Sorry, I didn't quite understand that.\n"
            "Type 'help' to see what I can assist you with, "
            "or try rephrasing your question."
        )


# ──────────────────────────────────────────────
# Main Response Dispatcher
# ──────────────────────────────────────────────

def get_response(user_input: str, context: dict) -> tuple:
    """
    Main dispatcher. Detects intent and routes to appropriate handler.
    Uses context for conversational memory and implicit intent resolution.
    Returns (bot_response, updated_context).
    """
    # If we're waiting for an order ID, treat any input as part of order tracking
    if context.get("awaiting_order_id"):
        response, context = handle_track_order(user_input, context)
        return response, context

    intent = detect_intent(user_input, context)

    # Store last intent for context
    if intent != "unknown":
        context["last_intent"] = intent

    if intent == "greeting":
        return handle_greeting(), context

    elif intent == "farewell":
        context["should_exit"] = True
        return handle_farewell(), context

    elif intent == "help":
        return handle_help(), context

    elif intent == "track_order":
        response, context = handle_track_order(user_input, context)
        return response, context

    elif intent == "product_availability":
        response, context = handle_product_availability(user_input, context)
        return response, context

    elif intent == "delivery_estimate":
        return handle_delivery_estimate(), context

    elif intent == "return_policy":
        return handle_return_policy(), context

    elif intent == "refund_process":
        return handle_refund_process(), context

    elif intent == "payment_methods":
        return handle_payment_methods(), context

    elif intent == "cart_add":
        return handle_cart_add(user_input, context)

    elif intent == "cart_view":
        return handle_cart_view(context)

    elif intent == "cart_remove":
        return handle_cart_remove(user_input, context)

    elif intent == "cart_clear":
        return handle_cart_clear(context)

    else:
        return handle_unknown(user_input), context
