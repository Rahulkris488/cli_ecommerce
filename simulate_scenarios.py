
"""
simulate_scenarios.py
Automated simulation of user interactions with ShopEase CLI v3.0.
Verifies fixes for search, cart, and tracking logic.
"""

import time
import sys
from engine import IntentEngine

def run_simulation():
    engine = IntentEngine()
    
    scenarios = [
        {
            "name": "🔍 Scenario 1: Smart Search Fixes",
            "inputs": [
                "mobile phones under 50000",
                "show gym items",
                "buy laptopss",  # typo test
                "show iphones"
            ]
        },
        {
            "name": "🛒 Scenario 2: Shopping Cart Flow",
            "inputs": [
                "show macbook",
                "add to cart",
                "view cart",
                "checkout"
            ]
        },
        {
            "name": "📦 Scenario 3: Order Tracking & Context",
            "inputs": [
                "track 1001",
                "when will it arrive"  # Context test (it -> 1001)
            ]
        }
    ]

    print("🚀 Starting ShopEase V3.0 Automated Simulation...\n")
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        context = {} # Reset context per scenario
        
        for user_input in scenario['inputs']:
            print(f"You: {user_input}")
            response, context, debug = engine.get_response(user_input, context)
            
            # Clean up response for display (remove some markdown for readability if needed, but keeping it is fine)
            # Just indenting
            print(f"Bot: {response.replace(chr(10), chr(10) + '     ')}")
            # print(f"     [Debug: {debug}]")
            print("")
            time.sleep(0.5)
        print("--------------------------------------------------\n")

    print("✅ Simulation Complete.")

if __name__ == "__main__":
    run_simulation()
