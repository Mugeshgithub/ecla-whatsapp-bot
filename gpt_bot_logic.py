import sqlite3
import re
import json
from datetime import datetime
from typing import Dict, List, Tuple
import openai
import os
from dotenv import load_dotenv

load_dotenv()

class GPTECLABot:
    def __init__(self):
        self.conversation_states = {}  # Track user conversation state
        self.db_path = 'ecla_bot.db'
        self.user_names = {}  # Store user names for personalization
        self.conversation_history = {}  # Store conversation history for context
        self.pending_matches = {}  # Track pending match confirmations
        self.active_requests = {}  # Track active service requests
        self.init_db()
        
        # Initialize OpenAI
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
    def init_db(self):
        """Initialize database tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Users table (service providers)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT UNIQUE NOT NULL,
                services TEXT NOT NULL,
                location TEXT NOT NULL,
                availability TEXT DEFAULT 'available',
                rating REAL DEFAULT 5.0,
                total_services INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Requests table (service seekers)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT NOT NULL,
                service TEXT NOT NULL,
                time TEXT NOT NULL,
                location TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                matched_helper TEXT,
                price_offered REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Matches table (for tracking successful connections)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                seeker_phone TEXT NOT NULL,
                provider_phone TEXT NOT NULL,
                service TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                rating INTEGER
            )
        ''')
        
        # Add sample service providers
        sample_providers = [
            ("Marie", "+33123456789", "French-English translation, prefecture assistance", "Main Campus", "available", 5.0, 12),
            ("Pierre", "+33987654321", "English-French translation, official documents", "Student Housing", "available", 4.8, 8),
            ("Sophie", "+33555555555", "Translation services, medical appointments", "Library", "available", 4.9, 15),
            ("Alex", "+33666666666", "IT support, web design, tech help", "Computer Lab", "available", 4.7, 6),
            ("Sarah", "+33777777777", "Food delivery, grocery shopping, KFC delivery", "Cafeteria", "available", 4.6, 10),
            ("Mike", "+33888888888", "Car lending, airport pickup, transportation", "Parking Lot", "available", 4.5, 5),
            ("Emma", "+33999999999", "Laundry help, cleaning services", "Dormitory", "available", 4.8, 7),
            ("David", "+33000000000", "Printing papers, document help", "Library", "available", 4.7, 9)
        ]
        
        for name, phone, services, location, availability, rating, total_services in sample_providers:
            cursor.execute('''
                INSERT OR IGNORE INTO users (name, phone, services, location, availability, rating, total_services)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, phone, services, location, availability, rating, total_services))
        
        conn.commit()
        conn.close()
    
    def get_conversation_history(self, phone: str) -> List[Dict]:
        """Get conversation history for context"""
        return self.conversation_history.get(phone, [])
    
    def add_to_history(self, phone: str, role: str, content: str):
        """Add message to conversation history"""
        if phone not in self.conversation_history:
            self.conversation_history[phone] = []
        
        self.conversation_history[phone].append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        
        # Keep only last 10 messages for context
        if len(self.conversation_history[phone]) > 10:
            self.conversation_history[phone] = self.conversation_history[phone][-10:]
    
    def create_system_prompt(self) -> str:
        """Create system prompt for GPT"""
        return """You are an ECLA premium community service matching bot. Your role is to connect ECLA community members through smart, conversational registration and intelligent 3-option matching. You can respond in English, French, or any language the user prefers.

FIRST GREETING RESPONSE:
When a user sends their first message (like "Hey", "Hello", etc.), respond with:
"Hey Neighbour! 👋 I'm your ECLA Community Services Assistant!

🏠 **Whether it's finding someone for IT help, laundry, moving boxes, or anything in between, we make it super easy.**

I made this very customizable using our previous requests from the ECLA group. Now you can find what you need here!

**💡 Just say things like:**
• "Hey I need someone to lend a car"
• "I want someone to pickup/drop to airport" 
• "I need food delivery to pickup"
• "I need a cig" 😄

It will redirect you to the right person who is available for this kind of service, and once people are accepted, they will be invited to the same chat and you can connect directly!

**💪 Advantages:**
• No more lost requests in the group
• Direct connection with neighbors
• Quick and easy matching
• Perfect for ECLA community needs

Just say your name and let's get started! 😊"

REGISTRATION FLOW:
1. Ask for name: "What's your name?"
2. Ask for services: "What do you usually need help with?" or "What services do you offer?"
3. Ask for location: "Where are you located?"
4. Confirm registration: "Perfect! You're all set! I'll connect you with neighbors when needed."

