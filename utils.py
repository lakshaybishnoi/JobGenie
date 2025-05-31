import pandas as pd
import os
from typing import List, Dict, Any
from datetime import datetime

def export_to_csv(data: List[Dict[str, Any]], filename: str = None) -> str:
    """Export data to CSV file."""
    if not data:
        raise ValueError("No data to export")
    
    # Generate filename if not provided
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"jobgenie_export_{timestamp}.csv"
    
    # Ensure .csv extension
    if not filename.endswith('.csv'):
        filename += '.csv'
    
    # Create DataFrame and export
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)
    
    return filename

def format_salary(salary_str: str) -> str:
    """Format salary string for better display."""
    if not salary_str or salary_str.lower() in ['not specified', 'n/a', '']:
        return "Not specified"
    
    return salary_str

def format_location(location_str: str) -> str:
    """Format location string for better display."""
    if not location_str or location_str.lower() in ['not specified', 'n/a', '']:
        return "Not specified"
    
    # Clean up common formatting issues
    location = location_str.strip()
    location = location.replace('  ', ' ')  # Remove double spaces
    
    return location

def format_date(date_str: str) -> str:
    """Format date string for better display."""
    if not date_str or date_str.lower() in ['not specified', 'n/a', '']:
        return "Not specified"
    
    # Try to parse and reformat common date formats
    common_formats = [
        "%Y-%m-%d",
        "%Y-%m-%d %H:%M:%S",
        "%m/%d/%Y",
        "%d/%m/%Y"
    ]
    
    for fmt in common_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime("%B %d, %Y")
        except ValueError:
            continue
    
    # If parsing fails, return original string cleaned up
    return date_str.strip()

def truncate_text(text: str, max_length: int = 100, add_ellipsis: bool = True) -> str:
    """Truncate text to specified length."""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    truncated = text[:max_length]
    if add_ellipsis:
        truncated += "..."
    
    return truncated

def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    import re
    
    if not text:
        return ""
    
    # Remove HTML tags
    clean_text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    clean_text = re.sub(r'\s+', ' ', clean_text)
    
    return clean_text.strip()

def calculate_match_score_color(score: float) -> str:
    """Return color code based on match score."""
    if score >= 80:
        return "#28a745"  # Green
    elif score >= 60:
        return "#ffc107"  # Yellow
    elif score >= 40:
        return "#fd7e14"  # Orange
    else:
        return "#dc3545"  # Red

def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_url(url: str) -> bool:
    """Validate URL format."""
    import re
    
    if not url:
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))

def get_file_size(file_path: str) -> str:
    """Get human-readable file size."""
    if not os.path.exists(file_path):
        return "0 B"
    
    size = os.path.getsize(file_path)
    
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    
    return f"{size:.1f} TB"

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations."""
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename

def format_number(number: float, decimal_places: int = 1) -> str:
    """Format number with proper decimal places and thousands separator."""
    if number == 0:
        return "0"
    
    if number < 1000:
        return f"{number:.{decimal_places}f}"
    elif number < 1000000:
        return f"{number/1000:.{decimal_places}f}K"
    elif number < 1000000000:
        return f"{number/1000000:.{decimal_places}f}M"
    else:
        return f"{number/1000000000:.{decimal_places}f}B"

def extract_keywords_from_text(text: str, min_length: int = 3, max_words: int = 50) -> List[str]:
    """Extract keywords from text for analysis."""
    import re
    from collections import Counter
    
    if not text:
        return []
    
    # Convert to lowercase and extract words
    text_lower = text.lower()
    words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text_lower)
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 
        'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 
        'that', 'these', 'those', 'they', 'them', 'their', 'there', 'where', 'when', 'why', 
        'how', 'what', 'who', 'which', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 
        'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'one', 
        'two', 'three', 'first', 'second', 'new', 'good', 'great', 'best'
    }
    
    # Filter out stop words
    filtered_words = [word for word in words if word not in stop_words]
    
    # Count frequency and get most common
    word_counts = Counter(filtered_words)
    keywords = [word for word, count in word_counts.most_common(max_words)]
    
    return keywords

def create_download_link(data: bytes, filename: str, link_text: str = "Download") -> str:
    """Create a download link for data."""
    import base64
    
    b64 = base64.b64encode(data).decode()
    return f'<a href="data:application/octet-stream;base64,{b64}" download="{filename}">{link_text}</a>'

def log_user_action(action: str, details: Dict[str, Any] = None):
    """Log user actions for analytics (simple file-based logging)."""
    import json
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'action': action,
        'details': details or {}
    }
    
    try:
        log_file = 'user_actions.log'
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        # Silently fail if logging doesn't work
        pass

def get_environment_info() -> Dict[str, str]:
    """Get information about the current environment."""
    import platform
    import sys
    
    return {
        'python_version': sys.version,
        'platform': platform.platform(),
        'processor': platform.processor(),
        'architecture': platform.architecture()[0],
        'system': platform.system(),
        'release': platform.release()
    }

def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
