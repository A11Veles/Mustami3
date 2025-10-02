// Dashboard Data Integration Script
// Links agent results to index2.html UI sections

// Store the current analysis data
let currentAnalysisData = null;

/**
 * Load analysis data and populate the dashboard
 * This function should be called when the page loads or when new analysis is available
 */
async function loadDashboardData(analysisData) {
    console.log('📊 Loading dashboard data...', analysisData);
    
    if (!analysisData || !analysisData.results) {
        console.error('Invalid analysis data provided:', analysisData);
        return;
    }
    
    currentAnalysisData = analysisData;
    
    console.log('📝 Summary data:', analysisData.results.summary);
    console.log('🗣️ Transcription data:', analysisData.results.transcription);
    console.log('💡 Recommendations data:', analysisData.results.recommendations);
    
    // Populate the three main sections
    populateCallSummary(analysisData.results.summary);
    populateCallTranscript(analysisData.results.transcription);
    populateActionableInsights(analysisData.results.recommendations);
    
    console.log('✅ Dashboard data loaded successfully');
}

/**
 * Populate Call Summary section
 * Maps to: summary agent output
 */
function populateCallSummary(summaryData) {
    if (!summaryData || summaryData.status !== 'success') {
        console.warn('Summary data not available');
        return;
    }
    
    const summaryElement = document.querySelector('.summary-text');
    if (summaryElement && summaryData.summary) {
        summaryElement.textContent = summaryData.summary;
        console.log('✅ Call Summary populated');
    }
}

/**
 * Populate Call Transcript section
 * Maps to: transcription agent output
 */
function populateCallTranscript(transcriptionData) {
    if (!transcriptionData || transcriptionData.status !== 'success') {
        console.warn('Transcription data not available');
        return;
    }
    
    const transcriptContent = document.getElementById('transcriptContent');
    if (!transcriptContent || !transcriptionData.transcript) {
        return;
    }
    
    // Clear existing content
    transcriptContent.innerHTML = '';
    
    // Parse the transcript text into lines
    const transcript = transcriptionData.transcript;
    const lines = transcript.split('\n').filter(line => line.trim());
    
    // Create transcript line elements
    lines.forEach((line, index) => {
        const trimmedLine = line.trim();
        if (!trimmedLine) return;
        
        // Detect speaker (Callcenter/Agent or Patient/Customer)
        let speaker = 'agent';
        let speakerLabel = 'Agent';
        let text = trimmedLine;
        
        // Check for different speaker patterns
        if (trimmedLine.toLowerCase().includes('callcenter:') || 
            trimmedLine.toLowerCase().includes('agent:')) {
            speaker = 'agent';
            speakerLabel = 'Agent';
            text = trimmedLine.split(':').slice(1).join(':').trim();
        } else if (trimmedLine.toLowerCase().includes('patient:') || 
                   trimmedLine.toLowerCase().includes('customer:')) {
            speaker = 'customer';
            speakerLabel = 'Customer';
            text = trimmedLine.split(':').slice(1).join(':').trim();
        }
        
        // Create transcript line element
        const lineDiv = document.createElement('div');
        lineDiv.className = `transcript-line ${speaker}`;
        
        // Estimate time based on line index (rough approximation)
        const estimatedTime = formatTime(index * 15); // ~15 seconds per exchange
        
        lineDiv.innerHTML = `
            <span class="transcript-time">${estimatedTime}</span>
            <span class="transcript-speaker">(${speakerLabel}):</span>
            <span class="transcript-text">${text}</span>
        `;
        
        transcriptContent.appendChild(lineDiv);
    });
    
    console.log('✅ Call Transcript populated');
}

/**
 * Populate AI-Generated Actionable Insights section
 * Maps to: recommendation agent output
 */
