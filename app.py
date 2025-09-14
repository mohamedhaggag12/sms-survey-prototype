import os
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, flash
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import sqlite3
import pytz
import hmac
import hashlib
import time
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # For flash messages

# TextBelt SMS config - Much simpler than Twilio!
TEXTBELT_API_KEY = os.getenv('TEXTBELT_API_KEY', 'textbelt')  # 'textbelt' for free testing
TEXTBELT_URL = 'https://textbelt.com/text'

print("📱 Using TextBelt SMS API - Simple and reliable!")

def send_sms(phone, message):
    """Send SMS using TextBelt API with webhook for replies"""
    try:
        # Get webhook URL from environment variable
        # In production, this will be set to your deployed app URL
        webhook_url = os.getenv('WEBHOOK_URL')  # e.g., 'https://your-app.railway.app/sms_webhook'

        payload = {
            'phone': phone,
            'message': message,
            'key': TEXTBELT_API_KEY,
        }

        # Only add webhook if we have a public URL
        if webhook_url:
            payload['replyWebhookUrl'] = webhook_url
            print(f"📡 Using webhook: {webhook_url}")
        else:
            print("⚠️ No webhook URL set - replies won't be collected automatically")

        response = requests.post(TEXTBELT_URL, payload)
        result = response.json()

        if result.get('success'):
            print(f"✅ SMS sent successfully to {phone} (Text ID: {result.get('textId')})")
            return result.get('textId')  # Return text ID for tracking
        else:
            print(f"❌ SMS failed to {phone}: {result.get('error', 'Unknown error')}")
            return False
    except Exception as e:
        print(f"❌ SMS error to {phone}: {str(e)}")
        return False

