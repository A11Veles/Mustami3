# Clean Call Center Agent Server with Firebase Authentication
import os
import sys
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import load_env_variable, ENV_VARS
from utils.firebase import firebase_auth, firebase_db
from utils.helpers import is_valid_google_drive_link, get_audio_file_identifier
from agents.master import process_single_audio

# Set static folder path
STATIC_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')
print(f"Static folder path: {STATIC_FOLDER}")
print(f"Static folder exists: {os.path.exists(STATIC_FOLDER)}")

# Initialize Flask app with static folder configuration
app = Flask(__name__, static_folder=STATIC_FOLDER, static_url_path='/static')
CORS(app)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = load_env_variable(ENV_VARS['JWT_SECRET_KEY'])
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
jwt = JWTManager(app)

# ============================================================================
# STATIC FILE SERVING
# ============================================================================

@app.route('/')
def serve_login():
    """Serve the login page."""
    return send_from_directory(STATIC_FOLDER, 'login.html')

@app.route('/upload')
def serve_upload():
    """Serve the upload page."""
    return send_from_directory(STATIC_FOLDER, 'upload.html')

@app.route('/dashboard')
def serve_dashboard():
    """Serve the dashboard UI (index2.html)."""
    return send_from_directory(STATIC_FOLDER, 'index2.html')

# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """User registration endpoint."""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'status': 'error', 
                'message': 'Email and password are required'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        display_name = data.get('displayName', email.split('@')[0])
        
        # Validate password strength
        if len(password) < 6:
            return jsonify({
                'status': 'error', 
                'message': 'Password must be at least 6 characters'
            }), 400
        
        # Create user account
        result = firebase_auth.create_user(email, password, display_name)
        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Registration failed: {str(e)}'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        data = request.get_json()
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({
                'status': 'error', 
                'message': 'Email and password are required'
            }), 400
        
        email = data.get('email')
        password = data.get('password')
        
        # Authenticate user
        result = firebase_auth.login_user(email, password)
        
        # Get user profile if login successful
        if result['status'] == 'success' and firebase_db.db:
            try:
                profile_result = firebase_db.get_user_profile(result['user']['uid'])
                if profile_result['status'] == 'success':
                    result['user']['profile'] = profile_result['profile']
            except Exception as e:
                print(f"Warning: Could not load user profile: {e}")
        
        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Login failed: {str(e)}'
        }), 500

@app.route('/api/auth/verify', methods=['GET'])
def verify_auth():
    """Verify current authentication status."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return jsonify({
            'status': 'error', 
            'message': 'Missing or invalid authorization header'
        }), 401
    
    token = auth_header.split(' ')[1]
    result = firebase_auth.verify_token(token)
    
    if result['status'] == 'success':
        return jsonify({
            'status': 'success',
            'user': {
                'uid': result['uid'],
                'email': result['email'],
                'email_verified': result['email_verified']
            }
        })
    else:
        return jsonify(result), 401

# ============================================================================
# USER PROFILE ROUTES
# ============================================================================

@app.route('/api/user/profile', methods=['GET'])
def get_profile():
    """Get user profile."""
    user = get_current_user_from_token()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        result = firebase_db.get_user_profile(user['uid'])
        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Failed to get profile: {str(e)}'
        }), 500

@app.route('/api/user/history', methods=['GET'])
def get_history():
    """Get user processing history."""
    user = get_current_user_from_token()
    if not user:
        return jsonify({'status': 'error', 'message': 'Unauthorized'}), 401
    
    try:
        limit = request.args.get('limit', 10, type=int)
        result = firebase_db.get_user_history(user['uid'], limit)
        status_code = 200 if result['status'] == 'success' else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({
            'status': 'error', 
            'message': f'Failed to get history: {str(e)}'
        }), 500

# ============================================================================
# AUDIO ANALYSIS ROUTES
# ============================================================================

@app.route('/api/analyze', methods=['POST'])
def analyze_audio():
    """Audio analysis endpoint with optional authentication."""
    print("🎯 Audio analysis request received")
    
    # Get current user (optional)
    user = get_current_user_from_token()
    
    try:
        # Validate request data
        if not request.is_json:
            return jsonify({
                'status': 'error', 
                'message': 'Request must be JSON'
            }), 400
        
        data = request.json
        if not data:
            return jsonify({
                'status': 'error', 
                'message': 'No data provided'
            }), 400
        
        drive_link = data.get('driveLink')
        custom_prompt = data.get('prompt')
        
        if not drive_link:
            return jsonify({
                'status': 'error', 
                'message': 'Google Drive link is required'
            }), 400
        
        # Validate Google Drive link
        if not is_valid_google_drive_link(drive_link):
            return jsonify({
                'status': 'error', 
                'message': 'Invalid Google Drive link format'
            }), 400
        
        # Check rate limits for authenticated users
        if user and firebase_db.db:
            if not check_user_rate_limit(user['uid']):
                return jsonify({
                    'status': 'error', 
                    'message': 'Rate limit exceeded. Please try again later.'
                }), 429
        
        print(f"🎯 Processing audio: {drive_link}")
        
        # Process audio file through master agent
        start_time = datetime.now()
        result = process_single_audio(drive_link, custom_prompt)
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # Add processing metadata
        result['processing_time'] = processing_time
        result['authenticated'] = user is not None
        result['timestamp'] = datetime.now().isoformat()
        
        # Save results for authenticated users
        if user and result.get('status') in ['completed', 'completed_with_errors']:
            save_user_processing_result(user['uid'], result, drive_link)
        
        print(f"✅ Processing completed in {processing_time:.2f}s with status: {result.get('status')}")
        
        return jsonify({
            'status': 'success',
            'analysis': result,
            'message': 'Audio processed successfully'
        })
        
    except Exception as e:
        print(f"❌ Analysis error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': f'Analysis failed: {str(e)}'
        }), 500

@app.route('/api/dashboard/data', methods=['GET'])
def get_dashboard_data():
    """Get formatted data for the dashboard UI (index2.html)."""
    print("🎯 Dashboard data request received")
    
    try:
        # Get the latest analysis result from query params or session
        # For now, we'll return mock data structure that matches what the UI expects
        # In production, you'd fetch this from database or session
        
        # This endpoint expects either:
        # 1. A file_id parameter to fetch specific analysis
        # 2. Or returns the most recent analysis for the user
        
        file_id = request.args.get('file_id')
        
        # TODO: Implement fetching from database
        # For now, return structure that matches the UI expectations
        
        return jsonify({
            'status': 'success',
            'message': 'Dashboard data endpoint ready. Pass analysis results from /api/analyze to populate the UI.',
            'data': {
                'call_summary': None,
                'call_transcript': None,
                'actionable_insights': None
            }
        })
        
    except Exception as e:
        print(f"❌ Dashboard data error: {str(e)}")
        return jsonify({
            'status': 'error', 
            'message': f'Failed to get dashboard data: {str(e)}'
        }), 500

# ============================================================================
# HEALTH CHECK ROUTES
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0.0',
        'features': {
            'authentication': True,
            'database': firebase_db.db is not None,
            'ai_processing': True,
            'dashboard': True
        }
    })

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_current_user_from_token():
    """Extract and verify user from authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    try:
        token = auth_header.split(' ')[1]
        result = firebase_auth.verify_token(token)
        
        if result['status'] == 'success':
            return {
                'uid': result['uid'],
                'email': result['email'],
                'email_verified': result['email_verified']
            }
    except Exception as e:
        print(f"Token verification error: {e}")
    
    return None

