# SMS Survey Prototype

A Flask-based web application that sends daily SMS surveys to users asking about their wellbeing (joy, achievement, meaningfulness ratings).

## 🎯 Project Overview

This prototype demonstrates a complete SMS survey system with:
- **Admin interface** for managing users and campaigns
- **Daily SMS scheduling** at 7am ET
- **Simple survey questions** about daily wellbeing
- **Database storage** for users and responses
- **Response collection** via SMS webhook
- **Data visualization** with statistics dashboard
- **Web-based management** interface

## 🚀 Quick Start

1. **Clone and setup**:
   ```bash
   cd new-folder
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install flask apscheduler requests python-dotenv
   ```

2. **Configure SMS API**:
   ```bash
   # For testing (free but limited)
   echo "TEXTBELT_API_KEY=textbelt" > .env

   # For production, get a paid key from https://textbelt.com/create-key/
   echo "TEXTBELT_API_KEY=your_paid_api_key_here" > .env
   ```

3. **Run the application**:
   ```bash
   python3 app.py
   ```

4. **Access admin interface**:
   Open http://127.0.0.1:5001/admin

## 📱 SMS Provider Journey: From Twilio to TextBelt

### The Problem with Twilio

Initially, this project used Twilio for SMS delivery, but we encountered several regulatory hurdles:

#### 1. **Toll-Free Number Verification (Error 30032)**
- Toll-free numbers require business verification
- Process takes 1-3 business days
- Requires detailed business information

#### 2. **A2P 10DLC Registration (Error 30034)**
- US local numbers require A2P 10DLC registration
- Complex compliance process for business messaging
- Can take weeks to complete
- Requires brand registration and campaign approval

#### 3. **Trial Account Limitations**
- Can only send to verified phone numbers
- Limited to one phone number purchase
- Complex verification workflows

### The TextBelt Solution

**TextBelt** provides a much simpler alternative:

```python
# Simple TextBelt integration
import requests

response = requests.post('https://textbelt.com/text', {
    'phone': '5555555555',
    'message': 'Your survey message',
    'key': 'your_api_key',
})
```

#### ✅ **Advantages of TextBelt**:
- **No account setup** required for testing
- **No phone number verification** needed
- **No complex compliance** processes
- **Simple HTTP API** - just POST requests
- **Transparent pricing** - pay per message
- **Works immediately** for prototyping

#### ⚠️ **Considerations**:
- Free tier limited (1 SMS/day/IP for testing)
- Paid plans required for production use
- Less feature-rich than Twilio (no advanced features)

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────┐
│   Admin Web     │    │   Flask      │    │  TextBelt   │
│   Interface     │───▶│   Backend    │───▶│   SMS API   │
│                 │    │              │    │             │
└─────────────────┘    └──────────────┘    └─────────────┘
                              │                    │
                              ▼                    │ (webhook)
                       ┌──────────────┐            │
                       │   SQLite     │            ▼
                       │   Database   │    ┌─────────────┐
                       └──────────────┘    │ SMS Replies │
                                           │ Collection  │
                                           └─────────────┘
```

## 📱 SMS Response Collection

The system automatically collects and parses user replies to survey SMS messages:

### **Survey Message Format**
```
Daily Survey: Rate yesterday 1-10 for Joy, Achievement, Meaning.
Reply with 3 numbers (e.g., 7 8 6). What influenced your ratings most?
```

### **Expected Response Format**
Users reply with: `8 7 9 Had a productive day at work`

- **First number**: Joy rating (1-10)
- **Second number**: Achievement rating (1-10)
- **Third number**: Meaning rating (1-10)
- **Text after numbers**: What influenced their ratings

### **Response Processing**
1. **TextBelt webhook** receives SMS replies
2. **Parser extracts** the 3 ratings and influence text
3. **Database stores** responses linked to users
4. **Admin dashboard** displays collected data with statistics

### **Testing Response Collection**
```bash
# Run the test script to simulate SMS replies
python3 test_webhook.py

# View collected responses
# Open http://127.0.0.1:5001/responses
```

## 📊 Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    phone TEXT NOT NULL
);

-- Campaign settings table
CREATE TABLE campaign (
    id INTEGER PRIMARY KEY,
    start_date TEXT,
    end_date TEXT
);
```

## 🔧 Configuration

### Environment Variables (.env)
```bash
# TextBelt SMS API Configuration
TEXTBELT_API_KEY=textbelt  # Use 'textbelt' for free testing

# For production, get a paid key from:
# https://textbelt.com/create-key/
```

### Survey Message
The app sends this concise message to avoid SMS length limits:
```
Daily Survey: Rate yesterday 1-10 for Joy, Achievement, Meaning.
Reply with 3 numbers (e.g., 7 8 6). What influenced your ratings most?
```

## 🎮 Usage

### Admin Interface Features
- **Add/remove users** by phone number
- **Set campaign dates** for survey period
- **Send test SMS** to all users
- **View current configuration**

### Daily Scheduling
- Automatically sends surveys at **7am ET** daily
- Uses APScheduler for reliable background scheduling
- Converts to UTC for server compatibility

## 🧪 Testing

### Manual Testing
```bash
# Test SMS sending via admin interface
curl -X POST http://127.0.0.1:5001/send_test_sms
```

### API Testing
```python
# Test TextBelt directly
import requests

response = requests.post('https://textbelt.com/text', {
    'phone': '5555555555',
    'message': 'Test message',
    'key': 'textbelt',
})
print(response.json())
```

## 🚀 Deployment Considerations

### For Production:
1. **Get TextBelt API key** from https://textbelt.com/create-key/
2. **Use proper WSGI server** (gunicorn, uWSGI)
3. **Set up proper database** (PostgreSQL recommended)
4. **Configure environment variables** securely
5. **Set up monitoring** for SMS delivery

### Cost Estimation:
- TextBelt: ~$0.02-0.05 per SMS
- For 100 users daily: ~$2-5/month
- Much more predictable than Twilio's complex pricing

## 🔍 Lessons Learned

1. **SMS regulations are complex** - especially in the US
2. **Twilio's power comes with complexity** - great for enterprise, overkill for prototypes
3. **Simple solutions often work better** for MVPs and prototypes
4. **Regulatory compliance** can be the biggest blocker, not technical implementation
5. **TextBelt's simplicity** makes it perfect for rapid prototyping

## 🛠️ Future Enhancements

- [ ] **Response processing** - Parse and store user replies
- [ ] **Analytics dashboard** - Visualize survey responses
- [ ] **User management** - Web interface for adding users
- [ ] **Survey customization** - Configurable questions
- [ ] **Notification preferences** - User opt-out handling
- [ ] **Multi-language support** - Internationalization

## 📝 License

MIT License - Feel free to use this for your own projects!

---

**Built with ❤️ as a prototype to demonstrate SMS survey functionality**
