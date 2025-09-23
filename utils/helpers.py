# Helper utilities for Call Center Agent
import re
import os
import hashlib
from urllib.parse import urlparse, parse_qs
from typing import Optional
from pathlib import Path

def extract_google_drive_file_id(url: str) -> Optional[str]:
    """Extract file ID from various Google Drive URL formats."""
    if not url:
        return None
    
    # Pattern 1: /file/d/FILE_ID/
    pattern1 = r'/file/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern1, url)
    if match:
        return match.group(1)
    
    # Pattern 2: ?id=FILE_ID
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    if 'id' in query_params:
        return query_params['id'][0]
    
    # Pattern 3: /folders/FOLDER_ID for folder links
    pattern3 = r'/folders/([a-zA-Z0-9-_]+)'
    match = re.search(pattern3, url)
    if match:
        return match.group(1)
    
    # Pattern 4: Google Docs/Sheets/Slides - /document/d/FILE_ID/, /spreadsheets/d/FILE_ID/, /presentation/d/FILE_ID/
    pattern4 = r'/(?:document|spreadsheets|presentation)/d/([a-zA-Z0-9-_]+)'
    match = re.search(pattern4, url)
    if match:
        return match.group(1)
    
    return None

def get_audio_file_identifier(audio_url: Optional[str] = None, local_path: Optional[str] = None) -> str:
    """Generate a unique identifier for an audio file."""
    if audio_url:
        file_id = extract_google_drive_file_id(audio_url)
        if file_id:
            return f"{file_id}_MPE"  # MPE = Master Processing Engine
    
    if local_path:
        # Use filename or hash of path
        filename = Path(local_path).stem
        if filename and filename != "tmp" and len(filename) > 3:
            return f"{filename}_MPE"
        else:
            # Create hash of the full path
            path_hash = hashlib.md5(local_path.encode()).hexdigest()[:8]
            return f"local_{path_hash}_MPE"
    
    # Fallback
    import time
    return f"audio_{int(time.time())}_MPE"

def is_valid_google_drive_link(url: str) -> bool:
    """Check if URL is a valid Google Drive link."""
    if not url:
        return False
    
    try:
        parsed = urlparse(url)
        return (parsed.hostname in ['drive.google.com', 'docs.google.com'] and
                extract_google_drive_file_id(url) is not None)
    except:
        return False

def is_audio_file(filename: str) -> bool:
    """Check if filename has a valid audio extension."""
    from config.settings import AUDIO_EXTENSIONS
    return any(filename.lower().endswith(ext) for ext in AUDIO_EXTENSIONS)

def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes."""
    if not os.path.exists(file_path):
        return 0.0
    return os.path.getsize(file_path) / (1024 * 1024)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file system operations."""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200-len(ext)] + ext
    
    return filename

def create_temp_audio_file(suffix: str = '.wav') -> str:
    """Create a temporary audio file path."""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        return tmp_file.name

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.1f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.1f}s"

def validate_audio_file(file_path: str) -> dict:
    """Validate audio file and return status info."""
    result = {
        'valid': False,
        'exists': False,
        'size_mb': 0.0,
        'is_audio': False,
        'error': None
    }
    
    try:
        if not os.path.exists(file_path):
            result['error'] = 'File does not exist'
            return result
        
        result['exists'] = True
        result['size_mb'] = get_file_size_mb(file_path)
        
        if result['size_mb'] == 0:
            result['error'] = 'File is empty'
            return result
        
        if not is_audio_file(file_path):
            result['error'] = 'File is not a recognized audio format'
            return result
        
        result['is_audio'] = True
        result['valid'] = True
        
    except Exception as e:
        result['error'] = f'Validation error: {str(e)}'
    
    return result

def clean_text_for_processing(text: str) -> str:
    """Clean and normalize text for processing."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove special characters that might interfere with processing
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)
    
    return text.strip()
