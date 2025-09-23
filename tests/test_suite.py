# Comprehensive Test Suite for Call Center Agent
import os
import sys
import json
import tempfile
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_configuration():
    """Test configuration loading and environment variables."""
    print("\n=== Testing Configuration ===")
    try:
        from config.settings import (
            OPENAI_MODELS, SYSTEM_PROMPTS, FILE_PATTERNS,
            load_env_variable, get_file_path
        )
        
        # Test environment variable loading
        test_var = load_env_variable("NONEXISTENT_VAR", default="test_default")
        assert test_var == "test_default", "Default value not working"
        
        # Test file path generation
        test_path = get_file_path("TRANSCRIPT", "test_file")
        assert "test_file_formatted_transcript.txt" in str(test_path)
        
        print("✅ Configuration tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_helpers():
    """Test helper utilities."""
    print("\n=== Testing Helper Functions ===")
    try:
        from utils.helpers import (
            extract_google_drive_file_id, get_audio_file_identifier,
            is_valid_google_drive_link, validate_audio_file, 
            format_duration, clean_text_for_processing
        )
        
        # Test Google Drive ID extraction
        test_url = "https://drive.google.com/file/d/1234567890abcdef/view?usp=sharing"
        file_id = extract_google_drive_file_id(test_url)
        assert file_id == "1234567890abcdef", f"Expected '1234567890abcdef', got '{file_id}'"
        
        # Test file identifier generation
        identifier = get_audio_file_identifier("test_url", "test/path.wav")
        assert identifier and "_MPE" in identifier, "File identifier generation failed"
        
        # Test duration formatting
        duration = format_duration(125.5)
        assert "2m 5.5s" in duration, f"Duration format failed: {duration}"
        
        # Test text cleaning
        dirty_text = "  Hello\n\n  World  \t"
        clean_text = clean_text_for_processing(dirty_text)
        assert clean_text == "Hello World", f"Text cleaning failed: '{clean_text}'"
        
        print("✅ Helper function tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Helper function tests failed: {e}")
        return False

def test_firebase_connection():
    """Test Firebase connection and authentication."""
    print("\n=== Testing Firebase Connection ===")
    try:
        from utils.firebase import firebase_auth, firebase_db
        
        # Test Firebase initialization (non-destructive)
        if firebase_auth.pyrebase_app:
            print("✅ Firebase Auth initialized")
        else:
            print("⚠️  Firebase Auth not initialized (check config)")
        
        if firebase_db.db:
            print("✅ Firebase Database initialized")
        else:
            print("⚠️  Firebase Database not initialized (check config)")
        
        print("✅ Firebase connection tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection test failed: {e}")
        return False

def test_transcription_agent():
    """Test transcription agent functionality."""
    print("\n=== Testing Transcription Agent ===")
    try:
        from agents.transcription import TranscriptionAgent

        # Initialize agent
        agent = TranscriptionAgent()

        # Look for test.wav in audio_files directory
        audio_files_dir = project_root / "audio_files"
        test_audio_path = audio_files_dir / "test.wav"

        if test_audio_path.exists():
            # Test audio duration calculation
            duration = agent.get_audio_duration(str(test_audio_path))
            assert duration > 0, "Audio duration should be positive"

            print(f"✅ Audio duration test passed: {duration}s")
            print(f"✅ Found test audio file: {test_audio_path}")
        else:
            print(f"⚠️  Test audio file not found: {test_audio_path}")
            print("Please place a test.wav file in the audio_files directory")

        print("✅ Transcription agent tests completed")
        return True

    except Exception as e:
        print(f"❌ Transcription agent test failed: {e}")
        return False

def test_summary_agent():
    """Test summary agent functionality."""
    print("\n=== Testing Summary Agent ===")
    try:
        from agents.summary import SummaryAgent

        # Initialize agent
        agent = SummaryAgent()

        # Look for test transcript in transcripts directory
        transcripts_dir = project_root / "transcripts"
        test_transcript_path = transcripts_dir / "test_transcript.txt"

        if test_transcript_path.exists():
            # Test transcript reading
            with open(test_transcript_path, 'r', encoding='utf-8') as f:
                content = f.read()

            assert len(content) > 0, "Test transcript should have content"
            print("✅ Transcript reading test passed")
            print(f"✅ Found test transcript: {test_transcript_path}")
        else:
            print(f"⚠️  Test transcript file not found: {test_transcript_path}")
            print("Please place a test_transcript.txt file in the transcripts directory")

        print("✅ Summary agent tests completed")
        return True

    except Exception as e:
        print(f"❌ Summary agent test failed: {e}")
        return False

def test_openai_connection():
    """Test OpenAI API connection."""
    print("\n=== Testing OpenAI Connection ===")
    try:
        from config.settings import load_env_variable, ENV_VARS
        from openai import OpenAI
        
        api_key = load_env_variable(ENV_VARS['OPENAI_API_KEY'])
        
        if api_key and api_key != "your-openai-api-key":
            client = OpenAI(api_key=api_key)
            
            # Test with minimal request (models list)
            models = client.models.list()
            if models.data:
                print(f"✅ OpenAI connection successful, found {len(models.data)} models")
            else:
                print("⚠️  OpenAI connection successful but no models found")
        else:
            print("⚠️  OpenAI API key not configured")
        
        print("✅ OpenAI connection tests completed")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI connection test failed: {e}")
        return False

def test_file_operations():
    """Test file operations and path handling."""
    print("\n=== Testing File Operations ===")
    try:
        from config.settings import OUTPUTS_DIR, get_file_path
        
        # Test outputs directory creation
        assert OUTPUTS_DIR.exists(), "Outputs directory should exist"
        
        # Test file path generation
        test_paths = ['TRANSCRIPT', 'SUMMARY', 'EVALUATION_JSON']
        for pattern in test_paths:
            path = get_file_path(pattern, "test_123")
            assert path.parent == OUTPUTS_DIR, f"Path should be in outputs dir: {path}"
            assert "test_123" in str(path), f"File ID should be in path: {path}"
        
        print("✅ File operations tests passed")
        return True
        
    except Exception as e:
        print(f"❌ File operations test failed: {e}")
        return False

def test_google_drive_functions():
    """Test Google Drive URL handling."""
    print("\n=== Testing Google Drive Functions ===")
    try:
        from utils.helpers import extract_google_drive_file_id, is_valid_google_drive_link
        
        # Test various Google Drive URL formats
        test_urls = [
            "https://drive.google.com/file/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/view?usp=sharing",
            "https://drive.google.com/open?id=1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms",
            "https://docs.google.com/document/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit?usp=sharing"
        ]
        
        for url in test_urls:
            file_id = extract_google_drive_file_id(url)
            is_valid = is_valid_google_drive_link(url)
            
            assert file_id is not None, f"Should extract file ID from: {url}"
            assert is_valid, f"Should be valid Google Drive link: {url}"
        
        # Test invalid URLs
        invalid_urls = ["https://example.com/file.mp3", "not-a-url", ""]
        for url in invalid_urls:
            is_valid = is_valid_google_drive_link(url)
            assert not is_valid, f"Should be invalid: {url}"
        
        print("✅ Google Drive functions tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Google Drive functions test failed: {e}")
        return False

def create_test_audio_file():
    """Create a minimal test audio file."""
    try:
        import wave
        import numpy as np
        
        # Create temporary file
        temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_file.close()
        
        # Generate 1 second of silence
        sample_rate = 16000
        duration = 1
        samples = np.zeros(sample_rate * duration, dtype=np.int16)
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(samples.tobytes())
        
        return temp_file.name
        
    except Exception as e:
        print(f"Could not create test audio file: {e}")
        return None

def create_test_transcript():
    """Create a test transcript file."""
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', 
                                               encoding='utf-8', delete=False)
        temp_file.write("""Callcenter: السلام عليكم، مع حضرتك من خدمة العملاء.
Patient: أهلا وسهلا.
Callcenter: كيف يمكنني مساعدتك اليوم؟
Patient: عندي استفسار بخصوص الموعد.
Callcenter: تفضل، أنا في الخدمة.
Patient: شكرًا جزيلاً.""")
        temp_file.close()
        return temp_file.name
        
    except Exception as e:
        print(f"Could not create test transcript: {e}")
        return None

def run_all_tests():
    """Run all test functions."""
    print("🧪 Starting Call Center Agent Test Suite...")
    print("=" * 50)
    
    test_functions = [
        test_configuration,
        test_helpers,
        test_file_operations,
        test_google_drive_functions,
        test_firebase_connection,
        test_transcription_agent,
        test_summary_agent,
        test_openai_connection,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ {test_func.__name__} crashed: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    print(f"🧪 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
    else:
        print(f"⚠️  {failed} tests failed")
    
    return failed == 0

if __name__ == "__main__":
    # Individual test functions that can be uncommented to run specific tests
    
    # Uncomment the tests you want to run:
    
    # test_configuration()
    # test_helpers()
    # test_file_operations()
    # test_google_drive_functions()
    # test_firebase_connection()
    # test_transcription_agent()
    # test_summary_agent()
    # test_openai_connection()
    
    # Run all tests (comment this if you want to run individual tests)
    run_all_tests()
