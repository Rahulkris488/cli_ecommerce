import json
import re
import os

DB_FILE = os.path.join(os.path.dirname(__file__), 'database.json')

def load_data():
    """Load data from JSON file."""
    if not os.path.exists(DB_FILE):
        return {}
    with open(DB_FILE, 'r') as f:
        return json.load(f)

def extract_order_id(text):
    """
    Extracts a 4-digit order ID using Regex.
    Pattern: \b\d{4}\b -> matches distinct 4-digit numbers.
    """
    match = re.search(r'\b\d{4}\b', text)
    if match:
        return match.group(0)
    return None

def get_response(user_input):
    """
    Main logic function.
    Determines intent based on keywords and regex.
    Returns a string response.
    """
    user_input = user_input.lower()
    data = load_data()

    # 1. Check for Order ID presence -> Direct Tracking
    order_id = extract_order_id(user_input)
    if order_id:
        orders = data.get("orders", {})
        if order_id in orders:
            order = orders[order_id]
            return f"Order {order_id}: {order['status']}. Estimated Delivery: {order['delivery_date']}"
        else:
            return f"Order {order_id} not found. Please check the ID."

    # 2. Check for Tracking Intent (without ID)
    if "track" in user_input or "where" in user_input or "status" in user_input:
        return "Please provide your 4-digit Order ID (e.g., 'Track 1001')."

    # 3. Check for Product Availability/Price
    # Simple keyword search against product keys
    products = data.get("products", {})
    for product_name in products:
        if product_name in user_input:
            info = products[product_name]
            price = info['price']
            status = "Available" if info['available'] else "Out of Stock"
            return f"{product_name.title()}: ₹{price} ({status})"

    if "price" in user_input or "cost" in user_input or "available" in user_input:
        return "Which product? We have: iPhone, MacBook, Headphones, Shoes."

    # 4. Check for Policies
    policies = data.get("policies", {})
    if "return" in user_input:
        return f"Return Policy: {policies['return']}"
    if "refund" in user_input:
        return f"Refund Process: {policies['refund']}"
    if "pay" in user_input or "card" in user_input: # covers payment, pay, card
        return f"Payment Methods: {policies['payment']}"
    
    # 5. Greetings / Help / Exit
    if "hi" in user_input or "hello" in user_input:
        return "Hello! I am your E-commerce Assistant. Ask me about orders, products, or policies."
    
    if "help" in user_input:
        return "Try asking: 'Track 1001', 'Price of iPhone', 'Return policy', or 'Payment options'."

    if "bye" in user_input or "exit" in user_input:
        return "Goodbye! Thanks for shopping."

    # 6. Fallback
    return "I didn't understand that. Please try asking for 'Help'."