def check_user_rate_limit(uid: str) -> bool:
    """Check if user has exceeded rate limits."""
    try:
        # Simple rate limiting - get recent history
        result = firebase_db.get_user_history(uid, limit=20)
        
        if result['status'] != 'success':
            return True  # Allow if we can't check
        
        history = result.get('history', [])
        
        # Count requests in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        recent_requests = 0
        
        for record in history:
            try:
                record_time = datetime.fromisoformat(record['timestamp'].replace('Z', '+00:00'))
                if record_time > one_hour_ago:
                    recent_requests += 1
            except:
                continue
        
        # Allow up to 10 requests per hour for free users
        return recent_requests < 10
        
    except Exception as e:
        print(f"Rate limit check error: {e}")
        return True  # Allow if check fails

def save_user_processing_result(uid: str, result: dict, drive_link: str):
    """Save processing result to user's history."""
    try:
        if not firebase_db.db:
            return
        
        file_id = get_audio_file_identifier(drive_link)
        
        processing_data = {
            'audio_file_id': file_id,
            'audio_url': drive_link,
            'processing_type': 'full_analysis',
            'status': result.get('status', 'unknown'),
            'processing_time': result.get('processing_time', 0),
            'results': {
                'transcription': result.get('results', {}).get('transcription', {}),
                'summary': result.get('results', {}).get('summary', {}),
                'evaluation': result.get('results', {}).get('evaluation', {}),
                'recommendations': result.get('results', {}).get('recommendations', {}),
                'noise_analysis': result.get('results', {}).get('noise_analysis', {})
            },
            'errors': result.get('errors', []),
            'metadata': {
                'processing_summary': result.get('processing_summary', {}),
                'file_identifier': file_id
            }
        }
        
        save_result = firebase_db.save_processing_result(uid, processing_data)
        if save_result['status'] == 'success':
            print(f"💾 Results saved for user: {uid}")
        else:
            print(f"⚠️ Failed to save results: {save_result['message']}")
            
    except Exception as e:
        print(f"Error saving user results: {e}")

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'status': 'error', 'message': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'status': 'error', 'message': 'Internal server error'}), 500

@app.errorhandler(429)
def rate_limit_exceeded(error):
    return jsonify({'status': 'error', 'message': 'Rate limit exceeded'}), 429

# ============================================================================
# APPLICATION STARTUP
# ============================================================================

if __name__ == '__main__':
    print("🚀 Starting Clean Call Center Agent Server...")
    print("🔐 Authentication: Enabled")
    print("💾 Database: Firestore")
    print("🤖 AI Processing: Enabled")
    print("📊 Dashboard: Enabled at /dashboard")
    
    host = load_env_variable('HOST', default='0.0.0.0')
    port = int(load_env_variable('PORT', default='5000'))
    debug = load_env_variable('DEBUG', default='True').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)
