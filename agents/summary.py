# Summary Generation Agent
import os
from datetime import datetime
from openai import OpenAI
from typing import Dict, Any, Optional

from config.settings import (
    load_env_variable, ENV_VARS, OPENAI_MODELS,
    TEMPERATURE_SETTINGS, MAX_TOKEN_LIMITS, SYSTEM_PROMPTS,
    get_file_path
)
from utils.helpers import get_audio_file_identifier, clean_text_for_processing

class SummaryAgent:
    """Generates professional summaries of call center conversations."""
    
    def __init__(self):
        self.client = None
        self.initialize_openai()
    
    def initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = load_env_variable(ENV_VARS['OPENAI_API_KEY'], required=True)
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for summary generation")
        else:
            print("⚠️  OpenAI API key not found")
    
    def generate_summary(self, transcript_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Generate summary from transcript file."""
        if not self.client:
            return {
                "status": "error",
                "error_message": "OpenAI client not initialized"
            }
        
        # Validate transcript file
        if not os.path.exists(transcript_path):
            return {
                "status": "error", 
                "error_message": f"Transcript file not found: {transcript_path}"
            }
        
        file_id = get_audio_file_identifier(audio_url, transcript_path)
        
        try:
            # Read transcript
            with open(transcript_path, 'r', encoding='utf-8') as f:
                transcript = f.read()
            
            if not transcript.strip():
                return {
                    "status": "error",
                    "error_message": "Transcript is empty"
                }
            
            # Clean transcript
            transcript = clean_text_for_processing(transcript)
            
            # Generate summary using OpenAI
            messages = [
                {"role": "system", "content": SYSTEM_PROMPTS['SUMMARY']},
                {"role": "user", "content": f"Please summarize the following call center transcript in Arabic:\n\n{transcript}"}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODELS['SUMMARY'],
                messages=messages,
                temperature=TEMPERATURE_SETTINGS['SUMMARY'],
                max_tokens=MAX_TOKEN_LIMITS['SUMMARY']
            )
            
            summary = response.choices[0].message.content
            if not summary:
                return {
                    "status": "error",
                    "error_message": "OpenAI returned empty summary"
                }
            
            # Save summary to file
            summary_path = get_file_path('SUMMARY', file_id)
            self._save_summary_report(summary_path, summary, file_id, audio_url, transcript_path)
            
            return {
                "status": "success",
                "file_identifier": file_id,
                "summary": summary,
                "summary_path": str(summary_path),
                "summary_length": len(summary),
                "model_used": OPENAI_MODELS['SUMMARY'],
                "token_usage": {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0
                }
            }
            
        except Exception as e:
            return {
                "status": "error",
                "file_identifier": file_id,
                "error_message": f"Summary generation failed: {str(e)}"
            }
    
    def _save_summary_report(self, file_path: str, summary: str, file_id: str, 
                           audio_url: Optional[str], transcript_path: str):
        """Save formatted summary report to file."""
        header = f"""
Summary Report for: {file_id}
Audio URL: {audio_url or 'N/A'}
Transcript File: {os.path.basename(transcript_path)}
Generated on: {datetime.now().isoformat()}
=======================================================

"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header + summary)


def process_summary(transcript_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
    """Main function to process summary generation."""
    agent = SummaryAgent()
    return agent.generate_summary(transcript_path, audio_url)


if __name__ == "__main__":
    # Test summary agent
    print("Testing Summary Agent...")

    # Look for test transcript in transcripts directory
    transcripts_dir = os.path.join(os.path.dirname(__file__), '..', 'transcripts')
    test_transcript_path = os.path.join(transcripts_dir, 'test_transcript.txt')

    if os.path.exists(test_transcript_path):
        print(f"✅ Found test transcript: {test_transcript_path}")
        result = process_summary(test_transcript_path, "test/audio.wav")
        print(f"Test result: {result}")
    else:
        print(f"⚠️  Test transcript file not found: {test_transcript_path}")
        print("Please place a test_transcript.txt file in the transcripts directory")
        print("Or provide a transcript file path as input")
