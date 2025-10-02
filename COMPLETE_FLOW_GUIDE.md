# Complete Application Flow Guide

## Overview

This guide explains the complete user flow from login to viewing analysis results in the Mustami3 AI Call Analysis Platform.

## Application Flow

```
Login Page (/) → Upload Page (/upload) → Dashboard (/dashboard)
```

## Pages

### 1. Login Page (`/` or `login.html`)
- **URL**: `http://localhost:5001/`
- **Purpose**: User authentication
- **Features**:
  - Email/password login
  - Holographic theme matching index2.html
  - Firebase authentication integration
  - Auto-redirect if already logged in
  - Stores auth token in localStorage

### 2. Upload Page (`/upload` or `upload.html`)
- **URL**: `http://localhost:5001/upload`
- **Purpose**: Audio file submission
- **Features**:
  - Google Drive link input
  - User info display with logout option
  - Loading overlay during processing
  - Auto-redirect to dashboard after analysis
  - Protected route (requires authentication)

### 3. Dashboard (`/dashboard` or `index2.html`)
- **URL**: `http://localhost:5001/dashboard`
- **Purpose**: Display analysis results
- **Features**:
  - Call Summary (from summary agent)
  - Call Transcript (from transcription agent)
  - AI-Generated Actionable Insights (from recommendation agent)
  - Beautiful holographic UI
  - Loads data from localStorage

## Complete User Journey

### Step 1: Login
1. User visits `http://localhost:5001/`
2. Enters email and password
3. Clicks "Sign In"
4. System authenticates via `/api/auth/login`
5. On success:
   - Auth token stored in localStorage
   - User redirected to `/upload`

### Step 2: Upload Audio
1. User arrives at `/upload` page
2. System checks authentication:
   - If not logged in → redirect to `/`
   - If logged in → show upload form
3. User enters Google Drive link
4. Clicks "Start Analysis"
5. System processes audio via `/api/analyze`:
   - Downloads audio from Google Drive
   - Runs transcription agent
   - Runs summary agent
   - Runs recommendation agent
   - Returns complete analysis
6. Analysis stored in localStorage
7. User redirected to `/dashboard`

### Step 3: View Results
1. User arrives at `/dashboard`
2. Dashboard loads analysis from localStorage
3. Three sections populated:
   - **Call Summary**: AI-generated summary of the call
   - **Call Transcript**: Full conversation with speaker labels
   - **Actionable Insights**: Recommendations for improvement

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/verify` - Verify token

### Analysis
- `POST /api/analyze` - Process audio file
  - Input: `{ "driveLink": "..." }`
  - Output: Complete analysis object

### Dashboard
- `GET /api/dashboard/data` - Fetch dashboard data (future)

## Data Flow

### Analysis Result Structure
```javascript
{
  "file_identifier": "string",
  "audio_url": "string",
  "status": "completed",
  "results": {
    "transcription": {
      "status": "success",
      "transcript": "Full transcript text..."
    },
    "summary": {
      "status": "success",
      "summary": "Summary text..."
    },
    "recommendations": {
      "status": "success",
      "recommendations": "Recommendations text..."
    }
  }
}
```

### localStorage Keys
- `authToken` - JWT authentication token
- `currentUser` - User information object
- `latestAnalysis` - Most recent analysis results

## Authentication Flow

1. **Login**:
   ```javascript
   POST /api/auth/login
   Body: { email, password }
   Response: { status, user: { token, email, uid } }
   ```

2. **Token Storage**:
   ```javascript
   localStorage.setItem('authToken', token);
   localStorage.setItem('currentUser', JSON.stringify(user));
   ```

3. **Protected Requests**:
   ```javascript
   headers: {
     'Authorization': `Bearer ${authToken}`
   }
   ```

## Testing the Complete Flow

### 1. Start the Server
```bash
cd server
python app.py
```

Server will start on port 5001 (as configured in .env)

### 2. Access Login Page
Navigate to: `http://localhost:5001/`

### 3. Login
Use existing Firebase credentials or create a new account

### 4. Upload Audio
1. After login, you'll be at `/upload`
2. Enter a Google Drive link (must be publicly accessible)
3. Click "Start Analysis"
4. Wait for processing (may take 1-2 minutes)

### 5. View Dashboard
1. Automatically redirected to `/dashboard`
2. View the three main sections:
   - Call Summary
   - Call Transcript
   - AI-Generated Actionable Insights

## Troubleshooting

### Port Already in Use
If port 5001 is in use, modify `.env`:
```
PORT=5002
```

### Login Fails
- Check Firebase configuration in `.env`
- Verify Firebase service account JSON file exists
- Check console for error messages

### Upload Page Shows "Not Logged In"
- Clear localStorage and login again
- Check if auth token is valid

### Dashboard Shows No Data
- Check browser console for errors
- Verify localStorage has `latestAnalysis` key
- Ensure analysis completed successfully

### Analysis Takes Too Long
- Check Google Drive link is valid and public
- Verify OpenAI API key is configured
- Check server logs for processing status

## Security Notes

1. **Authentication**: Uses Firebase Authentication
2. **Authorization**: JWT tokens with 24-hour expiration
3. **Rate Limiting**: 10 requests per hour for authenticated users
4. **Data Storage**: Analysis results saved to Firestore for authenticated users

## Environment Variables

Required in `.env`:
```
OPENAI_API_KEY=your-key
FIREBASE_API_KEY=your-key
FIREBASE_AUTH_DOMAIN=your-domain
FIREBASE_PROJECT_ID=your-project
FIREBASE_STORAGE_BUCKET=your-bucket
FIREBASE_MESSAGING_SENDER_ID=your-id
FIREBASE_APP_ID=your-app-id
FIREBASE_DATABASE_URL=your-url
FIREBASE_SERVICE_ACCOUNT_PATH=./path-to-json
JWT_SECRET_KEY=your-secret
PORT=5001
HOST=0.0.0.0
```

## Features Summary

### ✅ Implemented
- Login page with holographic theme
- Upload page with holographic theme
- Dashboard with three linked sections
- Firebase authentication
- Audio processing pipeline
- localStorage persistence
- Auto-redirects based on auth state
- Loading states and error handling

### ⚠️ Static (Not Linked to Agents)
- Overall Score Gauge
- Sentiment Timeline Chart
- Talk Time Distribution
- Compliance Checklist
- Noise Level Chart
- Audio Waveform
- Call Topics
- Keyword Cloud

These can be enhanced in future iterations using data from evaluation and noise analysis agents.

## Next Steps

1. **Test with Real Audio**: Upload actual call recordings
2. **Verify Agent Outputs**: Check that all three sections display correctly
3. **Monitor Performance**: Check processing times and error rates
4. **User Feedback**: Gather feedback on UI/UX
5. **Enhance Features**: Add more agent data to static sections

## Support

For issues or questions:
1. Check server logs for errors
2. Check browser console for client-side errors
3. Verify all environment variables are set
4. Ensure Firebase and OpenAI services are accessible

## Quick Start Commands

```bash
# Navigate to server directory
cd server

# Start the application
python app.py

# Access in browser
# Login: http://localhost:5001/
# Upload: http://localhost:5001/upload
# Dashboard: http://localhost:5001/dashboard
```

The application is now ready for testing!
