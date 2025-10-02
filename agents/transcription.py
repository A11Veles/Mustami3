# Transcription and Diarization Agent
import os
import wave
import numpy as np
from openai import OpenAI
from typing import Dict, Any, Optional

from config.settings import (
    load_env_variable, ENV_VARS, OPENAI_MODELS, 
    TEMPERATURE_SETTINGS, get_file_path
)
from utils.helpers import get_audio_file_identifier, validate_audio_file

class TranscriptionAgent:
    """Handles audio transcription and basic speaker identification."""
    
    def __init__(self):
        self.client = None
        self.initialize_openai()
    
    def initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = load_env_variable(ENV_VARS['OPENAI_API_KEY'], required=True)
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for transcription")
        else:
            print("⚠️  OpenAI API key not found")
    
    def get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration in seconds."""
        try:
            with wave.open(file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                return frames / float(rate)
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    
    def transcribe_audio(self, file_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Transcribe audio file using OpenAI's gpt-4o-mini-transcribe model."""
        if not self.client:
            return {
                "status": "error",
                "error_message": "OpenAI client not initialized"
            }
        
        # Validate audio file
        validation = validate_audio_file(file_path)
        if not validation['valid']:
            return {
                "status": "error",
                "error_message": validation['error']
            }
        
        file_id = get_audio_file_identifier(audio_url, file_path)
        
        try:
            # Get audio duration
            duration = self.get_audio_duration(file_path)
            
            # Transcribe with speaker hints for better formatting
            with open(file_path, "rb") as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=OPENAI_MODELS['TRANSCRIPTION'],
                    file=audio_file,
                    response_format="text",
                    temperature=TEMPERATURE_SETTINGS['TRANSCRIPTION'],
                    language="ar",
                    prompt="Transcribe the conversation between a callcenter agent and a patient. Format the output as follows:\n\nCallcenter: [what the callcenter agent says]\nPatient: [what the patient says]\n\nMake sure to identify who is speaking for each turn in the conversation."
                )
            
            # Save transcript to file
            transcript_path = get_file_path('TRANSCRIPT', file_id)
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(response)
            
            return {
                "status": "success",
                "file_identifier": file_id,
                "audio_duration": duration,
                "transcript": response,
                "transcript_path": str(transcript_path),
                "speaker_turns_count": len([line for line in response.split('\n') if line.strip()]),
                "model_used": OPENAI_MODELS['TRANSCRIPTION']
            }
            
        except Exception as e:
            return {
                "status": "error",
                "file_identifier": file_id,
                "error_message": f"Transcription failed: {str(e)}"
            }


def process_transcription(audio_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
    """Main function to process audio transcription."""
    agent = TranscriptionAgent()
    return agent.transcribe_audio(audio_path, audio_url)


if __name__ == "__main__":
    # Test transcription agent
    print("Testing Transcription Agent...")

    # Look for test.wav in audio_files directory
    audio_files_dir = os.path.join(os.path.dirname(__file__), '..', 'audio_files')
    test_audio_path = os.path.join(audio_files_dir, 'test.wav')

    if os.path.exists(test_audio_path):
        print(f"✅ Found test audio file: {test_audio_path}")
        result = process_transcription(test_audio_path)
        print(f"Test result: {result}")
    else:
        print(f"⚠️  Test audio file not found: {test_audio_path}")
        print("Please place a test.wav file in the audio_files directory")
        print("Or provide a Google Drive link as input")
