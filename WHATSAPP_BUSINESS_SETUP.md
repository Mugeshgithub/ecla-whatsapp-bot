# WhatsApp Business API Setup Guide

## 🚀 **Option 1: WhatsApp Business API (Production Ready)**

### **Step 1: Get WhatsApp Business API Access**

#### **A. Through Meta Business**
1. **Create Meta Business Account**
   - Go to [business.facebook.com](https://business.facebook.com)
   - Create a business account
   - Verify your business

2. **Apply for WhatsApp Business API**
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Create a new app
   - Add WhatsApp Business API product
   - Submit for review

3. **Business Verification**
   - Provide business documentation
   - Wait for Meta approval (1-2 weeks)
   - Get production access

#### **B. Through WhatsApp Business Solution Providers**
- **Twilio** (what you're currently using)
- **MessageBird**
- **Infobip**
- **360dialog**

### **Step 2: Configure Your Bot**

#### **Update Environment Variables**
```bash
# Add to your .env file
WHATSAPP_BUSINESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
```

#### **Update main.py for WhatsApp Business API**
```python
# Add WhatsApp Business API endpoints
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        # Handle WhatsApp Business API webhook
        body = await request.json()
        
        # Extract message data
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("value", {}).get("messages"):
                        for message in change["value"]["messages"]:
                            # Process message
                            user_phone = message.get("from")
                            message_text = message.get("text", {}).get("body", "")
                            
                            if message_text and user_phone:
                                response = bot.process_message(user_phone, message_text)
                                
                                # Send response via WhatsApp Business API
                                await send_whatsapp_message(user_phone, response)
        
        return {"status": "ok"}
    
    except Exception as e:
        print(f"Webhook error: {e}")
        return {"status": "error", "detail": str(e)}

async def send_whatsapp_message(to_phone: str, message: str):
    """Send message via WhatsApp Business API"""
    import httpx
    
    url = f"https://graph.facebook.com/v17.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_BUSINESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": message}
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=data)
        return response.json()
```

## 📱 **Option 2: Enhanced Twilio WhatsApp (Current Setup)**

### **Your Current Setup is Already Good!**

You're already using Twilio WhatsApp, which is perfect for:
- ✅ **Quick setup** - no business verification needed
- ✅ **Testing** - great for development
- ✅ **Small scale** - up to 1000 messages/month free
- ✅ **Easy deployment** - works with your current code

### **Upgrade to Twilio WhatsApp Business**

#### **Step 1: Upgrade Twilio Account**
1. **Verify your Twilio account**
   - Add payment method
   - Complete business verification
   - Request WhatsApp Business access

2. **Get WhatsApp Business Phone Number**
   - Request dedicated WhatsApp number
   - Higher message limits
   - Better delivery rates

#### **Step 2: Update Your Code**
```python
# Your current code already works!
# Just update the webhook URL in Twilio console
# No code changes needed
```

## 🔧 **Option 3: Hybrid Approach (Recommended)**

### **Development: Twilio WhatsApp**
- ✅ **Fast setup** - immediate testing
- ✅ **No verification** - perfect for development
- ✅ **Free tier** - 1000 messages/month

### **Production: WhatsApp Business API**
- ✅ **Higher limits** - unlimited messages
- ✅ **Better features** - templates, media, etc.
- ✅ **Professional** - business verification

## 📋 **Implementation Steps**

### **Step 1: Choose Your Path**

#### **For Quick Launch (Recommended)**
```bash
# Stick with Twilio WhatsApp (what you have)
# Upgrade to Twilio WhatsApp Business
# No code changes needed
```

#### **For Production Scale**
```bash
# Apply for WhatsApp Business API
# Update code for Meta's API
# Handle business verification
```

### **Step 2: Update Your Deployment**

#### **Current Setup (Twilio)**
```yaml
# render.yaml (your current setup)
services:
  - type: web
    name: ecla-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: OPENAI_API_KEY
        value: your_openai_key
      - key: WHATSAPP_API_KEY
        value: your_twilio_key
```

#### **WhatsApp Business API Setup**
```yaml
# render.yaml (for WhatsApp Business API)
services:
  - type: web
    name: ecla-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py
    envVars:
      - key: OPENAI_API_KEY
        value: your_openai_key
      - key: WHATSAPP_BUSINESS_TOKEN
        value: your_whatsapp_token
      - key: WHATSAPP_PHONE_NUMBER_ID
        value: your_phone_number_id
```

### **Step 3: Test Your Integration**

#### **Test with Twilio (Current)**
```bash
# Your current setup works!
curl -X POST "https://your-app.onrender.com/webhook" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "Body=hi&From=+33123456789"
```

#### **Test with WhatsApp Business API**
```bash
# Test webhook verification
curl -X GET "https://your-app.onrender.com/webhook?hub.mode=subscribe&hub.challenge=test&hub.verify_token=your_token"
```

## 💰 **Cost Comparison**

### **Twilio WhatsApp (Current)**
- ✅ **Free tier**: 1000 messages/month
- ✅ **Paid tier**: $0.0075 per message
- ✅ **Setup**: $0
- ✅ **Time**: 5 minutes

### **WhatsApp Business API**
- ✅ **Free tier**: 1000 messages/month
- ✅ **Paid tier**: $0.005 per message
- ✅ **Setup**: $0 (but requires business verification)
- ✅ **Time**: 1-2 weeks for approval

## 🎯 **Recommendation for ECLA Bot**

### **Phase 1: Launch with Twilio (Now)**
```bash
# Your current setup is perfect for launch
# Deploy to production
# Start with ECLA students
# Test the market
```

### **Phase 2: Scale with WhatsApp Business API**
```bash
# After 6 months of success
# Apply for WhatsApp Business API
# Migrate to Meta's API
# Scale to other universities
```

## 🚀 **Quick Start (Your Current Setup)**

### **Deploy to Production**
```bash
# Your current code is ready!
# Just deploy to Railway/Render/Vercel
# Update Twilio webhook URL
# Start marketing to ECLA students
```

### **Update Twilio Webhook**
1. **Go to Twilio Console**
2. **WhatsApp > Sandbox**
3. **Update webhook URL**: `https://your-app.onrender.com/webhook`
4. **Save changes**

### **Test Production**
```bash
# Send "hi" to your Twilio WhatsApp number
# Should get the enhanced bot response
# Ready for ECLA students!
```

## 📊 **Your Bot is Production Ready!**

### **Current Features Working:**
- ✅ **Smart 3-option matching**
- ✅ **Two-way acceptance flow**
- ✅ **Rating system**
- ✅ **Privacy protection**
- ✅ **Business model integration**

### **Ready to Launch:**
- ✅ **Deploy to production**
- ✅ **Connect to Twilio WhatsApp**
- ✅ **Market to ECLA students**
- ✅ **Start generating revenue**

**Your enhanced ECLA bot is ready to revolutionize how students help each other! 🚀✨** 