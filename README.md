# 📱 WellBeing Survey - Daily SMS Insights

A comprehensive Flask application for tracking daily wellbeing through SMS surveys with automated insights and beautiful analytics.

## ✨ Features Overview

### 📊 Core Functionality
- **Daily SMS Surveys** - Automated daily wellbeing check-ins via SMS
- **Smart Response Parsing** - Parse responses in format: "8 7 9 Had a great day!"
- **Weekly Insights** - Automatic weekly reports with cumulative analysis
- **Token-Based Security** - Secure survey links with expiration
- **Real-time Analytics** - Beautiful charts and statistics

### 🎨 User Interface
- **Modern Design** - Consistent purple gradient theme across all pages
- **Mobile Responsive** - Works perfectly on all devices
- **Intuitive Navigation** - Clean, professional interface
- **Interactive Charts** - Visual representation of wellbeing data

### 👥 Admin Features
- **User Management** - Add, view, and delete users with cascade deletion
- **SMS Controls** - Send daily surveys, feedback reports, or custom messages
- **Campaign Management** - Set survey periods and track progress
- **Live Statistics** - Real-time user and response counts

### 📱 SMS Capabilities
- **Multiple SMS Types**:
  - Daily wellbeing surveys with personalized links
  - Weekly insight reports with cumulative scores
  - Custom messages up to 160 characters
- **Smart Scheduling** - Weekly reports sent automatically after 7, 14, 21+ responses
- **User-Friendly Interface** - Click phone numbers to open SMS options modal

## 🚀 Quick Start

### 1. Installation
```bash
# Clone the repository
git clone <repository-url>
cd new-folder

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup
Create a `.env` file with:
```env
TEXTBELT_API_KEY=your_textbelt_api_key
BASE_URL=https://your-app-url.com
```

### 3. Run Application
```bash
python app.py
```

Visit `http://localhost:5000` to access the application.

## 📋 Usage Guide

### Admin Dashboard (`/admin`)
1. **Add Users** - Enter phone numbers to register new users
2. **Manage Campaigns** - Set start/end dates for survey periods
3. **Send SMS** - Click any phone number to open SMS options:
   - 📅 **Daily Survey** - Send today's wellbeing check-in
   - 📊 **Feedback Report** - Send personalized insights link
   - ✏️ **Custom Message** - Send any text up to 160 characters

### Analytics (`/responses`)
- View total responses and average scores
- See detailed response history with timestamps
- Track wellbeing trends over time

### User Experience
Users receive SMS like:
```
🌅 Good morning! Time for your daily wellbeing check-in.

Rate yesterday (1-10):
😊 Joy • 🎯 Achievement • 💫 Meaning

Click here: [survey_link]

Takes just 30 seconds. Thank you! 💙
```

## 📊 Response Format

Users respond with: `[joy] [achievement] [meaning] [optional comment]`

**Examples:**
- `8 7 9 Had a great day with family!`
- `6 8 7 Work was challenging but rewarding`
- `9 6 8`

## 🔧 Technical Details

### Database Schema
- **users** - User information and phone numbers
- **responses** - Daily wellbeing ratings and comments
- **survey_tokens** - Secure token management with expiration
- **campaign** - Survey campaign date management

### API Endpoints
- `POST /send_survey_sms` - Send daily survey to specific user
- `POST /send_feedback_sms` - Send feedback report link
- `POST /send_custom_sms` - Send custom message
- `POST /webhook` - Receive SMS responses
- `GET /survey/<token>` - Token-based survey form
- `GET /feedback/<user_id>` - Personalized insights page

### Weekly Insights Algorithm
- Calculates cumulative scores for Joy, Achievement, and Meaning
- Compares against recommended thresholds (7+ points per day)
- Provides personalized feedback and recommendations
- Automatically triggers after every 7 responses

## 🌐 Deployment

### Railway Deployment
The app is pre-configured for Railway with:
- `Procfile` - Web process configuration
- `runtime.txt` - Python 3.9 specification
- Environment variable support

### Environment Variables
```env
TEXTBELT_API_KEY=your_api_key    # TextBelt SMS API key
BASE_URL=your_domain             # Your app's public URL
```

## 📱 SMS Provider

Uses **TextBelt API** for reliable SMS delivery:
- Simple integration
- Global SMS support
- Reasonable pricing
- No complex setup required

## 🎨 Design System

### Color Scheme
- **Primary**: Purple gradient (`#667eea` to `#764ba2`)
- **Accent**: Blue gradient (`#007bff` to `#0056b3`)
- **Success**: Green (`#10b981`)
- **Warning**: Amber (`#f59e0b`)

### Components
- Centered white containers with rounded corners
- Consistent card-based layouts
- Hover effects and smooth transitions
- Professional typography and spacing

## 📈 Analytics Features

### Summary Statistics
- Total responses collected
- Average scores across all metrics
- User engagement metrics

### Detailed Views
- Individual response history
- Timestamp tracking
- Comment analysis
- Trend visualization

## 🔒 Security Features

- **Token-based surveys** - Secure, expiring links
- **Input validation** - Sanitized user inputs
- **Error handling** - Graceful failure management
- **Database integrity** - Proper foreign key constraints

## 🎯 Perfect For

- **Mental Health Tracking** - Daily wellbeing monitoring
- **Research Studies** - Longitudinal wellbeing research
- **Corporate Wellness** - Employee satisfaction tracking
- **Personal Development** - Individual growth monitoring

## 📞 Support

For issues or questions, check the application logs or review the comprehensive error handling built into each route.

---

**Built with Flask, SQLite, Bootstrap 5, and TextBelt SMS API** 🚀
