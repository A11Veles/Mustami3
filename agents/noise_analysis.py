# Noise Analysis Agent for Audio Quality Assessment
import os
import wave
import json
import numpy as np
from datetime import datetime
from typing import Dict, Any, Optional

from config.settings import get_file_path
from utils.helpers import get_audio_file_identifier, validate_audio_file, format_duration

class NoiseAnalysisAgent:
    """Analyzes audio quality and noise levels in call recordings."""
    
    def analyze_audio_quality(self, audio_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
        """Analyze audio file for noise and quality metrics."""
        
        # Validate audio file
        validation = validate_audio_file(audio_path)
        if not validation['valid']:
            return {
                "status": "error",
                "error_message": validation['error']
            }
        
        file_id = get_audio_file_identifier(audio_url, audio_path)
        
        try:
            # Basic audio analysis
            audio_stats = self._extract_audio_stats(audio_path)
            
            # Calculate quality metrics
            quality_metrics = self._calculate_quality_metrics(audio_stats)
            
            # Generate noise report
            noise_report = self._generate_noise_report(quality_metrics, audio_stats, file_id)
            
            # Save noise analysis to file
            json_path = get_file_path('NOISE_JSON', file_id)
            self._save_noise_report(json_path, noise_report, file_id, audio_url, audio_path)
            
            return {
                "status": "success",
                "file_identifier": file_id,
                "noise_metrics": quality_metrics,
                "audio_stats": audio_stats,
                "noise_report_path": str(json_path),
                "quality_summary": noise_report.get('quality_summary', {})
            }
            
        except Exception as e:
            return {
                "status": "error",
                "file_identifier": file_id,
                "error_message": f"Noise analysis failed: {str(e)}"
            }
    
    def _extract_audio_stats(self, audio_path: str) -> Dict[str, Any]:
        """Extract basic audio statistics."""
        try:
            with wave.open(audio_path, 'rb') as wav_file:
                # Get basic properties
                frames = wav_file.getnframes()
                sample_rate = wav_file.getframerate()
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                
                # Calculate duration
                duration = frames / sample_rate
                
                # Read audio data for analysis
                raw_data = wav_file.readframes(frames)
                
                # Convert to numpy array
                if sample_width == 1:
                    audio_data = np.frombuffer(raw_data, dtype=np.int8)
                elif sample_width == 2:
                    audio_data = np.frombuffer(raw_data, dtype=np.int16)
                else:
                    audio_data = np.frombuffer(raw_data, dtype=np.int32)
                
                # Handle stereo by taking first channel
                if channels > 1:
                    audio_data = audio_data[::channels]
                
                return {
                    "sample_rate": sample_rate,
                    "channels": channels,
                    "sample_width": sample_width,
                    "duration": duration,
                    "frames": frames,
                    "audio_data": audio_data,
                    "file_size_mb": os.path.getsize(audio_path) / (1024 * 1024)
                }
                
        except Exception as e:
            raise Exception(f"Failed to extract audio stats: {str(e)}")
    
    def _calculate_quality_metrics(self, audio_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate audio quality metrics."""
        try:
            audio_data = audio_stats['audio_data']
            sample_rate = audio_stats['sample_rate']
            
            # Convert to float for calculations
            audio_float = audio_data.astype(np.float64)
            
            # Calculate RMS (Root Mean Square) - measure of signal power
            rms = np.sqrt(np.mean(audio_float ** 2))
            
            # Calculate peak amplitude
            peak_amplitude = np.max(np.abs(audio_float))
            
            # Estimate SNR (Signal-to-Noise Ratio) - simplified approach
            # Split audio into segments and analyze variance
            segment_size = sample_rate // 4  # 0.25 second segments
            num_segments = len(audio_float) // segment_size
            
            if num_segments > 4:
                segments = audio_float[:num_segments * segment_size].reshape(num_segments, segment_size)
                segment_powers = np.mean(segments ** 2, axis=1)
                
                # Assume quiet segments represent noise floor
                noise_floor = np.percentile(segment_powers, 25)  # Bottom 25%
                signal_power = np.percentile(segment_powers, 75)  # Top 25%
                
                # Calculate SNR in dB
                if noise_floor > 0:
                    snr_db = 10 * np.log10(signal_power / noise_floor)
                else:
                    snr_db = 60  # Very high SNR if no noise detected
            else:
                snr_db = 30  # Default moderate SNR for short files
            
            # Calculate dynamic range
            dynamic_range = 20 * np.log10(peak_amplitude / (rms + 1e-10))
            
            # Detect clipping (values at maximum)
            max_value = 2 ** (audio_stats['sample_width'] * 8 - 1) - 1
            clipping_percentage = np.sum(np.abs(audio_data) >= max_value * 0.99) / len(audio_data) * 100
            
            # Calculate zero crossing rate (indicates speech vs noise)
            zero_crossings = np.sum(np.diff(np.signbit(audio_float)))
            zcr = zero_crossings / len(audio_float)
            
            return {
                "rms": float(rms),
                "peak_amplitude": float(peak_amplitude),
                "snr_db": float(snr_db),
                "dynamic_range_db": float(dynamic_range),
                "clipping_percentage": float(clipping_percentage),
                "zero_crossing_rate": float(zcr),
                "sample_rate": audio_stats['sample_rate'],
                "duration": audio_stats['duration']
            }
            
        except Exception as e:
            raise Exception(f"Failed to calculate quality metrics: {str(e)}")
    
    def _generate_noise_report(self, metrics: Dict[str, Any], audio_stats: Dict[str, Any], 
                             file_id: str) -> Dict[str, Any]:
        """Generate comprehensive noise analysis report."""
        
        # Determine quality ratings
        snr = metrics['snr_db']
        clipping = metrics['clipping_percentage']
        
        # Quality classification
        if snr >= 25 and clipping < 1:
            quality_label = "Excellent"
            quality_score = 9 + min(1, (snr - 25) / 10)
        elif snr >= 20 and clipping < 3:
            quality_label = "Good"
            quality_score = 7 + (snr - 20) / 5
        elif snr >= 15 and clipping < 5:
            quality_label = "Fair"
            quality_score = 5 + (snr - 15) / 5
        elif snr >= 10:
            quality_label = "Poor"
            quality_score = 3 + (snr - 10) / 5
        else:
            quality_label = "Very Poor"
            quality_score = max(1, snr / 10)
        
        # Generate recommendations
        recommendations = []
        if snr < 20:
            recommendations.append("Consider noise reduction preprocessing")
        if clipping > 2:
            recommendations.append("Audio has clipping - check recording levels")
        if metrics['dynamic_range_db'] < 20:
            recommendations.append("Low dynamic range - may indicate compression issues")
        if not recommendations:
            recommendations.append("Audio quality is acceptable for processing")
        
        return {
            "file_identifier": file_id,
            "timestamp": datetime.now().isoformat(),
            "quality_summary": {
                "overall_quality_score": round(quality_score, 1),
                "quality_label": quality_label,
                "average_snr": round(metrics['snr_db'], 1),
                "clipping_detected": clipping > 1,
                "duration_formatted": format_duration(audio_stats['duration'])
            },
            "detailed_metrics": {
                "signal_to_noise_ratio_db": round(metrics['snr_db'], 2),
                "rms_level": round(metrics['rms'], 2),
                "peak_amplitude": round(metrics['peak_amplitude'], 2),
                "dynamic_range_db": round(metrics['dynamic_range_db'], 2),
                "clipping_percentage": round(clipping, 2),
                "zero_crossing_rate": round(metrics['zero_crossing_rate'], 4)
            },
            "audio_properties": {
                "sample_rate": audio_stats['sample_rate'],
                "channels": audio_stats['channels'],
                "sample_width_bits": audio_stats['sample_width'] * 8,
                "duration_seconds": round(audio_stats['duration'], 2),
                "file_size_mb": round(audio_stats['file_size_mb'], 2)
            },
            "recommendations": recommendations
        }
    
    def _save_noise_report(self, json_path: str, report: Dict[str, Any], 
                          file_id: str, audio_url: Optional[str], audio_path: str):
        """Save noise analysis report to JSON file."""
        # Add metadata
        report_with_metadata = {
            **report,
            "analysis_metadata": {
                "audio_url": audio_url,
                "local_audio_path": os.path.basename(audio_path),
                "analysis_version": "1.0"
            }
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report_with_metadata, f, indent=2, ensure_ascii=False)


def process_noise_analysis(audio_path: str, audio_url: Optional[str] = None) -> Dict[str, Any]:
    """Main function to process noise analysis."""
    agent = NoiseAnalysisAgent()
    return agent.analyze_audio_quality(audio_path, audio_url)


if __name__ == "__main__":
    # Test noise analysis agent
    print("Testing Noise Analysis Agent...")
    
    # Create a simple test audio file
    test_audio_path = "test_noise_audio.wav"
    
    if not os.path.exists(test_audio_path):
        try:
            # Generate test audio with some noise characteristics
            sample_rate = 16000
            duration = 2  # 2 seconds
            t = np.linspace(0, duration, sample_rate * duration)
            
            # Create a mix of sine waves (simulating speech) and noise
            signal = np.sin(2 * np.pi * 400 * t) * 0.3  # 400 Hz tone
            signal += np.sin(2 * np.pi * 800 * t) * 0.2  # 800 Hz tone
            noise = np.random.normal(0, 0.05, len(t))    # Background noise
            
            audio = signal + noise
            audio = (audio * 32767).astype(np.int16)  # Convert to 16-bit
            
            with wave.open(test_audio_path, 'w') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio.tobytes())
            
            print(f"✅ Created test audio file: {test_audio_path}")
            
        except Exception as e:
            print(f"❌ Could not create test audio file: {e}")
    
    if os.path.exists(test_audio_path):
        result = process_noise_analysis(test_audio_path, "test/noise_audio.wav")
        print(f"Test result status: {result.get('status')}")
        if result.get('quality_summary'):
            print(f"Quality: {result['quality_summary']}")
        
        # Clean up test file
        try:
            os.remove(test_audio_path)
            print(f"✅ Cleaned up test file")
        except:
            pass
    else:
        print("⚠️  No test audio file available")
