# 🚀 Deploy to Render (FREE)

## Quick Steps:

1. **Go to [render.com](https://render.com)**
2. **Sign up with GitHub** (free)
3. **Click "New +" → "Web Service"**
4. **Connect your GitHub repository**
5. **Configure:**
   - **Name**: `ecla-whatsapp-bot`
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python main.py`
   - **Plan**: `Free`

## Your Bot Will Be Live At:
- **Dashboard**: `https://ecla-whatsapp-bot.onrender.com`
- **Webhook**: `https://ecla-whatsapp-bot.onrender.com/webhook`
- **API Stats**: `https://ecla-whatsapp-bot.onrender.com/api/stats`

## Test After Deployment:
```bash
# Test the API
curl https://ecla-whatsapp-bot.onrender.com/api/stats

# Test the webhook
curl -X POST https://ecla-whatsapp-bot.onrender.com/webhook \
  -H "Content-Type: application/json" \
  -d '{"test": "data"}'
```

## Total Cost: $0
✅ **Hosting**: Render (FREE)  
✅ **Domain**: Render subdomain (FREE)  
✅ **SSL**: Automatic (FREE)  
✅ **Deployment**: Automatic (FREE)  

**Your bot will be live in 5 minutes!** 🚀 