SERVICE REQUEST FLOW:
1. Extract service from message
2. Find 3 best matches with ratings and pricing
3. Present options: "Found 3 neighbors who can help: [options]"
4. Handle selection: "Perfect! Let me check with [name]..."
5. Two-way acceptance: Ask provider if available
6. Connect users: "Great! Connecting you both..."

Keep responses friendly, helpful, and community-focused. Use emojis and natural language."""
    
    def extract_info_with_gpt(self, message: str, phone: str) -> Dict:
        """Use GPT to extract information from message"""
        try:
            # Get conversation history for context
            history = self.get_conversation_history(phone)
            
            # Create messages for GPT
            messages = [
                {"role": "system", "content": """Extract key information from this message. Consider translation services (French-English, prefecture help) and ECLA campus locations. 

IMPORTANT INTENT CLASSIFICATION:
- If message contains 'I can help with' or 'I offer' or 'I provide' or 'I want to provide service' or 'register as provider' OR 'I can help people' OR 'I am able to help' OR 'I help people', classify as OFFER_HELP intent.

- If message contains direct service requests like 'I need food delivery', 'I want someone to lend a car', 'I need IT help', 'I need translation', 'I need laundry help', 'I need airport pickup', classify as REQUEST_HELP intent.

- If message contains 'English', 'Français', 'French', 'language', '🇫🇷', '🇬🇧', classify as LANGUAGE_SELECTION intent.

- If message contains French greetings like 'Bonjour', 'Salut', 'Bonsoir', 'Coucou', classify as FRENCH_GREETING intent.

- If message contains English greetings like 'Hi', 'Hello', 'Hey', classify as GREETING intent.

- If message contains questions about how the bot works like 'how can you help', 'how does this work', 'how do you work', 'what can you do', 'explain', 'process', classify as GENERAL_QUERY intent.

For service requests, extract the actual service mentioned:
- 'I need food delivery' = 'food delivery'
- 'I want someone to lend a car' = 'car lending'
- 'I need IT help' = 'IT support'
- 'I need translation' = 'translation'
- 'I need laundry help' = 'laundry'
- 'I need airport pickup' = 'airport pickup'
- 'I need a cig' = 'cigarettes'

Return JSON with: intent (REQUEST_HELP/OFFER_HELP/REGISTER/GREETING/THANKS/GENERAL_QUERY/LANGUAGE_SELECTION/FRENCH_GREETING), service (if mentioned), time (if mentioned), location (if mentioned), confidence (0-1). If no info, use null."""},
                {"role": "user", "content": f"Message: {message}"}
            ]
            
            # Add recent conversation context
            if history:
                context = "Recent conversation:\n" + "\n".join([f"{msg['role']}: {msg['content']}" for msg in history[-3:]])
                messages.insert(1, {"role": "user", "content": context})
            
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.1
            )
            
            # Parse JSON response
            content = response.choices[0].message.content
            try:
                return json.loads(content)
            except:
                # Fallback parsing
                return {
                    "intent": "UNKNOWN",
                    "service": None,
                    "time": None,
                    "location": None,
                    "confidence": 0.5
                }
                
        except Exception as e:
            print(f"GPT extraction error: {e}")
            return {
                "intent": "UNKNOWN",
                "service": None,
                "time": None,
                "location": None,
                "confidence": 0.5
            }
    
    def generate_response_with_gpt(self, message: str, phone: str, extracted_info: Dict, user_state: Dict) -> str:
        """Use GPT to generate natural response"""
        try:
            # Get conversation history
            history = self.get_conversation_history(phone)
            
            # Create context for GPT
            context = f"""
