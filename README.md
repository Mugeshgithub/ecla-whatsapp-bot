# ECLA WhatsApp Service Matching Bot

A smart WhatsApp-based service matching system for ECLA students built with Python FastAPI and natural conversation handling.

## 🎯 Features

- **WhatsApp Integration**: Students can request/offer services via WhatsApp
- **Smart Matching**: Automatically matches seekers with available helpers
- **Google Sheets Database**: Stores all user data and requests
- **Real-time Notifications**: Instant WhatsApp notifications for matches
- **Learning System**: Improves matching based on usage patterns

## 🏗️ Architecture

```
WhatsApp → FastAPI → SQLite Database → Smart Matching → Notifications
```

## 📋 Prerequisites

- Python 3.8+
- WhatsApp Business API (optional for testing)
- OpenAI API (optional for enhanced features)

## 🚀 Quick Start

1. **Clone and setup:**
   ```bash
   python setup.py
   ```

2. **Test the bot:**
   ```bash
   python test_bot.py
   ```

3. **Start the server:**
   ```bash
   python main.py
   ```

4. **Access web interface:**
   - Open http://localhost:8000
   - View real-time stats and activity

## 📊 Data Structure

### Users Table (Helpers)
| Name | Services | Location | Phone | Created |
|------|----------|----------|-------|---------|
| Alex | IT, computer help | Room 305 | +33... | 2024-01-15 |

### Requests Table (Service Seekers)
| Name | Service | Time | Location | Status | Matched Helper |
|------|---------|------|----------|--------|----------------|
| Sarah | Laundry | Today 5pm | Laundry Room | Pending | - |

## 🔧 Configuration

### Environment Variables (.env file)
- `WHATSAPP_API_KEY`: Your WhatsApp Business API key
- `OPENAI_API_KEY`: (Optional) For enhanced AI features
- `DATABASE_URL`: SQLite database path

## 📱 User Flow

### For Service Providers:
1. Send "help" to WhatsApp
2. Bot asks: Name, Services, Availability, Location
3. Data stored in Google Sheets
4. Notified when requests match

### For Service Seekers:
1. Send request to WhatsApp
2. Bot asks: Service needed, Time, Location, Name
3. Bot searches for matches
4. Both parties notified

## 🧠 Smart Features

- **Natural Conversation**: Handles any user message intelligently
- **Context Awareness**: Remembers conversation state
- **Smart Matching**: Finds best helpers based on service and location
- **Service Extraction**: Automatically identifies service types from messages
- **Time & Location Parsing**: Extracts timing and location from natural language

## 🔒 Security & Privacy

- All data stored in Google Sheets (your control)
- No sensitive data collected
- User consent for data usage
- GDPR compliant for EU students

## 📈 Scaling

- Add more service categories
- Implement payment integration
- Add admin dashboard
- Expand to other student residences

## 🛠️ Troubleshooting

### Common Issues:
1. **Python dependencies**: Run `pip install -r requirements.txt`
2. **Database errors**: Check file permissions for `ecla_bot.db`
3. **WhatsApp webhook errors**: Verify webhook URL in WhatsApp Business console
4. **Bot not responding**: Check conversation state in `bot_logic.py`

## 📞 Support

For issues or questions:
- Check the troubleshooting section
- Review n8n logs
- Verify all API credentials 