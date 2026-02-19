
"""
simulate_final_polish.py
Verifies the 'Real Chatbot' feel:
1. Multi-turn Context (Track -> 1001)
2. Single-word Commands (Cart, Help)
3. Smart Cart (Add -> Adds last item)
"""

import time
from engine import IntentEngine

def run_simulation():
    engine = IntentEngine()
    
    scenarios = [
        {
            "name": "🔄 Multi-turn Tracking",
            "inputs": [
                "track",        # Should ask for ID
                "1001"          # Should track 1001
            ]
        },
        {
            "name": "🛒 Smart Cart Flow",
            "inputs": [
                "iphone",       # Search
                "add",          # Should add iPhone implicitly
                "cart",         # Should show cart
                "checkout"      # Should place order
            ]
        },
        {
            "name": "⚡ Single Word Speed",
            "inputs": [
                "help",
                "status",       # Synonym for track
                "bye"
            ]
        }
    ]

    print("🚀 Starting Final Polish Verification...\n")
    
    for scenario in scenarios:
        print(f"--- {scenario['name']} ---")
        context = {} # Reset context per scenario
        
        for user_input in scenario['inputs']:
            print(f"You: {user_input}")
            response, context, debug = engine.get_response(user_input, context)
            print(f"Bot: {response.replace(chr(10), chr(10) + '     ')}")
            # print(f"     [Debug state: {context.get('state')}]")
            print("")
        print("--------------------------------------------------\n")

    print("✅ Simulation Complete.")

if __name__ == "__main__":
    run_simulation()