Current user state: {user_state.get('state', 'idle')}
Extracted info: {extracted_info}
User message: {message}
"""
            
            # Add database context
            db_context = self.get_database_context(phone)
            if db_context:
                context += f"\nDatabase context: {db_context}"
            
            messages = [
                {"role": "system", "content": self.create_system_prompt()},
                {"role": "user", "content": f"{context}\n\nGenerate a concise, helpful response focused on service matching. Be friendly but brief. Keep it under 100 words."}
            ]
            
            # Add recent conversation for context
            if history:
                recent_messages = history[-5:]  # Last 5 messages
                for msg in recent_messages:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            client = openai.OpenAI(api_key=openai.api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            print(f"GPT response error: {e}")
            return "I'm having trouble understanding right now. Could you try rephrasing that?"
    
    def get_database_context(self, phone: str) -> str:
        """Get relevant database information for context"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if user is registered
            cursor.execute("SELECT name, services, location FROM users WHERE phone = ?", (phone,))
            user = cursor.fetchone()
            
            # Check recent requests
            cursor.execute("SELECT service, time, location, status FROM requests WHERE phone = ? ORDER BY created_at DESC LIMIT 3", (phone,))
            requests = cursor.fetchall()
            
            conn.close()
            
            context = ""
            if user:
                context += f"User is registered as {user[0]} offering {user[1]} at {user[2]}. "
            
            if requests:
                context += f"Recent requests: {', '.join([f'{r[0]} at {r[2]} ({r[3]})' for r in requests])}. "
            
            return context
            
        except Exception as e:
            print(f"Database context error: {e}")
            return ""
    
    def process_message(self, phone: str, message: str) -> str:
        """Main message processing with GPT"""
        # Add user message to history
        self.add_to_history(phone, "user", message)
        
        # Get current user state
        user_state = self.get_user_state(phone)
        
        # Extract information using GPT
        extracted_info = self.extract_info_with_gpt(message, phone)
        
        # Handle based on intent and state
        response = self.handle_message_with_gpt(phone, message, extracted_info, user_state)
        
        # Add bot response to history
        self.add_to_history(phone, "assistant", response)
        
        return response
    
    def handle_message_with_gpt(self, phone: str, message: str, extracted_info: Dict, user_state: Dict) -> str:
        """Handle message based on GPT-extracted intent"""
        intent = extracted_info.get("intent", "UNKNOWN")
        
        # Check if this is a provider confirmation first
        if self.is_provider_confirmation(phone, message):
            return self.handle_provider_confirmation(phone, message)
        
        # Handle conversation states
        if user_state.get('state') != 'idle':
            return self.handle_conversation_state_with_gpt(phone, message, extracted_info, user_state)
        
        # Check if this is a first-time user (no conversation history)
        history = self.get_conversation_history(phone)
        if intent == "GREETING":
            # Set state to registering name directly
            self.set_user_state(phone, 'registering_name')
            return self.handle_first_time_greeting(phone)
        
        # Handle common "how does this work" questions directly
        message_lower = message.lower()
        if any(word in message_lower for word in ['how does this work', 'what does this bot do', 'explain', 'how can you help', 'what can you do']):
            return self.handle_how_it_works(phone, message)
        
        # Handle new intents
        if intent == "REQUEST_HELP":
            return self.handle_help_request_with_gpt(phone, message, extracted_info)
        elif intent == "OFFER_HELP" or intent == "REGISTER":
            return self.handle_registration_with_gpt(phone, message, extracted_info)
        elif intent == "LANGUAGE_SELECTION":
            return self.handle_language_selection(phone, message)
        elif intent == "FRENCH_GREETING":
            return self.handle_french_greeting(phone, message)
        elif intent == "GREETING":
            return self.generate_response_with_gpt(message, phone, extracted_info, user_state)
        elif intent == "THANKS":
            return self.generate_response_with_gpt(message, phone, extracted_info, user_state)
        elif intent == "GENERAL_QUERY":
            return self.handle_how_it_works(phone, message)
        else:
            return self.generate_response_with_gpt(message, phone, extracted_info, user_state)
    
    def is_provider_confirmation(self, phone: str, message: str) -> bool:
        """Check if this message is from a provider confirming availability"""
        # Check if this phone number has any pending matches as a provider
        for match_id, match_data in self.pending_matches.items():
            if match_data['provider_phone'] == phone:
                return True
        return False
    
    def handle_conversation_state_with_gpt(self, phone: str, message: str, extracted_info: Dict, user_state: Dict) -> str:
        """Handle ongoing conversations with GPT"""
        state = user_state.get('state', 'idle')
        
        if state == 'registering_name':
            # Check if this is the first message (greeting) or actual name
            if message and message.lower().strip() in ['hey', 'hi', 'hello', 'bonjour', 'salut']:
                return self.handle_first_time_greeting(phone)
            else:
                return self.handle_name_registration_with_gpt(phone, message, extracted_info)
        elif state == 'asking_role':
            return self.handle_role_selection(phone, message)
        elif state == 'asking_service_need':
            return self.handle_service_need(phone, message)
        elif state == 'registering_services':
            return self.handle_services_registration_with_gpt(phone, message, extracted_info)
        elif state == 'registering_location':
            return self.handle_location_registration_with_gpt(phone, message, extracted_info)
        elif state == 'registering_availability':
            return self.handle_availability_registration(phone, message)
        elif state == 'registering_time_preference':
            return self.handle_time_preference_registration(phone, message)
        elif state == 'registering_pricing':
            return self.handle_pricing_registration(phone, message)
        elif state == 'requesting_service':
            return self.handle_service_request_with_gpt(phone, message, extracted_info)
        elif state == 'requesting_time':
            return self.handle_time_request_with_gpt(phone, message, extracted_info)
        elif state == 'requesting_location':
            return self.handle_location_request_with_gpt(phone, message, extracted_info)
        elif state == 'choosing_provider':
            return self.handle_provider_choice_with_gpt(phone, message, extracted_info)
        elif state == 'selecting_language':
            return self.handle_language_selection(phone, message)
        elif state == 'welcome_english':
            return self.handle_english_welcome(phone)
        else:
            return self.generate_response_with_gpt(message, phone, extracted_info, user_state)
    
    def extract_name_from_context(self, phone: str) -> str:
        """Try to extract user name from context or return None"""
        # For now, we'll use a simple approach
        # In a real implementation, you could:
        # 1. Check if user has a saved profile
        # 2. Use WhatsApp profile name if available
        # 3. Ask user to provide their name
        return None  # We'll ask for name in the next step
    
    def handle_french_greeting(self, phone: str, message: str) -> str:
        """Handle French greetings and automatically switch to French mode"""
        # Set language preference to French
        self.set_user_state(phone, 'registering_name', {'language': 'french'})
        
        return """Bonjour! 👋 Je suis votre assistant ECLA!

🏠 **Comment ça marche:**
• Besoin d'aide? Dites-moi ce dont vous avez besoin (lessive, nourriture, traduction, etc.)
• Voulez-vous aider les autres? Dites "Je veux fournir un service" pour vous inscrire
• Je vous connecterai avec 3 voisins qui peuvent aider

💡 **Services populaires:** Lessive, livraison de nourriture, traduction, courses, aide informatique, assistance préfecture

Comment puis-je vous aider aujourd'hui?"""
    
    def handle_english_welcome(self, phone: str) -> str:
        """Handle English welcome message with clear examples"""
        return """Hey there! 👋 I'm your ECLA Services Assistant.

🏠 **How it works:**
• Need help? Tell me what you need (laundry, food, translation, etc.)
• Want to help others? Say "I want to provide service" to register
• I'll connect you with 3 neighbors who can help

💡 **Popular services:** Laundry, food delivery, translation, shopping, tech help, prefecture assistance

What can I help you with today?"""
    
    def handle_language_selection(self, phone: str, message: str) -> str:
        """Handle language preference selection"""
        message_lower = message.lower().strip()
        print(f"Language selection: '{message}' -> '{message_lower}'")
        
        if any(word in message_lower for word in ['français', 'french', 'francais', '🇫🇷']):
            # Set language preference and ask for name
            self.set_user_state(phone, 'registering_name', {'language': 'french'})
            return "Parfait! 🇫🇷 Comment vous appelez-vous?"
        elif any(word in message_lower for word in ['english', '🇬🇧', 'en']):
            # Set language preference and show welcome message
            self.set_user_state(phone, 'welcome_english', {'language': 'english'})
            return self.handle_english_welcome(phone)
        else:
            # Default to English and show welcome message
            self.set_user_state(phone, 'welcome_english', {'language': 'english'})
            return self.handle_english_welcome(phone)
    
    def handle_how_it_works(self, phone: str, message: str) -> str:
        """Handle questions about how the bot works"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['how', 'help', 'work', 'process', 'explain', 'what', 'does', 'do']):
            return """🌟 **Hey Neighbour! Welcome to ECLA Community Services!**

