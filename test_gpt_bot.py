#!/usr/bin/env python3
"""
Test script for GPT-powered ECLA WhatsApp Bot
"""

from gpt_bot_logic import GPTECLABot
import os
from dotenv import load_dotenv

def test_gpt_bot():
    """Test the GPT bot with various scenarios"""
    print("🧪 Testing GPT-powered ECLA WhatsApp Bot")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Check API key
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ OpenAI API key not found. Run: python setup_gpt.py")
        return
    
    # Initialize bot
    bot = GPTECLABot()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Food Delivery Request",
            "message": "I want someone to pick up my food at near KFC",
            "phone": "+1234567890"
        },
        {
            "name": "Laundry Help Request", 
            "message": "Need help with laundry, I'm in room 305",
            "phone": "+1234567891"
        },
        {
            "name": "IT Help Offer",
            "message": "I can help with IT support and computer problems",
            "phone": "+1234567892"
        },
        {
            "name": "General Greeting",
            "message": "Hi there! How does this work?",
            "phone": "+1234567893"
        },
        {
            "name": "Complex Request",
            "message": "I'm stuck studying and really hungry, can someone grab me lunch from the cafeteria?",
            "phone": "+1234567894"
        }
    ]
    
    print("\n🚀 Testing GPT Bot Responses:")
    print("-" * 40)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{i}. {test['name']}")
        print(f"📱 User: {test['message']}")
        
        try:
            response = bot.process_message(test['phone'], test['message'])
            print(f"🤖 Bot: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("-" * 40)
    
    print("\n✅ GPT Bot testing completed!")
    print("\n💡 The bot now understands natural language and provides intelligent responses!")

if __name__ == "__main__":
    test_gpt_bot() 