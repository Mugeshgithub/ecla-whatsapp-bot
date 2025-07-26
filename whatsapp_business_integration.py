"""
WhatsApp Business API Integration for ECLA Bot
This module provides integration with Meta's WhatsApp Business API
"""

import httpx
import json
import os
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class WhatsAppBusinessAPI:
    def __init__(self):
        self.access_token = os.getenv('WHATSAPP_BUSINESS_TOKEN')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN')
        self.api_version = "v17.0"
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
    async def send_text_message(self, to_phone: str, message: str) -> Dict:
        """Send text message via WhatsApp Business API"""
        if not self.access_token or not self.phone_number_id:
            raise ValueError("WhatsApp Business API credentials not configured")
        
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
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
    
    async def send_template_message(self, to_phone: str, template_name: str, language_code: str = "en_US") -> Dict:
        """Send template message via WhatsApp Business API"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            return response.json()
    
    async def send_interactive_message(self, to_phone: str, header_text: str, body_text: str, buttons: list) -> Dict:
        """Send interactive message with buttons"""
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Format buttons for WhatsApp API
        formatted_buttons = []
        for i, button in enumerate(buttons[:3]):  # WhatsApp allows max 3 buttons
            formatted_buttons.append({
                "type": "reply",
                "reply": {
                    "id": f"btn_{i}",
                    "title": button
                }
            })
        
        data = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "header": {
                    "type": "text",
                    "text": header_text
                },
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": formatted_buttons
                }
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            return response.json()
    
    def verify_webhook(self, mode: str, challenge: str, verify_token: str) -> Optional[str]:
        """Verify webhook for WhatsApp Business API"""
        if mode == "subscribe" and verify_token == self.verify_token:
            return challenge
        return None
    
    def parse_webhook(self, body: Dict) -> list:
        """Parse incoming webhook messages"""
        messages = []
        
        if body.get("object") == "whatsapp_business_account":
            for entry in body.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("value", {}).get("messages"):
                        for message in change["value"]["messages"]:
                            if message.get("type") == "text":
                                messages.append({
                                    "from": message.get("from"),
                                    "text": message.get("text", {}).get("body", ""),
                                    "timestamp": message.get("timestamp"),
                                    "message_id": message.get("id")
                                })
        
        return messages

# Enhanced main.py integration
def create_whatsapp_business_endpoints(app, bot):
    """Add WhatsApp Business API endpoints to FastAPI app"""
    
    whatsapp_api = WhatsAppBusinessAPI()
    
    @app.post("/webhook")
    async def whatsapp_webhook(request: Request):
        try:
            # Handle webhook verification
            form_data = await request.form()
            if form_data.get("hub.mode") == "subscribe":
                challenge = form_data.get("hub.challenge")
                verify_token = form_data.get("hub.verify_token")
                response = whatsapp_api.verify_webhook("subscribe", challenge, verify_token)
                if response:
                    return HTMLResponse(response)
                else:
                    return HTMLResponse("Forbidden", status_code=403)
            
            # Handle incoming messages
            body = await request.json()
            messages = whatsapp_api.parse_webhook(body)
            
            for message in messages:
                user_phone = message["from"]
                message_text = message["text"]
                
                if message_text and user_phone:
                    # Process message with bot
                    response = bot.process_message(user_phone, message_text)
                    
                    # Send response via WhatsApp Business API
                    await whatsapp_api.send_text_message(user_phone, response)
            
            return {"status": "ok"}
        
        except Exception as e:
            print(f"Webhook error: {e}")
            return {"status": "error", "detail": str(e)}
    
    @app.get("/webhook")
    async def verify_webhook(request: Request):
        """Handle webhook verification for WhatsApp Business API"""
        params = request.query_params
        
        mode = params.get("hub.mode")
        challenge = params.get("hub.challenge")
        verify_token = params.get("hub.verify_token")
        
        if mode and challenge and verify_token:
            response = whatsapp_api.verify_webhook(mode, challenge, verify_token)
            if response:
                return HTMLResponse(response)
        
        return HTMLResponse("Forbidden", status_code=403)
    
    return app

# Example usage in main.py
"""
# Add this to your main.py

from whatsapp_business_integration import create_whatsapp_business_endpoints

# After creating your FastAPI app and bot
app = create_whatsapp_business_endpoints(app, bot)
"""

# Environment variables needed:
"""
WHATSAPP_BUSINESS_TOKEN=your_access_token_from_meta
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_verify_token
""" 