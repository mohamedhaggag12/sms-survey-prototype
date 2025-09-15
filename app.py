import os
import requests
import secrets
import uuid
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
    """Send SMS using TextBelt API (basic version)"""
    try:
        payload = {
            'phone': phone,
            'message': message,
            'key': TEXTBELT_API_KEY,
        }

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

def send_survey_sms(user_id, phone, name=None):
    """Send SMS with survey link to a user"""
    try:
        # Create survey token
        token = create_survey_token(user_id, expires_hours=24)
        if not token:
            print(f"❌ Failed to create survey token for user {user_id}")
            return False

        # Get base URL from environment
        base_url = os.getenv('BASE_URL', 'https://sms-survey-prototype-production.up.railway.app')
        survey_url = f"{base_url}/survey/{token}"

        # Create personalized message
        greeting = f"Hi {name}!" if name else "Hi!"
        message = f"""{greeting}

Time for your daily wellbeing check-in! 🌟

Please rate your day (1-10):
• Joy & Happiness
• Achievement & Progress
• Meaning & Purpose

Click here: {survey_url}

Takes just 30 seconds. Thank you! 💙"""

        # Send SMS
        text_id = send_sms(phone, message)
        if text_id:
            print(f"📱 Survey SMS sent to {phone} with token {token[:8]}...")
            return token
        else:
            print(f"❌ Failed to send survey SMS to {phone}")
            return False

    except Exception as e:
        print(f"❌ Error sending survey SMS to {phone}: {str(e)}")
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

    # Create survey tokens table for link-based surveys
    c.execute('''CREATE TABLE IF NOT EXISTS survey_tokens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        token TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP NOT NULL,
        used_at TIMESTAMP NULL,
        is_used BOOLEAN DEFAULT FALSE,
        FOREIGN KEY(user_id) REFERENCES users(id)
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
        success_count, total_count = send_daily_sms()
        if success_count == total_count:
            flash(f'✅ Survey SMS sent successfully to all {total_count} users!', 'success')
        elif success_count > 0:
            flash(f'⚠️ Survey SMS sent to {success_count}/{total_count} users. Check logs for details.', 'warning')
        else:
            flash(f'❌ Failed to send survey SMS to any users. Check configuration.', 'error')
    except Exception as e:
        flash(f'Error sending SMS: {str(e)}', 'error')
    return redirect(url_for('admin'))

def send_daily_sms():
    """Send daily survey SMS with links to all users"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, phone FROM users')
    users = c.fetchall()
    conn.close()

    success_count = 0
    total_count = len(users)

    for user_id, phone in users:
        try:
            token = send_survey_sms(user_id, phone)
            if token:
                success_count += 1
                print(f"✅ Survey SMS sent to {phone}")
            else:
                print(f"❌ Failed to send survey SMS to {phone}")
        except Exception as e:
            print(f"❌ Error sending survey SMS to {phone}: {e}")

    print(f"📊 Daily SMS Summary: {success_count}/{total_count} sent successfully")
    return success_count, total_count

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
        return utc_timestamp_str

def generate_survey_token():
    """Generate a unique survey token"""
    return secrets.token_urlsafe(32)

def create_survey_token(user_id, expires_hours=24):
    """Create a new survey token for a user"""
    token = generate_survey_token()
    expires_at = datetime.now() + timedelta(hours=expires_hours)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            INSERT INTO survey_tokens (token, user_id, expires_at)
            VALUES (?, ?, ?)
        ''', (token, user_id, expires_at))
        conn.commit()
        return token
    except Exception as e:
        print(f"Error creating survey token: {e}")
        return None
    finally:
        conn.close()

