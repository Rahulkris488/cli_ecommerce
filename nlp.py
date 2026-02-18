"""
nlp.py — Natural Language Processing utilities for ShopEase Chatbot
Provides fuzzy matching, text normalization, synonym expansion, and
smart product matching — all in pure Python (no external NLP libraries).
"""

import re
import string


# ──────────────────────────────────────────────
# Stop words — filtered out when extracting keywords
# ──────────────────────────────────────────────

STOP_WORDS = {
    "i", "me", "my", "the", "a", "an", "is", "are", "was", "were",
    "do", "does", "did", "can", "could", "will", "would", "should",
    "it", "its", "this", "that", "to", "of", "in", "for", "on",
    "with", "at", "from", "by", "about", "and", "or", "but", "not",
    "you", "your", "we", "our", "they", "them", "please", "just",
    "want", "need", "like", "tell", "show", "give", "get", "know",
    "some", "any", "what", "which", "how", "so", "very", "really",
    "right", "now", "also", "too", "still", "has", "have", "had",
    "been", "be", "am",
}


# ──────────────────────────────────────────────
# Synonym / alias map → canonical intent keywords
# Each key is a phrase/word a user might type;
# each value is a canonical action the bot understands.
# ──────────────────────────────────────────────

SYNONYMS = {
    # Product / price queries
    "cost": "price",
    "pricing": "price",
    "how much": "price",
    "rate": "price",
    "charges": "price",

    # Cart actions
    "add to cart": "cart_add",
    "add it": "cart_add",
    "add this": "cart_add",
    "buy it": "cart_add",
    "buy this": "cart_add",
    "purchase": "cart_add",
    "order it": "cart_add",
    "i want it": "cart_add",
    "i'll take it": "cart_add",
    "add": "cart_add",
    "buy": "cart_add",

    # Cart view
    "show cart": "cart_view",
    "my cart": "cart_view",
    "view cart": "cart_view",
    "cart": "cart_view",
    "checkout": "cart_view",
    "what's in my cart": "cart_view",
    "show my cart": "cart_view",

    # Cart remove
    "remove from cart": "cart_remove",
    "remove": "cart_remove",
    "delete from cart": "cart_remove",
    "clear cart": "cart_clear",
    "empty cart": "cart_clear",

    # Availability synonyms
    "do you have": "available",
    "got any": "available",
    "in stock": "available",
    "do you sell": "available",
    "is there": "available",

    # Delivery synonyms
    "when will it come": "delivery",
    "delivery time": "delivery",
    "shipping time": "delivery",
    "how long to ship": "delivery",
}

# Intent keywords that fuzzy-match should try to recover
INTENT_KEYWORDS = {
    "track": "track_order",
    "tracking": "track_order",
    "order": "track_order",
    "available": "product_availability",
    "availability": "product_availability",
    "stock": "product_availability",
    "price": "product_availability",
    "delivery": "delivery_estimate",
    "shipping": "delivery_estimate",
    "return": "return_policy",
    "exchange": "return_policy",
    "refund": "refund_process",
    "payment": "payment_methods",
    "pay": "payment_methods",
    "help": "help",
    "hello": "greeting",
    "hi": "greeting",
    "hey": "greeting",
    "bye": "farewell",
    "goodbye": "farewell",
    "exit": "farewell",
    "quit": "farewell",
    "thanks": "farewell",
}


# ──────────────────────────────────────────────
# Core NLP Functions
# ──────────────────────────────────────────────

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute the Levenshtein (edit) distance between two strings.
    Uses a full dynamic-programming matrix.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    prev_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Insertion, deletion, substitution
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row

    return prev_row[-1]


def fuzzy_match(word: str, candidates: list, threshold: int = 2) -> str | None:
    """
    Find the best-matching candidate for `word` within edit-distance `threshold`.
    Returns the best match or None if nothing is close enough.
    """
    word = word.lower()
    best_match = None
    best_distance = threshold + 1

    for candidate in candidates:
        dist = levenshtein_distance(word, candidate.lower())
        if dist < best_distance:
            best_distance = dist
            best_match = candidate

    if best_distance <= threshold:
        return best_match
    return None


def normalize(text: str) -> str:
    """Lowercase, strip extra whitespace, collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def extract_keywords(text: str) -> list:
    """
    Split text into meaningful tokens after removing stop words and punctuation.
    """
    text = normalize(text)
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    tokens = text.split()
    return [t for t in tokens if t not in STOP_WORDS]


def check_synonym(text: str) -> str | None:
    """
    Check if the user's text matches any synonym phrase.
    Tries longest phrases first so 'add to cart' beats 'add'.
    Returns the canonical action or None.
    """
    text_lower = normalize(text)
    # Sort by descending length so multi-word phrases match first
    for phrase in sorted(SYNONYMS.keys(), key=len, reverse=True):
        if phrase in text_lower:
            return SYNONYMS[phrase]
    return None


def fuzzy_intent_from_keywords(text: str, threshold: int = 2) -> str | None:
    """
    When regex-based detection fails, try fuzzy-matching individual words
    in the user's input against known intent keywords.
    Returns the intent string or None.
    """
    keywords = extract_keywords(text)
    for word in keywords:
        match = fuzzy_match(word, list(INTENT_KEYWORDS.keys()), threshold)
        if match:
            return INTENT_KEYWORDS[match]
    return None


def find_best_product_match(text: str, products: dict, threshold: int = 2) -> str | None:
    """
    Try to match user text to a product key in the database.
    Strategy (in order):
      1. Exact substring match on product keys (e.g. 'mouse' in text)
      2. Exact substring match on product names (e.g. 'wireless headphones')
      3. Keyword-level fuzzy match against product keys and name words

    Returns the product key (e.g. 'headphones') or None.
    """
    text_lower = normalize(text)

    # Strategy 1: exact key substring
    for key in products:
        if key in text_lower:
            return key

    # Strategy 2: exact product name substring
    for key, product in products.items():
        if product["name"].lower() in text_lower:
            return key

    # Strategy 3: fuzzy match user keywords against product keys + name words
    user_keywords = extract_keywords(text)
    all_product_tokens = {}  # token → product key

    for key, product in products.items():
        # Add the key itself (e.g. "headphones", "laptop stand")
        for part in key.split():
            all_product_tokens[part] = key
        # Add words from the product name
        for part in product["name"].lower().split():
            if part not in STOP_WORDS:
                all_product_tokens[part] = key

    token_list = list(all_product_tokens.keys())

    for word in user_keywords:
        match = fuzzy_match(word, token_list, threshold)
        if match:
            return all_product_tokens[match]

    return None


def suggest_did_you_mean(text: str, products: dict) -> str | None:
    """
    When everything fails, generate a 'Did you mean...?' suggestion
    by fuzzy-matching against product names and common actions.
    Returns a suggestion string or None.
    """
    product_match = find_best_product_match(text, products, threshold=3)
    if product_match:
        return f"'{products[product_match]['name']}'"

    # Try matching against common action phrases
    actions = [
        "track my order", "product availability", "delivery estimate",
        "return policy", "refund process", "payment methods",
        "view cart", "add to cart", "help",
    ]
    text_lower = normalize(text)
    match = fuzzy_match(text_lower, actions, threshold=3)
    if match:
        return f"'{match}'"

    return None
