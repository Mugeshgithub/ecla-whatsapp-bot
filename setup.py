#!/usr/bin/env python3
"""
Setup script for ECLA WhatsApp Service Matching Bot
"""

import subprocess
import sys
import os

def install_dependencies():
    """Install required dependencies"""
    print("📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Failed to install dependencies. Please run: pip install -r requirements.txt")
        return False
    return True

def test_bot():
    """Test the bot functionality"""
    print("\n🧪 Testing bot functionality...")
    try:
        subprocess.check_call([sys.executable, "test_bot.py"])
        print("✅ Bot test completed successfully!")
    except subprocess.CalledProcessError:
        print("❌ Bot test failed. Please check the error messages above.")
        return False
    return True

def create_env_file():
    """Create .env file with placeholder values"""
    if not os.path.exists('.env'):
        print("\n📝 Creating .env file...")
        with open('.env', 'w') as f:
            f.write("""# ECLA WhatsApp Bot Configuration
# Add your API keys and configuration here

# WhatsApp Business API (optional for testing)
WHATSAPP_API_KEY=your_whatsapp_api_key_here

# OpenAI API (optional for enhanced features)
OPENAI_API_KEY=your_openai_api_key_here

# Database configuration
DATABASE_URL=sqlite:///ecla_bot.db
""")
        print("✅ .env file created!")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function"""
    print("🚀 ECLA WhatsApp Service Matching Bot Setup")
    print("=" * 50)
    
    # Install dependencies
    if not install_dependencies():
        return
    
    # Create .env file
    create_env_file()
    
    # Test bot
    if not test_bot():
        return
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Configure your WhatsApp Business API (optional)")
    print("2. Run the server: python main.py")
    print("3. Access the web interface: http://localhost:8000")
    print("4. Test the bot: python test_bot.py")
    
    print("\n💡 For WhatsApp integration:")
    print("- Sign up for WhatsApp Business API")
    print("- Configure webhook URL to: http://your-domain.com/webhook")
    print("- Update .env file with your API keys")

if __name__ == "__main__":
    main() 