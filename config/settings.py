# Configuration settings for Call Center Agent
import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Load environment variables from .env file
load_dotenv(BASE_DIR / '.env')

# Output directory for processed files
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(exist_ok=True)

# Audio processing constants
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac']
DEFAULT_AUDIO_EXTENSION = '.wav'

# OpenAI Configuration
OPENAI_MODELS = {
    'TRANSCRIPTION': 'gpt-4o-mini-transcribe',
    'SUMMARY': 'gpt-4o-mini',
    'EVALUATION': 'gpt-4o-mini',
    'RECOMMENDATION': 'gpt-4o-mini'
}

# Processing constants
MAX_TOKEN_LIMITS = {
    'SUMMARY': 1000,
    'EVALUATION': 1500,
    'RECOMMENDATION': 1200
}

TEMPERATURE_SETTINGS = {
    'TRANSCRIPTION': 0.2,
    'SUMMARY': 0.3,
    'EVALUATION': 0.1,
    'RECOMMENDATION': 0.3
}

# Environment variable names
ENV_VARS = {
    'OPENAI_API_KEY': 'OPENAI_API_KEY',
    'HUGGINGFACE_TOKEN': 'HUGGINGFACE_TOKEN',
    'JWT_SECRET_KEY': 'JWT_SECRET_KEY',
    
    # Firebase config
    'FIREBASE_API_KEY': 'FIREBASE_API_KEY',
    'FIREBASE_AUTH_DOMAIN': 'FIREBASE_AUTH_DOMAIN',
    'FIREBASE_PROJECT_ID': 'FIREBASE_PROJECT_ID',
    'FIREBASE_STORAGE_BUCKET': 'FIREBASE_STORAGE_BUCKET',
    'FIREBASE_MESSAGING_SENDER_ID': 'FIREBASE_MESSAGING_SENDER_ID',
    'FIREBASE_APP_ID': 'FIREBASE_APP_ID',
    'FIREBASE_DATABASE_URL': 'FIREBASE_DATABASE_URL',
    'FIREBASE_SERVICE_ACCOUNT_PATH': 'FIREBASE_SERVICE_ACCOUNT_PATH'
}

# Default values for environment variables
ENV_DEFAULTS = {
    'JWT_SECRET_KEY': 'your-secret-key-change-this',
    'FIREBASE_DATABASE_URL': '',
    'FIREBASE_SERVICE_ACCOUNT_PATH': 'firebase-service-account.json'
}

# System prompts for AI agents
SYSTEM_PROMPTS = {
    'SUMMARY': """You are the Format/Summary Agent in a Call Center Evaluation Framework. You receive the raw audio transcription of a customer service call. Your job is to:

a) Summarize the call professionally and clearly in Arabic language.
b) Focus on the **main purpose** of the call, the **key events**, and the **final outcome**.
c) Ensure the summary is understandable without listening to the original call or seeing the full transcript.
d) Avoid speculation or opinion — use only what is explicitly present in the transcript.
e) Maintain a neutral and professional tone suitable for stakeholders, team leads, or quality control analysts.

Summary Guidelines:
- Keep it concise but comprehensive
- Use bullet points or structured formatting to enhance readability when possible.
- Do **not mimic the flow of the conversation**; instead, extract **issues**, **resolutions**, and **noteworthy moments**.
- Highlight any products/services mentioned, customer frustrations, or special requests. If none exist, don't mention them

Please provide the summary in Arabic as requested.""",

    'EVALUATION': """You are the Evaluation Agent in a Call Center Quality Assurance Framework. You receive a formatted transcript of a customer service call. Your job is to evaluate the call across multiple dimensions and provide scores.

Evaluation Criteria (score each from 1-10):
1. **Communication Clarity**: How clear and understandable was the agent's communication?
2. **Problem Resolution**: How effectively was the customer's issue resolved?
3. **Professionalism**: How professional and courteous was the agent?
4. **Customer Satisfaction**: How satisfied did the customer appear to be?
5. **Process Adherence**: How well did the agent follow proper procedures?

Additional Analysis:
- **Complaint Detected**: Was there a customer complaint? (Yes/No)
- **Issue Category**: What type of issue was discussed?
- **Resolution Status**: Was the issue fully resolved?

Provide your evaluation in structured JSON format with scores and explanations.""",

    'RECOMMENDATION': """You are the Recommendation Agent in a Call Center Quality Improvement Framework. Based on the call transcript and evaluation results, provide actionable recommendations for improvement.

Focus Areas:
1. **Communication Improvements**: Specific ways to enhance agent communication
2. **Process Improvements**: Suggestions for better procedures or workflows  
3. **Training Recommendations**: Areas where additional training might help
4. **System Improvements**: Any technical or procedural system changes needed

Guidelines:
- Be specific and actionable
- Prioritize recommendations by impact
- Consider both agent performance and system/process issues
- Provide recommendations in Arabic
- Focus on constructive feedback that leads to measurable improvements

Format your recommendations clearly with priority levels (High/Medium/Low)."""
}

# Rate limiting configuration
RATE_LIMITS = {
    'FREE_TIER': {
        'REQUESTS_PER_HOUR': 10,
        'REQUESTS_PER_DAY': 50
    },
    'PREMIUM_TIER': {
        'REQUESTS_PER_HOUR': 100,
        'REQUESTS_PER_DAY': 500
    }
}

# File naming patterns
FILE_PATTERNS = {
    'TRANSCRIPT': '{file_id}_formatted_transcript.txt',
    'SUMMARY': '{file_id}_summary_report.txt', 
    'EVALUATION_JSON': '{file_id}_evaluation_report.json',
    'EVALUATION_TXT': '{file_id}_evaluation_report.txt',
    'RECOMMENDATIONS': '{file_id}_recommendations.txt',
    'NOISE_JSON': '{file_id}_noise_report.json'
}

def load_env_variable(var_name: str, required: bool = False, default: str = None) -> str:
    """Load environment variable with fallback to default."""
    value = os.getenv(var_name, default or ENV_DEFAULTS.get(var_name))
    
    if required and not value:
        raise ValueError(f"Required environment variable {var_name} is not set")
        
    return value

def get_file_path(pattern_key: str, file_id: str) -> Path:
    """Get full file path for a given pattern and file ID."""
    filename = FILE_PATTERNS[pattern_key].format(file_id=file_id)
    return OUTPUTS_DIR / filename
