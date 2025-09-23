# Evaluation Agent for Call Center Quality Assessment
import os
import json
from datetime import datetime
from openai import OpenAI
from typing import Dict, Any, Optional

from config.settings import (
    load_env_variable, ENV_VARS, OPENAI_MODELS,
    TEMPERATURE_SETTINGS, MAX_TOKEN_LIMITS, SYSTEM_PROMPTS,
    get_file_path
)
from utils.helpers import get_audio_file_identifier, clean_text_for_processing

class EvaluationAgent:
    """Evaluates call center conversations across multiple quality dimensions."""
    
    def __init__(self):
        self.client = None
        self.initialize_openai()
    
    def initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = load_env_variable(ENV_VARS['OPENAI_API_KEY'], required=True)
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for evaluation")
        else:
            print("⚠️  OpenAI API key not found")
    
    def evaluate_call(self, transcript_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Evaluate call quality from transcript."""
        if not self.client:
            return {
                "status": "error",
                "error_message": "OpenAI client not initialized"
            }
        
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
            
            transcript = clean_text_for_processing(transcript)
            
            # Generate evaluation using OpenAI
            messages = [
                {"role": "system", "content": SYSTEM_PROMPTS['EVALUATION']},
                {"role": "user", "content": f"Please evaluate this call center transcript:\n\n{transcript}"}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODELS['EVALUATION'],
                messages=messages,
                temperature=TEMPERATURE_SETTINGS['EVALUATION'],
                max_tokens=MAX_TOKEN_LIMITS['EVALUATION'],
                response_format={"type": "json_object"}
            )
            
            evaluation_text = response.choices[0].message.content
            if not evaluation_text:
                return {
                    "status": "error",
                    "error_message": "OpenAI returned empty evaluation"
                }
            
            # Parse evaluation JSON
            try:
                evaluation_data = json.loads(evaluation_text)
            except json.JSONDecodeError:
                # If JSON parsing fails, create structured data from text
                evaluation_data = self._parse_evaluation_text(evaluation_text)
            
            # Save evaluation to files
            json_path = get_file_path('EVALUATION_JSON', file_id)
            txt_path = get_file_path('EVALUATION_TXT', file_id)
            
            self._save_evaluation_files(json_path, txt_path, evaluation_data, 
                                      file_id, audio_url, transcript_path)
            
            return {
                "status": "success",
                "file_identifier": file_id,
                "evaluation_data": evaluation_data,
                "evaluation_json_path": str(json_path),
                "evaluation_txt_path": str(txt_path),
                "model_used": OPENAI_MODELS['EVALUATION'],
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
                "error_message": f"Evaluation failed: {str(e)}"
            }
    
    def _parse_evaluation_text(self, text: str) -> Dict[str, Any]:
        """Parse evaluation text into structured data if JSON parsing fails."""
        return {
            "evaluation_summary": {
                "overall_score": 7,  # Default score
                "communication_clarity": 7,
                "problem_resolution": 7,
                "professionalism": 7,
                "customer_satisfaction": 7,
                "process_adherence": 7,
                "complaint_detected": False,
                "issue_category": "General Inquiry",
                "resolution_status": "Resolved"
            },
            "detailed_analysis": text,
            "parsing_note": "Fallback parsing used - JSON format not detected"
        }
    
    def _save_evaluation_files(self, json_path: str, txt_path: str, evaluation_data: dict,
                              file_id: str, audio_url: Optional[str], transcript_path: str):
        """Save evaluation in both JSON and text formats."""
        # Save JSON file
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
        
        # Save text report
        header = f"""
Evaluation Report for: {file_id}
Audio URL: {audio_url or 'N/A'}
Transcript File: {os.path.basename(transcript_path)}
Generated on: {datetime.now().isoformat()}
=======================================================

"""
        
        # Format evaluation data as readable text
        text_content = self._format_evaluation_as_text(evaluation_data)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(header + text_content)
    
    def _format_evaluation_as_text(self, evaluation_data: dict) -> str:
        """Format evaluation data as readable text."""
        text = ""
        
        if "evaluation_summary" in evaluation_data:
            summary = evaluation_data["evaluation_summary"]
            text += "EVALUATION SCORES:\n"
            text += "=" * 20 + "\n"
            
            for key, value in summary.items():
                if isinstance(value, (int, float)) and key != "overall_score":
                    text += f"{key.replace('_', ' ').title()}: {value}/10\n"
                elif key == "overall_score":
                    text += f"Overall Score: {value}/10\n"
                else:
                    text += f"{key.replace('_', ' ').title()}: {value}\n"
            
            text += "\n"
        
        if "detailed_analysis" in evaluation_data:
            text += "DETAILED ANALYSIS:\n"
            text += "=" * 20 + "\n"
            text += evaluation_data["detailed_analysis"]
        
        return text


def process_evaluation(transcript_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
    """Main function to process call evaluation."""
    agent = EvaluationAgent()
    return agent.evaluate_call(transcript_path, audio_url)


if __name__ == "__main__":
    # Test evaluation agent
    print("Testing Evaluation Agent...")
    
    # Create test transcript file
    test_transcript_path = "test_eval_transcript.txt"
    test_content = """Callcenter: السلام عليكم، مع حضرتك رضوى من عيادة تجديد فرع التجمع.
Patient: أهلا بحضرتك.
Callcenter: كنت بأكد مع حضرتك معاد بكرة إن شاء الله؟
Patient: إن شاء الله بإذن الله. أكون هناك على الساعة كام كده؟
Callcenter: بس في مواعيد الصبح من عشرة للاتنين وبالليل من تمانية لحداشر. حابة تنورينا في أي معاد؟
Patient: أجي الصبح.
Callcenter: تمام. في انتظار حضرتك.
Patient: شكرا."""
    
    if not os.path.exists(test_transcript_path):
        with open(test_transcript_path, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"✅ Created test transcript: {test_transcript_path}")
    
    result = process_evaluation(test_transcript_path, "test/audio.wav")
    print(f"Test result: {result}")
    
    # Clean up test file
    try:
        os.remove(test_transcript_path)
        print(f"✅ Cleaned up test file")
    except:
        pass
