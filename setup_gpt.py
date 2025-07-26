#!/usr/bin/env python3
"""
Setup script for GPT-powered ECLA WhatsApp Bot
"""

import os
import sys
from dotenv import load_dotenv

def setup_gpt_bot():
    """Setup GPT bot with OpenAI API key"""
    print("🤖 Setting up GPT-powered ECLA WhatsApp Bot")
    print("=" * 50)
    
    # Check if .env exists
    if not os.path.exists('.env'):
        print("📝 Creating .env file...")
        api_key = input("🔑 Enter your OpenAI API key (get from https://platform.openai.com/api-keys): ").strip()
        
        if not api_key:
            print("❌ No API key provided. Please get one from OpenAI platform.")
            return False
        
        # Create .env file
        with open('.env', 'w') as f:
            f.write(f"OPENAI_API_KEY={api_key}\n")
            f.write("DATABASE_URL=sqlite:///ecla_bot.db\n")
            f.write("WHATSAPP_API_KEY=your_whatsapp_api_key_here\n")
        
        print("✅ .env file created successfully!")
    else:
        print("✅ .env file already exists")
    
    # Test OpenAI connection
    print("\n🧪 Testing OpenAI connection...")
    try:
        load_dotenv()
        import openai
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
        # Test with a simple request
        client = openai.OpenAI(api_key=openai.api_key)
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=10
        )
        
        print("✅ OpenAI connection successful!")
        print("🚀 Your GPT-powered bot is ready!")
        
    except Exception as e:
        print(f"❌ OpenAI connection failed: {e}")
        print("Please check your API key and try again.")
        return False
    
    print("\n📋 Next steps:")
    print("1. Run: python main.py")
    print("2. Test with: python test_gpt_bot.py")
    print("3. Deploy to your hosting platform")
    
    return True

if __name__ == "__main__":
    setup_gpt_bot() 