# Database setup
DB_PATH = 'survey.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS responses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        joy INTEGER,
        achievement INTEGER,
        meaningfulness INTEGER,
        influence TEXT,
        date TEXT,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS campaign (
        id INTEGER PRIMARY KEY,
        start_date TEXT,
        end_date TEXT
    )''')
    conn.commit()
    conn.close()

init_db()

# Routes
@app.route('/')
def index():
    """Landing page with overview"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get stats
    c.execute('SELECT COUNT(*) FROM users')
    user_count = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM responses')
    response_count = c.fetchone()[0]

    conn.close()

    return render_template('index.html',
                         user_count=user_count,
                         response_count=response_count)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if request.method == 'POST':
        phone = request.form.get('phone')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date')

        if phone:
            # Validate phone number format (basic E.164 check)
            if phone.startswith('+') and len(phone) >= 10:
                c.execute('INSERT INTO users (phone) VALUES (?)', (phone,))
                flash(f"✅ Added user: {phone}", 'success')
            else:
                flash("❌ Invalid phone format. Use E.164 format (e.g., +1234567890)", 'error')

        if start_date and end_date:
            # Validate campaign dates
            from datetime import datetime, date

            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
                end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
                today = date.today()

                # Check if start date is in the past
                if start_dt < today:
                    flash("❌ Campaign start date cannot be in the past", 'error')
                # Check if end date is before start date
                elif end_dt < start_dt:
                    flash("❌ Campaign end date cannot be before start date", 'error')
                # Check if campaign duration is reasonable (not too long)
                elif (end_dt - start_dt).days > 365:
                    flash("❌ Campaign duration cannot exceed 1 year", 'error')
                else:
                    c.execute('DELETE FROM campaign')
                    c.execute('INSERT INTO campaign (id, start_date, end_date) VALUES (1, ?, ?)', (start_date, end_date))
                    flash(f"✅ Campaign dates set: {start_date} to {end_date}", 'success')

            except ValueError:
                flash("❌ Invalid date format", 'error')

        conn.commit()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    c.execute('SELECT start_date, end_date FROM campaign WHERE id=1')
    campaign = c.fetchone() or (None, None)
    conn.close()
    campaign_start, campaign_end = campaign
    return render_template('admin.html', users=users, campaign_start=campaign_start, campaign_end=campaign_end)

# Manual test SMS endpoint
@app.route('/send_test_sms', methods=['POST'])
def send_test_sms():
    try:
        send_daily_sms()
        flash('Test SMS sent successfully to all users!', 'success')
    except Exception as e:
        flash(f'Error sending SMS: {str(e)}', 'error')
    return redirect(url_for('admin'))

# Send daily SMS - Engaging and delightful copy
survey_message = ("🌅 Good morning! Time for your daily wellbeing check-in.\n\n"
                 "Rate yesterday (1-10):\n"
                 "😊 Joy • 🎯 Achievement • 💫 Meaning\n\n"
                 "Reply: \"8 7 9 Had a great day with friends!\"\n"
                 "What influenced your ratings most?")

def send_daily_sms():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT phone FROM users')
    users = c.fetchall()
    conn.close()
    for (phone,) in users:
        send_sms(phone, survey_message)

scheduler = BackgroundScheduler()
# Schedule for 7am ET (convert to UTC for server)
scheduler.add_job(send_daily_sms, 'cron', hour=11, minute=0)  # 7am ET == 11am UTC
scheduler.start()

def verify_textbelt_webhook(api_key, timestamp, signature, payload):
    """Verify TextBelt webhook signature"""
    try:
        # Check timestamp is not more than 15 minutes old
        current_time = int(time.time())
        webhook_time = int(timestamp)
        if abs(current_time - webhook_time) > 900:  # 15 minutes
            print(f"⚠️ Webhook timestamp too old: {abs(current_time - webhook_time)} seconds")
            return False

        # Create signature
        message = timestamp + payload
        expected_signature = hmac.new(
            api_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        # Compare signatures
        return hmac.compare_digest(signature, expected_signature)
    except Exception as e:
        print(f"❌ Signature verification error: {e}")
        return False

# TextBelt webhook to receive SMS replies
@app.route('/sms_webhook', methods=['POST'])
def sms_webhook():
    """Receive and process SMS replies from TextBelt"""
    try:
        # Log all incoming webhook data for debugging
        headers = dict(request.headers)
        raw_data = request.get_data().decode('utf-8')

        print(f"🔍 Webhook received - Headers: {headers}")
        print(f"🔍 Webhook received - Raw data: {raw_data}")

        # Check for TextBelt signature verification
        textbelt_signature = headers.get('X-Textbelt-Signature')
        textbelt_timestamp = headers.get('X-Textbelt-Timestamp')

        if textbelt_signature and textbelt_timestamp:
            print(f"🔐 TextBelt signature found, verifying...")
            api_key = os.getenv('TEXTBELT_API_KEY')
            if api_key and not verify_textbelt_webhook(api_key, textbelt_timestamp, textbelt_signature, raw_data):
                print(f"❌ Invalid TextBelt signature")
                return 'Invalid signature', 401
            print(f"✅ TextBelt signature verified")
        else:
            print(f"⚠️ No TextBelt signature headers found (testing mode)")

        # Store for debugging endpoint
        webhook_logs.append({
            'timestamp': datetime.now().isoformat(),
            'headers': headers,
            'raw_data': raw_data,
            'method': request.method,
            'content_type': request.content_type
        })

        # Try to get JSON payload from TextBelt
        data = request.get_json()

        # Also try form data in case TextBelt sends form-encoded data
        if not data:
            data = request.form.to_dict()
            print(f"🔍 Trying form data: {data}")

        if not data:
            print("❌ No JSON or form data received")
            return 'No data', 400

        # TextBelt webhook format: {"fromNumber": "+1555123456", "text": "reply"}
        # Our test format: {"textId": "12345", "fromNumber": "+1555123456", "text": "reply"}
        text_id = data.get('textId', 'webhook-reply')  # Default for real webhooks
        from_number = data.get('fromNumber')
        reply_text = data.get('text', '').strip()

        print(f"📱 Received SMS reply from {from_number}: {reply_text}")
        print(f"🔍 Full webhook data: {data}")

        # Validate required fields
        if not from_number or not reply_text:
            print(f"⚠️ Missing required fields: fromNumber={from_number}, text='{reply_text}'")
            return 'Missing required fields', 400

        # Parse the survey response
        joy, achievement, meaning, influence = parse_survey_response(reply_text)

        if joy is not None:  # Valid response parsed
            # Store in database
            store_survey_response(from_number, joy, achievement, meaning, influence, reply_text)
            print(f"✅ Stored survey response from {from_number}")
        else:
            print(f"⚠️ Could not parse survey response: {reply_text}")

        return 'OK', 200

    except Exception as e:
        print(f"❌ Webhook error: {str(e)}")
        return 'Error', 500

def parse_survey_response(text):
    """Parse survey response text to extract ratings and influence"""
    import re

    # Look for 3 numbers (joy, achievement, meaning ratings)
    numbers = re.findall(r'\b([1-9]|10)\b', text)

    if len(numbers) >= 3:
        try:
            joy = int(numbers[0])
            achievement = int(numbers[1])
            meaning = int(numbers[2])

            # Extract influence text (everything after the numbers)
            # Remove the numbers and clean up the remaining text
            influence_text = text
            for num in numbers[:3]:
                influence_text = influence_text.replace(num, '', 1)
            influence_text = re.sub(r'[^\w\s]', ' ', influence_text).strip()
            influence_text = ' '.join(influence_text.split())  # Clean whitespace

            return joy, achievement, meaning, influence_text
        except ValueError:
            pass

    return None, None, None, None

def convert_utc_to_eastern(utc_timestamp_str):
    """Convert UTC timestamp string to Eastern Time"""
    try:
        # Parse the UTC timestamp
        utc_dt = datetime.strptime(utc_timestamp_str, '%Y-%m-%d %H:%M:%S')

        # Set UTC timezone
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)

        # Convert to Eastern Time
        eastern = pytz.timezone('US/Eastern')
        eastern_dt = utc_dt.astimezone(eastern)

        # Return formatted string with 12-hour format
        return eastern_dt.strftime('%Y-%m-%d %I:%M:%S %p %Z')
    except Exception as e:
        print(f"Error converting timestamp: {e}")
        return utc_timestamp_str  # Return original if conversion fails

def store_survey_response(phone, joy, achievement, meaning, influence, raw_message):
    """Store survey response in database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        # Find user_id from phone number
        c.execute('SELECT id FROM users WHERE phone = ?', (phone,))
        user_result = c.fetchone()

        if user_result:
            user_id = user_result[0]

            # Insert response
            c.execute('''INSERT INTO responses
                        (user_id, joy, achievement, meaningfulness, influence, date)
                        VALUES (?, ?, ?, ?, ?, datetime('now'))''',
                     (user_id, joy, achievement, meaning, influence))

            conn.commit()
            print(f"✅ Response stored for user {user_id}")
        else:
            print(f"⚠️ User not found for phone {phone}")

        conn.close()

    except Exception as e:
        print(f"❌ Database error: {str(e)}")
        if conn:
            conn.close()

# Manual response entry for testing
@app.route('/add_response', methods=['GET', 'POST'])
def add_response():
    """Manually add a response for testing"""
    if request.method == 'POST':
        phone = request.form.get('phone')
        response_text = request.form.get('response_text')

        if phone and response_text:
            # Parse the response
            joy, achievement, meaning, influence = parse_survey_response(response_text)

            if joy is not None:
                store_survey_response(phone, joy, achievement, meaning, influence, response_text)
                flash(f'✅ Response added successfully: {joy}, {achievement}, {meaning}', 'success')
            else:
                flash('❌ Invalid response format. Use: "8 7 9 Your comment"', 'error')
        else:
            flash('❌ Please fill in all fields', 'error')

        return redirect(url_for('add_response'))

    # GET request - show form
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT phone FROM users')
    users = c.fetchall()
    conn.close()

    return render_template('add_response.html', users=users)

# View survey responses
@app.route('/responses')
def view_responses():
    """Admin page to view all survey responses"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Get all responses with user phone numbers
    c.execute('''SELECT r.id, u.phone, r.joy, r.achievement, r.meaningfulness,
                        r.influence, r.date
                 FROM responses r
                 JOIN users u ON r.user_id = u.id
                 ORDER BY r.date DESC''')
    raw_responses = c.fetchall()
    conn.close()

    # Convert timestamps to Eastern Time
    responses = []
    for response in raw_responses:
        response_list = list(response)
        # Convert the date field (index 6) to Eastern Time
        response_list[6] = convert_utc_to_eastern(response[6])
        responses.append(tuple(response_list))

    return render_template('responses.html', responses=responses)

# Store webhook logs for debugging
webhook_logs = []

@app.route('/debug/webhooks')
def debug_webhooks():
    """Show recent webhook calls for debugging"""
    return {
        'recent_webhooks': webhook_logs[-10:],  # Last 10 webhooks
        'total_received': len(webhook_logs)
    }

# Debug endpoint to check environment variables
@app.route('/debug/env')
def debug_env():
    webhook_url = os.getenv('WEBHOOK_URL')
    textbelt_key = os.getenv('TEXTBELT_API_KEY')
    flask_env = os.getenv('FLASK_ENV')

    return {
        'webhook_url': webhook_url,
        'textbelt_key_set': bool(textbelt_key),
        'flask_env': flask_env,
        'all_env_vars': list(os.environ.keys())
    }

# Feedback endpoint
@app.route('/feedback/<user_id>')
def feedback(user_id):
    # ...existing code...
    return 'Feedback page (to be implemented)'

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
