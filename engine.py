"""
engine.py — Core Logic & NLP Engine for ShopEase CLI v2.1
Handles intent detection, fuzzy matching, weighted scoring, and state management.
"""

import re
import json
import os
import random

class IntentEngine:
    def __init__(self, data_file="data.json"):
        self.data_file = data_file
        self.db = self.load_data()
        self.stop_words = {
            "i", "me", "my", "the", "a", "an", "is", "are", "to", "for", "in", "on", 
            "with", "and", "or", "but", "so", "be", "have", "do", "will", "can", "please"
        }
        
    def load_data(self):
        """Loads the JSON database."""
        if not os.path.exists(self.data_file):
            return {}
        with open(self.data_file, "r") as f:
            return json.load(f)

    def levenshtein_distance(self, s1, s2):
        """Calculates Levenshtein distance between two strings."""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]

    def fuzzy_match(self, word, candidates, threshold=80):
        """
        Fuzzy matches a word against a list of candidates.
        Returns the best match if score > threshold (0-100 scale).
        """
        best_match = None
        highest_score = 0
        
        word = word.lower()
        
        for candidate in candidates:
            dist = self.levenshtein_distance(word, candidate.lower())
            max_len = max(len(word), len(candidate))
            if max_len == 0:
                score = 100
            else:
                score = (1 - dist / max_len) * 100
            
            if score > highest_score:
                highest_score = score
                best_match = candidate
                
        if highest_score >= threshold:
            return best_match
        return None

    def extract_order_id(self, text):
        """Extracts 4-6 digit order ID from text using Regex."""
        match = re.search(r'\b\d{4,6}\b', text)
        if match:
            return match.group(0)
        return None

    def detect_intent(self, user_input, context):
        """
        Determines the user's intent using Weighted Scoring and Context State.
        Returns (intent, score, entities).
        """
        user_input_lower = user_input.lower().strip()
        
        # ──────────────────────────────────────────────
        # 1. State Machine Checks (Priority #1)
        # ──────────────────────────────────────────────
        current_state = context.get("state")
        
        if current_state == "AWAITING_ORDER_ID":
            # Check if user wants to abort
            if user_input_lower in ["cancel", "abort", "stop", "no"]:
                context["state"] = None
                return "greeting", 100, {} # Reset to neutral
            
            # Treat ANY input as potential Order ID if it contains digits
            # or if it's a short string (assuming user typed ID)
            if re.search(r'\d+', user_input) or len(user_input_lower) < 10:
                return "track_order_provided", 100, {}
        
        # ──────────────────────────────────────────────
        # 2. Single-Word / Short Phrase Optimizations (Priority #2)
        # ──────────────────────────────────────────────
        # Instant mapping for common short commands
        direct_maps = {
            "track": "track_order",
            "status": "track_order",
            "help": "help",
            "menu": "help",
            "hi": "greeting",
            "hello": "greeting",
            "cart": "cart_view",
            "bag": "cart_view",
            "exit": "exit",
            "quit": "exit",
            "bye": "exit",
            "checkout": "checkout",
            "pay": "checkout"
        }
        if user_input_lower in direct_maps:
            return direct_maps[user_input_lower], 100, {}

        # ──────────────────────────────────────────────
        # 3. Keyword & Fuzzy Logic (Standard)
        # ──────────────────────────────────────────────
        words = [w for w in re.split(r'\W+', user_input_lower) if w and w not in self.stop_words]
        
        # Define Intents and Keywords with Weights
        intents = {
            "track_order": {"keywords": ["track", "order", "status", "where", "shipment", "package", "arriving"], "weight": 10},
            "cancel_order": {"keywords": ["cancel", "stop", "drop"], "weight": 90}, 
            "refund_order": {"keywords": ["refund", "money", "back", "return"], "weight": 30}, # Lower weight to avoid conflict with 'return policy'
            "return_policy": {"keywords": ["policy", "return", "exchange", "warranty"], "weight": 30},
            "product_search": {"keywords": ["buy", "price", "cost", "search", "looking", "available", "stock", "show", "find", 
                                            "phone", "laptop", "watch", "shoe", "fridge", "tv", "ac", "tshirt", "shirt", "jeans", "macbook", "iphone"], "weight": 10},
            "cart_add": {"keywords": ["add", "cart", "bag", "basket", "buy", "take"], "weight": 15},
            "cart_view": {"keywords": ["view", "show", "check", "my"], "weight": 10},
            "cart_remove": {"keywords": ["remove", "delete", "clear"], "weight": 20},
            "checkout": {"keywords": ["checkout", "pay", "payment", "placing", "order"], "weight": 30},
            "product_info": {"keywords": ["details", "specs", "features", "about"], "weight": 10},
            "help": {"keywords": ["help", "support", "menu", "options", "assist"], "weight": 20},
            "greeting": {"keywords": ["hi", "hello", "hey", "start", "greetings"], "weight": 5},
            "exit": {"keywords": ["bye", "exit", "quit", "close", "goodbye"], "weight": 100}
        }
        
        scores = {intent: 0 for intent in intents}
        
        # Scoring Logic
        for word in words:
            for intent, data in intents.items():
                match = self.fuzzy_match(word, data["keywords"])
                if match:
                    scores[intent] += data["weight"]

        # Composite phrase boosting
        if "add" in user_input_lower and ("cart" in user_input_lower or "bag" in user_input_lower):
            scores["cart_add"] += 50
        if "view" in user_input_lower and "cart" in user_input_lower:
            scores["cart_view"] += 50
        if "my cart" in user_input_lower:
            scores["cart_view"] += 40
        if "checkout" in user_input_lower or "place order" in user_input_lower:
            scores["checkout"] += 50
        if "return" in user_input_lower and "policy" in user_input_lower:
            scores["return_policy"] += 50

        # Context Boost
        if context.get("last_intent") == "product_search" and "add" in user_input_lower:
            scores["cart_add"] += 30 
        
        if context.get("last_intent") == "track_order" and self.extract_order_id(user_input):
             scores["track_order"] += 50

        # Select Best Intent
        best_intent = max(scores, key=scores.get)
        
        # If score is 0, default to 'product_search' if it looks like a query, else 'unknown'
        if scores[best_intent] == 0:
            # Heuristic: If it has words and isn't gibberish, treat as search
            if len(words) > 0 and len(user_input_lower) > 2:
                return "product_search", 10, {}
            return "unknown", 0, {}
            
        return best_intent, scores[best_intent], {}

    def filter_products(self, query):
        """Advanced product filtering based on query string."""
        products = self.db.get("products", {}).values()
        filtered = []
        
        query = query.lower()
        
        # Check specific category filters
        # Check specific category filters
        category_map = {
            "electronics": "Electronics", "gadget": "Electronics", "phone": "Electronics", "mobile": "Electronics", "laptop": "Electronics", "watch": "Electronics", "earphone": "Electronics", "headphone": "Electronics",
            "fashion": "Fashion", "cloth": "Fashion", "wear": "Fashion", "shoe": "Fashion", "sneaker": "Fashion", "shirt": "Fashion", "pant": "Fashion", "jeans": "Fashion",
            "home": "Home", "kitchen": "Home", "furniture": "Home", "decor": "Home", "fridge": "Home", "vacuum": "Home",
            "sports": "Sports", "gym": "Sports", "fitness": "Sports", "cycle": "Sports", "cricket": "Sports",
            "books": "Books", "read": "Books", "novel": "Books",
            "gaming": "Gaming", "ps5": "Gaming", "xbox": "Gaming", "console": "Gaming"
        }
        target_category = None
        for k, v in category_map.items():
            if k in query:
                target_category = v
                break
        
        # Check price filters
        max_price = 9999999
        if "under" in query:
            match = re.search(r'under\s?(\d+)', query)
            if match:
                max_price = int(match.group(1))

        # Extract potential keywords to filter by (ignoring stopwords)
        ignore = ["under", "in", "show", "me", "find", "buy", "price", "cost", "looking", "for", "a", "an", "the"]
        keywords = [w for w in query.split() if w not in ignore and not w.isdigit()]

        for p in products:
            # 1. Category Filter
            if target_category and p["category"] != target_category:
                continue
            
            # 2. Price Filter
            if p["price"] > max_price:
                continue
                
            # 3. Fuzzy Keyword Match
            if keywords:
                 # Check if any keyword fuzzy matches name or category
                 match_found = False
                 for k in keywords:
                     # Check exact match first
                     if k in p["name"].lower() or k in p["category"].lower():
                         match_found = True
                         break
                     
                     # Check fuzzy match against name parts
                     name_parts = p["name"].lower().split()
                     if self.fuzzy_match(k, name_parts, threshold=75): # Lower threshold for search
                         match_found = True
                         break
                         
                     # Check fuzzy match against plural/singular (simple heuristic)
                     if k.endswith('s') and k[:-1] in p["name"].lower():
                         match_found = True
                         break
                         
                 if not match_found:
                     continue

            filtered.append(p)
            
        return filtered

    def get_response(self, user_input, context):
        """
        Main method to get bot response.
        Updates context and returns (response_markdown, updated_context).
        """
        intent, score, entities = self.detect_intent(user_input, context)
        
        # Helper to get/init cart
        if "cart" not in context: context["cart"] = []

        # Extract Order ID
        order_id = self.extract_order_id(user_input)
        if order_id:
            context["last_order_id"] = order_id
            # If we were awaiting an ID, clear that state
            if context.get("state") == "AWAITING_ORDER_ID":
                context["state"] = None
                intent = "track_order" # Force intent

        # Debug Info
        debug_info = f"[DEBUG] Intent: {intent} (Score: {score}) | State: {context.get('state')}"
        
        response = ""
        
        # ──────────────────────────────────────────────
        # Intent Handlers
        # ──────────────────────────────────────────────
        
        if intent == "track_order_provided":
             # User provided input while we were awaiting ID. Treat input as ID.
             # The regex extraction above might have already caught 4-6 digits.
             # If not, try to use the raw input as ID if it's numeric
             if not order_id and user_input.isdigit():
                 order_id = user_input
             
             context["state"] = None # Reset state
             intent = "track_order" # Force tracking logic below via recursion or fallthrough
             # fallthrough to track_order logic...

        if intent == "track_order":
            oid = order_id or context.get("last_order_id")
            
            # If we don't have an ID, ask for it and set State
            if not oid:
                context["state"] = "AWAITING_ORDER_ID"
                response = "Please provide your **Order ID** (e.g., 1001)."
            else:
                order = self.db.get("orders", {}).get(oid)
                if order:
                    status = order["status"]
                    response = f"📦 **Order #{oid}** - {order.get('product')}\n"
                    response += f"**Status:** {status}\n"
                    if status == "Delivered":
                        response += f"✅ Delivered on {order.get('delivery_date')}.\n"
                    elif status == "Out for Delivery":
                        response += f"🚚 Out for Delivery! Arriving today.\n"
                    else:
                         response += f"Current Status: {status}\nTracking: {order.get('tracking_location')}"
                else:
                    response = f"⚠️ Order #{oid} not found."
                    context["state"] = "AWAITING_ORDER_ID" # Ask again just in case it was a typo

        elif intent == "product_search":
            found = self.filter_products(user_input)
            
            if found:
                response = f"Found {len(found)} product(s):\n"
                # Limit to 5 for brevity
                for p in found[:5]:
                    stock_msg = f"{p['stock']} left" if p['available'] else "Out of Stock"
                    price = f"₹{p['price']:,}"
                    rating = "⭐" * int(p['rating'])
                    # Store ID for context (naive lookup by name for now)
                    context["last_viewed_product"] = p
                    response += f"- **{p['name']}** \n  Price: {price} | {rating} | {stock_msg}\n"
                
                if len(found) > 5:
                    response += f"\n*...and {len(found)-5} more. Try filtering by price or category.*"
            else:
                response = "No products found. Try 'Electronics', 'Shoes', or 'Budget laptop'."

        elif intent == "cart_add":
            # Smart Logic: Use last viewed product if user didn't specify
            product_to_add = None
            found = self.filter_products(user_input)
            
            # If input has specific product (e.g., "add iphone"), use that
            # Logic: If filter found 1 specific item (or very few), assume user meant those. 
            # If filter found generic (like "search iphone" -> 2 items), pick first.
            if found and (len(found) < 3 or "add" not in user_input.lower()): 
                 product_to_add = found[0]
            
            # Fallback to context
            if not product_to_add:
                product_to_add = context.get("last_viewed_product")

            if product_to_add:
                context["cart"].append(product_to_add)
                response = f"🛒 Added **{product_to_add['name']}** to your cart!\n"
                response += f"Cart: {len(context['cart'])} item(s) | Total: ₹{sum(x['price'] for x in context['cart']):,}."
            else:
                response = "Which product? Search for one first (e.g. 'Show iPhones') then say 'Add'."

        elif intent == "cart_view":
            if context["cart"]:
                total = sum(x['price'] for x in context["cart"])
                response = "🛒 **Your Cart**\n\n"
                for i, item in enumerate(context["cart"], 1):
                    response += f"{i}. {item['name']} - ₹{item['price']:,}\n"
                response += f"\n**Total: ₹{total:,}**\nType 'checkout' to proceed."
            else:
                response = "Your cart is empty. Go shopping!"

        elif intent == "cart_remove":
             context["cart"] = [] # Simple clear for now
             response = "🗑️ Cart cleared."

        elif intent == "checkout":
            if context["cart"]:
                total = sum(x['price'] for x in context["cart"])
                response = f"🎉 Order Placed!\nTotal: ₹{total:,}\nMode: COD\nOrder ID: #{random.randint(1000,9999)}"
                context["cart"] = []
            else:
                 response = "Cart is empty. Add items first!"
        
        elif intent == "cancel_order":
             response = "To cancel, provide Order ID. (e.g., 'Cancel 1001')"
        
        elif intent == "help":
            # Interactive Help Menu
            response = "🤖 **Command Menu**\nType a topic to see commands:\n\n"
            response += "🛒 **Shopping**\n   _Search, Cart, Checkout_\n\n"
            response += "📦 **Tracking**\n   _Track Order, Status_\n\n"
            response += "💳 **Support**\n   _Returns, Refunds, Policy_"
            context["state"] = "AWAITING_HELP_SELECTION"

        # ──────────────────────────────────────────────
        # Help Sub-menus (Handled via state or keywords)
        # ──────────────────────────────────────────────
        elif context.get("state") == "AWAITING_HELP_SELECTION" or "menu" in user_input.lower():
            if any(k in user_input_lower for k in ["shop", "buy", "store"]):
                response = "🛒 **Shopping Commands**\n"
                response += "• `Show iPhones` (Search products)\n"
                response += "• `Mobile under 15000` (Filter by price)\n"
                response += "• `Add to cart` (Add item)\n"
                response += "• `View cart` / `Checkout`"
                context["state"] = None
            elif any(k in user_input_lower for k in ["track", "order", "status"]):
                response = "📦 **Tracking Commands**\n"
                response += "• `Track 1001` (Track specific order)\n"
                response += "• `Where is my order?` (Ask for status)\n"
                response += "• `My orders` (List recent)"
                context["state"] = None
            elif any(k in user_input_lower for k in ["support", "help", "return", "policy"]):
                response = "💳 **Support Commands**\n"
                response += "• `Return policy` (View rules)\n"
                response += "• `Refund status` (Check refund)\n"
                response += "• `Customer care` (Contact info)"
                context["state"] = None
            elif intent == "help": # Re-trigger main help if they type help again
                 context["state"] = "AWAITING_HELP_SELECTION" # Keep state
            else:
                 # If user types something else, maybe they want to execute a command directly
                 # logic already handled by intent detection, just clear state if it's a valid command
                 if intent != "unknown":
                     context["state"] = None
                     # Let the next loop or fallthrough handle it? 
                     # Actually get_response is one-pass. We need to recursively call or return.
                     # For now, just return the standard unknown message BUT with a hint.
                     response = "Please type **Shopping**, **Tracking**, or **Support** to see commands."

        elif intent == "greeting":
            response = "Hello! 👋 Welcome to ShopEase v3. Type **Help** to see what I can do."

        elif intent == "return_policy":
            response = "🔄 **Return Policy**:\nReturn within 7 days of delivery for a full refund. Items must be unused."

        elif intent == "exit":
            response = "See you soon! Happy Shopping! 🛍️"
            context["should_exit"] = True
            
        else:
            response = "I didn't quite get that. Type **Help** for the command menu."

        context["last_intent"] = intent
        return response, context, debug_info

    def get_suggestions(self, intent, context):
        """Returns predictive suggestions based on the current intent and context."""
        suggestions = []
        if intent == "track_order":
            status = context.get("last_order_status") # This would need to be set in get_response
            if status == "Delivered":
                suggestions = ["Return this order", "Rate product", "Shop more"]
            else:
                suggestions = ["Check delivery date", "Contact support"]
        elif intent == "product_search":
            suggestions = ["Add to cart", "Check reviews", "Compare prices"]
        elif intent == "greeting":
            suggestions = ["Track order", "Best sellers", "New arrivals"]
            
        return suggestions

if __name__ == "__main__":
    # Simple CLI Test for Engine
    engine = IntentEngine()
    ctx = {}
    print("Engine Loaded. Type 'exit' to quit.")
    while True:
        txt = input("You: ")
        resp, ctx, dbg = engine.get_response(txt, ctx)
        print(f"Bot: {resp}")
        print(f"{dbg}")
        if ctx.get("should_exit"):
            break
