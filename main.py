from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
import json
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv
from bot_logic import ECLABot

load_dotenv()

app = FastAPI(title="ECLA WhatsApp Service Matching Bot")

# Initialize bot
bot = ECLABot()

# Database setup
def init_db():
    conn = sqlite3.connect('ecla_bot.db')
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

# Initialize database
init_db()

# Favicon route to prevent 404 errors
@app.get("/favicon.ico")
async def favicon():
    return HTMLResponse("", status_code=204)

# WhatsApp webhook endpoint
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    try:
        body = await request.json()
        
        # Extract message data (adjust based on your WhatsApp API)
        if 'entry' in body and body['entry']:
            entry = body['entry'][0]
            if 'changes' in entry and entry['changes']:
                change = entry['changes'][0]
                if 'value' in change and 'messages' in change['value']:
                    message = change['value']['messages'][0]
                    
                    # Extract message details
                    user_phone = message['from']
                    message_text = message['text']['body']
                    
                    # Process the message using enhanced bot logic
                    response = bot.process_message(user_phone, message_text)
                    
                    # Here you would send the response back to WhatsApp
                    # For now, we'll just return it
                    return {"response": response, "user_phone": user_phone}
        
        return {"status": "received"}
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Simple web interface
@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ECLA Service Matching Bot</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>🤖</text></svg>">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                margin: 0; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container { 
                max-width: 900px; 
                margin: 0 auto; 
                background: white; 
                border-radius: 16px; 
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 40px; 
                text-align: center;
            }
            .header h1 { 
                margin: 0; 
                font-size: 2.5em; 
                font-weight: 300;
            }
            .content { 
                padding: 40px; 
            }
            .card { 
                border: 1px solid #e1e5e9; 
                padding: 30px; 
                margin: 20px 0; 
                border-radius: 12px; 
                background: #f8f9fa;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            .card h2 { 
                margin-top: 0; 
                color: #2c3e50; 
                font-weight: 600;
            }
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 20px 0;
            }
            .stat-item {
                background: white;
                padding: 20px;
                border-radius: 8px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }
            .stat-label {
                color: #6c757d;
                font-size: 0.9em;
                margin-top: 5px;
            }
            .btn { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                padding: 12px 24px; 
                border: none; 
                border-radius: 8px; 
                cursor: pointer; 
                font-weight: 500;
                transition: transform 0.2s;
            }
            .btn:hover {
                transform: translateY(-2px);
            }
            ul {
                list-style: none;
                padding: 0;
            }
            li {
                padding: 10px 0;
                border-bottom: 1px solid #e1e5e9;
            }
            li:last-child {
                border-bottom: none;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                background: #28a745;
                margin-right: 8px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🤖 ECLA Service Matching Bot</h1>
                <p>Smart WhatsApp-based service matching for ECLA students</p>
            </div>
            
            <div class="content">
                <div class="card">
                    <h2>📊 Live Statistics</h2>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number" id="helpers-count">-</div>
                            <div class="stat-label">Active Helpers</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number" id="requests-count">-</div>
                            <div class="stat-label">Pending Requests</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number" id="matches-count">-</div>
                            <div class="stat-label">Successful Matches</div>
                        </div>
                    </div>
                </div>
                
                <div class="card">
                    <h2>📱 How to Use</h2>
                    <p>Send these messages to our WhatsApp bot:</p>
                    <ul>
                        <li><strong>Request Help:</strong> "I need laundry help today at 5pm"</li>
                        <li><strong>Offer Help:</strong> "I can help with IT support"</li>
                        <li><strong>Ask Questions:</strong> "What services are available?"</li>
                        <li><strong>Check Status:</strong> "Check my status"</li>
                    </ul>
                </div>
                
                <div class="card">
                    <h2>🔄 System Status</h2>
                    <p><span class="status-indicator"></span> Bot is running and ready to receive messages</p>
                    <p><span class="status-indicator"></span> Database connected and operational</p>
                    <p><span class="status-indicator"></span> Webhook endpoint active at /webhook</p>
                </div>
            </div>
        </div>
        
        <script>
            // Simple polling to update stats
            function updateStats() {
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('helpers-count').textContent = data.helpers_count;
                        document.getElementById('requests-count').textContent = data.requests_count;
                        document.getElementById('matches-count').textContent = data.matches_count;
                    })
                    .catch(error => {
                        console.log('Error updating stats:', error);
                    });
            }
            
            // Update every 30 seconds
            setInterval(updateStats, 30000);
            updateStats();
        </script>
    </body>
    </html>
    """

# API endpoint for stats
@app.get("/api/stats")
async def get_stats():
    conn = sqlite3.connect('ecla_bot.db')
    cursor = conn.cursor()
    
    # Get counts
    cursor.execute("SELECT COUNT(*) FROM users")
    helpers_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'pending'")
    requests_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM requests WHERE status = 'matched'")
    matches_count = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        "helpers_count": helpers_count,
        "requests_count": requests_count,
        "matches_count": matches_count
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 