I noticed so many requests going unnoticed in our group, so I created this smart way to connect neighbors! 🤝

**🏠 How it works:**

🔄 **Smart Matching System**
• You register as either a service provider OR service seeker
• I store your data securely
• When someone needs help, I find the perfect match
• You get 3 options to choose from
• Once accepted, you both get invited to chat directly!

**💡 Popular ECLA Services:**
• 🚗 "Hey I need someone to lend a car"
• ✈️ "I want someone to pickup/drop to airport"
• 🍕 "I need food delivery to pickup"
• 🧺 "I need laundry help"
• 💻 "I need IT help"
• 🇫🇷 "I need French translation for prefecture"
• 🛒 "I need shopping assistance"
• 📦 "I need help moving boxes"

**🎯 The Process:**
1. Say your name
2. Choose: Service Provider OR Service Seeker
3. Tell me what you offer/need
4. I'll match you with neighbors
5. You choose who to connect with
6. Chat directly - no middleman!

**💪 Advantages:**
• No more lost requests in the group
• Direct connection with neighbors
• Quick and easy matching
• Perfect for ECLA community needs

Ready to get started? Just say your name! 😊"""
        
        return self.generate_response_with_gpt(message, phone, {}, {'state': 'idle'})

    def handle_first_time_greeting(self, phone: str) -> str:
        """Handle first-time user greeting with simple, friendly approach"""
        return """Hey Neighbour! 👋 I'm your ECLA Community Services Assistant!

