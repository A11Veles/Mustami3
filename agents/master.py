# Master Agent - Orchestrates all call center analysis agents
import os
import sys
import json
import gdown
import tempfile
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import OUTPUTS_DIR
from utils.helpers import (
    extract_google_drive_file_id, get_audio_file_identifier, 
    validate_audio_file, create_temp_audio_file
)

# Import all agent processors
from agents.transcription import process_transcription
from agents.noise_analysis import process_noise_analysis
from agents.summary import process_summary
from agents.evaluation import process_evaluation
from agents.recommendation import process_recommendations

class MasterAgent:
    """Orchestrates the complete call center analysis pipeline."""
    
    def __init__(self):
        self.results = {}
        self.temp_files = []
    
    def process_audio_file(self, audio_url: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Process a single audio file through the complete pipeline."""
        
        print(f"🎯 Starting Master Agent processing for: {audio_url}")
        
        # Initialize result structure
        file_id = get_audio_file_identifier(audio_url)
        result = {
            "file_identifier": file_id,
            "audio_url": audio_url,
            "processing_start_time": datetime.now().isoformat(),
            "status": "processing",
            "results": {},
            "errors": []
        }
        
        try:
            # Step 1: Download audio file
            print("📥 Step 1: Downloading audio file...")
            audio_path = self._download_audio(audio_url)
            if not audio_path:
                result["status"] = "error"
                result["errors"].append("Failed to download audio file")
                return result
            
            # Step 2: Run transcription
            print("🗣️ Step 2: Running transcription...")
            transcription_result = process_transcription(audio_path, audio_url)
            result["results"]["transcription"] = transcription_result
            
            if transcription_result.get("status") != "success":
                result["errors"].append("Transcription failed")
                # Continue with other analyses that don't depend on transcript
            
            # Step 3: Run noise analysis
            print("🔊 Step 3: Running noise analysis...")
            noise_result = process_noise_analysis(audio_path, audio_url)
            result["results"]["noise_analysis"] = noise_result
            
            if noise_result.get("status") != "success":
                result["errors"].append("Noise analysis failed")
            
            # Step 4: Run evaluation (if transcription succeeded)
            transcript_path = transcription_result.get("transcript_path")
            if transcript_path and os.path.exists(transcript_path):
                print("📊 Step 4: Running evaluation...")
                evaluation_result = process_evaluation(transcript_path, audio_url)
                result["results"]["evaluation"] = evaluation_result
                
                if evaluation_result.get("status") != "success":
                    result["errors"].append("Evaluation failed")
            else:
                result["errors"].append("Skipped evaluation - no transcript available")
            
            # Step 5: Run summary (if transcription succeeded)
            if transcript_path and os.path.exists(transcript_path):
                print("📝 Step 5: Running summary...")
                summary_result = process_summary(transcript_path, audio_url)
                result["results"]["summary"] = summary_result
                
                if summary_result.get("status") != "success":
                    result["errors"].append("Summary failed")
            else:
                result["errors"].append("Skipped summary - no transcript available")
            
            # Step 6: Run recommendations (if transcript and evaluation succeeded)
            evaluation_json_path = None
            if "evaluation" in result["results"]:
                evaluation_json_path = result["results"]["evaluation"].get("evaluation_json_path")
            
            if transcript_path and os.path.exists(transcript_path):
                print("💡 Step 6: Running recommendations...")
                rec_result = process_recommendations(transcript_path, evaluation_json_path, audio_url)
                result["results"]["recommendations"] = rec_result
                
                if rec_result.get("status") != "success":
                    result["errors"].append("Recommendations failed")
            else:
                result["errors"].append("Skipped recommendations - no transcript available")
            
            # Finalize result
            result["processing_end_time"] = datetime.now().isoformat()
            result["status"] = "completed" if not result["errors"] else "completed_with_errors"
            
            # Calculate processing summary
            result["processing_summary"] = self._create_processing_summary(result)
            
            print(f"✅ Master Agent processing completed with status: {result['status']}")
            
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Master processing error: {str(e)}")
            result["processing_end_time"] = datetime.now().isoformat()
            print(f"❌ Master Agent processing failed: {str(e)}")
        
        finally:
            # Clean up temporary files
            self._cleanup_temp_files()
        
        return result
    
    def process_multiple_files(self, audio_urls: List[str], 
                             custom_prompt: Optional[str] = None) -> Dict[str, Any]:
        """Process multiple audio files."""
        
        print(f"🎯 Starting batch processing for {len(audio_urls)} files")
        
        batch_result = {
            "batch_start_time": datetime.now().isoformat(),
            "total_files": len(audio_urls),
            "processed_files": 0,
            "successful_files": 0,
            "failed_files": 0,
            "files": [],
            "batch_summary": {}
        }
        
        for i, audio_url in enumerate(audio_urls, 1):
            print(f"\n📁 Processing file {i}/{len(audio_urls)}")
            
            file_result = self.process_audio_file(audio_url, custom_prompt)
            batch_result["files"].append(file_result)
            batch_result["processed_files"] += 1
            
            if file_result["status"] in ["completed", "completed_with_errors"]:
                batch_result["successful_files"] += 1
            else:
                batch_result["failed_files"] += 1
        
        batch_result["batch_end_time"] = datetime.now().isoformat()
        batch_result["batch_summary"] = self._create_batch_summary(batch_result)
        
        print(f"\n✅ Batch processing completed: {batch_result['successful_files']} successful, {batch_result['failed_files']} failed")
        
        return batch_result
    
    def _download_audio(self, audio_url: str) -> Optional[str]:
        """Download audio file from Google Drive."""
        try:
            file_id = extract_google_drive_file_id(audio_url)
            if not file_id:
                print(f"❌ Could not extract file ID from URL: {audio_url}")
                return None
            
            # Create temporary file
            temp_path = create_temp_audio_file()
            self.temp_files.append(temp_path)
            
            # Download using gdown
            output_path = gdown.download(url=audio_url, output=temp_path, quiet=False, fuzzy=True)
            
            if not output_path or not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
                print(f"❌ Download failed or file is empty")
                return None
            
            # Validate the downloaded file
            validation = validate_audio_file(temp_path)
            if not validation['valid']:
                print(f"❌ Downloaded file validation failed: {validation['error']}")
                return None
            
            print(f"✅ Successfully downloaded: {validation['size_mb']:.1f} MB")
            return temp_path
            
        except Exception as e:
            print(f"❌ Download error: {str(e)}")
            return None
    
    def _create_processing_summary(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of processing results."""
        summary = {
            "total_steps": 6,  # transcription, noise, evaluation, summary, recommendations
            "successful_steps": 0,
            "failed_steps": 0,
            "step_details": {}
        }
        
        steps = ["transcription", "noise_analysis", "evaluation", "summary", "recommendations"]
        
        for step in steps:
            if step in result["results"]:
                step_result = result["results"][step]
                if step_result.get("status") == "success":
                    summary["successful_steps"] += 1
                    summary["step_details"][step] = "success"
                else:
                    summary["failed_steps"] += 1
                    summary["step_details"][step] = "failed"
            else:
                summary["failed_steps"] += 1
                summary["step_details"][step] = "skipped"
        
        return summary
    
    def _create_batch_summary(self, batch_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of batch processing."""
        step_counts = {
            "transcription": {"success": 0, "failed": 0},
            "noise_analysis": {"success": 0, "failed": 0}, 
            "evaluation": {"success": 0, "failed": 0},
            "summary": {"success": 0, "failed": 0},
            "recommendations": {"success": 0, "failed": 0}
        }
        
        for file_result in batch_result["files"]:
            for step, counts in step_counts.items():
                if step in file_result.get("results", {}):
                    step_result = file_result["results"][step]
                    if step_result.get("status") == "success":
                        counts["success"] += 1
                    else:
                        counts["failed"] += 1
                else:
                    counts["failed"] += 1
        
        return {
            "total_files": batch_result["total_files"],
            "successful_files": batch_result["successful_files"],
            "failed_files": batch_result["failed_files"],
            "step_success_rates": {
                step: f"{counts['success']}/{batch_result['total_files']}" 
                for step, counts in step_counts.items()
            }
        }
    
    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as e:
                print(f"Warning: Could not clean up temp file {temp_file}: {e}")
        
        self.temp_files = []
    
    def save_results_to_json(self, results: Dict[str, Any], filename: Optional[str] = None):
        """Save processing results to JSON file."""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"master_processing_results_{timestamp}.json"
        
        output_path = OUTPUTS_DIR / filename
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Results saved to: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"❌ Failed to save results: {str(e)}")
            return None


def process_single_audio(audio_url: str, custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to process a single audio file."""
    agent = MasterAgent()
    return agent.process_audio_file(audio_url, custom_prompt)


def process_multiple_audios(audio_urls: List[str], custom_prompt: Optional[str] = None) -> Dict[str, Any]:
    """Convenience function to process multiple audio files."""
    agent = MasterAgent()
    return agent.process_multiple_files(audio_urls, custom_prompt)


if __name__ == "__main__":
    # Test master agent
    print("Testing Master Agent...")
    
    test_url = "https://drive.google.com/file/d/1PFfIG3aD4GMZasILcEQXIoPhYAmy_MPE/view?usp=sharing"
    result = process_single_audio(test_url)
    print(f"Test result status: {result.get('status')}")
    
    print("✅ Master Agent module loaded successfully")
    print("📝 To test with real files, provide Google Drive URLs to process_single_audio() or process_multiple_audios()")
