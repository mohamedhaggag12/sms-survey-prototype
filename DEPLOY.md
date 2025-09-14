# 🚀 Deployment Guide

## Quick Deploy to Railway (Recommended)

### 1. Push to GitHub
```bash
cd new-folder
git init
git add .
git commit -m "Initial commit - SMS Survey App"
git branch -M main
git remote add origin https://github.com/yourusername/sms-survey-app.git
git push -u origin main
```

### 2. Deploy to Railway
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect it's a Python app and deploy

### 3. Set Environment Variables
In Railway dashboard, go to Variables tab and add:
```
TEXTBELT_API_KEY=your_textbelt_api_key_here
WEBHOOK_URL=https://your-app-name.up.railway.app/sms_webhook
FLASK_ENV=production
```

### 4. Get Your App URL
- Railway will give you a URL like: `https://your-app-name.up.railway.app`
- Update the WEBHOOK_URL variable with this URL + `/sms_webhook`

## Alternative: Heroku

### 1. Install Heroku CLI
```bash
# macOS
brew install heroku/brew/heroku

# Or download from heroku.com
```

### 2. Deploy
```bash
cd new-folder
heroku create your-sms-survey-app
heroku config:set TEXTBELT_API_KEY=your_api_key_here
heroku config:set FLASK_ENV=production
git push heroku main
```

### 3. Set Webhook URL
```bash
heroku config:set WEBHOOK_URL=https://your-sms-survey-app.herokuapp.com/sms_webhook
```

## Testing Deployment

1. Visit your app URL
2. Add a user (your phone number)
3. Send test SMS
4. Reply to the SMS
5. Check responses page to see if reply was captured

## 🎉 Your App is Live!

Users can now:
- Receive real SMS surveys
- Reply with their ratings
- Have responses automatically collected
- View their data on the web dashboard
