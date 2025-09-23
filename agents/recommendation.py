# Recommendation Agent for Call Center Process Improvement
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

class RecommendationAgent:
    """Generates actionable recommendations for call center improvement."""
    
    def __init__(self):
        self.client = None
        self.initialize_openai()
    
    def initialize_openai(self):
        """Initialize OpenAI client."""
        api_key = load_env_variable(ENV_VARS['OPENAI_API_KEY'], required=True)
        if api_key:
            self.client = OpenAI(api_key=api_key)
            print("✅ OpenAI client initialized for recommendations")
        else:
            print("⚠️  OpenAI API key not found")
    
    def generate_recommendations(self, transcript_path: str, evaluation_json_path: Optional[str] = None, 
                               audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Generate recommendations based on transcript and optional evaluation."""
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
            
            # Read evaluation data if available
            evaluation_context = ""
            if evaluation_json_path and os.path.exists(evaluation_json_path):
                try:
                    with open(evaluation_json_path, 'r', encoding='utf-8') as f:
                        evaluation_data = json.load(f)
                    evaluation_context = f"\n\nEvaluation Results:\n{json.dumps(evaluation_data, indent=2, ensure_ascii=False)}"
                except Exception as e:
                    print(f"Warning: Could not read evaluation file: {e}")
            
            # Generate recommendations using OpenAI
            user_content = f"Please provide recommendations for improvement based on this call center transcript:{evaluation_context}\n\nTranscript:\n{transcript}"
            
            messages = [
                {"role": "system", "content": SYSTEM_PROMPTS['RECOMMENDATION']},
                {"role": "user", "content": user_content}
            ]
            
            response = self.client.chat.completions.create(
                model=OPENAI_MODELS['RECOMMENDATION'],
                messages=messages,
                temperature=TEMPERATURE_SETTINGS['RECOMMENDATION'],
                max_tokens=MAX_TOKEN_LIMITS['RECOMMENDATION']
            )
            
            recommendations = response.choices[0].message.content
            if not recommendations:
                return {
                    "status": "error",
                    "error_message": "OpenAI returned empty recommendations"
                }
            
            # Parse recommendations into structured format
            parsed_recommendations = self._parse_recommendations(recommendations)
            
            # Save recommendations to file
            recommendations_path = get_file_path('RECOMMENDATIONS', file_id)
            self._save_recommendations_report(recommendations_path, recommendations, parsed_recommendations,
                                            file_id, audio_url, transcript_path, evaluation_json_path)
            
            return {
                "status": "success",
                "file_identifier": file_id,
                "recommendations": recommendations,
                "parsed_recommendations": parsed_recommendations,
                "recommendations_path": str(recommendations_path),
                "model_used": OPENAI_MODELS['RECOMMENDATION'],
                "evaluation_used": evaluation_json_path is not None and os.path.exists(evaluation_json_path or ""),
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
                "error_message": f"Recommendations generation failed: {str(e)}"
            }
    
    def _parse_recommendations(self, recommendations_text: str) -> Dict[str, Any]:
        """Parse recommendations text into structured categories."""
        # Simple parsing based on common patterns
        categories = {
            "high_priority": [],
            "medium_priority": [],
            "low_priority": [],
            "communication_improvements": [],
            "process_improvements": [],
            "training_recommendations": [],
            "system_improvements": []
        }
        
        lines = recommendations_text.split('\n')
        current_category = "general"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect priority levels
            if any(keyword in line.lower() for keyword in ['عالية الأولوية', 'high priority', 'urgent']):
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    categories["high_priority"].append(line[1:].strip())
            elif any(keyword in line.lower() for keyword in ['متوسطة الأولوية', 'medium priority', 'moderate']):
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    categories["medium_priority"].append(line[1:].strip())
            elif any(keyword in line.lower() for keyword in ['منخفضة الأولوية', 'low priority', 'minor']):
                if line.startswith('-') or line.startswith('•') or line.startswith('*'):
                    categories["low_priority"].append(line[1:].strip())
            
            # Detect improvement categories
            elif any(keyword in line.lower() for keyword in ['تحسين التواصل', 'communication', 'تواصل']):
                current_category = "communication_improvements"
            elif any(keyword in line.lower() for keyword in ['تحسين العمليات', 'process', 'عمليات']):
                current_category = "process_improvements"
            elif any(keyword in line.lower() for keyword in ['تدريب', 'training']):
                current_category = "training_recommendations"
            elif any(keyword in line.lower() for keyword in ['نظام', 'system']):
                current_category = "system_improvements"
            elif line.startswith('-') or line.startswith('•') or line.startswith('*'):
                # Add to current category
                if current_category in categories:
                    categories[current_category].append(line[1:].strip())
        
        return categories
    
    def _save_recommendations_report(self, file_path: str, recommendations: str, 
                                   parsed_recommendations: dict, file_id: str,
                                   audio_url: Optional[str], transcript_path: str,
                                   evaluation_json_path: Optional[str]):
        """Save formatted recommendations report."""
        header = f"""
Recommendations Report for: {file_id}
Audio URL: {audio_url or 'N/A'}
Transcript File: {os.path.basename(transcript_path)}
Evaluation File: {os.path.basename(evaluation_json_path) if evaluation_json_path else 'N/A'}
Generated on: {datetime.now().isoformat()}
=======================================================

ORIGINAL RECOMMENDATIONS:
{recommendations}

STRUCTURED RECOMMENDATIONS:
=========================

"""
        
        # Add structured recommendations
        structured_content = ""
        for category, items in parsed_recommendations.items():
            if items:
                category_title = category.replace('_', ' ').title()
                structured_content += f"{category_title}:\n"
                structured_content += "-" * len(category_title) + ":\n"
                for item in items:
                    structured_content += f"• {item}\n"
                structured_content += "\n"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(header + structured_content)


def process_recommendations(transcript_path: str, evaluation_json_path: Optional[str] = None,
                          audio_url: Optional[str] = None) -> Dict[str, Any]:
    """Main function to process recommendations generation."""
    agent = RecommendationAgent()
    return agent.generate_recommendations(transcript_path, evaluation_json_path, audio_url)


if __name__ == "__main__":
    # Test recommendation agent
    print("Testing Recommendation Agent...")
    
    # Create test transcript file
    test_transcript_path = "test_rec_transcript.txt"
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
    
    result = process_recommendations(test_transcript_path, None, "test/audio.wav")
    print(f"Test result: {result}")
    
    # Clean up test file
    try:
        os.remove(test_transcript_path)
        print(f"✅ Cleaned up test file")
    except:
        pass