🏠 **Whether it's finding someone for IT help, laundry, moving boxes, or anything in between, we make it super easy.**

I made this very customizable using our previous requests from the ECLA group. Now you can find what you need here!

**💡 Just say things like:**
• "Hey I need someone to lend a car"
• "I want someone to pickup/drop to airport" 
• "I need food delivery to pickup"
• "I need a cig" 😄

It will redirect you to the right person who is available for this kind of service, and once people are accepted, they will be invited to the same chat and you can connect directly!

**💪 Advantages:**
• No more lost requests in the group
• Direct connection with neighbors
• Quick and easy matching
• Perfect for ECLA community needs

Just say your name and let's get started! 😊"""

    def handle_help_request_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle help requests with enhanced 3-option matching"""
        service = extracted_info.get("service", "general")
        
        # Use the enhanced service request flow
        return self.handle_service_request_with_gpt(phone, message, extracted_info)
    
    def handle_registration_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle smart conversational registration with GPT"""
        self.set_user_state(phone, 'registering_name')
        return "I'm your ECLA assistant! 👋 What's your name?"
    
    def handle_name_registration_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle name registration with GPT"""
        name = message.strip()
        self.user_names[phone] = name
        
        # Get current user data and add name
        user_data = self.get_user_state(phone)['data']
        user_data['name'] = name
        self.set_user_state(phone, 'asking_role', user_data)
        
        return f"Nice to meet you, {name}! 😊\n\nAre you a service provider or service seeker?\n\n🛠️ **Service Provider** - You help others (laundry, food, translation, shopping, tech help, etc.)\n🤝 **Service Seeker** - You need help from others\n\nJust tell me which one you are!"
    
    def handle_role_selection(self, phone: str, message: str) -> str:
        """Handle role selection (provider vs seeker)"""
        message_lower = message.lower().strip()
        
        if any(word in message_lower for word in ['provider', 'help', 'offer', 'service provider', '🛠️']):
            # User wants to be a service provider
            user_data = self.get_user_state(phone)['data']
            user_data['role'] = 'provider'
            self.set_user_state(phone, 'registering_services', user_data)
            
            return "Great! 🛠️ What services can you offer?\n\nExamples: laundry, food delivery, translation, shopping, tech help, prefecture assistance, etc.\n\nJust tell me what you can help with!"
        
        elif any(word in message_lower for word in ['seeker', 'need', 'help me', 'service seeker', '🤝']):
            # User needs help
            user_data = self.get_user_state(phone)['data']
            user_data['role'] = 'seeker'
            self.set_user_state(phone, 'asking_service_need', user_data)
            
            return "Perfect! 🤝 What do you need help with?\n\nExamples: I need cigarettes, I need laundry help, I need someone to go to prefecture with me, etc.\n\nJust tell me what you need!"
        
        else:
            # Default to asking for service need
            user_data = self.get_user_state(phone)['data']
            user_data['role'] = 'seeker'
            self.set_user_state(phone, 'asking_service_need', user_data)
            
            return "I'll help you find what you need! 🤝\n\nWhat do you need help with?\n\nExamples: I need cigarettes, I need laundry help, I need someone to go to prefecture with me, etc.\n\nJust tell me what you need!"

    def handle_service_need(self, phone: str, message: str) -> str:
        """Handle when user tells us what they need with enhanced matching"""
        service = message.strip()
        
        # Use the enhanced service request flow
        extracted_info = {"service": service}
        return self.handle_service_request_with_gpt(phone, message, extracted_info)
    
    def handle_services_registration_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle services registration with GPT"""
        services = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['services'] = services
        self.set_user_state(phone, 'registering_location', user_data)
        return f"Great! You offer: {services} 🛠️\n\nWhich block are you in? (e.g., Block A, Block B, Main Campus, Student Housing)"
    
    def handle_location_registration_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle location registration with GPT"""
        location = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['location'] = location
        
        # Ask for availability
        self.set_user_state(phone, 'registering_availability', user_data)
        
        return f"Perfect! You're in {location} 📍\n\nWhat days are you available?\n\nExamples: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday\n\nOr just say: 'Every day' or 'Weekends only'"
    
    def handle_availability_registration(self, phone: str, message: str) -> str:
        """Handle availability registration"""
        availability = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['availability'] = availability
        
        # Ask for time preference
        self.set_user_state(phone, 'registering_time_preference', user_data)
        
        return f"Great! You're available: {availability} 📅\n\nWhat time of day do you prefer?\n\n🌅 Morning (6 AM - 12 PM)\n🌞 Afternoon (12 PM - 6 PM)\n🌙 Evening (6 PM - 12 AM)\n\nOr say: 'Any time' or 'Flexible'"
    
    def handle_time_preference_registration(self, phone: str, message: str) -> str:
        """Handle time preference registration"""
        time_preference = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['time_preference'] = time_preference
        
        # Ask for pricing (optional)
        self.set_user_state(phone, 'registering_pricing', user_data)
        
        return f"Perfect! You prefer: {time_preference} ⏰\n\nWhat's your typical charge for this service?\n\nExamples: 10€, 15-20€, Free, Negotiable\n\nOr just say: 'I'll discuss with the person'"
    
    def handle_pricing_registration(self, phone: str, message: str) -> str:
        """Handle pricing registration"""
        pricing = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['pricing'] = pricing
        
        # Save user to database with all details
        self.save_user_with_details(phone, user_data)
        
        # Reset state
        self.set_user_state(phone, 'idle')
        
        return f"Perfect! You're all set! 🎉\n\n**Your Profile:**\n• Name: {user_data['name']}\n• Services: {user_data['services']}\n• Location: {user_data['location']}\n• Available: {user_data['availability']}\n• Time: {user_data['time_preference']}\n• Pricing: {user_data['pricing']}\n\nI'll connect you with neighbors when they need your help! 🤝"
    
    def complete_request_with_gpt(self, phone: str, user_data: Dict) -> str:
        """Complete a help request with GPT"""
        # Find matches
        matches = self.find_matches(user_data['service'], user_data['location'])
        
        if matches:
            # Show top 3 matches with pricing and availability
            response = "Found 3 neighbors who can help:\n\n"
            for i, match in enumerate(matches[:3], 1):
                availability = "Available now" if i == 1 else f"Available in {i*30}min" if i == 2 else "Available tonight"
                price = f"{i*2}€" if i == 1 else f"{i*1.5}€" if i == 2 else f"{i*3}€"
                response += f"{i}️⃣ {match['name']} - {availability}, {price}\n"
            response += "\nReply with 1, 2, or 3 to connect!"
            # Set state to choosing provider
            self.set_user_state(phone, 'choosing_provider', user_data)
        else:
            response = f"📝 I've saved your request!\n\nService: {user_data['service']}\nTime: {user_data['time']}\nLocation: {user_data['location']}\n\nI'll notify you when someone becomes available!"
        
        # Save request only if no matches found
        if not matches:
            user_name = self.user_names.get(phone, "User")
            self.save_request(phone, user_name, user_data['service'], user_data['time'], user_data['location'])
        
        # Reset state
        self.set_user_state(phone, 'idle')
        
        return response
    
    def get_user_state(self, phone: str) -> Dict:
        """Get current conversation state for a user"""
        return self.conversation_states.get(phone, {
            'state': 'idle',
            'data': {},
            'last_message': None
        })
    
    def set_user_state(self, phone: str, state: str, data: Dict = None):
        """Set conversation state for a user"""
        if data is None:
            data = {}
        self.conversation_states[phone] = {
            'state': state,
            'data': data,
            'last_message': datetime.now()
        }
    
    def save_user(self, phone: str, name: str, services: str, location: str):
        """Save user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO users (phone, name, services, location)
            VALUES (?, ?, ?, ?)
        ''', (phone, name, services, location))
        
        conn.commit()
        conn.close()
    
    def save_user_with_details(self, phone: str, user_data: Dict):
        """Save user with detailed information"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create extended user table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users_extended (
                phone TEXT PRIMARY KEY,
                name TEXT,
                services TEXT,
                location TEXT,
                availability TEXT,
                time_preference TEXT,
                pricing TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            INSERT OR REPLACE INTO users_extended 
            (phone, name, services, location, availability, time_preference, pricing)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            phone,
            user_data.get('name', ''),
            user_data.get('services', ''),
            user_data.get('location', ''),
            user_data.get('availability', ''),
            user_data.get('time_preference', ''),
            user_data.get('pricing', '')
        ))
        
        conn.commit()
        conn.close()
    
    def save_request(self, phone: str, name: str, service: str, time: str, location: str):
        """Save request to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Ensure all required fields have values
        time = time or "flexible"
        location = location or "campus"
        name = name or "User"
        
        cursor.execute('''
            INSERT INTO requests (phone, name, service, time, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (phone, name, service, time, location))
        
        conn.commit()
        conn.close()
    
    def find_matches(self, service: str, location: str) -> List[Dict]:
        """Find 3 best matching helpers with ratings and pricing"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Enhanced matching logic with ratings and availability
        if 'translation' in service.lower() or 'prefecture' in service.lower() or 'french' in service.lower():
            cursor.execute('''
                SELECT name, phone, services, location, rating, total_services, availability
                FROM users 
                WHERE (services LIKE ? OR services LIKE ? OR services LIKE ?) 
                AND availability = 'available'
                ORDER BY rating DESC, total_services DESC
                LIMIT 3
            ''', ('%translation%', '%french%', '%prefecture%'))
        else:
            cursor.execute('''
                SELECT name, phone, services, location, rating, total_services, availability
                FROM users 
                WHERE services LIKE ? AND availability = 'available'
                ORDER BY rating DESC, total_services DESC
                LIMIT 3
            ''', (f'%{service}%',))
        
        matches = []
        for row in cursor.fetchall():
            name, phone, services, location, rating, total_services, availability = row
            # Calculate pricing based on service type and provider rating
            base_price = self.calculate_base_price(service)
            adjusted_price = base_price * (1 + (5.0 - rating) * 0.1)  # Higher rating = lower price
            
            matches.append({
                'name': name,
                'phone': phone,
                'services': services,
                'location': location,
                'rating': rating,
                'total_services': total_services,
                'price': round(adjusted_price, 2),
                'availability': availability
            })
        
        conn.close()
        return matches
    
    def calculate_base_price(self, service: str) -> float:
        """Calculate base price for different service types"""
        service_lower = service.lower()
        
        if any(word in service_lower for word in ['translation', 'french', 'prefecture']):
            return 15.0  # Translation services
        elif any(word in service_lower for word in ['car', 'airport', 'transport']):
            return 20.0  # Transportation
        elif any(word in service_lower for word in ['food', 'delivery', 'kfc']):
            return 5.0   # Food delivery
        elif any(word in service_lower for word in ['it', 'tech', 'computer']):
            return 12.0  # Tech help
        elif any(word in service_lower for word in ['laundry', 'cleaning']):
            return 8.0   # Cleaning services
        elif any(word in service_lower for word in ['print', 'document']):
            return 3.0   # Printing
        else:
            return 10.0  # General services
    
    def handle_service_request_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle service request with enhanced 3-option matching"""
        service = extracted_info.get("service", "general")
        
        # Find 3 best matches
        matches = self.find_matches(service, "campus")
        
        if not matches:
            return f"Sorry! I couldn't find anyone available for {service} right now. 😔\n\nTry again later or ask for a different service!"
        
        # Store active request for tracking
        self.active_requests[phone] = {
            'service': service,
            'matches': matches,
            'timestamp': datetime.now()
        }
        
        # Set state to choosing provider
        self.set_user_state(phone, 'choosing_provider', {'service': service})
        
        # Format response with 3 options
        response = f"Found {len(matches)} neighbors who can help with {service}:\n\n"
        
        for i, match in enumerate(matches, 1):
            emoji = "1️⃣" if i == 1 else "2️⃣" if i == 2 else "3️⃣"
            response += f"{emoji} **{match['name']}** - {match['location']}\n"
            response += f"   ⭐ Rating: {match['rating']}/5 ({match['total_services']} services)\n"
            response += f"   💰 Price: {match['price']}€\n"
            response += f"   📍 Available: {match['availability']}\n\n"
        
        response += "Reply with 1, 2, or 3 to connect with your chosen neighbor! 🚀"
        
        return response
    
    def handle_provider_choice_with_gpt(self, phone: str, message: str, extracted_info: Dict) -> str:
        """Handle user's choice and initiate two-way acceptance"""
        choice = message.strip()
        
        if choice not in ['1', '2', '3']:
            return "Please reply with 1, 2, or 3 to select a provider."
        
        # Get active request
        if phone not in self.active_requests:
            return "Sorry, your request has expired. Please start a new request!"
        
        active_request = self.active_requests[phone]
        matches = active_request['matches']
        
        if int(choice) > len(matches):
            return "Sorry, that option is not available. Please choose 1, 2, or 3."
        
        selected_provider = matches[int(choice) - 1]
        
        # Store pending match for two-way acceptance
        match_id = f"{phone}_{selected_provider['phone']}_{active_request['service']}"
        self.pending_matches[match_id] = {
            'seeker_phone': phone,
            'provider_phone': selected_provider['phone'],
            'provider_name': selected_provider['name'],
            'service': active_request['service'],
            'price': selected_provider['price'],
            'timestamp': datetime.now()
        }
        
        # Clear active request and reset state
        del self.active_requests[phone]
        self.set_user_state(phone, 'idle')
        
        return f"Perfect! Let me check with {selected_provider['name']}...\n\n🔄 Asking {selected_provider['name']}..."
    
    def handle_provider_confirmation(self, provider_phone: str, message: str) -> str:
        """Handle provider's confirmation or decline"""
        # Find pending match for this provider
        pending_match = None
        match_id = None
        
        for mid, match in self.pending_matches.items():
            if match['provider_phone'] == provider_phone:
                pending_match = match
                match_id = mid
                break
        
        if not pending_match:
            return "Sorry, I don't see any pending requests for you."
        
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['yes', 'ok', 'sure', 'available', 'can help']):
            # Provider accepts
            seeker_phone = pending_match['seeker_phone']
            service = pending_match['service']
            price = pending_match['price']
            
            # Save successful match
            self.save_match(pending_match)
            
            # Remove from pending
            del self.pending_matches[match_id]
            
            return f"Great! You're connected with the seeker for {service}.\n\n💰 Price: {price}€\n\nYou can discuss details directly in this chat! 🚀"
        
        elif any(word in message_lower for word in ['no', 'sorry', 'busy', 'unavailable', 'cant']):
            # Provider declines
            seeker_phone = pending_match['seeker_phone']
            service = pending_match['service']
            
            # Remove from pending
            del self.pending_matches[match_id]
            
            # Notify seeker and offer alternatives
            remaining_matches = self.find_matches(service, "campus")
            if remaining_matches:
                response = f"Sorry, {pending_match['provider_name']} is not available.\n\nWould you like to try:\n"
                for i, match in enumerate(remaining_matches[:2], 1):
                    emoji = "1️⃣" if i == 1 else "2️⃣"
                    response += f"{emoji} {match['name']} - {match['price']}€\n"
                response += "\nReply with 1 or 2, or say 'no thanks' to cancel."
            else:
                response = "Sorry, no other providers are available right now. Try again later!"
            
            return response
        
        else:
            return "Please reply with 'yes' if you're available, or 'no' if you're busy."
    
    def save_match(self, match_data: Dict):
        """Save successful match to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO matches (seeker_phone, provider_phone, service, price, status)
            VALUES (?, ?, ?, ?, ?)
        ''', (match_data['seeker_phone'], match_data['provider_phone'], 
              match_data['service'], match_data['price'], 'active'))
        
        conn.commit()
        conn.close()
    
    def complete_service(self, match_id: int, rating: int = None):
        """Mark service as completed and update ratings"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update match status
        cursor.execute('''
            UPDATE matches 
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP, rating = ?
            WHERE id = ?
        ''', (rating, match_id))
        
        # Get provider phone for rating update
        cursor.execute('SELECT provider_phone FROM matches WHERE id = ?', (match_id,))
        result = cursor.fetchone()
        
        if result and rating:
            provider_phone = result[0]
            # Update provider rating
            cursor.execute('''
                UPDATE users 
                SET rating = (rating * total_services + ?) / (total_services + 1),
                    total_services = total_services + 1
                WHERE phone = ?
            ''', (rating, provider_phone))
        
        conn.commit()
        conn.close()
    
    def get_user_rating(self, phone: str) -> float:
        """Get user's current rating"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT rating FROM users WHERE phone = ?', (phone,))
        result = cursor.fetchone()
        
        conn.close()
        return result[0] if result else 5.0 