function populateActionableInsights(recommendationsData) {
    if (!recommendationsData || recommendationsData.status !== 'success') {
        console.warn('Recommendations data not available');
        return;
    }
    
    // Find the insights card content - look for the paragraph in the Actionable Insights section
    const insightsSection = Array.from(document.querySelectorAll('.glass-card')).find(card => {
        const title = card.querySelector('.section-title');
        return title && title.textContent.includes('AI-Generated Actionable Insights');
    });
    
    if (insightsSection && recommendationsData.recommendations) {
        const insightParagraph = insightsSection.querySelector('.insight-card .insight-content p');
        if (insightParagraph) {
            // Replace the entire content with the recommendations
            insightParagraph.innerHTML = `<strong class="text-purple-300">Recommendation:</strong> ${recommendationsData.recommendations}`;
            console.log('✅ Actionable Insights populated');
        }
    }
}

/**
 * Format seconds into MM:SS format
 */
function formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

/**
 * Fetch analysis data from the server
 * This can be called with a file_id to load specific analysis
 */
async function fetchAnalysisData(fileId = null) {
    try {
        const url = fileId 
            ? `/api/dashboard/data?file_id=${fileId}`
            : '/api/dashboard/data';
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.status === 'success' && data.data) {
            return data.data;
        } else {
            console.warn('No analysis data available from server');
            return null;
        }
    } catch (error) {
        console.error('Error fetching analysis data:', error);
        return null;
    }
}

/**
 * Initialize dashboard with data from URL parameters or localStorage
 */
function initializeDashboard() {
    console.log('🚀 Initializing dashboard...');
    
    // Check if analysis data is passed via URL parameters
    const urlParams = new URLSearchParams(window.location.search);
    const fileId = urlParams.get('file_id');
    
    console.log('🔍 URL file_id parameter:', fileId);
    
    if (fileId) {
        console.log('📥 Fetching data for file_id:', fileId);
        // Fetch data for specific file
        fetchAnalysisData(fileId).then(data => {
            if (data) {
                loadDashboardData(data);
            } else {
                console.warn('⚠️ No data returned from server for file_id:', fileId);
            }
        });
    } else {
        console.log('💾 Checking localStorage for analysis data...');
        // Check localStorage for recent analysis
        const storedData = localStorage.getItem('latestAnalysis');
        console.log('💾 localStorage data exists:', !!storedData);
        
        if (storedData) {
            console.log('💾 Raw localStorage data length:', storedData.length);
            try {
                const analysisData = JSON.parse(storedData);
                console.log('💾 Parsed analysis data:', analysisData);
                console.log('💾 Has results?', !!analysisData.results);
                console.log('💾 Results keys:', analysisData.results ? Object.keys(analysisData.results) : 'N/A');
                loadDashboardData(analysisData);
            } catch (error) {
                console.error('❌ Error parsing stored analysis data:', error);
                console.error('❌ Raw data that failed to parse:', storedData.substring(0, 200));
            }
        } else {
            console.warn('⚠️ No analysis data found in localStorage');
            console.log('💡 Tip: Make sure to upload and process an audio file first');
        }
    }
}

/**
 * Store analysis data in localStorage for persistence
 */
function storeAnalysisData(analysisData) {
    try {
        localStorage.setItem('latestAnalysis', JSON.stringify(analysisData));
        console.log('✅ Analysis data stored in localStorage');
    } catch (error) {
        console.error('Error storing analysis data:', error);
    }
}

/**
 * Public API for external scripts to load data
 */
window.DashboardAPI = {
    loadData: loadDashboardData,
    fetchData: fetchAnalysisData,
    storeData: storeAnalysisData,
    getCurrentData: () => currentAnalysisData
};

// Initialize dashboard when DOM is ready
console.log('🔧 Dashboard script starting...');
console.log('🔧 Document ready state:', document.readyState);

if (document.readyState === 'loading') {
    console.log('🔧 Waiting for DOMContentLoaded...');
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🔧 DOMContentLoaded fired!');
        initializeDashboard();
    });
} else {
    console.log('🔧 DOM already loaded, initializing immediately...');
    initializeDashboard();
}

console.log('📊 Dashboard integration script loaded');
