# Firebase utilities for Call Center Agent
import os
import json
import firebase_admin
from firebase_admin import credentials, firestore, auth
import pyrebase
from datetime import datetime
from typing import Dict, Any, Optional

from config.settings import load_env_variable, ENV_VARS, BASE_DIR

class FirebaseAuth:
    """Firebase Authentication handler."""
    
    def __init__(self):
        self.pyrebase_app = None
        self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialize Firebase services."""
        try:
            # Initialize Firebase Admin SDK
            self._init_admin_sdk()
            
            # Initialize Pyrebase for client auth
            self._init_pyrebase()
            
        except Exception as e:
            print(f"Warning: Firebase initialization failed: {e}")
    
    def _init_admin_sdk(self):
        """Initialize Firebase Admin SDK."""
        try:
            service_account_path = load_env_variable(ENV_VARS['FIREBASE_SERVICE_ACCOUNT_PATH'])
            project_id = load_env_variable(ENV_VARS['FIREBASE_PROJECT_ID'], required=True)

            # Resolve the service account path relative to BASE_DIR
            if service_account_path:
                if service_account_path.startswith('./'):
                    # Remove leading ./ and resolve relative to BASE_DIR
                    relative_path = service_account_path[2:]
                    absolute_path = BASE_DIR / relative_path
                    service_account_path = str(absolute_path)
                elif not os.path.isabs(service_account_path):
                    # If it's a relative path without ./, resolve relative to BASE_DIR
                    absolute_path = BASE_DIR / service_account_path
                    service_account_path = str(absolute_path)

            if service_account_path and os.path.exists(service_account_path):
                cred = credentials.Certificate(service_account_path)
                firebase_admin.initialize_app(cred, {'projectId': project_id})
                print(f"✅ Firebase Admin SDK initialized with service account")
            else:
                # Try default credentials
                firebase_admin.initialize_app(options={'projectId': project_id})
                print(f"✅ Firebase Admin SDK initialized with default credentials")

        except Exception as e:
            print(f"⚠️  Firebase Admin SDK initialization failed: {e}")
    
    def _init_pyrebase(self):
        """Initialize Pyrebase for client authentication."""
        try:
            config = {
                "apiKey": load_env_variable(ENV_VARS['FIREBASE_API_KEY'], required=True),
                "authDomain": load_env_variable(ENV_VARS['FIREBASE_AUTH_DOMAIN'], required=True),
                "projectId": load_env_variable(ENV_VARS['FIREBASE_PROJECT_ID'], required=True),
                "storageBucket": load_env_variable(ENV_VARS['FIREBASE_STORAGE_BUCKET'], required=True),
                "messagingSenderId": load_env_variable(ENV_VARS['FIREBASE_MESSAGING_SENDER_ID'], required=True),
                "appId": load_env_variable(ENV_VARS['FIREBASE_APP_ID'], required=True),
                "databaseURL": load_env_variable(ENV_VARS['FIREBASE_DATABASE_URL'])
            }
            
            self.pyrebase_app = pyrebase.initialize_app(config)
            print("✅ Pyrebase initialized successfully")
            
        except Exception as e:
            print(f"⚠️  Pyrebase initialization failed: {e}")
    
    def create_user(self, email: str, password: str, display_name: str = None) -> Dict[str, Any]:
        """Create a new user account."""
        try:
            if not self.pyrebase_app:
                return {"status": "error", "message": "Firebase not initialized"}
            
            auth_client = self.pyrebase_app.auth()
            user = auth_client.create_user_with_email_and_password(email, password)
            
            # Send email verification
            auth_client.send_email_verification(user['idToken'])
            
            return {
                "status": "success",
                "message": "User created successfully. Please verify your email.",
                "user": {
                    "uid": user['localId'],
                    "email": email,
                    "email_verified": False
                }
            }
            
        except Exception as e:
            error_message = str(e)
            if "EMAIL_EXISTS" in error_message:
                return {"status": "error", "message": "Email already exists"}
            elif "WEAK_PASSWORD" in error_message:
                return {"status": "error", "message": "Password is too weak"}
            elif "INVALID_EMAIL" in error_message:
                return {"status": "error", "message": "Invalid email format"}
            else:
                return {"status": "error", "message": f"Registration failed: {error_message}"}
    
    def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user with email and password."""
        try:
            if not self.pyrebase_app:
                return {"status": "error", "message": "Firebase not initialized"}
            
            auth_client = self.pyrebase_app.auth()
            user = auth_client.sign_in_with_email_and_password(email, password)
            
            return {
                "status": "success",
                "message": "Login successful",
                "user": {
                    "uid": user['localId'],
                    "email": user['email'],
                    "email_verified": user.get('emailVerified', False),
                    "token": user['idToken'],
                    "refresh_token": user['refreshToken']
                }
            }
            
        except Exception as e:
            error_message = str(e)
            if "INVALID_PASSWORD" in error_message:
                return {"status": "error", "message": "Invalid password"}
            elif "EMAIL_NOT_FOUND" in error_message:
                return {"status": "error", "message": "Email not found"}
            elif "USER_DISABLED" in error_message:
                return {"status": "error", "message": "User account is disabled"}
            else:
                return {"status": "error", "message": f"Login failed: {error_message}"}
    
    def verify_token(self, id_token: str) -> Dict[str, Any]:
        """Verify Firebase ID token."""
        try:
            decoded_token = auth.verify_id_token(id_token)
            return {
                "status": "success",
                "uid": decoded_token['uid'],
                "email": decoded_token.get('email'),
                "email_verified": decoded_token.get('email_verified', False)
            }
        except Exception as e:
            return {"status": "error", "message": f"Token verification failed: {str(e)}"}
    
    def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Firebase token."""
        try:
            if not self.pyrebase_app:
                return {"status": "error", "message": "Firebase not initialized"}
            
            auth_client = self.pyrebase_app.auth()
            user = auth_client.refresh(refresh_token)
            
            return {
                "status": "success",
                "token": user['idToken'],
                "refresh_token": user['refreshToken']
            }
        except Exception as e:
            return {"status": "error", "message": f"Token refresh failed: {str(e)}"}


class FirebaseDatabase:
    """Firebase Firestore database handler."""
    
    def __init__(self):
        self.db = None
        self.initialize_db()
    
    def initialize_db(self):
        """Initialize Firestore database."""
        try:
            self.db = firestore.client()
            # Test connection
            test_doc = self.db.collection('_test').document('connection')
            test_doc.set({'timestamp': datetime.now(), 'test': True}, merge=True)
            print("✅ Firestore client initialized and connection verified")
        except Exception as e:
            print(f"⚠️  Failed to initialize Firestore: {e}")
            self.db = None
    
    def save_processing_result(self, uid: str, processing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save audio processing result to user's history."""
        try:
            if not self.db:
                return {"status": "error", "message": "Database not initialized"}
            
            processing_record = {
                'uid': uid,
                'audio_file_id': processing_data.get('audio_file_id'),
                'audio_url': processing_data.get('audio_url'),
                'processing_type': processing_data.get('processing_type', 'audio_analysis'),
                'results': processing_data.get('results', {}),
                'timestamp': datetime.now(),
                'status': processing_data.get('status', 'completed'),
                'processing_time': processing_data.get('processing_time', 0),
                'file_size': processing_data.get('file_size', 0),
                'metadata': processing_data.get('metadata', {})
            }
            
            # Add to processing history
            doc_ref = self.db.collection('processing_history').add(processing_record)
            
            # Update user usage stats
            user_ref = self.db.collection('users').document(uid)
            user_ref.update({
                'usage_stats.files_processed': firestore.Increment(1),
                'usage_stats.total_processing_time': firestore.Increment(processing_record['processing_time']),
                'usage_stats.last_activity': datetime.now()
            })
            
            return {
                "status": "success",
                "message": "Processing result saved",
                "document_id": doc_ref[1].id
            }
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to save result: {str(e)}"}
    
    def get_user_history(self, uid: str, limit: int = 10) -> Dict[str, Any]:
        """Get user's processing history."""
        try:
            if not self.db:
                return {"status": "error", "message": "Database not initialized"}
            
            query = (self.db.collection('processing_history')
                    .where('uid', '==', uid)
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit))
            
            docs = query.stream()
            history = []
            for doc in docs:
                record = doc.to_dict()
                record['id'] = doc.id
                if 'timestamp' in record:
                    record['timestamp'] = record['timestamp'].isoformat()
                history.append(record)
            
            return {"status": "success", "history": history}
            
        except Exception as e:
            return {"status": "error", "message": f"Failed to get history: {str(e)}"}
    
    def get_user_profile(self, uid: str) -> Dict[str, Any]:
        """Get user profile data."""
        try:
            if not self.db:
                return {"status": "error", "message": "Database not initialized"}
            
            user_doc = self.db.collection('users').document(uid).get()
            if user_doc.exists:
                profile = user_doc.to_dict()
                if 'created_at' in profile:
                    profile['created_at'] = profile['created_at'].isoformat()
                if 'usage_stats' in profile and 'last_activity' in profile['usage_stats']:
                    profile['usage_stats']['last_activity'] = profile['usage_stats']['last_activity'].isoformat()
                
                return {"status": "success", "profile": profile}
            else:
                return {"status": "error", "message": "User profile not found"}
                
        except Exception as e:
            return {"status": "error", "message": f"Failed to get profile: {str(e)}"}


# Global instances
firebase_auth = FirebaseAuth()
firebase_db = FirebaseDatabase()
