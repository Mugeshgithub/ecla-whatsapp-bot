import sqlite3
import re
from datetime import datetime
from typing import Dict, List, Tuple

class ECLABot:
    def __init__(self):
        self.conversation_states = {}  # Track user conversation state
        self.db_path = 'ecla_bot.db'
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
    
    def understand_intent(self, message: str) -> str:
        """Enhanced intent recognition"""
        message_lower = message.lower()
        
        # Help requests - more specific
        if any(word in message_lower for word in ["need", "looking for", "want"]) and "help" in message_lower:
            return "REQUEST_HELP"
        
        # Service offers - more specific
        if any(word in message_lower for word in ["can help", "offer", "good at", "know how to", "expert"]) and "available" not in message_lower:
            return "OFFER_HELP"
        
        # Registration
        if any(word in message_lower for word in ["register", "sign up", "join", "start"]):
            return "REGISTER"
        
        # Status check
        if any(word in message_lower for word in ["status", "check", "my", "requests"]):
            return "CHECK_STATUS"
        
        # General queries (check this last to avoid conflicts)
        if any(word in message_lower for word in ["what", "how", "services", "available", "info"]) and not any(word in message_lower for word in ["can help", "offer"]):
            return "GENERAL_QUERY"
        
        return "UNKNOWN"
    
    def extract_service_from_message(self, message: str) -> str:
        """Extract service type from message"""
        message_lower = message.lower()
        
        services = {
            'laundry': ['laundry', 'washing', 'clothes', 'wash'],
            'it': ['it', 'computer', 'tech', 'software', 'hardware', 'internet'],
            'cleaning': ['cleaning', 'clean', 'housekeeping', 'tidy'],
            'cooking': ['cooking', 'food', 'meal', 'kitchen', 'cook'],
            'tutoring': ['tutor', 'study', 'homework', 'academic', 'teaching'],
            'transport': ['transport', 'ride', 'car', 'lift', 'drive']
        }
        
        for service, keywords in services.items():
            if any(keyword in message_lower for keyword in keywords):
                return service
        
        return "general"
    
    def extract_time_from_message(self, message: str) -> str:
        """Extract time information from message"""
        time_patterns = [
            r'today\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            r'tomorrow\s+at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            r'(\d{1,2}(?::\d{2})?\s*(?:am|pm)?)',
            r'(\d{1,2}:\d{2})'
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(1)
        
        return "flexible"
    
    def extract_location_from_message(self, message: str) -> str:
        """Extract location from message"""
        location_patterns = [
            r'room\s+(\d+)',
            r'floor\s+(\d+)',
            r'building\s+([a-zA-Z0-9]+)',
            r'laundry\s+room',
            r'common\s+area',
            r'kitchen'
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, message.lower())
            if match:
                return match.group(0)
        
        return "flexible"
    
    def process_message(self, phone: str, message: str) -> str:
        """Main message processing logic"""
        current_state = self.get_user_state(phone)
        intent = self.understand_intent(message)
        
        # Handle based on current state
        if current_state['state'] == 'registering_name':
            return self.handle_name_registration(phone, message)
        
        elif current_state['state'] == 'registering_services':
            return self.handle_services_registration(phone, message)
        
        elif current_state['state'] == 'registering_location':
            return self.handle_location_registration(phone, message)
        
        elif current_state['state'] == 'requesting_service':
            return self.handle_service_request(phone, message)
        
        elif current_state['state'] == 'requesting_time':
            return self.handle_time_request(phone, message)
        
        elif current_state['state'] == 'requesting_location':
            return self.handle_location_request(phone, message)
        
        # Handle based on intent (only if not in a conversation state)
        if intent == "REQUEST_HELP":
            return self.start_help_request(phone, message)
        
        elif intent == "OFFER_HELP":
            return self.start_registration(phone, message)
        
        elif intent == "GENERAL_QUERY":
            return self.handle_general_query(message)
        
        elif intent == "CHECK_STATUS":
            return self.check_user_status(phone)
        
        else:
            return self.handle_unknown_message()
    
    def start_registration(self, phone: str, message: str) -> str:
        """Start user registration process"""
        self.set_user_state(phone, 'registering_name', {})
        return "Great! I'd love to add you as a helper. What's your name?"
    
    def handle_name_registration(self, phone: str, message: str) -> str:
        """Handle name input during registration"""
        current_state = self.get_user_state(phone)
        current_state['data']['name'] = message.strip()
        self.set_user_state(phone, 'registering_services', current_state['data'])
        
        return "Thanks! What services can you offer? (e.g., laundry, IT, cleaning, cooking, tutoring)"
    
    def handle_services_registration(self, phone: str, message: str) -> str:
        """Handle services input during registration"""
        current_state = self.get_user_state(phone)
        services = self.extract_service_from_message(message)
        current_state['data']['services'] = services
        self.set_user_state(phone, 'registering_location', current_state['data'])
        
        return "Perfect! What's your room number or location?"
    
    def handle_location_registration(self, phone: str, message: str) -> str:
        """Handle location input during registration"""
        current_state = self.get_user_state(phone)
        location = message.strip()
        
        # Save user to database
        self.save_user(phone, current_state['data']['name'], 
                      current_state['data']['services'], location)
        
        # Reset state
        self.set_user_state(phone, 'idle', {})
        
        return f"Excellent! You're now registered as a helper. I'll notify you when someone needs {current_state['data']['services']} help near {location}."
    
    def start_help_request(self, phone: str, message: str) -> str:
        """Start help request process"""
        service = self.extract_service_from_message(message)
        
        # If service is already mentioned in the message, extract time and location too
        time_info = self.extract_time_from_message(message)
        location = self.extract_location_from_message(message)
        
        if service != "general" and time_info != "flexible" and location != "flexible":
            # Complete request in one message
            matches = self.find_matches(service, location)
            if matches:
                match_text = "\n".join([f"• {match['name']} (Room {match['location']})" for match in matches[:3]])
                response = f"Found {len(matches)} helpers available:\n{match_text}\n\nI'll connect you with them!"
                self.save_request(phone, "User", service, time_info, location)
            else:
                response = f"Sorry, no helpers available for {service} near {location}. I'll keep your request active and notify you when someone becomes available."
                self.save_request(phone, "User", service, time_info, location)
            return response
        else:
            self.set_user_state(phone, 'requesting_service', {'service': service})
            if service != "general":
                return f"I see you need {service} help. When do you need it?"
            else:
                return "What service do you need? (laundry, IT, cleaning, cooking, tutoring, transport)"
    
    def handle_service_request(self, phone: str, message: str) -> str:
        """Handle service type during help request"""
        current_state = self.get_user_state(phone)
        service = self.extract_service_from_message(message)
        current_state['data']['service'] = service
        self.set_user_state(phone, 'requesting_time', current_state['data'])
        
        return f"Got it! When do you need {service} help?"
    
    def handle_time_request(self, phone: str, message: str) -> str:
        """Handle time input during help request"""
        current_state = self.get_user_state(phone)
        time_info = self.extract_time_from_message(message)
        current_state['data']['time'] = time_info
        self.set_user_state(phone, 'requesting_location', current_state['data'])
        
        return "Where do you need this help? (room number, building, etc.)"
    
    def handle_location_request(self, phone: str, message: str) -> str:
        """Handle location input during help request"""
        current_state = self.get_user_state(phone)
        location = message.strip()
        
        # Find matches
        matches = self.find_matches(current_state['data']['service'], location)
        
        if matches:
            match_text = "\n".join([f"• {match['name']} (Room {match['location']})" for match in matches[:3]])
            response = f"Found {len(matches)} helpers available:\n{match_text}\n\nI'll connect you with them!"
            
            # Save request
            self.save_request(phone, "User", current_state['data']['service'], 
                            current_state['data']['time'], location)
        else:
            response = f"Sorry, no helpers available for {current_state['data']['service']} near {location}. I'll keep your request active and notify you when someone becomes available."
        
        # Reset state
        self.set_user_state(phone, 'idle', {})
        
        return response
    
    def handle_general_query(self, message: str) -> str:
        """Handle general questions"""
        if "services" in message.lower() or "available" in message.lower():
            return """Currently available services:
- Laundry help
- IT support
- Cleaning assistance
- Cooking/meal prep
- Tutoring
- Transport/rides

Just say what you need or can offer!"""
        else:
            return """Hi! I'm your ECLA service matching bot. You can:
- Request help: "I need laundry help"
- Offer help: "I can help with IT"
- Ask: "What services are available?" """
    
    def check_user_status(self, phone: str) -> str:
        """Check user's current status"""
        # Check if user is registered
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT name, services FROM users WHERE phone = ?", (phone,))
        user = cursor.fetchone()
        
        cursor.execute("SELECT service, time, location, status FROM requests WHERE phone = ? ORDER BY created_at DESC LIMIT 3", (phone,))
        requests = cursor.fetchall()
        
        conn.close()
        
        if user:
            response = f"You're registered as: {user[0]}\nServices: {user[1]}"
        else:
            response = "You're not registered yet. Say 'I can help with...' to register!"
        
        if requests:
            response += "\n\nYour recent requests:"
            for req in requests:
                response += f"\n- {req[0]} help at {req[1]} ({req[2]}) - {req[3]}"
        
        return response
    
    def handle_unknown_message(self) -> str:
        """Handle unrecognized messages"""
        return """I didn't understand that. You can:
- Request help: "I need laundry help"
- Offer help: "I can help with IT"
- Ask: "What services are available?" """
    
    def save_user(self, phone: str, name: str, services: str, location: str):
        """Save user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO users (phone, name, services, location)
            VALUES (?, ?, ?, ?)
        """, (phone, name, services, location))
        
        conn.commit()
        conn.close()
    
    def save_request(self, phone: str, name: str, service: str, time: str, location: str):
        """Save request to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO requests (phone, name, service, time, location)
            VALUES (?, ?, ?, ?, ?)
        """, (phone, name, service, time, location))
        
        conn.commit()
        conn.close()
    
    def find_matches(self, service: str, location: str) -> List[Dict]:
        """Find matching helpers for a request"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT name, services, location FROM users 
            WHERE services LIKE ? OR services = 'general'
        """, (f'%{service}%',))
        
        matches = []
        for row in cursor.fetchall():
            matches.append({
                'name': row[0],
                'services': row[1],
                'location': row[2]
            })
        
        conn.close()
        return matches 