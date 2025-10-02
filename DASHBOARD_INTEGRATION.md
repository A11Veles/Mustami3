# Dashboard Integration Guide

## Overview

This document explains how the new dashboard UI (index2.html) is integrated with the existing Mustami3 agents to display call analysis results.

## Architecture

### Components

1. **Server Routes** (`server/app.py`)
   - `/dashboard` - Serves the index2.html dashboard UI
   - `/api/analyze` - Processes audio files and returns analysis results
   - `/api/dashboard/data` - Endpoint for fetching dashboard data (future enhancement)

2. **Dashboard UI** (`static/index2.html`)
   - Beautiful holographic-themed dashboard
   - Three main sections linked to agents:
     - **Call Summary** → Summary Agent
     - **Call Transcript** → Transcription Agent
     - **AI-Generated Actionable Insights** → Recommendation Agent

3. **Integration Script** (`static/dashboard.js`)
   - Handles data mapping between agents and UI
   - Provides API for loading analysis results
   - Manages localStorage for data persistence

## Agent Mapping

### 1. Call Summary Section
- **Agent**: `agents/summary.py`
- **Output Field**: `results.summary.summary`
- **UI Element**: `.summary-text` paragraph
- **Description**: Displays the AI-generated summary of the call

### 2. Call Transcript Section
- **Agent**: `agents/transcription.py`
- **Output Field**: `results.transcription.transcript`
- **UI Element**: `#transcriptContent` div
- **Description**: Displays the full conversation with speaker identification and timestamps

### 3. AI-Generated Actionable Insights Section
- **Agent**: `agents/recommendation.py`
- **Output Field**: `results.recommendations.recommendations`
- **UI Element**: `.insight-card .insight-content p`
- **Description**: Displays actionable recommendations for improvement

## Usage

### Method 1: Direct API Integration

After processing an audio file through `/api/analyze`, you can load the results into the dashboard:

```javascript
// After getting analysis results from /api/analyze
fetch('/api/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ driveLink: 'your-google-drive-link' })
})
.then(response => response.json())
.then(data => {
    if (data.status === 'success') {
        // Store the analysis data
        window.DashboardAPI.storeData(data.analysis);
        
        // Redirect to dashboard
        window.location.href = '/dashboard';
    }
});
```

### Method 2: Using the Dashboard API

The dashboard provides a global API accessible via `window.DashboardAPI`:

```javascript
// Load data into dashboard
window.DashboardAPI.loadData(analysisData);

// Fetch data from server
const data = await window.DashboardAPI.fetchData(fileId);

// Store data in localStorage
window.DashboardAPI.storeData(analysisData);

// Get current loaded data
const currentData = window.DashboardAPI.getCurrentData();
```

### Method 3: URL Parameters

You can pass a file ID via URL to load specific analysis:

```
http://localhost:5000/dashboard?file_id=your-file-id
```

### Method 4: localStorage

The dashboard automatically checks localStorage for the most recent analysis on page load.

## Data Structure

The expected analysis data structure:

```javascript
{
    "file_identifier": "string",
    "audio_url": "string",
    "status": "completed",
    "results": {
        "transcription": {
            "status": "success",
            "transcript": "Full transcript text...",
            "transcript_path": "/path/to/transcript.txt"
        },
        "summary": {
            "status": "success",
            "summary": "Summary text...",
            "summary_path": "/path/to/summary.txt"
        },
        "recommendations": {
            "status": "success",
            "recommendations": "Recommendations text...",
            "recommendations_path": "/path/to/recommendations.txt"
        }
    }
}
```

## Testing

### 1. Start the Server

```bash
cd server
python app.py
```

### 2. Access the Dashboard

Navigate to: `http://localhost:5000/dashboard`

### 3. Test with Sample Data

Open browser console and run:

```javascript
// Sample test data
const testData = {
    results: {
        summary: {
            status: 'success',
            summary: 'This is a test summary of the call.'
        },
        transcription: {
            status: 'success',
            transcript: 'Agent: Hello, how can I help you?\nCustomer: I need assistance with my account.'
        },
        recommendations: {
            status: 'success',
            recommendations: 'Agent should improve greeting protocol and follow up procedures.'
        }
    }
};

// Load the test data
window.DashboardAPI.loadData(testData);
```

## Integration Workflow

### Complete Flow

1. **User uploads audio** → `/api/analyze` endpoint
2. **Master agent processes** → Runs all agents (transcription, summary, recommendations)
3. **Results returned** → Complete analysis object
4. **Store in localStorage** → For persistence
5. **Redirect to dashboard** → `/dashboard` route
6. **Dashboard loads data** → From localStorage or URL params
7. **UI populates** → Three sections filled with agent results

### Example Integration Code

```javascript
// In your main application
async function processAndShowDashboard(driveLink) {
    try {
        // Step 1: Analyze audio
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ driveLink })
        });
        
        const result = await response.json();
        
        if (result.status === 'success') {
            // Step 2: Store results
            localStorage.setItem('latestAnalysis', JSON.stringify(result.analysis));
            
            // Step 3: Navigate to dashboard
            window.location.href = '/dashboard';
        }
    } catch (error) {
        console.error('Error:', error);
    }
}
```

## Features

### Current Features
- ✅ Call Summary display from summary agent
- ✅ Call Transcript display from transcription agent
- ✅ Actionable Insights display from recommendation agent
- ✅ Automatic speaker detection (Agent/Customer)
- ✅ Timestamp estimation for transcript lines
- ✅ localStorage persistence
- ✅ URL parameter support for specific file loading

### Not Implemented (Static UI Elements)
- ⚠️ Overall Score Gauge (static)
- ⚠️ Sentiment Timeline Chart (static)
- ⚠️ Talk Time Distribution (static)
- ⚠️ Compliance Checklist (static)
- ⚠️ Noise Level Chart (static)
- ⚠️ Audio Waveform (static)
- ⚠️ Call Topics (static)
- ⚠️ Keyword Cloud (static)

These elements display mock data and can be enhanced in future iterations to use data from evaluation and noise analysis agents.

## Notes

- The integration focuses on the three main sections as requested
- No fallbacks or agent logic modifications were made
- The dashboard gracefully handles missing data by showing warnings in console
- All agent outputs are mapped directly to UI without transformation
- The system preserves the original agent logic and only links results to display

## Future Enhancements

1. Implement `/api/dashboard/data` endpoint to fetch from database
2. Add real-time updates via WebSocket
3. Integrate evaluation agent data for compliance checklist
4. Integrate noise analysis agent data for noise level chart
5. Add export functionality for reports
6. Implement user authentication for dashboard access

## Troubleshooting

### Dashboard shows no data
- Check browser console for errors
- Verify localStorage has data: `localStorage.getItem('latestAnalysis')`
- Ensure analysis was successful before redirecting

### Transcript not displaying correctly
- Verify transcript format includes speaker labels (Agent:/Customer:)
- Check that transcript data exists in results object

### Summary or Insights not showing
- Confirm agent status is 'success' in results
- Check that the text fields are not empty
- Verify the correct CSS selectors are being used

## Support

For issues or questions, please refer to the main project documentation or contact the development team.