def get_survey_token_info(token):
    """Get survey token information and validate it"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print(f"🔍 Validating token: {token[:8]}...")

        cursor.execute('''
            SELECT st.id, st.user_id, st.expires_at, st.is_used, u.phone,
                   COALESCE(u.name, '') as name
            FROM survey_tokens st
            JOIN users u ON st.user_id = u.id
            WHERE st.token = ?
        ''', (token,))

        result = cursor.fetchone()
        print(f"🔍 Database query result: {result}")

        if not result:
            print(f"❌ Token not found in database: {token}")
            return None, "Invalid token"

        token_id, user_id, expires_at_str, is_used, phone, name = result
        print(f"🔍 Token info: id={token_id}, user_id={user_id}, expires_at={expires_at_str}, is_used={is_used}")

        # Check if token is already used
        if is_used:
            print(f"❌ Token already used: {token}")
            return None, "Token already used"

        # Check if token is expired
        try:
            # Try different datetime formats
            expires_at = None
            for fmt in ['%Y-%m-%d %H:%M:%S.%f', '%Y-%m-%d %H:%M:%S']:
                try:
                    expires_at = datetime.strptime(expires_at_str, fmt)
                    break
                except ValueError:
                    continue

            if expires_at is None:
                print(f"❌ Could not parse expires_at: {expires_at_str}")
                return None, "Token validation error"

            if datetime.now() > expires_at:
                print(f"❌ Token expired: {expires_at} < {datetime.now()}")
                return None, "Token expired"

        except Exception as date_error:
            print(f"❌ Date parsing error: {date_error}")
            return None, "Token validation error"

        print(f"✅ Token validation successful")
        return {
            'token_id': token_id,
            'user_id': user_id,
            'phone': phone,
            'name': name,
            'expires_at': expires_at
        }, None

    except Exception as e:
        print(f"❌ Error validating token: {e}")
        import traceback
        traceback.print_exc()
        return None, "Token validation error"
    finally:
        conn.close()

def mark_token_used(token):
    """Mark a survey token as used"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE survey_tokens
            SET is_used = TRUE, used_at = CURRENT_TIMESTAMP
            WHERE token = ?
        ''', (token,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error marking token as used: {e}")
        return False
    finally:
        conn.close()  # Return original if conversion fails

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

@app.route('/survey/<token>', methods=['GET', 'POST'])
def survey(token):
    """Handle survey display and submission"""
    # Validate token
    token_info, error = get_survey_token_info(token)
    if error:
        return render_template('error.html',
                             title="Survey Not Available",
                             message=error,
                             icon="fas fa-exclamation-triangle"), 400

    if request.method == 'GET':
        # Display survey form
        return render_template('survey.html',
                             user_name=token_info.get('name'),
                             token=token)

    elif request.method == 'POST':
        # Process survey submission
        try:
            # Get form data
            joy = int(request.form.get('joy', 0))
            achievement = int(request.form.get('achievement', 0))
            meaning = int(request.form.get('meaning', 0))
            influence = request.form.get('influence', '').strip()

            # Validate ratings
            if not all(1 <= rating <= 10 for rating in [joy, achievement, meaning]):
                return render_template('error.html',
                                     title="Invalid Ratings",
                                     message="All ratings must be between 1 and 10.",
                                     icon="fas fa-exclamation-triangle"), 400

            # Store response in database
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO responses (user_id, joy, achievement, meaningfulness, influence, date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (token_info['user_id'], joy, achievement, meaning, influence, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))

            conn.commit()
            conn.close()

            # Mark token as used
            mark_token_used(token)

            print(f"✅ Survey response stored for user {token_info['user_id']}: Joy={joy}, Achievement={achievement}, Meaning={meaning}")

            # Redirect to thank you page
            return redirect(url_for('survey_thanks', token=token,
                                  joy=joy, achievement=achievement, meaning=meaning))

        except ValueError:
            return render_template('error.html',
                                 title="Invalid Data",
                                 message="Please provide valid ratings.",
                                 icon="fas fa-exclamation-triangle"), 400
        except Exception as e:
            print(f"❌ Error storing survey response: {e}")
            return render_template('error.html',
                                 title="Submission Error",
                                 message="There was an error saving your response. Please try again.",
                                 icon="fas fa-exclamation-triangle"), 500

@app.route('/survey/<token>/thanks')
def survey_thanks(token):
    """Thank you page after survey completion"""
    # Get ratings from URL parameters
    joy = request.args.get('joy', type=int)
    achievement = request.args.get('achievement', type=int)
    meaning = request.args.get('meaning', type=int)

    # Validate that we have all ratings
    if not all(rating is not None for rating in [joy, achievement, meaning]):
        return render_template('error.html',
                             title="Invalid Request",
                             message="Missing survey data.",
                             icon="fas fa-exclamation-triangle"), 400

    return render_template('survey_thanks.html',
                         joy=joy,
                         achievement=achievement,
                         meaning=meaning,
                         token=token)

@app.route('/debug/database')
def debug_database():
    """Debug endpoint to check database schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        # Check if survey_tokens table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='survey_tokens'")
        tokens_table_exists = cursor.fetchone() is not None

        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        # Get survey_tokens table schema if it exists
        tokens_schema = None
        if tokens_table_exists:
            cursor.execute("PRAGMA table_info(survey_tokens)")
            tokens_schema = cursor.fetchall()

        # Get users table schema
        cursor.execute("PRAGMA table_info(users)")
        users_schema = cursor.fetchall()

        # Get recent tokens
        recent_tokens = []
        if tokens_table_exists:
            cursor.execute("SELECT token, user_id, created_at, expires_at, is_used FROM survey_tokens ORDER BY created_at DESC LIMIT 5")
            recent_tokens = cursor.fetchall()

        # Get users data
        cursor.execute("SELECT * FROM users LIMIT 5")
        users_data = cursor.fetchall()

        return jsonify({
            'database_path': DB_PATH,
            'tables': tables,
            'survey_tokens_exists': tokens_table_exists,
            'survey_tokens_schema': tokens_schema,
            'users_schema': users_schema,
            'users_data': users_data,
            'recent_tokens': recent_tokens
        })
    except Exception as e:
        return jsonify({
            'error': str(e),
            'database_path': DB_PATH
        }), 500
    finally:
        conn.close()

@app.route('/debug/token/<token>')
def debug_token(token):
    """Debug a specific token"""
    token_info, error = get_survey_token_info(token)
    return jsonify({
        'token': token,
        'token_info': token_info,
        'error': error,
        'validation_successful': error is None
    })

@app.route('/test_survey_link')
def test_survey_link():
    """Generate a test survey link for testing purposes"""
    # Get or create a test user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check if test user exists
    cursor.execute('SELECT id FROM users WHERE phone = ?', ('test_user',))
    result = cursor.fetchone()

    if result:
        user_id = result[0]
    else:
        # Create test user
        cursor.execute('INSERT INTO users (phone) VALUES (?)', ('test_user',))
        user_id = cursor.lastrowid
        conn.commit()

    conn.close()

    # Create survey token
    token = create_survey_token(user_id, expires_hours=24)
    if token:
        base_url = os.getenv('BASE_URL', 'https://sms-survey-prototype-production.up.railway.app')
        survey_url = f"{base_url}/survey/{token}"
        return jsonify({
            'success': True,
            'survey_url': survey_url,
            'token': token,
            'expires_in_hours': 24,
            'message': 'Test survey link generated successfully!'
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Failed to create survey token'
        }), 500

# Feedback endpoint
@app.route('/feedback/<user_id>')

@app.route('/test_textbelt_webhook')
def test_textbelt_webhook():
    """Test TextBelt webhook with various phone number formats"""
    test_phone = request.args.get('phone', '5555555555')

    # Test different phone number formats
    formats_to_test = [
        test_phone,
        f"+1{test_phone}" if not test_phone.startswith('+') else test_phone,
        test_phone.replace('+1', '') if test_phone.startswith('+1') else test_phone,
        test_phone.replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
    ]

    results = []
    webhook_url = os.getenv('WEBHOOK_URL')

    for phone_format in formats_to_test:
        try:
            payload = {
                'phone': phone_format,
                'message': f'Webhook test to {phone_format}',
                'key': TEXTBELT_API_KEY + '_test',  # Use test mode
                'replyWebhookUrl': webhook_url
            }

            response = requests.post(TEXTBELT_URL, payload)
            result = response.json()

            results.append({
                'phone_format': phone_format,
                'success': result.get('success'),
                'error': result.get('error'),
                'textId': result.get('textId'),
                'quotaRemaining': result.get('quotaRemaining')
            })
        except Exception as e:
            results.append({
                'phone_format': phone_format,
                'success': False,
                'error': str(e)
            })

    return jsonify({
        'test_results': results,
        'webhook_url': webhook_url,
        'recommendation': 'Use the format that shows success=true for real SMS sending'
    })
def feedback(user_id):
    # ...existing code...
    return 'Feedback page (to be implemented)'

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
