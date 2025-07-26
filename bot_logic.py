import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Tuple
import random

class ECLABot:
    def __init__(self):
        self.conversation_states = {}  # Track user conversation state
        self.db_path = 'ecla_bot.db'
        self.user_names = {}  # Store user names for personalization
        self.init_db()
    
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
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
    
    def is_greeting(self, message: str) -> bool:
        """Check if message is a greeting"""
        greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening', 'sup', 'yo']
        return any(greeting in message.lower() for greeting in greetings)
    
    def is_thanks(self, message: str) -> bool:
        """Check if message is a thank you"""
        thanks = ['thanks', 'thank you', 'thx', 'ty', 'appreciate it']
        return any(thank in message.lower() for thank in thanks)
    
    def get_greeting_response(self, phone: str) -> str:
        """Generate personalized greeting response"""
        user_name = self.user_names.get(phone, "there")
        greetings = [
            f"Hey {user_name}! 👋 How can I help you today?",
            f"Hi {user_name}! 😊 What service do you need?",
            f"Hello {user_name}! 🌟 Ready to connect you with ECLA helpers!",
            f"Hey {user_name}! 🚀 What can I do for you?"
        ]
        return random.choice(greetings)
    
    def get_thanks_response(self) -> str:
        """Generate response to thank you messages"""
        responses = [
            "You're welcome! 😊 Happy to help!",
            "Anytime! 🌟 Let me know if you need anything else!",
            "My pleasure! 😄 Feel free to ask more questions!",
            "Glad I could help! ✨ Don't hesitate to reach out again!"
        ]
        return random.choice(responses)
    
    def understand_intent(self, message: str) -> str:
        """Enhanced intent recognition with greetings and thanks"""
        message_lower = message.lower()
        
        # Greetings
        if self.is_greeting(message):
            return "GREETING"
        
        # Thanks
        if self.is_thanks(message):
            return "THANKS"
        
        # Help requests - more comprehensive
        help_keywords = ["need", "looking for", "want", "require", "pick up", "get", "bring", "deliver", "help me"]
        if any(word in message_lower for word in help_keywords):
            return "REQUEST_HELP"
        
        # Service offers - more specific
        if any(word in message_lower for word in ["can help", "offer", "good at", "know how to", "expert", "available to help", "willing to"]) and "available" not in message_lower:
            return "OFFER_HELP"
        
        # Registration
        if any(word in message_lower for word in ["register", "sign up", "join", "start", "become a helper"]):
            return "REGISTER"
        
        # Status check
        if any(word in message_lower for word in ["status", "check", "my", "requests", "pending"]):
            return "CHECK_STATUS"
        
        # General queries (check this last to avoid conflicts)
        if any(word in message_lower for word in ["what", "how", "services", "available", "info", "tell me"]) and not any(word in message_lower for word in ["can help", "offer"]):
            return "GENERAL_QUERY"
        
        return "UNKNOWN"
    
    def extract_service_from_message(self, message: str) -> str:
        """Extract service type from message with expanded categories"""
        message_lower = message.lower()
        
        services = {
            'food_delivery': ['food', 'pick up', 'deliver', 'takeout', 'restaurant', 'kfc', 'mcdonalds', 'pizza', 'burger', 'coffee', 'lunch', 'dinner', 'breakfast'],
            'errands': ['errand', 'pick up', 'get', 'bring', 'fetch', 'collect'],
            'transport': ['transport', 'ride', 'car', 'drive', 'pickup', 'lift'],
            'laundry': ['laundry', 'washing', 'clothes', 'wash', 'dry clean'],
            'it': ['it', 'computer', 'tech', 'software', 'hardware', 'internet', 'coding', 'programming'],
            'cleaning': ['cleaning', 'clean', 'housekeeping', 'tidy', 'organize'],
            'cooking': ['cooking', 'meal', 'kitchen', 'cook', 'baking'],
            'tutoring': ['tutor', 'study', 'homework', 'academic', 'teaching', 'math', 'science'],
            'shopping': ['shopping', 'buy', 'purchase', 'grocery', 'store'],
            'maintenance': ['maintenance', 'repair', 'fix', 'install'],
            'design': ['design', 'graphic', 'art', 'creative', 'logo'],
            'writing': ['writing', 'content', 'essay', 'resume', 'document'],
            'moving': ['move', 'carry', 'lift', 'heavy', 'furniture'],
            'photography': ['photo', 'photography', 'camera', 'picture'],
            'music': ['music', 'instrument', 'guitar', 'piano', 'singing'],
            'fitness': ['gym', 'workout', 'exercise', 'fitness', 'training'],
            'beauty': ['hair', 'makeup', 'beauty', 'styling'],
            'pet_care': ['pet', 'dog', 'cat', 'walk', 'feed'],
            'gaming': ['game', 'gaming', 'esports', 'tournament'],
            'language': ['language', 'translate', 'speak', 'conversation']
        }
        
        for service, keywords in services.items():
            if any(keyword in message_lower for keyword in keywords):
                return service
        
        return "general"
    
    def extract_time_from_message(self, message: str) -> str:
        """Extract time information from message"""
        message_lower = message.lower()
        
        time_patterns = {
            'today': ['today', 'tonight', 'this evening'],
            'tomorrow': ['tomorrow', 'tmr'],
            'this week': ['this week', 'weekend'],
            'asap': ['asap', 'urgent', 'now', 'immediately'],
            'flexible': ['anytime', 'flexible', 'whenever']
        }
        
        for time_key, patterns in time_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return time_key
        
        # Extract specific times
        time_regex = r'\b\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?\b'
        times = re.findall(time_regex, message)
        if times:
            return f"at {times[0]}"
        
        return "flexible"
    
    def extract_location_from_message(self, message: str) -> str:
        """Extract location information from message"""
        message_lower = message.lower()
        
        location_patterns = {
            'campus': ['campus', 'university', 'college', 'school'],
            'dorm': ['dorm', 'room', 'residence', 'hostel'],
            'library': ['library', 'study room'],
            'cafeteria': ['cafeteria', 'cafe', 'food court'],
            'online': ['online', 'virtual', 'zoom', 'meet']
        }
        
        for location_key, patterns in location_patterns.items():
            if any(pattern in message_lower for pattern in patterns):
                return location_key
        
        # Extract room numbers
        room_regex = r'\b(?:room|rm)\s*\d{3,4}\b'
        rooms = re.findall(room_regex, message_lower)
        if rooms:
            return rooms[0]
        
        return "campus"
    
    def process_message(self, phone: str, message: str) -> str:
        """Main message processing with enhanced conversation flow"""
        user_state = self.get_user_state(phone)
        intent = self.understand_intent(message)
        
        # Handle greetings
        if intent == "GREETING":
            return self.get_greeting_response(phone)
        
        # Handle thanks
        if intent == "THANKS":
            return self.get_thanks_response()
        
        # Handle conversation states
        if user_state['state'] != 'idle':
            return self.handle_conversation_state(phone, message, user_state)
        
        # Handle new intents
        if intent == "REQUEST_HELP":
            return self.start_help_request(phone, message)
        elif intent == "OFFER_HELP":
            return self.start_registration(phone, message)
        elif intent == "REGISTER":
            return self.start_registration(phone, message)
        elif intent == "CHECK_STATUS":
            return self.check_user_status(phone)
        elif intent == "GENERAL_QUERY":
            return self.handle_general_query(message)
        else:
            return self.handle_unknown_message()
    
    def handle_conversation_state(self, phone: str, message: str, user_state: Dict) -> str:
        """Handle ongoing conversations"""
        state = user_state['state']
        
        if state == 'registering_name':
            return self.handle_name_registration(phone, message)
        elif state == 'registering_services':
            return self.handle_services_registration(phone, message)
        elif state == 'registering_location':
            return self.handle_location_registration(phone, message)
        elif state == 'requesting_service':
            return self.handle_service_request(phone, message)
        elif state == 'requesting_time':
            return self.handle_time_request(phone, message)
        elif state == 'requesting_location':
            return self.handle_location_request(phone, message)
        else:
            return self.handle_unknown_message()
    
    def start_registration(self, phone: str, message: str) -> str:
        """Start the registration process"""
        self.set_user_state(phone, 'registering_name')
        return "Great! I'd love to add you as a helper! 😊\n\nWhat's your name?"
    
    def handle_name_registration(self, phone: str, message: str) -> str:
        """Handle name registration"""
        name = message.strip()
        self.user_names[phone] = name
        self.set_user_state(phone, 'registering_services', {'name': name})
        return f"Nice to meet you, {name}! 🌟\n\nWhat services can you help with? (e.g., laundry, IT, cooking, tutoring)"
    
    def handle_services_registration(self, phone: str, message: str) -> str:
        """Handle services registration"""
        services = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['services'] = services
        self.set_user_state(phone, 'registering_location', user_data)
        return f"Perfect! You can help with: {services} 👍\n\nWhere are you located? (e.g., campus, dorm, room number)"
    
    def handle_location_registration(self, phone: str, message: str) -> str:
        """Handle location registration"""
        location = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['location'] = location
        
        # Save user to database
        self.save_user(phone, user_data['name'], user_data['services'], location)
        
        # Reset state
        self.set_user_state(phone, 'idle')
        
        return f"Awesome! 🎉 You're now registered as a helper!\n\nName: {user_data['name']}\nServices: {user_data['services']}\nLocation: {location}\n\nStudents can now find you when they need help!"
    
    def start_help_request(self, phone: str, message: str) -> str:
        """Start the help request process"""
        service = self.extract_service_from_message(message)
        user_data = {'service': service}
        self.set_user_state(phone, 'requesting_service', user_data)
        
        if service != "general":
            return f"I can help you find someone for {service}! 👍\n\nWhen do you need this service? (e.g., today, tomorrow, ASAP)"
        else:
            return "I'd be happy to help you find assistance! 😊\n\nWhat type of service do you need? (e.g., laundry, IT, cooking, tutoring)"
    
    def handle_service_request(self, phone: str, message: str) -> str:
        """Handle service request"""
        user_data = self.get_user_state(phone)['data']
        
        if user_data.get('service') == "general":
            service = self.extract_service_from_message(message)
            user_data['service'] = service
        
        self.set_user_state(phone, 'requesting_time', user_data)
        return f"Great! Looking for {user_data['service']} help! ⏰\n\nWhen do you need this service? (e.g., today, tomorrow, ASAP)"
    
    def handle_time_request(self, phone: str, message: str) -> str:
        """Handle time request"""
        time = self.extract_time_from_message(message)
        user_data = self.get_user_state(phone)['data']
        user_data['time'] = time
        
        self.set_user_state(phone, 'requesting_location', user_data)
        return f"Perfect! {time} works! 📍\n\nWhere do you need this service? (e.g., campus, dorm, room number)"
    
    def handle_location_request(self, phone: str, message: str) -> str:
        """Handle location request"""
        location = message.strip()
        user_data = self.get_user_state(phone)['data']
        user_data['location'] = location
        
        # Find matches
        matches = self.find_matches(user_data['service'], location)
        
        if matches:
            match = matches[0]
            response = f"🎉 Found a perfect match!\n\nHelper: {match['name']}\nServices: {match['services']}\nLocation: {match['location']}\n\nI'll connect you both!"
        else:
            response = f"📝 I've saved your request!\n\nService: {user_data['service']}\nTime: {user_data['time']}\nLocation: {location}\n\nI'll notify you when someone becomes available!"
        
        # Save request
        user_name = self.user_names.get(phone, "User")
        self.save_request(phone, user_name, user_data['service'], user_data['time'], location)
        
        # Reset state
        self.set_user_state(phone, 'idle')
        
        return response
    
    def handle_general_query(self, message: str) -> str:
        """Handle general queries with more natural responses"""
        message_lower = message.lower()
        
        if "services" in message_lower or "available" in message_lower:
            return """🌟 Available Services at ECLA:
            
📦 **Food & Delivery:**
• Food Pickup & Delivery (KFC, McDonalds, etc.)
• Grocery Shopping
• Coffee Runs

🚗 **Transport & Errands:**
• Rides & Pickup
• Shopping Errands
• Package Pickup

🏠 **Home & Living:**
• Laundry & Dry Cleaning
• Cleaning & Organization
• Moving & Heavy Lifting
• Maintenance & Repairs

💻 **Tech & Creative:**
• IT Support & Tech Help
• Design & Creative Work
• Writing & Content
• Photography

📚 **Academic & Skills:**
• Tutoring & Homework Help
• Language Learning
• Music Lessons

💪 **Health & Lifestyle:**
• Fitness Training
• Beauty & Styling
• Pet Care

🎮 **Entertainment:**
• Gaming & Esports
• Event Planning

Just say what you need! Examples:
• "Pick up my food at KFC"
• "Need help with laundry"
• "Can someone give me a ride?" 😊"""
        
        elif "how" in message_lower and "work" in message_lower:
            return """🤖 How I Work:
            
1. Tell me what you need help with
2. I'll ask when and where you need it
3. I'll find the perfect helper for you!
4. You both get connected instantly

It's that simple! Ready to try? 😄"""
        
        elif "register" in message_lower or "become" in message_lower:
            return "Great! I'd love to add you as a helper! 😊\n\nJust say 'I can help with [service]' and I'll guide you through registration!"
        
        else:
            return """Hi! I'm your ECLA Service Matching Bot! 🤖

I help students connect with each other for various services. 

Need help? Just tell me what you need!
Want to help? Say what services you can offer!

What would you like to do? 😊"""
    
    def check_user_status(self, phone: str) -> str:
        """Check user's pending requests"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT service, time, location, status, created_at 
            FROM requests 
            WHERE phone = ? 
            ORDER BY created_at DESC
        ''', (phone,))
        
        requests = cursor.fetchall()
        conn.close()
        
        if not requests:
            return "You don't have any pending requests. Need help with something? 😊"
        
        response = "📋 Your Recent Requests:\n\n"
        for req in requests[:3]:  # Show last 3 requests
            service, time, location, status, created = req
            response += f"• {service} help ({time}) at {location} - {status}\n"
        
        response += "\nNeed to make a new request? Just tell me what you need!"
        return response
    
    def handle_unknown_message(self) -> str:
        """Handle unknown messages with helpful suggestions"""
        responses = [
            "I'm not sure I understood that. 🤔\n\nTry saying:\n• 'I need laundry help'\n• 'I can help with IT'\n• 'What services are available?'",
            "Hmm, I didn't catch that. 😅\n\nYou can:\n• Ask for help: 'I need cooking help'\n• Offer help: 'I can help with cleaning'\n• Ask questions: 'How does this work?'",
            "I'm still learning! 😊\n\nTry these:\n• Request help: 'I need tutoring'\n• Offer services: 'I can help with transport'\n• Get info: 'What services do you have?'"
        ]
        return random.choice(responses)
    
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
    
    def save_request(self, phone: str, name: str, service: str, time: str, location: str):
        """Save request to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO requests (phone, name, service, time, location)
            VALUES (?, ?, ?, ?, ?)
        ''', (phone, name, service, time, location))
        
        conn.commit()
        conn.close()
    
    def find_matches(self, service: str, location: str) -> List[Dict]:
        """Find matching helpers"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT name, services, location 
            FROM users 
            WHERE services LIKE ? AND location LIKE ?
        ''', (f'%{service}%', f'%{location}%'))
        
        matches = []
        for row in cursor.fetchall():
            matches.append({
                'name': row[0],
                'services': row[1],
                'location': row[2]
            })
        
        conn.close()
        return matches 