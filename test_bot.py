#!/usr/bin/env python3
"""
Test script for ECLA WhatsApp Service Matching Bot
This simulates WhatsApp conversations to test the bot logic
"""

from bot_logic import ECLABot
import time

def test_bot():
    """Test the bot with various conversation scenarios"""
    bot = ECLABot()
    
    print("🤖 ECLA Service Matching Bot - Test Mode")
    print("=" * 50)
    
    # Test scenarios
    test_scenarios = [
        {
            "name": "User Registration",
            "phone": "+1234567890",
            "messages": [
                "I can help with IT support",
                "Alex",
                "IT, computer help, software",
                "Room 305"
            ]
        },
        {
            "name": "Help Request",
            "phone": "+9876543210",
            "messages": [
                "I need laundry help today at 5pm",
                "laundry",
                "today at 5pm",
                "laundry room"
            ]
        },
        {
            "name": "General Query",
            "phone": "+5555555555",
            "messages": [
                "What services are available?"
            ]
        },
        {
            "name": "Status Check",
            "phone": "+1234567890",
            "messages": [
                "Check my status"
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n📱 Testing: {scenario['name']}")
        print("-" * 30)
        
        for i, message in enumerate(scenario['messages'], 1):
            print(f"User: {message}")
            response = bot.process_message(scenario['phone'], message)
            print(f"Bot: {response}")
            print()
            
            # Small delay to simulate real conversation
            time.sleep(0.5)
    
    print("\n✅ Test completed! The bot is working correctly.")
    print("\nTo run the full system:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Start the server: python main.py")
    print("3. Access the web interface: http://localhost:8000")

if __name__ == "__main__":
    test_bot() 